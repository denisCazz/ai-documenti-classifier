-- =====================================================
-- MVP-MISTRAL: Multi-Tenant RAG SaaS - Database Schema
-- Target: Supabase (PostgreSQL + pgvector)
-- =====================================================

-- Abilita estensione pgvector (necessaria per embeddings)
create extension if not exists vector;

-- =====================================================
-- 1. Tabella Organizzazioni (I Tenant / Gruppi)
-- =====================================================
create table organizations (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- =====================================================
-- 2. Tabella Configurazioni (Le API Key per gruppo)
--    Tabella separata per sicurezza delle chiavi
-- =====================================================
create table organization_settings (
  id uuid default gen_random_uuid() primary key,
  org_id uuid references organizations(id) on delete cascade not null,
  provider text default 'openai',        -- 'openai', 'anthropic', 'mistral', etc.
  api_key text,                           -- La chiave API specifica del cliente
  model_name text default 'gpt-4o-mini', -- Modello di default
  system_prompt text default 'Sei un assistente utile.', -- Prompt di sistema personalizzabile
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(org_id)
);

-- =====================================================
-- 3. Profili Utente (collega auth.users <-> organizations)
-- =====================================================
create table user_profiles (
  id uuid references auth.users on delete cascade primary key,
  org_id uuid references organizations(id),
  role text default 'member', -- 'admin', 'member'
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- =====================================================
-- 4. Documenti con Vector Embeddings (segregati per org)
-- =====================================================
create table documents (
  id uuid default gen_random_uuid() primary key,
  org_id uuid references organizations(id) not null,  -- FONDAMENTALE PER RLS
  name text not null,
  content text,                   -- Contenuto testuale estratto
  url text,                       -- URL del file originale (Supabase Storage)
  metadata jsonb default '{}'::jsonb,  -- Metadati extra (pagine, tipo file, ecc.)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- =====================================================
-- 5. Chunks dei documenti con embeddings
-- =====================================================
create table document_chunks (
  id uuid default gen_random_uuid() primary key,
  document_id uuid references documents(id) on delete cascade not null,
  org_id uuid references organizations(id) not null,  -- Denormalizzato per RLS
  content text not null,
  embedding vector(1536),          -- Per OpenAI text-embedding-3-small
  chunk_index integer not null,
  metadata jsonb default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Indice per ricerca vettoriale (cosine similarity)
create index on document_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- =====================================================
-- RLS (Row Level Security) - TASSATIVO
-- =====================================================

-- Helper function: ottieni org_id dell'utente corrente
create or replace function get_user_org_id()
returns uuid as $$
  select org_id from user_profiles where id = auth.uid();
$$ language sql security definer;

-- === Organizations ===
alter table organizations enable row level security;
create policy "Users can view own organization" on organizations
  for select using (id = get_user_org_id());

-- === Organization Settings ===
alter table organization_settings enable row level security;
create policy "Admins can manage own org settings" on organization_settings
  for all using (
    org_id = get_user_org_id()
    and exists (
      select 1 from user_profiles
      where id = auth.uid() and role = 'admin'
    )
  );
create policy "Members can view own org settings" on organization_settings
  for select using (org_id = get_user_org_id());

-- === User Profiles ===
alter table user_profiles enable row level security;
create policy "Users can view own profile" on user_profiles
  for select using (id = auth.uid());
create policy "Users can view org members" on user_profiles
  for select using (org_id = get_user_org_id());

-- === Documents ===
alter table documents enable row level security;
create policy "Users can manage own org documents" on documents
  for all using (org_id = get_user_org_id());

-- === Document Chunks ===
alter table document_chunks enable row level security;
create policy "Users can access own org chunks" on document_chunks
  for all using (org_id = get_user_org_id());

-- =====================================================
-- Funzione RPC per ricerca vettoriale (similarity search)
-- =====================================================
create or replace function match_documents(
  query_embedding vector(1536),
  match_threshold float default 0.7,
  match_count int default 5,
  p_org_id uuid default null
)
returns table (
  id uuid,
  document_id uuid,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    dc.id,
    dc.document_id,
    dc.content,
    dc.metadata,
    1 - (dc.embedding <=> query_embedding) as similarity
  from document_chunks dc
  where
    dc.org_id = coalesce(p_org_id, get_user_org_id())
    and 1 - (dc.embedding <=> query_embedding) > match_threshold
  order by dc.embedding <=> query_embedding
  limit match_count;
end;
$$;
