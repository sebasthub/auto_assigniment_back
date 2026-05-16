from fastapi import APIRouter

from app.routes import assignment, auth, topic

router = APIRouter()

router.include_router(assignment.router)
router.include_router(auth.router)
router.include_router(topic.router)
