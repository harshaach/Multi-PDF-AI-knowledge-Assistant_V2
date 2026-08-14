import shutil
import uuid
from typing import List

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.config.settings import settings
from app.services.pdf_service import PDFService
from app.services.rag_services import RAGService
from app.services.work_spacemanager import workspace_manager

router = APIRouter()

pdf_service = PDFService()


class QueryRequest(BaseModel):
    question: str
    top_k: int = settings.DEFAULT_TOP_K


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]


class UploadResponse(BaseModel):
    filename: str
    chunks_indexed: int


@router.get("/health")
def health():
    return {
        "status": "ok",
        "workspaces": len(workspace_manager.workspaces),
    }


@router.get("/documents")
def documents(chat_id: str = Query(...)):

    workspace = workspace_manager.get_workspace(chat_id)

    return {
        "documents": workspace.documents
    }


@router.post("/upload", response_model=List[UploadResponse])
async def upload_pdfs(
    chat_id: str = Query(...),
    files: List[UploadFile] = File(...)
):

    workspace = workspace_manager.get_workspace(chat_id)

    rag_service = RAGService(
        embedding_service=workspace.embedding_service,
        api_key=settings.GEMINI_API_KEY,
    )

    results = []

    for file in files:

        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename} is not a PDF",
            )

        temp_path = (
            settings.UPLOAD_DIR
            / f"{uuid.uuid4().hex}_{file.filename}"
        )

        try:

            with temp_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            _, chunks = pdf_service.extract_chunks(temp_path)

            workspace.embedding_service.add_chunks(chunks)

            if file.filename not in workspace.documents:
                workspace.documents.append(file.filename)

            results.append(
                UploadResponse(
                    filename=file.filename,
                    chunks_indexed=len(chunks),
                )
            )

        finally:

            if temp_path.exists():
                temp_path.unlink()

    return results


@router.post("/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    chat_id: str = Query(...),
):

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    workspace = workspace_manager.get_workspace(chat_id)

    rag_service = RAGService(
        embedding_service=workspace.embedding_service,
        api_key=settings.GEMINI_API_KEY,
    )

    result = rag_service.ask(
        request.question,
        request.top_k,
    )

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
    )