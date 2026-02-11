"""
Documents Router — Upload e gestione documenti.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from uuid import UUID

from ..dependencies import get_current_user, get_current_tenant_config
from ..models.schemas import (
    CurrentUser,
    TenantConfig,
    DocumentCreate,
    DocumentResponse,
)
from ..services.ingestion import IngestionService
from ..supabase_client import get_supabase_admin_client

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Lista tutti i documenti dell'organizzazione."""
    supabase = get_supabase_admin_client()
    result = (
        supabase.table("documents")
        .select("*")
        .eq("org_id", str(current_user.org_id))
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@router.post("/", response_model=DocumentResponse)
async def create_document(
    doc: DocumentCreate,
    current_user: CurrentUser = Depends(get_current_user),
    tenant_config: TenantConfig = Depends(get_current_tenant_config),
):
    """
    Crea un documento e avvia l'ingestione.
    Il contenuto viene chunked e indicizzato con embeddings.
    """
    supabase = get_supabase_admin_client()

    # Crea il record documento
    doc_data = {
        "org_id": str(current_user.org_id),
        "name": doc.name,
        "url": doc.url,
        "content": doc.content,
        "metadata": doc.metadata or {},
    }

    result = supabase.table("documents").insert(doc_data).execute()
    document = result.data[0]

    # Se c'è contenuto testuale, avvia ingestione
    if doc.content:
        try:
            ingestion = IngestionService(tenant_config=tenant_config)
            chunks_count = await ingestion.ingest_document(
                document_id=UUID(document["id"]),
                org_id=current_user.org_id,
                content=doc.content,
            )
            # Aggiorna metadata con info ingestione
            supabase.table("documents").update({
                "metadata": {**(doc.metadata or {}), "chunks_count": chunks_count}
            }).eq("id", document["id"]).execute()
        except Exception as e:
            # Log dell'errore ma non fallire la creazione documento
            print(f"Errore ingestione documento {document['id']}: {e}")

    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Elimina un documento e tutti i suoi chunks."""
    supabase = get_supabase_admin_client()

    # Verifica che il documento appartenga all'org dell'utente
    doc = (
        supabase.table("documents")
        .select("id, org_id")
        .eq("id", str(document_id))
        .eq("org_id", str(current_user.org_id))
        .single()
        .execute()
    )

    if not doc.data:
        raise HTTPException(status_code=404, detail="Documento non trovato.")

    # I chunks vengono eliminati in cascata (FK constraint)
    supabase.table("documents").delete().eq("id", str(document_id)).execute()

    return {"message": "Documento eliminato con successo."}
