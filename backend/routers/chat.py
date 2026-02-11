"""
Chat Router — Endpoint per la chat RAG multi-tenant.
Usa le dipendenze per iniettare TenantConfig nel RAGEngine.
"""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_user, get_current_tenant_config
from ..models.schemas import (
    CurrentUser,
    TenantConfig,
    ChatRequest,
    ChatResponse,
)
from ..services.rag_engine import RAGEngine

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    tenant_config: TenantConfig = Depends(get_current_tenant_config),
):
    """
    Endpoint principale della chat RAG.

    Flusso:
      1. Il frontend invia il token JWT nell'header Authorization
      2. get_current_user() verifica il JWT e identifica l'utente + org_id
      3. get_current_tenant_config() carica api_key e model_name dal DB
      4. TenantConfig viene iniettato nel RAGEngine
      5. RAGEngine usa la API key del TENANT per embeddings + LLM
      6. Risposta con answer + sources

    Il frontend NON conosce e NON invia la API key.
    Tutto è risolto server-side dal tenant dell'utente.
    """
    try:
        # Crea RAGEngine con la config del tenant (runtime injection)
        rag_engine = RAGEngine(tenant_config=tenant_config)

        # Esegui la pipeline RAG
        result = await rag_engine.chat(query=request.message)

        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            model_used=result["model_used"],
            conversation_id=request.conversation_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante la chat: {str(e)}",
        )


@router.get("/health")
async def chat_health(
    current_user: CurrentUser = Depends(get_current_user),
    tenant_config: TenantConfig = Depends(get_current_tenant_config),
):
    """
    Verifica che la configurazione del tenant sia valida.
    Utile per il frontend per mostrare se la chat è pronta.
    """
    return {
        "status": "ready",
        "model": tenant_config.model_name,
        "provider": tenant_config.provider,
        "org_id": str(tenant_config.org_id),
    }
