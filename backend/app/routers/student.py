"""Student Router (/api/v1/student/*).

Protected by require_student dependency. Accessible exclusively to users with role='student'.
"""

from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_student
from app.models import User

router = APIRouter(
    prefix="/api/v1/student",
    tags=["Student"],
    dependencies=[Depends(require_student)],
)


@router.get("/dashboard", status_code=status.HTTP_200_OK)
def student_dashboard(student: User = Depends(require_student)) -> dict:
    """Returns student personal examination portal dashboard."""
    return {
        "status": "ok",
        "message": f"Chào mừng thí sinh {student.full_name}",
        "student_id": str(student.id),
        "username": student.username,
    }
