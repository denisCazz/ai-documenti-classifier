/**
 * API Client — Comunicazione con il Backend FastAPI
 *
 * IMPORTANTE: Ogni richiesta include il JWT token di Supabase
 * nell'header Authorization. Il backend usa questo token per:
 * 1. Identificare l'utente
 * 2. Risolvere l'organizzazione (tenant)
 * 3. Caricare la API key corretta dal DB
 *
 * Il frontend NON conosce e NON invia la API key OpenAI.
 */

import { createClient } from "./supabase/client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Ottieni il token JWT corrente dell'utente.
 */
async function getAuthToken(): Promise<string | null> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token || null;
}

/**
 * Fetch wrapper con autenticazione automatica.
 * Aggiunge il JWT token a tutte le richieste.
 */
async function authFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = await getAuthToken();

  if (!token) {
    throw new Error("Non autenticato. Effettua il login.");
  }

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`, // <-- IL BACKEND USA QUESTO PER RISOLVERE IL TENANT
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: "Errore sconosciuto",
    }));
    throw new Error(error.detail || `Errore HTTP ${response.status}`);
  }

  return response;
}

// =====================================================
// API Functions
// =====================================================

/**
 * Chat — Invia un messaggio al RAG engine.
 * Il backend risolve automaticamente quale API key usare
 * basandosi sull'utente loggato e la sua organizzazione.
 */
export async function sendChatMessage(
  message: string,
  conversationId?: string
) {
  const response = await authFetch("/api/chat/", {
    method: "POST",
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });
  return response.json();
}

/**
 * Settings — Recupera le settings dell'organizzazione.
 * La API key è mascherata nella response.
 */
export async function getSettings() {
  const response = await authFetch("/api/settings/");
  return response.json();
}

/**
 * Settings — Aggiorna le settings (solo admin).
 */
export async function updateSettings(data: {
  api_key?: string;
  model_name?: string;
  system_prompt?: string;
  provider?: string;
}) {
  const response = await authFetch("/api/settings/", {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return response.json();
}

/**
 * Chat Health — Verifica che il tenant sia configurato per la chat.
 */
export async function checkChatHealth() {
  const response = await authFetch("/api/chat/health");
  return response.json();
}

/**
 * Documents — Lista documenti.
 */
export async function getDocuments() {
  const response = await authFetch("/api/documents/");
  return response.json();
}

/**
 * Documents — Crea documento con contenuto.
 */
export async function createDocument(data: {
  name: string;
  content: string;
  url?: string;
}) {
  const response = await authFetch("/api/documents/", {
    method: "POST",
    body: JSON.stringify(data),
  });
  return response.json();
}

/**
 * Documents — Elimina documento.
 */
export async function deleteDocument(documentId: string) {
  const response = await authFetch(`/api/documents/${documentId}`, {
    method: "DELETE",
  });
  return response.json();
}

/**
 * User Info — Recupera info utente corrente.
 */
export async function getCurrentUser() {
  const response = await authFetch("/api/settings/me");
  return response.json();
}
