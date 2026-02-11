"""
MVP-MISTRAL: Pydantic Models & Schemas
Tutti i modelli per request/response e configurazioni tenant.
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# =====================================================
# Auth & User Models
# =====================================================

class UserProfile(BaseModel):
    """Profilo utente con info tenant."""
    id: UUID
    org_id: UUID
    role: str = "member"

    class Config:
        from_attributes = True


class CurrentUser(BaseModel):
    """Utente corrente dopo validazione JWT."""
    id: UUID
    email: Optional[str] = None
    org_id: UUID
    role: str = "member"


# =====================================================
# Tenant Configuration Models
# =====================================================

class TenantConfig(BaseModel):
    """
    Configurazione dinamica del tenant.
    Questo oggetto viene iniettato nei servizi AI a runtime.
    MAI usare os.getenv() — tutto viene dal DB.
    """
    org_id: UUID
    provider: str = "openai"
    api_key: str
    model_name: str = "gpt-4o-mini"
    system_prompt: str = "Sei un assistente utile."


class TenantSettingsUpdate(BaseModel):
    """Schema per aggiornamento settings dal frontend."""
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    provider: Optional[str] = None


class TenantSettingsResponse(BaseModel):
    """Response settings (API key mascherata per sicurezza)."""
    org_id: UUID
    provider: str
    model_name: str
    system_prompt: str
    api_key_configured: bool  # True se una key è presente, MAI esporre la key
    api_key_preview: Optional[str] = None  # Solo ultimi 4 caratteri: "sk-...ab1c"


# =====================================================
# Document Models
# =====================================================

class DocumentCreate(BaseModel):
    """Schema per upload documento."""
    name: str
    url: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[dict] = None


class DocumentResponse(BaseModel):
    """Response documento."""
    id: UUID
    org_id: UUID
    name: str
    url: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================
# Chat Models
# =====================================================

class ChatRequest(BaseModel):
    """Richiesta chat dall'utente."""
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Risposta chat con contesto RAG."""
    answer: str
    sources: list[dict] = []
    model_used: str
    conversation_id: Optional[str] = None


class ChunkResult(BaseModel):
    """Risultato di un chunk dalla similarity search."""
    id: UUID
    document_id: UUID
    content: str
    metadata: Optional[dict] = None
    similarity: float
