"""
FastAPI Dependencies per Multi-Tenancy.
Questo è il CUORE dell'architettura multi-tenant.

Flusso:
  1. get_current_user() → Verifica JWT Supabase, restituisce CurrentUser
  2. get_current_tenant_config() → Dato l'utente, carica config dal DB
  3. I routers iniettano TenantConfig nei services AI
"""

import jwt
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import get_settings, Settings
from .supabase_client import get_supabase_admin_client
from .models.schemas import CurrentUser, TenantConfig

# Security scheme per JWT Bearer
security = HTTPBearer()


# =====================================================
# 1. GET CURRENT USER — Verifica JWT Supabase
# =====================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """
    Verifica il token JWT di Supabase e restituisce l'utente corrente
    con il suo org_id e ruolo.

    Steps:
      1. Decodifica JWT con il secret di Supabase
      2. Estrae user_id dal token
      3. Query user_profiles per ottenere org_id e role
      4. Restituisce CurrentUser
    """
    token = credentials.credentials

    # Step 1: Decodifica e verifica JWT
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token scaduto. Effettua nuovamente il login.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido.",
        )

    # Step 2: Estrai user_id
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non contiene un user ID valido.",
        )

    user_email = payload.get("email")

    # Step 3: Query user_profiles per org_id e role
    supabase = get_supabase_admin_client()
    try:
        result = (
            supabase.table("user_profiles")
            .select("org_id, role")
            .eq("id", user_id)
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profilo utente non trovato. Contatta l'amministratore.",
        )

    profile = result.data
    if not profile or not profile.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utente non associato a nessuna organizzazione.",
        )

    # Step 4: Ritorna CurrentUser
    return CurrentUser(
        id=UUID(user_id),
        email=user_email,
        org_id=UUID(profile["org_id"]),
        role=profile["role"],
    )


# =====================================================
# 2. GET CURRENT TENANT CONFIG — Configurazione dinamica
# =====================================================

async def get_current_tenant_config(
    current_user: CurrentUser = Depends(get_current_user),
) -> TenantConfig:
    """
    Dato l'utente loggato, recupera la configurazione del suo tenant.

    Steps:
      1. Prende org_id dall'utente
      2. Query organization_settings per api_key, model_name, etc.
      3. Restituisce TenantConfig pronto per l'injection nei services

    Questo oggetto viene poi passato a rag_engine, ingestion, etc.
    MAI usare os.getenv() nei services AI!
    """
    supabase = get_supabase_admin_client()

    try:
        result = (
            supabase.table("organization_settings")
            .select("provider, api_key, model_name, system_prompt")
            .eq("org_id", str(current_user.org_id))
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configurazione organizzazione non trovata. "
                   "L'admin deve configurare le API key nelle Settings.",
        )

    settings_data = result.data
    if not settings_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nessuna configurazione trovata per questa organizzazione.",
        )

    if not settings_data.get("api_key"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API Key non configurata. L'admin deve inserirla nelle Settings.",
        )

    return TenantConfig(
        org_id=current_user.org_id,
        provider=settings_data.get("provider", "openai"),
        api_key=settings_data["api_key"],
        model_name=settings_data.get("model_name", "gpt-4o-mini"),
        system_prompt=settings_data.get("system_prompt", "Sei un assistente utile."),
    )


# =====================================================
# 3. REQUIRE ADMIN — Guard per endpoint admin-only
# =====================================================

async def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Verifica che l'utente sia admin della sua organizzazione."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono eseguire questa operazione.",
        )
    return current_user
