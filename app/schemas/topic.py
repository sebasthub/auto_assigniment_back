from pydantic import BaseModel, ConfigDict, Field

class TopicBase(BaseModel):
    question: str = Field(min_length=1)
    response: str = Field(min_length=1)
    validated_response: str = Field(min_length=1)
    model_config = ConfigDict(str_strip_whitespace=True)


class TopicCreate(TopicBase):
    assignment_id: int = Field(gt=0)


class TopicGet(TopicCreate):
    id: int
    active: bool
    deleted: bool
    model_config = ConfigDict(from_attributes=True)


class PaginatedTopics(BaseModel):
    items: list[TopicGet]
    total: int
    page: int
    page_size: int
