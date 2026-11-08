"""Admin Student Management Endpoints (/api/v1/admin/students/*)."""

import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import require_admin
from app.core.errors import AppError
from app.core.security import generate_random_password, hash_password
from app.db.session import get_db
from app.models import Class, ClassMember, User
from app.models import Session as SessionModel
from app.routers.admin_classes import escape_like_pattern
from app.schemas.student_schema import (
    ClassSimple,
    CsvImportResult,
    ResetPasswordRequest,
    ResetPasswordResponse,
    StudentCreate,
    StudentDetailResponse,
    StudentListResponse,
    StudentResponse,
    StudentUpdate,
)
from app.services.csv_import_service import process_csv_import

router = APIRouter(
    prefix="/students",
    tags=["Admin Students"],
    dependencies=[Depends(require_admin)],
)


@router.post("", response_model=StudentDetailResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> StudentDetailResponse:
    """Creates a new student account.

    If password is not specified, a secure random password is generated and displayed once.
    """
    # 1. Check for duplicate username
    existing = db.execute(
        select(User).where(User.username == payload.username)
    ).scalar_one_or_none()
    if existing:
        raise AppError(
            code="username_taken",
            message=f"Tên đăng nhập '{payload.username}' đã được sử dụng.",
            status_code=409,
            details={"username": payload.username},
        )

    # 2. Handle password
    raw_password = payload.password or generate_random_password(8)
    hashed_pwd = hash_password(raw_password)

    # 3. Create student
    student = User(
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hashed_pwd,
        role="student",
        is_active=True,
    )
    db.add(student)
    db.flush()

    # 4. Enroll in classes if requested
    assigned_classes = []
    if payload.class_ids:
        classes = (
            db.execute(
                select(Class).where(Class.id.in_(payload.class_ids), Class.is_archived.is_(False))
            )
            .scalars()
            .all()
        )
        for cls_obj in classes:
            db.add(ClassMember(class_id=cls_obj.id, student_id=student.id))
            assigned_classes.append(
                ClassSimple(id=cls_obj.id, code=cls_obj.code, name=cls_obj.name)
            )

    db.commit()
    db.refresh(student)

    return StudentDetailResponse(
        id=student.id,
        username=student.username,
        full_name=student.full_name,
        is_active=student.is_active,
        created_at=student.created_at,
        classes=assigned_classes,
        generated_password=raw_password,
    )


@router.get("", response_model=StudentListResponse, status_code=status.HTTP_200_OK)
def list_students(
    limit: int = Query(default=20, ge=1, le=100, description="Số lượng học sinh mỗi trang (1-100)"),
    offset: int = Query(default=0, ge=0, description="Vị trí bắt đầu (>= 0)"),
    q: str | None = Query(default=None, description="Từ khóa tìm kiếm theo họ tên hoặc username"),
    class_id: uuid.UUID | None = Query(default=None, description="Lọc theo lớp học"),
    is_active: bool | None = Query(default=None, description="Lọc theo trạng thái hoạt động"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> StudentListResponse:
    """Lists students with pagination, search, class filter, and eagerloaded enrolled classes."""
    filters = [User.role == "student"]

    if is_active is not None:
        filters.append(User.is_active == is_active)

    if q and q.strip():
        escaped_q = escape_like_pattern(q.strip())
        pattern = f"%{escaped_q}%"
        filters.append(
            or_(
                User.full_name.ilike(pattern, escape="\\"),
                User.username.ilike(pattern, escape="\\"),
            )
        )

    if class_id:
        filters.append(User.class_memberships.any(ClassMember.class_id == class_id))

    # Total count query
    count_stmt = select(func.count()).select_from(User).where(*filters)
    total = db.execute(count_stmt).scalar() or 0

    # Fetch students with eagerloaded memberships and classes (2 queries total, no N+1)
    stmt = (
        select(User)
        .options(selectinload(User.class_memberships).joinedload(ClassMember.class_))
        .where(*filters)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    students = db.execute(stmt).scalars().all()

    items = [
        StudentResponse(
            id=s.id,
            username=s.username,
            full_name=s.full_name,
            is_active=s.is_active,
            created_at=s.created_at,
            classes=[
                ClassSimple(id=m.class_.id, code=m.class_.code, name=m.class_.name)
                for m in s.class_memberships
                if m.class_ and not m.class_.is_archived
            ],
        )
        for s in students
    ]

    return StudentListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/import", response_model=CsvImportResult, status_code=status.HTTP_200_OK)
async def import_students_csv(
    file: UploadFile = File(..., description="Tệp CSV danh sách học sinh"),
    dry_run: bool = Query(default=True, description="Chế độ kiểm tra xem trước (dry-run)"),
    auto_generate_passwords: bool = Query(
        default=False,
        description="Tự động sinh mật khẩu ngẫu nhiên an toàn cho các ô mật khẩu để trống",
    ),
    default_class_id: uuid.UUID | None = Query(
        default=None, description="ID lớp mặc định nếu dòng trong CSV không chứa mã lớp"
    ),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> CsvImportResult:
    """Imports students in batch from a CSV file (two-phase: dry-run -> atomic commit)."""
    raw_bytes = await file.read()
    return process_csv_import(
        raw_bytes=raw_bytes,
        db=db,
        dry_run=dry_run,
        auto_generate_passwords=auto_generate_passwords,
        default_class_id=default_class_id,
    )


@router.get("/{student_id}", response_model=StudentResponse, status_code=status.HTTP_200_OK)
def get_student(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> StudentResponse:
    """Returns single student detail with enrolled classes."""
    stmt = (
        select(User)
        .options(selectinload(User.class_memberships).joinedload(ClassMember.class_))
        .where(User.id == student_id, User.role == "student")
    )
    student = db.execute(stmt).scalar_one_or_none()
    if not student:
        raise AppError(
            code="student_not_found", message="Không tìm thấy học sinh.", status_code=404
        )

    return StudentResponse(
        id=student.id,
        username=student.username,
        full_name=student.full_name,
        is_active=student.is_active,
        created_at=student.created_at,
        classes=[
            ClassSimple(id=m.class_.id, code=m.class_.code, name=m.class_.name)
            for m in student.class_memberships
            if m.class_ and not m.class_.is_archived
        ],
    )


@router.patch("/{student_id}", response_model=StudentResponse, status_code=status.HTTP_200_OK)
def update_student(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> StudentResponse:
    """Updates student profile. If is_active is False, revokes active sessions."""
    stmt = (
        select(User)
        .options(selectinload(User.class_memberships).joinedload(ClassMember.class_))
        .where(User.id == student_id, User.role == "student")
    )
    student = db.execute(stmt).scalar_one_or_none()
    if not student:
        raise AppError(
            code="student_not_found", message="Không tìm thấy học sinh.", status_code=404
        )

    if payload.full_name is not None:
        student.full_name = payload.full_name

    if payload.is_active is not None:
        student.is_active = payload.is_active
        if not payload.is_active:
            # Terminate all active sessions immediately
            db.execute(delete(SessionModel).where(SessionModel.user_id == student_id))

    db.commit()
    db.refresh(student)

    return StudentResponse(
        id=student.id,
        username=student.username,
        full_name=student.full_name,
        is_active=student.is_active,
        created_at=student.created_at,
        classes=[
            ClassSimple(id=m.class_.id, code=m.class_.code, name=m.class_.name)
            for m in student.class_memberships
            if m.class_ and not m.class_.is_archived
        ],
    )


@router.post(
    "/{student_id}/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
)
def reset_student_password(
    student_id: uuid.UUID,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ResetPasswordResponse:
    """Resets student password, invalidates sessions, and returns one-time password."""
    student = db.execute(
        select(User).where(User.id == student_id, User.role == "student")
    ).scalar_one_or_none()
    if not student:
        raise AppError(
            code="student_not_found", message="Không tìm thấy học sinh.", status_code=404
        )

    raw_password = payload.password or generate_random_password(8)
    student.hashed_password = hash_password(raw_password)

    # Invalidate all active sessions for this student
    db.execute(delete(SessionModel).where(SessionModel.user_id == student_id))
    db.commit()

    return ResetPasswordResponse(
        status="ok",
        student_id=student.id,
        generated_password=raw_password,
    )
