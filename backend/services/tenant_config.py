"""
TenantConfigService — Gestione configurazioni per organizzazione.
Operazioni CRUD sulle settings del tenant (organization_settings).
"""

from uuid import UUID
from typing import Optional

from ..supabase_client import get_supabase_admin_client
from ..models.schemas import TenantConfig, TenantSettingsResponse, TenantSettingsUpdate


class TenantConfigService:
    """
    Service per gestire le configurazioni di un'organizzazione.
    Usato dai routers per leggere/aggiornare settings.
    """

    @staticmethod
    def get_config(org_id: UUID) -> Optional[TenantConfig]:
        """Recupera la configurazione completa di un tenant."""
        supabase = get_supabase_admin_client()
        result = (
            supabase.table("organization_settings")
            .select("*")
            .eq("org_id", str(org_id))
            .single()
            .execute()
        )

        data = result.data
        if not data:
            return None

        return TenantConfig(
            org_id=org_id,
            provider=data.get("provider", "openai"),
            api_key=data.get("api_key", ""),
            model_name=data.get("model_name", "gpt-4o-mini"),
            system_prompt=data.get("system_prompt", "Sei un assistente utile."),
        )

    @staticmethod
    def get_safe_settings(org_id: UUID) -> Optional[TenantSettingsResponse]:
        """
        Recupera settings con API key MASCHERATA.
        Da usare per le response al frontend.
        MAI esporre la key completa!
        """
        supabase = get_supabase_admin_client()
        result = (
            supabase.table("organization_settings")
            .select("org_id, provider, model_name, system_prompt, api_key")
            .eq("org_id", str(org_id))
            .single()
            .execute()
        )

        data = result.data
        if not data:
            return None

        api_key = data.get("api_key")
        api_key_configured = bool(api_key)
        api_key_preview = None
        if api_key and len(api_key) > 8:
            api_key_preview = f"{api_key[:3]}...{api_key[-4:]}"

        return TenantSettingsResponse(
            org_id=UUID(data["org_id"]),
            provider=data.get("provider", "openai"),
            model_name=data.get("model_name", "gpt-4o-mini"),
            system_prompt=data.get("system_prompt", "Sei un assistente utile."),
            api_key_configured=api_key_configured,
            api_key_preview=api_key_preview,
        )

    @staticmethod
    def update_settings(org_id: UUID, updates: TenantSettingsUpdate) -> TenantSettingsResponse:
        """
        Aggiorna le settings dell'organizzazione.
        Solo i campi forniti vengono aggiornati (partial update).
        """
        supabase = get_supabase_admin_client()

        # Costruisci solo i campi da aggiornare
        update_data = {}
        if updates.api_key is not None:
            update_data["api_key"] = updates.api_key
        if updates.model_name is not None:
            update_data["model_name"] = updates.model_name
        if updates.system_prompt is not None:
            update_data["system_prompt"] = updates.system_prompt
        if updates.provider is not None:
            update_data["provider"] = updates.provider

        if not update_data:
            # Nessun campo da aggiornare, restituisci settings correnti
            return TenantConfigService.get_safe_settings(org_id)

        # Upsert: crea se non esiste, aggiorna se esiste
        result = (
            supabase.table("organization_settings")
            .upsert({
                "org_id": str(org_id),
                **update_data,
            }, on_conflict="org_id")
            .execute()
        )

        # Restituisci settings aggiornate (mascherate)
        return TenantConfigService.get_safe_settings(org_id)

    @staticmethod
    def create_default_settings(org_id: UUID) -> None:
        """Crea settings di default per una nuova organizzazione."""
        supabase = get_supabase_admin_client()
        supabase.table("organization_settings").insert({
            "org_id": str(org_id),
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "system_prompt": "Sei un assistente utile.",
        }).execute()
