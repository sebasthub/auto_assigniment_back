from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies.auth import get_current_user
from app.models.assignment import Assignment
from app.models.topic import Topic
from app.models.user import User
from app.schemas.topic import PaginatedTopics, TopicBase, TopicCreate, TopicGet

router = APIRouter(tags=["Topics"])
CurrentUser = Annotated[User, Depends(get_current_user)]

async def get_assignment_or_404(assignment_id: int, user: User) -> Assignment:
    assignment = await Assignment.get_or_none(id=assignment_id, active=True, deleted=False, user=user)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


async def get_topic_or_404(topic_id: int, user: User) -> Topic:
    topic = await Topic.get_or_none(id=topic_id, active=True, deleted=False, assignment__user=user)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.get("/topics", response_model=PaginatedTopics)
async def get_topics(
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    total = await Topic.filter(active=True, deleted=False, assignment__user=current_user).count()
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
async def create_topic(topic: TopicCreate, current_user: CurrentUser):
    await get_assignment_or_404(topic.assignment_id, current_user)
    topic = await Topic.create(**topic.model_dump())
    return TopicGet.model_validate(topic)


@router.get("/topics/{topic_id}", response_model=TopicGet)
async def get_topic(topic_id: int, current_user: CurrentUser):
    topic = await get_topic_or_404(topic_id, current_user)
    return TopicGet.model_validate(topic)


@router.put("/topics/{topic_id}", response_model=TopicGet)
async def update_topic(topic_id: int, topic: TopicBase, current_user: CurrentUser):
    existing_topic = await get_topic_or_404(topic_id, current_user)
    await Topic.filter(id=existing_topic.id).update(**topic.model_dump())
    existing_topic = await get_topic_or_404(topic_id, current_user)
    return TopicGet.model_validate(existing_topic)


@router.delete("/topics/{topic_id}", response_model=TopicGet)
async def delete_topic(topic_id: int, current_user: CurrentUser):
    topic = await get_topic_or_404(topic_id, current_user)
    await Topic.filter(id=topic.id).update(active=False, deleted=True)
    topic.active = False
    topic.deleted = True
    return TopicGet.model_validate(topic)
