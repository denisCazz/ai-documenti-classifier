"""
RAG Engine Service — Retrieval Augmented Generation.
Accetta TenantConfig come argomento obbligatorio (runtime injection).
NON legge .env per le API keys!
"""

from uuid import UUID
from openai import OpenAI

from ..models.schemas import TenantConfig, ChunkResult
from ..supabase_client import get_supabase_admin_client


class RAGEngine:
    """
    Motore RAG multi-tenant:
    1. Riceve una domanda dall'utente
    2. Genera embedding della domanda con la API key del TENANT
    3. Cerca i chunks più simili nel DB (filtrati per org_id)
    4. Costruisce il prompt con il contesto trovato
    5. Chiama il modello LLM con la API key del TENANT
    6. Restituisce la risposta con le fonti
    """

    def __init__(self, tenant_config: TenantConfig):
        """
        Inizializzazione con la configurazione del tenant.
        La API key viene dal DB, NON da os.getenv()!
        """
        self.config = tenant_config
        self.client = OpenAI(api_key=tenant_config.api_key)
        self.supabase = get_supabase_admin_client()

    def generate_query_embedding(self, query: str) -> list[float]:
        """Genera embedding per la query dell'utente."""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
        )
        return response.data[0].embedding

    async def search_similar_chunks(
        self,
        query_embedding: list[float],
        match_threshold: float = 0.7,
        match_count: int = 5,
    ) -> list[ChunkResult]:
        """
        Ricerca vettoriale nei chunks dell'organizzazione del tenant.
        Usa la funzione RPC match_documents del DB.
        """
        result = self.supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
                "p_org_id": str(self.config.org_id),
            },
        ).execute()

        if not result.data:
            return []

        return [
            ChunkResult(
                id=chunk["id"],
                document_id=chunk["document_id"],
                content=chunk["content"],
                metadata=chunk.get("metadata"),
                similarity=chunk["similarity"],
            )
            for chunk in result.data
        ]

    def build_rag_prompt(self, query: str, context_chunks: list[ChunkResult]) -> str:
        """
        Costruisce il prompt RAG con il contesto dei documenti trovati.
        Usa il system_prompt personalizzato del tenant.
        """
        if not context_chunks:
            context_text = "Nessun documento rilevante trovato nel database."
        else:
            context_parts = []
            for i, chunk in enumerate(context_chunks, 1):
                context_parts.append(
                    f"[Fonte {i}] (Similarità: {chunk.similarity:.2f})\n{chunk.content}"
                )
            context_text = "\n\n---\n\n".join(context_parts)

        return f"""Contesto dai documenti dell'organizzazione:

{context_text}

---

Domanda dell'utente: {query}

Rispondi basandoti ESCLUSIVAMENTE sul contesto fornito sopra. 
Se il contesto non contiene informazioni sufficienti, dillo chiaramente.
Cita le fonti quando possibile (es. [Fonte 1])."""

    async def chat(
        self,
        query: str,
        match_threshold: float = 0.5,
        match_count: int = 5,
    ) -> dict:
        """
        Pipeline RAG completa:
        1. Embedding della query
        2. Ricerca chunks simili
        3. Costruzione prompt
        4. Chiamata LLM
        5. Risposta con fonti

        Returns:
            dict con 'answer', 'sources', 'model_used'
        """
        # Step 1: Embedding della query
        query_embedding = self.generate_query_embedding(query)

        # Step 2: Ricerca chunks simili (filtrati per org_id)
        chunks = await self.search_similar_chunks(
            query_embedding,
            match_threshold=match_threshold,
            match_count=match_count,
        )

        # Step 3: Costruisci prompt RAG
        rag_prompt = self.build_rag_prompt(query, chunks)

        # Step 4: Chiama LLM con la config del tenant
        response = self.client.chat.completions.create(
            model=self.config.model_name,
            messages=[
                {
                    "role": "system",
                    "content": self.config.system_prompt,
                },
                {
                    "role": "user",
                    "content": rag_prompt,
                },
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        answer = response.choices[0].message.content

        # Step 5: Prepara fonti per la response
        sources = [
            {
                "document_id": str(chunk.document_id),
                "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "similarity": round(chunk.similarity, 3),
            }
            for chunk in chunks
        ]

        return {
            "answer": answer,
            "sources": sources,
            "model_used": self.config.model_name,
        }
