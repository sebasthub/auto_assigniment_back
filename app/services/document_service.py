from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from fastapi import UploadFile

from app.config.settings import settings
from app.models.assignment import Assignment
from app.models.document_record import DocumentRecord
from app.schemas.document_record import DocumentSummary, UploadResponse
from app.services.storage import create_document_storage


DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


class DocumentServiceError(Exception):
    pass


class AssignmentNotFoundError(DocumentServiceError):
    pass


class DocumentNotFoundError(DocumentServiceError):
    pass


class InvalidDocumentError(DocumentServiceError):
    pass


async def list_documents() -> list[DocumentSummary]:
    records = await DocumentRecord.filter(deleted=False).order_by("-updated_at")
    return [
        DocumentSummary(
            id=record.uuid,
            original_name=record.original_name,
            created_at=record.created_at,
            updated_at=record.updated_at,
            download_url=settings.browser_url(f"/documents/{record.uuid}/download"),
        )
        for record in records
    ]


async def upload_assignment_document(
    assignment_id: int,
    file: UploadFile,
) -> UploadResponse:
    _ensure_docx(file.filename)
    contents = await file.read()
    if not contents:
        raise InvalidDocumentError("O arquivo esta vazio.")

    assignment = await Assignment.get_or_none(
        id=assignment_id,
        active=True,
        deleted=False,
    )
    if assignment is None:
        raise AssignmentNotFoundError

    record = await DocumentRecord.get_or_none(assignment_id=assignment.id)
    if record is None:
        document_id = uuid4()
        record = await DocumentRecord.create(
            uuid=document_id,
            original_name=_safe_filename(file.filename, f"{document_id}.docx"),
            filename=f"{document_id}.docx",
            key=build_document_key(document_id),
            assignment=assignment,
        )
    else:
        record.original_name = _safe_filename(file.filename, record.filename)
        record.key = build_document_key(record.uuid)
        record.deleted = False
        record.updated_at = datetime.now(UTC)
        await record.save(
            update_fields=["original_name", "key", "deleted", "updated_at"]
        )

    await create_document_storage().save_document(
        record.filename,
        contents,
        DOCX_MEDIA_TYPE,
    )
    return UploadResponse(
        id=record.uuid,
        original_name=record.original_name,
        editor_url=settings.browser_url(f"/documents/{record.uuid}/config"),
    )


async def get_editor_config(document_id: str) -> dict:
    record = await get_document_record(document_id)
    if not await create_document_storage().document_exists(record.filename):
        raise DocumentNotFoundError

    record.key = build_document_key(record.uuid)
    record.updated_at = datetime.now(UTC)
    await record.save(update_fields=["key", "updated_at"])

    return {
        "documentServerUrl": settings.onlyoffice_url.rstrip("/"),
        "config": {
            "document": {
                "fileType": "docx",
                "key": record.key,
                "title": record.original_name,
                "url": settings.public_url(f"/documents/{record.uuid}/download"),
                "permissions": {
                    "download": True,
                    "edit": True,
                    "print": True,
                    "review": True,
                },
            },
            "documentType": "word",
            "editorConfig": {
                "callbackUrl": settings.public_url(
                    f"/onlyoffice/callback/{record.uuid}"
                ),
                "lang": "pt-BR",
                "mode": "edit",
                "user": {
                    "id": "local-user",
                    "name": "Usuario local",
                },
            },
            "height": "100%",
            "type": "desktop",
            "width": "100%",
        },
    }


async def get_document_file(document_id: str) -> tuple[DocumentRecord, bytes]:
    record = await get_document_record(document_id)
    try:
        contents = await create_document_storage().read_document(record.filename)
    except FileNotFoundError as exc:
        raise DocumentNotFoundError from exc
    return record, contents


async def handle_onlyoffice_callback(document_id: str, payload: dict) -> dict:
    if payload.get("status") not in {2, 6}:
        return {"error": 0}

    download_url = payload.get("url")
    if not download_url:
        return {"error": 1}

    record = await _get_document_record_or_none(document_id)
    if record is None:
        return {"error": 1}

    try:
        contents = await download_callback_file(download_url)
        await create_document_storage().save_document(
            record.filename,
            contents,
            DOCX_MEDIA_TYPE,
        )
        record.key = build_document_key(record.uuid)
        record.updated_at = datetime.now(UTC)
        await record.save(update_fields=["key", "updated_at"])
    except Exception:
        return {"error": 1}

    return {"error": 0}


async def delete_assignment_document(assignment_id: int) -> None:
    record = await DocumentRecord.get_or_none(
        assignment_id=assignment_id,
        deleted=False,
    )
    if record is None:
        return

    await create_document_storage().delete_document(record.filename)
    record.deleted = True
    record.updated_at = datetime.now(UTC)
    await record.save(update_fields=["deleted", "updated_at"])


async def get_document_record(document_id: str) -> DocumentRecord:
    record = await _get_document_record_or_none(document_id)
    if record is None:
        raise DocumentNotFoundError
    return record


async def download_callback_file(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


def build_document_key(document_id: UUID) -> str:
    return f"{document_id.hex}-{uuid4().hex[:16]}"


async def _get_document_record_or_none(document_id: str) -> DocumentRecord | None:
    try:
        document_uuid = UUID(document_id)
    except ValueError:
        return None
    return await DocumentRecord.get_or_none(uuid=document_uuid, deleted=False)


def _ensure_docx(filename: str | None) -> None:
    if not filename or not filename.lower().endswith(".docx"):
        raise InvalidDocumentError("Envie um arquivo .docx.")


def _safe_filename(filename: str | None, default: str) -> str:
    if not filename:
        return default
    return Path(filename).name
