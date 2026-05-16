from fastapi import APIRouter, HTTPException, Query

from app.models.assignment import Assignment
from app.models.document_record import DocumentRecord
from app.schemas.assignment import AssignmentBase, AssignmentGet, PaginatedAssignments
from app.services.document_service import delete_assignment_document

router = APIRouter(tags=["Assignments"])


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


async def get_assignment_or_404(assignment_id: int) -> Assignment:
    assignment = await Assignment.get_or_none(id=assignment_id, active=True, deleted=False)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.get("/assignments", response_model=PaginatedAssignments)
async def get_assignments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    total = await Assignment.filter(active=True, deleted=False).count()
    assignments = (
        await Assignment.filter(active=True, deleted=False)
        .prefetch_related("topics")
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
async def create_assignment(assignment: AssignmentBase):
    assignment = await Assignment.create(**assignment.model_dump())
    return await serialize_assignment(assignment)


@router.get("/assignments/{assignment_id}", response_model=AssignmentGet)
async def get_assignment(assignment_id: int):
    assignment = await get_assignment_or_404(assignment_id)
    return await serialize_assignment(assignment)


@router.put("/assignments/{assignment_id}", response_model=AssignmentGet)
async def update_assignment(assignment_id: int, assignment: AssignmentBase):
    existing_assignment = await get_assignment_or_404(assignment_id)
    await Assignment.filter(id=existing_assignment.id).update(**assignment.model_dump())
    existing_assignment = await get_assignment_or_404(assignment_id)
    return await serialize_assignment(existing_assignment)


@router.delete("/assignments/{assignment_id}", response_model=AssignmentGet)
async def delete_assignment(assignment_id: int):
    assignment = await get_assignment_or_404(assignment_id)
    await delete_assignment_document(assignment.id)
    await assignment.topics.filter(deleted=False).update(active=False, deleted=True)
    await Assignment.filter(id=assignment.id).update(active=False, deleted=True)
    assignment.active = False
    assignment.deleted = True
    return await serialize_assignment(assignment)
