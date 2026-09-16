from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.schemas.document import DocumentResponse, DocumentListResponse
from app.services.document_service import DocumentService
from app.api.deps import get_document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
):
    doc = await service.upload_document(file)
    return doc


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    offset: int = 0,
    limit: int = 20,
    service: DocumentService = Depends(get_document_service),
):
    return await service.list_documents(offset, limit)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    doc = await service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    deleted = await service.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
