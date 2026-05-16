from pydantic import BaseModel, ConfigDict, Field
from app.schemas.topic import TopicGet


class AssignmentBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    model_config = ConfigDict(str_strip_whitespace=True)

class AssignmentGet(AssignmentBase):
    id: int
    active: bool
    deleted: bool
    topics: list[TopicGet]
    model_config = ConfigDict(from_attributes=True)


class PaginatedAssignments(BaseModel):
    items: list[AssignmentGet]
    total: int
    page: int
    page_size: int

