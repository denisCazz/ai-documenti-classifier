"""
Client Supabase per il Backend.
Usa la SERVICE_ROLE_KEY per bypassare RLS quando necessario
(es. per leggere organization_settings in fase di dependency injection).
"""

from supabase import create_client, Client
from .config import get_settings


def get_supabase_admin_client() -> Client:
    """
    Client Supabase con service_role_key.
    ATTENZIONE: bypassa RLS — usare solo internamente nel backend.
    """
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )


def get_supabase_client_for_user(access_token: str) -> Client:
    """
    Client Supabase autenticato con il token dell'utente.
    Rispetta RLS — usare per operazioni user-facing.
    """
    settings = get_settings()
    client = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,  # Anon key in produzione
    )
    # Imposta l'header Authorization per rispettare RLS
    client.postgrest.auth(access_token)
    return client
