"""
Ingestion Service — Processa e indicizza documenti.
Accetta TenantConfig come argomento obbligatorio (runtime injection).
NON legge .env per le API keys!
"""

from uuid import UUID
from typing import Optional
from openai import OpenAI

from ..models.schemas import TenantConfig
from ..supabase_client import get_supabase_admin_client


class IngestionService:
    """
    Servizio per ingestione documenti:
    1. Riceve il testo di un documento
    2. Lo spezza in chunks
    3. Genera embeddings con la API key del TENANT
    4. Salva chunks + embeddings nel DB
    """

    def __init__(self, tenant_config: TenantConfig):
        """
        Inizializza con la configurazione del tenant.
        La API key viene dal DB, NON da os.getenv()!
        """
        self.config = tenant_config
        self.client = OpenAI(api_key=tenant_config.api_key)
        self.supabase = get_supabase_admin_client()

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """
        Divide il testo in chunks con overlap.
        Strategia semplice per MVP; in produzione usare tiktoken o LangChain splitters.
        """
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())
            start = end - overlap
        return [c for c in chunks if c]  # Rimuovi chunks vuoti

    def generate_embedding(self, text: str) -> list[float]:
        """
        Genera embedding per un singolo testo.
        Usa la API key del TENANT (iniettata nel costruttore).
        """
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    async def ingest_document(
        self,
        document_id: UUID,
        org_id: UUID,
        content: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> int:
        """
        Pipeline completa di ingestione:
        1. Chunking del testo
        2. Generazione embeddings per ogni chunk
        3. Salvataggio nel DB con org_id per RLS

        Returns: numero di chunks processati
        """
        # Step 1: Chunking
        chunks = self.chunk_text(content, chunk_size, overlap)

        if not chunks:
            return 0

        # Step 2 & 3: Embedding + salvataggio per ogni chunk
        records = []
        for i, chunk_text in enumerate(chunks):
            embedding = self.generate_embedding(chunk_text)
            records.append({
                "document_id": str(document_id),
                "org_id": str(org_id),
                "content": chunk_text,
                "embedding": embedding,
                "chunk_index": i,
                "metadata": {
                    "chunk_size": chunk_size,
                    "overlap": overlap,
                    "total_chunks": len(chunks),
                },
            })

        # Batch insert
        self.supabase.table("document_chunks").insert(records).execute()

        return len(records)

    async def delete_document_chunks(self, document_id: UUID) -> None:
        """Rimuovi tutti i chunks di un documento (per re-ingestione)."""
        self.supabase.table("document_chunks").delete().eq(
            "document_id", str(document_id)
        ).execute()
