"""
Configurazione applicazione backend.
Variabili d'ambiente per il BACKEND stesso (non per i clienti!).
Le chiavi API dei clienti vengono dal DB via TenantConfigService.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Settings del backend.
    NOTA: Queste NON sono le chiavi dei clienti.
    Le chiavi dei clienti sono in organization_settings nel DB.
    """

    # Supabase (per il backend stesso)
    supabase_url: str
    supabase_service_role_key: str  # Service role per operazioni admin
    supabase_jwt_secret: str        # Per verificare i JWT

    # App
    app_name: str = "MVP-MISTRAL RAG"
    debug: bool = False
    cors_origins: str = "http://localhost:3000"  # Comma-separated

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Singleton cached delle settings."""
    return Settings()
