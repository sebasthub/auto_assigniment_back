from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies.auth import get_current_user
from app.models.assignment import Assignment
from app.models.document_record import DocumentRecord
from app.models.user import User
from app.schemas.assignment import AssignmentBase, AssignmentGet, PaginatedAssignments
from app.services.document_service import delete_assignment_document

router = APIRouter(tags=["Assignments"])
CurrentUser = Annotated[User, Depends(get_current_user)]


async def serialize_assignment(assignment: Assignment) -> AssignmentGet:
    topics = await assignment.topics.filter(active=True, deleted=False)
    document_record = await DocumentRecord.get_or_none(
        assignment_id=assignment.id,
        deleted=False,
    )
    return AssignmentGet.model_validate(
        {
            "id": assignment.id,
            "title": assignment.title,
            "active": assignment.active,
            "deleted": assignment.deleted,
            "topics": topics,
            "document_record": document_record,
        }
    )


async def get_assignment_or_404(assignment_id: int, user: User) -> Assignment:
    assignment = await Assignment.get_or_none(
        id=assignment_id,
        user_id=user.id,
        active=True,
        deleted=False,
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.get("/assignments", response_model=PaginatedAssignments)
async def get_assignments(
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    assignment_filter = {
        "user_id": current_user.id,
        "active": True,
        "deleted": False,
    }
    total = await Assignment.filter(**assignment_filter).count()
    assignments = (
        await Assignment.filter(**assignment_filter)
        .prefetch_related("topics")
        .order_by("id")
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return PaginatedAssignments(
        items=[await serialize_assignment(a) for a in assignments],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/assignments", response_model=AssignmentGet)
async def create_assignment(
    assignment: AssignmentBase,
    current_user: CurrentUser,
):
    assignment = await Assignment.create(**assignment.model_dump(), user=current_user)
    return await serialize_assignment(assignment)


@router.get("/assignments/{assignment_id}", response_model=AssignmentGet)
async def get_assignment(
    assignment_id: int,
    current_user: CurrentUser,
):
    assignment = await get_assignment_or_404(assignment_id, current_user)
    return await serialize_assignment(assignment)


@router.put("/assignments/{assignment_id}", response_model=AssignmentGet)
async def update_assignment(
    assignment_id: int,
    assignment: AssignmentBase,
    current_user: CurrentUser,
):
    existing_assignment = await get_assignment_or_404(assignment_id, current_user)
    await Assignment.filter(id=existing_assignment.id).update(**assignment.model_dump())
    existing_assignment = await get_assignment_or_404(assignment_id, current_user)
    return await serialize_assignment(existing_assignment)


@router.delete("/assignments/{assignment_id}", response_model=AssignmentGet)
async def delete_assignment(
    assignment_id: int,
    current_user: CurrentUser,
):
    assignment = await get_assignment_or_404(assignment_id, current_user)
    await delete_assignment_document(assignment.id)
    await assignment.topics.filter(deleted=False).update(active=False, deleted=True)
    await Assignment.filter(id=assignment.id).update(active=False, deleted=True)
    assignment.active = False
    assignment.deleted = True
    return await serialize_assignment(assignment)
