from fastapi import APIRouter

from app.routes import assignment, topic

router = APIRouter()

router.include_router(assignment.router)
router.include_router(topic.router)
