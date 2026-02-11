"""
Settings Router — Gestione configurazioni organizzazione.
Solo admin possono modificare (require_admin).
I member possono solo leggere (con API key mascherata).
"""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_user, require_admin
from ..models.schemas import (
    CurrentUser,
    TenantSettingsUpdate,
    TenantSettingsResponse,
)
from ..services.tenant_config import TenantConfigService

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/", response_model=TenantSettingsResponse)
async def get_settings(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Recupera le settings dell'organizzazione dell'utente.
    La API key è MASCHERATA nella response (es. "sk-...ab1c").
    Qualsiasi member può leggere.
    """
    settings = TenantConfigService.get_safe_settings(current_user.org_id)

    if not settings:
        # Se non ci sono settings, restituisci un default vuoto
        return TenantSettingsResponse(
            org_id=current_user.org_id,
            provider="openai",
            model_name="gpt-4o-mini",
            system_prompt="Sei un assistente utile.",
            api_key_configured=False,
            api_key_preview=None,
        )

    return settings


@router.put("/", response_model=TenantSettingsResponse)
async def update_settings(
    updates: TenantSettingsUpdate,
    current_user: CurrentUser = Depends(require_admin),  # Solo admin!
):
    """
    Aggiorna le settings dell'organizzazione.
    SOLO ADMIN possono modificare.

    Campi aggiornabili:
    - api_key: La chiave API OpenAI (o altro provider)
    - model_name: Il modello da usare (es. gpt-4o-mini, gpt-4o)
    - system_prompt: Il prompt di sistema personalizzato
    - provider: Il provider AI (openai, anthropic, etc.)
    """
    try:
        result = TenantConfigService.update_settings(
            org_id=current_user.org_id,
            updates=updates,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore aggiornamento settings: {str(e)}",
        )


@router.get("/me")
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Restituisce info sull'utente corrente e il suo ruolo."""
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "org_id": str(current_user.org_id),
        "role": current_user.role,
    }
