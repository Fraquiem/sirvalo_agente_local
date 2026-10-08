from fastapi import APIRouter, File, UploadFile
from typing import List

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # TODO: Implementar procesamiento de archivo
    return {"filename": file.filename, "status": "processing"}

@router.get("/")
async def list_documents():
    # TODO: Listar documentos del usuario
    return {"documents": []}
