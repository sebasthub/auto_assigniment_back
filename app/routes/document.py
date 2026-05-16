from urllib.parse import quote

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.schemas.document_record import DocumentSummary, UploadResponse
from app.services.document_service import (
    AssignmentNotFoundError,
    DOCX_MEDIA_TYPE,
    DocumentNotFoundError,
    InvalidDocumentError,
    get_document_file,
    get_editor_config,
    list_documents,
    upload_assignment_document,
)

router = APIRouter(tags=["Documents"])


@router.get("/documents", response_model=list[DocumentSummary])
async def get_documents():
    return await list_documents()


@router.post(
    "/assignments/{assignment_id}/document",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document_for_assignment(
    assignment_id: int,
    file: UploadFile = File(...),
):
    try:
        return await upload_assignment_document(assignment_id, file)
    except AssignmentNotFoundError:
        raise HTTPException(status_code=404, detail="Assignment not found")
    except InvalidDocumentError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/documents/{document_id}/config")
async def get_document_config(document_id: str):
    try:
        return await get_editor_config(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/documents/{document_id}/download")
async def download_document(document_id: str):
    try:
        record, contents = await get_document_file(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = quote(record.original_name)
    return Response(
        content=contents,
        media_type=DOCX_MEDIA_TYPE,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
        },
    )
