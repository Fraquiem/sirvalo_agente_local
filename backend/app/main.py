from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.controllers import auth, chat, documents

app = FastAPI(
    title="Agente RAG de Cócteles API",
    description="API base para el chatbot de cócteles con FastAPI, LangChain, LangGraph y Supabase",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(documents.router)

@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "Agente RAG de Cócteles API",
        "version": "1.0.0",
    }
