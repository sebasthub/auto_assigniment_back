from fastapi import APIRouter, Request

from app.services.document_service import handle_onlyoffice_callback

router = APIRouter(tags=["OnlyOffice"])


@router.post("/onlyoffice/callback/{document_id}")
async def onlyoffice_callback(document_id: str, request: Request) -> dict:
    return await handle_onlyoffice_callback(document_id, await request.json())
