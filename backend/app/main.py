from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title="Agente RAG de Cócteles API",
    description="API base para el chatbot de cócteles con FastAPI, LangChain, LangGraph y Supabase",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "Agente RAG de Cócteles API",
        "version": "1.0.0"
    }
