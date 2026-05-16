from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UploadResponse(BaseModel):
    id: UUID
    original_name: str
    editor_url: str


class DocumentSummary(BaseModel):
    id: UUID
    original_name: str
    created_at: datetime
    updated_at: datetime
    download_url: str


class AssignmentDocumentRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_name: str
    filename: str
    key: str
    created_at: datetime
    updated_at: datetime
