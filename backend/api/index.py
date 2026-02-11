"""
Vercel Serverless Entry Point.
Vercel cerca un file in api/ che esporta una variabile 'app' ASGI/WSGI.
Questo file re-esporta la FastAPI app dal modulo backend.
"""

# Vercel richiede che gli import siano relativi alla root del progetto.
# Quando deployi la cartella backend/ come root del progetto Vercel,
# i moduli vengono importati senza il prefisso 'backend.'.

import sys
import os

# Aggiungi la directory parent al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import moduli backend direttamente (no relative imports su Vercel)
from config import get_settings
from routers import chat_router, settings_router, documents_router

# Init app
app = FastAPI(
    title="MVP-MISTRAL RAG API",
    description="Multi-Tenant Document Intelligence & RAG SaaS",
    version="0.1.0",
)

# CORS — includi URL di produzione
settings = get_settings()
origins = [origin.strip() for origin in settings.cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra routers
app.include_router(chat_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(documents_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "service": "MVP-MISTRAL RAG API",
        "version": "0.1.0",
        "status": "running",
        "runtime": "vercel-serverless",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
