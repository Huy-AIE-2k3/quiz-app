"""Administrative and Development CLI Commands.

Usage:
    python -m app.cli seed [--admin-username <username>]
    python -m app.cli create-admin
"""

import argparse
import sys
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models import Class, Exam, ExamClass, Question, User


def seed_development_data(admin_username: str | None = None) -> None:
    """Seeds sample development classes and an exam containing all 4 question types.

    Security Rule: Never hardcodes user passwords or default accounts.
    Requires an existing administrator user.
    """
    settings = get_settings()
    if settings.APP_ENV == "production":
        print("ERROR: CLI seed command is strictly prohibited in production environment!")
        sys.exit(1)

    session_factory = get_session_factory()
    with session_factory() as db:
        # Locate administrator user
        admin: User | None = None
        if admin_username:
            admin = db.execute(
                select(User).where(User.username == admin_username.lower(), User.role == "admin")
            ).scalar_one_or_none()
        else:
            admin = (
                db.execute(select(User).where(User.role == "admin").order_by(User.created_at.asc()))
                .scalars()
                .first()
            )

        if not admin:
            print(
                "ERROR: Không tìm thấy tài khoản admin nào trong hệ thống.\n"
                "Quy tắc bảo mật: Hệ thống không tự tạo tài khoản mặc định.\n"
                "Vui lòng tạo admin trước bằng lệnh 'python -m app.cli create-admin' "
                "hoặc chỉ định qua cờ: --admin-username <username>"
            )
            sys.exit(1)

        print(f"[*] Sử dụng tài khoản admin: {admin.username} ({admin.full_name})")

        # 1. Seed Classes
        classes_data = [
            {"code": "TOAN-10A1", "name": "Lớp 10A1 Chuyên Toán", "academic_year": 2024},
            {"code": "TIN-10A2", "name": "Lớp 10A2 Chuyên Tin", "academic_year": 2024},
        ]
        created_classes: list[Class] = []
        for cdata in classes_data:
            existing = db.execute(
                select(Class).where(Class.code == cdata["code"])
            ).scalar_one_or_none()
            if existing:
                print(f"[*] Lớp '{cdata['code']}' đã tồn tại, bỏ qua tạo mới.")
                created_classes.append(existing)
            else:
                new_class = Class(
                    code=cdata["code"],
                    name=cdata["name"],
                    academic_year=cdata["academic_year"],
                )
                db.add(new_class)
                created_classes.append(new_class)
        db.flush()

        # 2. Seed Sample Exam
        exam_title = "Đề kiểm tra khảo sát Toán & Tin học kỳ 1 (Mẫu)"
        existing_exam = db.execute(
            select(Exam).where(Exam.title == exam_title)
        ).scalar_one_or_none()

        if existing_exam:
            print(f"[*] Đề thi mẫu '{exam_title}' đã tồn tại, bỏ qua tạo mới.")
        else:
            sample_exam = Exam(
                title=exam_title,
                description_md=(
                    "## Hướng dẫn làm bài thi\n"
                    "- Bài thi gồm **4 câu hỏi** tương ứng 4 định dạng chuẩn của hệ thống.\n"
                    "- Thời gian làm bài: **45 phút**.\n"
                    "- Chúc các em hoàn thành tốt bài kiểm tra!"
                ),
                subject="math",
                duration_minutes=45,
                status="draft",
                created_by=admin.id,
                version=1,
            )
            db.add(sample_exam)
            db.flush()

            # Link exam to first class
            if created_classes:
                db.add(ExamClass(exam_id=sample_exam.id, class_id=created_classes[0].id))

            # 3. Seed 4 Questions covering all 4 question types
            questions_data: list[dict[str, Any]] = [
                # Type 1: MCQ (4 options)
                {
                    "position": 1,
                    "question_type": "mcq",
                    "content_md": (
                        "Cho phương trình bậc hai: $x^2 - 5x + 6 = 0$.\n"
                        "Giá trị nghiệm dương lớn hơn $2$ của phương trình là:"
                    ),
                    "config": {
                        "options": [
                            {"id": "o1", "content_md": "$x = 1$", "label": "A"},
                            {"id": "o2", "content_md": "$x = 2$", "label": "B"},
                            {"id": "o3", "content_md": "$x = 3$", "label": "C"},
                            {"id": "o4", "content_md": "$x = 6$", "label": "D"},
                        ],
                        "shuffle_options": True,
                    },
                    "answer_key": {"correct": "o3"},
                    "points": Decimal("1.00"),
                },
                # Type 2: True/False (4 sub-items with step_threshold scoring)
                {
                    "position": 2,
                    "question_type": "true_false",
                    "content_md": (
                        "Cho hàm số bậc ba $y = f(x) = x^3 - 3x^2 + 2$.\n"
                        "Xét tính đúng / sai của các mệnh đề sau:"
                    ),
                    "config": {
                        "format": "group_4",
                        "scoring_mode": "step_threshold",
                        "items": [
                            {"id": "a", "content_md": "Hàm số có điểm cực đại tại $x = 0$."},
                            {"id": "b", "content_md": "Hàm số đồng biến trên khoảng $(0; 2)$."},
                            {"id": "c", "content_md": "Giá trị cực tiểu của hàm số là $-2$."},
                            {"id": "d", "content_md": "Đồ thị hàm số đi qua gốc tọa độ $O(0; 0)$."},
                        ],
                    },
                    "answer_key": {
                        "format": "group_4",
                        "scoring_mode": "step_threshold",
                        "correct_items": {
                            "a": True,
                            "b": False,
                            "c": True,
                            "d": False,
                        },
                        "thresholds": {
                            "1": 0.1,
                            "2": 0.25,
                            "3": 0.5,
                            "4": 1.0,
                        },
                    },
                    "points": Decimal("1.00"),
                },
                # Type 3: Short Answer (Decimal number)
                {
                    "position": 3,
                    "question_type": "short_answer",
                    "content_md": (
                        "Tính giá trị của đạo hàm hàm số $g(x) = 2x^2 - 3x$ tại điểm $x = 1.5$.\n"
                        "*(Nhập kết quả dưới dạng số thập phân)*"
                    ),
                    "config": {
                        "tolerance": 0.01,
                        "placeholder": "Nhập số thập phân, ví dụ: 3.0",
                    },
                    "answer_key": {
                        "target": 3.0,
                        "tolerance": 0.01,
                    },
                    "points": Decimal("1.00"),
                },
                # Type 4: File Upload (Essay / Code file submission)
                {
                    "position": 4,
                    "question_type": "file_upload",
                    "content_md": (
                        "Viết chương trình tìm tất cả các số nguyên tố $\\le N$ bằng thuật toán "
                        "**Sàng Eratosthenes** (Sieve of Eratosthenes).\n"
                        "Nộp tệp mã nguồn (`.cpp`, `.py`) hoặc tài liệu (`.docx`, `.pdf`)."
                    ),
                    "config": {
                        "allowed_extensions": [".cpp", ".py", ".docx", ".pdf"],
                        "max_size_mb": 5,
                    },
                    "answer_key": {
                        "rubric_md": (
                            "- Thuật toán chính xác: 0.5 điểm\n"
                            "- Tối ưu độ phức tạp thời gian & bộ nhớ: 0.25 điểm\n"
                            "- Trình bày mã nguồn sạch sẽ, chú thích rõ ràng: 0.25 điểm"
                        )
                    },
                    "points": Decimal("1.00"),
                },
            ]

            for qdata in questions_data:
                q = Question(
                    exam_id=sample_exam.id,
                    position=qdata["position"],
                    question_type=qdata["question_type"],
                    content_md=qdata["content_md"],
                    config=qdata["config"],
                    answer_key=qdata["answer_key"],
                    points=qdata["points"],
                    version=1,
                )
                db.add(q)

            db.commit()
            print(f"[+] Đã seed thành công đề thi '{exam_title}' cùng 4 câu hỏi mẫu 4 định dạng!")

        print("[OK] Hoàn tất quá trình seed dữ liệu phát triển.")


def create_admin_user(
    username: str | None = None,
    password: str | None = None,
    full_name: str | None = None,
) -> bool:
    """Creates an administrator account enforcing security policies (min len 12, no defaults)."""
    import getpass

    from app.core.security import hash_password

    if not username:
        try:
            username = input("Nhập tên đăng nhập admin (tối thiểu 3 ký tự): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nĐã hủy thao tác.")
            return False

    username_clean = username.strip().lower()
    if len(username_clean) < 3:
        print("ERROR: Tên đăng nhập phải có ít nhất 3 ký tự.")
        return False

    session_factory = get_session_factory()
    with session_factory() as db:
        existing = db.execute(
            select(User).where(User.username == username_clean)
        ).scalar_one_or_none()
        if existing:
            print(f"ERROR: Tên đăng nhập '{username_clean}' đã tồn tại trong hệ thống.")
            return False

        if not full_name:
            try:
                full_name = input("Nhập họ và tên đầy đủ: ").strip()
            except (EOFError, KeyboardInterrupt):
                full_name = "Quản trị viên"
            if not full_name:
                full_name = "Quản trị viên"

        if not password:
            try:
                pw1 = getpass.getpass("Nhập mật khẩu bảo mật (tối thiểu 12 ký tự): ")
                pw2 = getpass.getpass("Xác nhận lại mật khẩu: ")
                if pw1 != pw2:
                    print("ERROR: Mật khẩu xác nhận không khớp.")
                    return False
                password = pw1
            except (EOFError, KeyboardInterrupt):
                print("\nĐã hủy thao tác.")
                return False

        if len(password) < 12:
            print("ERROR: Mật khẩu phải có độ dài tối thiểu 12 ký tự theo chuẩn bảo mật.")
            return False

        hashed_pw = hash_password(password)
        new_admin = User(
            username=username_clean,
            full_name=full_name,
            hashed_password=hashed_pw,
            role="admin",
            is_active=True,
        )
        db.add(new_admin)
        db.commit()
        print(f"[+] Khởi tạo thành công tài khoản quản trị viên: {username_clean} ({full_name})")
        return True


def main() -> None:
    """CLI dispatcher."""
    parser = argparse.ArgumentParser(description="Quiz App CLI Management Utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Seed command
    seed_parser = subparsers.add_parser("seed", help="Seed sample development classes and exam")
    seed_parser.add_argument(
        "--admin-username",
        type=str,
        default=None,
        help="Username of existing administrator to attribute created exam",
    )

    # Create admin command
    admin_parser = subparsers.add_parser(
        "create-admin", help="Interactively create the initial administrator account"
    )
    admin_parser.add_argument("--username", type=str, default=None, help="Administrator username")
    admin_parser.add_argument("--password", type=str, default=None, help="Administrator password")
    admin_parser.add_argument("--full-name", type=str, default=None, help="Full display name")

    args = parser.parse_args()
    if args.command == "seed":
        seed_development_data(admin_username=args.admin_username)
    elif args.command == "create-admin":
        success = create_admin_user(
            username=args.username,
            password=args.password,
            full_name=args.full_name,
        )
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
