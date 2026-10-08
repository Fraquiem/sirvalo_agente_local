from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    question: str

@router.post("/query")
async def query_agent(request: ChatRequest):
    # TODO: Llamar al agente LangGraph
    return {"response": "Pregunta recibida", "question": request.question}
