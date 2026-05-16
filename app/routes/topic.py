from fastapi import APIRouter, HTTPException, Query

from app.models.assignment import Assignment
from app.models.topic import Topic
from app.schemas.topic import PaginatedTopics, TopicBase, TopicCreate, TopicGet

router = APIRouter(tags=["Topics"])


async def get_assignment_or_404(assignment_id: int) -> Assignment:
    assignment = await Assignment.get_or_none(id=assignment_id, active=True, deleted=False)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


async def get_topic_or_404(topic_id: int) -> Topic:
    topic = await Topic.get_or_none(id=topic_id, active=True, deleted=False)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.get("/topics", response_model=PaginatedTopics)
async def get_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    total = await Topic.filter(active=True, deleted=False).count()
    topics = (
        await Topic.filter(active=True, deleted=False)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return PaginatedTopics(
        items=[TopicGet.model_validate(t) for t in topics],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/topics", response_model=TopicGet)
async def create_topic(topic: TopicCreate):
    await get_assignment_or_404(topic.assignment_id)
    topic = await Topic.create(**topic.model_dump())
    return TopicGet.model_validate(topic)


@router.get("/topics/{topic_id}", response_model=TopicGet)
async def get_topic(topic_id: int):
    topic = await get_topic_or_404(topic_id)
    return TopicGet.model_validate(topic)


@router.put("/topics/{topic_id}", response_model=TopicGet)
async def update_topic(topic_id: int, topic: TopicBase):
    existing_topic = await get_topic_or_404(topic_id)
    await Topic.filter(id=existing_topic.id).update(**topic.model_dump())
    existing_topic = await get_topic_or_404(topic_id)
    return TopicGet.model_validate(existing_topic)


@router.delete("/topics/{topic_id}", response_model=TopicGet)
async def delete_topic(topic_id: int):
    topic = await get_topic_or_404(topic_id)
    await Topic.filter(id=topic.id).update(active=False, deleted=True)
    topic.active = False
    topic.deleted = True
    return TopicGet.model_validate(topic)
