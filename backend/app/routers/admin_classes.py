"""Admin Class Management Endpoints (/api/v1/admin/classes/*)."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.core.errors import AppError
from app.db.session import get_db
from app.models import Class, ClassMember, ExamClass, User
from app.schemas.class_schema import (
    ClassCreate,
    ClassListResponse,
    ClassResponse,
    ClassUpdate,
)

router = APIRouter(
    prefix="/classes",
    tags=["Admin Classes"],
    dependencies=[Depends(require_admin)],
)


def escape_like_pattern(text: str) -> str:
    """Escapes special SQL LIKE wildcard characters (%, _, \\) with backslash."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    payload: ClassCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ClassResponse:
    """Creates a new classroom. Code is automatically capitalized and checked for uniqueness."""
    existing = db.execute(select(Class).where(Class.code == payload.code)).scalar_one_or_none()
    if existing:
        raise AppError(
            code="class_code_taken",
            message=f"Mã lớp '{payload.code}' đã tồn tại trong hệ thống.",
            status_code=409,
            details={"code": payload.code},
        )

    new_class = Class(
        code=payload.code,
        name=payload.name,
        academic_year=payload.academic_year,
        subject=payload.subject,
        version=1,
    )
    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    return ClassResponse(
        id=new_class.id,
        code=new_class.code,
        name=new_class.name,
        academic_year=new_class.academic_year,
        subject=new_class.subject,
        is_archived=new_class.is_archived,
        version=new_class.version,
        created_at=new_class.created_at,
        student_count=0,
        exam_count=0,
    )


@router.get("", response_model=ClassListResponse, status_code=status.HTTP_200_OK)
def list_classes(
    limit: int = Query(default=20, ge=1, le=100, description="Số lượng bản ghi mỗi trang (1-100)"),
    offset: int = Query(default=0, ge=0, description="Vị trí bắt đầu (>= 0)"),
    q: str | None = Query(default=None, description="Từ khóa tìm kiếm theo tên hoặc mã lớp"),
    sort: str = Query(
        default="created_desc",
        description=(
            "Thứ tự sắp xếp: created_desc, created_asc, name_asc, "
            "name_desc, code_asc, code_desc, year_desc"
        ),
    ),
    include_archived: bool = Query(default=False, description="Hiển thị cả lớp đã lưu trữ"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ClassListResponse:
    """Lists classrooms with pagination, search, sorting and member metrics without N+1 queries."""
    # Base filter
    filters = []
    if not include_archived:
        filters.append(Class.is_archived.is_(False))

    if q and q.strip():
        escaped_q = escape_like_pattern(q.strip())
        pattern = f"%{escaped_q}%"
        filters.append(
            or_(
                Class.name.ilike(pattern, escape="\\"),
                Class.code.ilike(pattern, escape="\\"),
            )
        )

    # 1. Total count query
    count_stmt = select(func.count()).select_from(Class).where(*filters)
    total = db.execute(count_stmt).scalar() or 0

    # 2. Sorting resolution
    sort_mapping = {
        "created_desc": Class.created_at.desc(),
        "created_asc": Class.created_at.asc(),
        "name_asc": Class.name.asc(),
        "name_desc": Class.name.desc(),
        "code_asc": Class.code.asc(),
        "code_desc": Class.code.desc(),
        "year_desc": Class.academic_year.desc(),
    }
    order_clause = sort_mapping.get(sort, Class.created_at.desc())

    # 3. Scalar subqueries for counts to avoid N+1 queries
    student_count_subq = (
        select(func.count(ClassMember.student_id))
        .where(ClassMember.class_id == Class.id)
        .scalar_subquery()
    )
    exam_count_subq = (
        select(func.count(ExamClass.exam_id))
        .where(ExamClass.class_id == Class.id)
        .scalar_subquery()
    )

    rows_stmt = (
        select(
            Class,
            student_count_subq.label("student_count"),
            exam_count_subq.label("exam_count"),
        )
        .where(*filters)
        .order_by(order_clause)
        .offset(offset)
        .limit(limit)
    )

    results = db.execute(rows_stmt).all()

    items = [
        ClassResponse(
            id=cls_obj.id,
            code=cls_obj.code,
            name=cls_obj.name,
            academic_year=cls_obj.academic_year,
            subject=cls_obj.subject,
            is_archived=cls_obj.is_archived,
            version=cls_obj.version,
            created_at=cls_obj.created_at,
            student_count=student_cnt or 0,
            exam_count=exam_cnt or 0,
        )
        for cls_obj, student_cnt, exam_cnt in results
    ]

    return ClassListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{class_id}", response_model=ClassResponse, status_code=status.HTTP_200_OK)
def get_class(
    class_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ClassResponse:
    """Returns single classroom detail with student and exam counts."""
    student_count_subq = (
        select(func.count(ClassMember.student_id))
        .where(ClassMember.class_id == Class.id)
        .scalar_subquery()
    )
    exam_count_subq = (
        select(func.count(ExamClass.exam_id))
        .where(ExamClass.class_id == Class.id)
        .scalar_subquery()
    )

    stmt = select(
        Class,
        student_count_subq.label("student_count"),
        exam_count_subq.label("exam_count"),
    ).where(Class.id == class_id)

    result = db.execute(stmt).first()
    if not result:
        raise AppError(code="class_not_found", message="Không tìm thấy lớp học.", status_code=404)

    cls_obj, student_cnt, exam_cnt = result
    return ClassResponse(
        id=cls_obj.id,
        code=cls_obj.code,
        name=cls_obj.name,
        academic_year=cls_obj.academic_year,
        subject=cls_obj.subject,
        is_archived=cls_obj.is_archived,
        version=cls_obj.version,
        created_at=cls_obj.created_at,
        student_count=student_cnt or 0,
        exam_count=exam_cnt or 0,
    )


@router.patch("/{class_id}", response_model=ClassResponse, status_code=status.HTTP_200_OK)
def update_class(
    class_id: uuid.UUID,
    payload: ClassUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ClassResponse:
    """Updates classroom metadata with optimistic locking version verification."""
    cls_obj = db.execute(select(Class).where(Class.id == class_id)).scalar_one_or_none()
    if not cls_obj:
        raise AppError(code="class_not_found", message="Không tìm thấy lớp học.", status_code=404)

    # Optimistic locking check
    if cls_obj.version != payload.version:
        raise AppError(
            code="version_conflict",
            message="Dữ liệu lớp học đã được cập nhật bởi một phiên khác. Vui lòng tải lại trang.",
            status_code=409,
            details={"current_version": cls_obj.version, "provided_version": payload.version},
        )

    if payload.name is not None:
        cls_obj.name = payload.name
    if payload.academic_year is not None:
        cls_obj.academic_year = payload.academic_year
    if payload.subject is not None:
        cls_obj.subject = payload.subject
    if payload.is_archived is not None:
        cls_obj.is_archived = payload.is_archived

    cls_obj.version += 1
    db.commit()
    db.refresh(cls_obj)

    # Get student count and exam count
    student_cnt = (
        db.execute(
            select(func.count(ClassMember.student_id)).where(ClassMember.class_id == class_id)
        ).scalar()
        or 0
    )
    exam_cnt = (
        db.execute(
            select(func.count(ExamClass.exam_id)).where(ExamClass.class_id == class_id)
        ).scalar()
        or 0
    )

    return ClassResponse(
        id=cls_obj.id,
        code=cls_obj.code,
        name=cls_obj.name,
        academic_year=cls_obj.academic_year,
        subject=cls_obj.subject,
        is_archived=cls_obj.is_archived,
        version=cls_obj.version,
        created_at=cls_obj.created_at,
        student_count=student_cnt,
        exam_count=exam_cnt,
    )


@router.delete("/{class_id}", status_code=status.HTTP_200_OK)
def delete_class(
    class_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    """Safely deletes classroom. Prevents deletion if class is assigned to exams."""
    cls_obj = db.execute(select(Class).where(Class.id == class_id)).scalar_one_or_none()
    if not cls_obj:
        raise AppError(code="class_not_found", message="Không tìm thấy lớp học.", status_code=404)

    # Verify if class is in use by any exam
    exam_cnt = (
        db.execute(
            select(func.count(ExamClass.exam_id)).where(ExamClass.class_id == class_id)
        ).scalar()
        or 0
    )

    if exam_cnt > 0:
        raise AppError(
            code="class_in_use",
            message=(
                "Lớp đã được giao đề thi, không thể xóa trực tiếp. "
                "Vui lòng chuyển sang lưu trữ (is_archived=true)."
            ),
            status_code=409,
            details={"assigned_exams": exam_cnt},
        )

    db.delete(cls_obj)
    db.commit()

    return {"status": "deleted", "id": str(class_id)}
