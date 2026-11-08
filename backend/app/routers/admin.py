"""Administrator Router (/api/v1/admin/*).

Protected by require_admin dependency. Accessible exclusively to users with role='admin'.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.core.errors import AppError
from app.db.session import get_db
from app.models import Session as SessionModel
from app.models import User

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("/dashboard", status_code=status.HTTP_200_OK)
def admin_dashboard(admin: User = Depends(require_admin)) -> dict:
    """Returns administrative dashboard summary metrics."""
    return {
        "status": "ok",
        "message": f"Chào mừng quản trị viên {admin.full_name}",
        "admin_id": str(admin.id),
    }


@router.post("/users/{user_id}/disable", status_code=status.HTTP_200_OK)
def disable_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    """Disables user account and immediately terminates all active sessions in one transaction."""
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise AppError(code="user_not_found", message="Không tìm thấy người dùng.", status_code=404)

    user.is_active = False

    # Invalidate all active sessions for this user in the same transaction
    deleted_count = db.execute(
        delete(SessionModel).where(SessionModel.user_id == user_id)
    ).rowcount

    db.commit()

    return {
        "status": "ok",
        "message": f"Đã khóa tài khoản {user.username} và hủy {deleted_count} phiên làm việc.",
        "user_id": str(user_id),
        "is_active": False,
        "revoked_sessions": deleted_count,
    }


@router.post("/users/{user_id}/enable", status_code=status.HTTP_200_OK)
def enable_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    """Re-enables a previously disabled user account."""
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise AppError(code="user_not_found", message="Không tìm thấy người dùng.", status_code=404)

    user.is_active = True
    db.commit()

    return {
        "status": "ok",
        "message": f"Đã mở khóa tài khoản {user.username}.",
        "user_id": str(user_id),
        "is_active": True,
    }


@router.post("/sessions/{session_id}/revoke", status_code=status.HTTP_200_OK)
def revoke_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    """Revokes a specific session by ID."""
    result = db.execute(delete(SessionModel).where(SessionModel.id == session_id))
    db.commit()
    if result.rowcount == 0:
        raise AppError(code="session_not_found", message="Phiên không tồn tại.", status_code=404)
    return {"status": "ok", "message": "Phiên đã bị thu hồi."}
