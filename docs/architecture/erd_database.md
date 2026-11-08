# THIẾT KẾ MÔ HÌNH DỮ LIỆU QUAN HỆ (ERD) — HỆ THỐNG QUIZ TOÁN – TIN

> **Tài liệu tham chiếu:** `ke-hoach-trien-khai-quiz.md` (Mục 2.2, 4.1 & 7.0), `quiz-toan-tin-spec.md`  
> **Công cụ:** Mermaid v11 (Mermaid Chart MCP)  
> **Cơ sở dữ liệu đích:** PostgreSQL 16 (Neon Serverless PgBouncer)  
> **ORM & Migration:** SQLAlchemy 2.0 + Alembic

---

## 1. Sơ đồ Thực thể Quan hệ Tổng thể (Mermaid ERD)

```mermaid
erDiagram
    USERS ||--o{ SESSIONS : "creates"
    USERS ||--o{ CLASS_MEMBERS : "belongs_to"
    USERS ||--o{ EXAMS : "authors"
    USERS ||--o{ ATTEMPTS : "undertakes"
    USERS ||--o{ ANSWERS : "grades"
    USERS ||--o{ FILES : "uploads"
    USERS ||--o{ AUDIT_LOGS : "triggers"

    CLASSES ||--o{ CLASS_MEMBERS : "contains"
    CLASSES ||--o{ EXAM_CLASSES : "assigned_exams"

    EXAMS ||--o{ EXAM_CLASSES : "assigned_to"
    EXAMS ||--|{ QUESTIONS : "contains"
    EXAMS ||--o{ ATTEMPTS : "generates"

    ATTEMPTS ||--o{ ANSWERS : "records"
    QUESTIONS ||--o{ ANSWERS : "receives"
    ANSWERS |o--o| FILES : "attaches_submission"

    USERS {
        uuid id PK "UUIDv4"
        varchar username UK "Check lower username, len >= 3"
        varchar full_name "Ho va ten"
        varchar hashed_password "Argon2id hash"
        varchar role "Check in admin, student"
        boolean is_active "Default true"
        timestamptz created_at "Default now"
        timestamptz updated_at "Default now"
    }

    SESSIONS {
        uuid id PK "UUIDv4"
        uuid user_id FK "Cascade delete on user"
        varchar token_hash UK "sha256 hex cua raw token 32 bytes"
        timestamptz created_at "Thoi diem dang nhap"
        timestamptz expires_at "TTL 12h truot"
        timestamptz last_seen_at "Cap nhat moi 5 phut"
        varchar user_agent "Client user agent"
        varchar ip_address "Client IP"
    }

    CLASSES {
        uuid id PK "UUIDv4"
        varchar code UK "Ma dinh danh lop duy nhat"
        varchar name "Ten lop hien thi"
        integer academic_year "Nam hoc"
        boolean is_archived "Default false"
        timestamptz created_at "Default now"
    }

    CLASS_MEMBERS {
        uuid class_id PK,FK "Lop hoc"
        uuid student_id PK,FK "Hoc sinh"
        timestamptz joined_at "Thoi diem ghi danh"
    }

    EXAMS {
        uuid id PK "UUIDv4"
        varchar title "Tieu de de thi"
        text description_md "Huong dan thi Markdown"
        varchar subject "Check in math, computer_science"
        integer duration_minutes "Thoi gian lam bai phut"
        varchar status "Check in draft, published, locked, archived"
        timestamptz open_at "Thoi diem mo de"
        timestamptz close_at "Thoi diem dong de"
        timestamptz locked_at "Khoa de khi hoc sinh dau tien nop"
        integer version "Khoa lac quan optimistic lock, default 1"
        uuid created_by FK "Giao vien tao de"
        timestamptz created_at "Default now"
    }

    EXAM_CLASSES {
        uuid exam_id PK,FK "De thi"
        uuid class_id PK,FK "Lop duoc giao"
    }

    QUESTIONS {
        uuid id PK "UUIDv4"
        uuid exam_id FK "De thi so huu"
        integer position "Thu tu cau hoi, Deferrable Deferred"
        varchar question_type "Check: mcq | true_false | short_answer | file_upload"
        text content_md "Noi dung cau hoi Markdown va KaTeX"
        jsonb config "Cau hinh tuy bien theo 4 dang cau hoi"
        jsonb answer_key "Dap an dung va bieu diem chi tiet (bao mat)"
        numeric points "Diem toi da cua cau, default 1.00, check >= 0"
        integer version "Khoa lac quan optimistic lock, default 1"
    }

    ATTEMPTS {
        uuid id PK "UUIDv4"
        uuid exam_id FK "Unique exam_id va student_id"
        uuid student_id FK "Hoc sinh lam bai"
        varchar status "Check in in_progress, submitted"
        timestamptz started_at "Thoi diem bam bat dau"
        timestamptz deadline_at "Han chot tinh theo server"
        bigint shuffle_seed "Seed ngau nhien dao cau"
        numeric score_total "Tong diem thi"
        timestamptz submitted_at "Thoi diem nop bai"
        timestamptz created_at "Default now"
    }

    ANSWERS {
        uuid id PK "UUIDv4"
        uuid attempt_id FK "Unique attempt_id va question_id"
        uuid question_id FK "Cau hoi tuong ung"
        uuid file_id FK "Khoa ngoai tep tin bai lam tu luan neu co"
        jsonb value "Dap an hoc sinh nop (chon/so/file)"
        jsonb sub_scores "Diem chi tiet tung y nho a b c d hoac tieu chi"
        bigint client_seq "Sequence client chong out-of-order, default 0"
        numeric score "Tong diem dat duoc cua cau"
        boolean is_correct "Dung hoan toan hoac Sai"
        text feedback_md "Loi nhan xet cua giao vien khi cham tay"
        uuid graded_by FK "Giao vien cham tay"
        timestamptz graded_at "Thoi diem cham"
        integer version "Khoa lac quan, default 1"
        timestamptz updated_at "Thoi diem cap nhat"
    }

    FILES {
        uuid id PK "UUIDv4"
        uuid user_id FK "Nguoi tai len"
        varchar original_name "Ten tep tin goc"
        varchar s3_key UK "Duong dan Cloudflare R2 hoac MinIO"
        varchar mime_type "Dinh dang MIME"
        bigint size_bytes "Kich thuoc byte, check > 0"
        timestamptz created_at "Default now"
    }

    AUDIT_LOGS {
        uuid id PK "UUIDv4"
        uuid user_id FK "User gay ra hanh dong"
        varchar action "Ten hanh dong"
        varchar resource_type "Loai tai nguyen"
        varchar resource_id "ID tai nguyen"
        jsonb details "Du lieu chi tiet da loc thong tin nhay cam"
        varchar ip_address "IP client"
        timestamptz created_at "Default now"
    }
```

---

## 2. Đặc Tả Chi Tiết 4 Dạng Câu Hỏi & Cấu Trúc JSON

### 2.1. Dạng 1: Câu hỏi trắc nghiệm (MCQ)
- **Phương án:** Cố định 4 phương án lựa chọn A, B, C, D (hoặc mã nội bộ $o_1, o_2, o_3, o_4$ để xáo trộn không làm lệch nhãn).
- **Cấu hình `QUESTIONS.config`:**
  ```json
  {
    "options": [
      {"id": "o1", "content_md": "Phương án A", "label": "A"},
      {"id": "o2", "content_md": "Phương án B", "label": "B"},
      {"id": "o3", "content_md": "Phương án C", "label": "C"},
      {"id": "o4", "content_md": "Phương án D", "label": "D"}
    ],
    "shuffle_options": true
  }
  ```
- **Đáp án đúng `QUESTIONS.answer_key`:**
  ```json
  {
    "correct": "o2"
  }
  ```
- **Bài nộp học sinh `ANSWERS.value`:**
  ```json
  {
    "selected": "o2"
  }
  ```

---

### 2.2. Dạng 2: Câu hỏi Đúng / Sai (True / False)

#### Thể dạng 2A: Một câu hỏi gồm 4 ý nhỏ $a, b, c, d$
Mỗi ý có 2 lựa chọn: Đúng / Sai. Giáo viên lựa chọn 1 trong 2 cơ chế tính điểm (`scoring_mode`):
1. **Kiểu 1 — Chia điểm theo từng ý (`scoring_mode = "per_item"`):**
   - Giáo viên tùy biến điểm cho từng ý nhỏ $a, b, c, d$ (ví dụ: $a=0.25$, $b=0.5$, $c=0.25$, $d=0.5$).
2. **Kiểu 2 — Tính điểm theo số lượng ý đúng (`scoring_mode = "step_threshold"` - Chuẩn đề thi TN THPT mới):**
   - Thang điểm lũy tiến theo số ý đúng do giáo viên tự customize (ví dụ: đúng 1/4 ý được 0.1đ, đúng 2/4 ý được 0.25đ, đúng 3/4 ý được 0.5đ, đúng 4/4 ý được 1.0đ).

- **Cấu hình `QUESTIONS.config`:**
  ```json
  {
    "format": "group_4",
    "items": [
      {"id": "a", "content_md": "Mệnh đề a"},
      {"id": "b", "content_md": "Mệnh đề b"},
      {"id": "c", "content_md": "Mệnh đề c"},
      {"id": "d", "content_md": "Mệnh đề d"}
    ],
    "scoring_mode": "step_threshold",
    "step_scores": {
      "1": 0.10,
      "2": 0.25,
      "3": 0.50,
      "4": 1.00
    },
    "item_points": {
      "a": 0.25,
      "b": 0.50,
      "c": 0.25,
      "d": 0.50
    }
  }
  ```
- **Đáp án đúng `QUESTIONS.answer_key`:**
  ```json
  {
    "answers": {
      "a": true,
      "b": false,
      "c": true,
      "d": true
    }
  }
  ```
- **Bài nộp học sinh `ANSWERS.value`:**
  ```json
  {
    "answers": {
      "a": true,
      "b": false,
      "c": false,
      "d": true
    }
  }
  ```
- **Điểm chi tiết lưu tại `ANSWERS.sub_scores`:**
  ```json
  {
    "correct_count": 3,
    "items": {
      "a": {"student": true, "correct": true, "is_match": true},
      "b": {"student": false, "correct": false, "is_match": true},
      "c": {"student": false, "correct": true, "is_match": false},
      "d": {"student": true, "correct": true, "is_match": true}
    },
    "awarded_score": 0.50
  }
  ```

#### Thể dạng 2B: Một câu hỏi duy nhất với 2 lựa chọn "Đúng" / "Sai"
- **Cấu hình `QUESTIONS.config`:**
  ```json
  {
    "format": "single",
    "options": [
      {"id": "true", "label": "Đúng"},
      {"id": "false", "label": "Sai"}
    ]
  }
  ```
- **Đáp án đúng `QUESTIONS.answer_key`:**
  ```json
  {
    "correct": true
  }
  ```
- **Bài nộp học sinh `ANSWERS.value`:**
  ```json
  {
    "selected": true
  }
  ```

---

### 2.3. Dạng 3: Câu hỏi trả lời ngắn dạng số thập phân (Short Answer Decimal)
- Học sinh nhập số thập phân (hỗ trợ dấu âm, số thực).
- Giáo viên cấu hình dung sai sai số (`tolerance`) và tập các giá trị chấp nhận được.
- **Cấu hình `QUESTIONS.config`:**
  ```json
  {
    "input_type": "decimal",
    "tolerance": 0.01,
    "tolerance_type": "abs",
    "unit": "cm"
  }
  ```
- **Đáp án đúng `QUESTIONS.answer_key`:**
  ```json
  {
    "accepted_values": [3.14, 3.1416],
    "tolerance": 0.01,
    "tolerance_type": "abs"
  }
  ```
- **Bài nộp học sinh `ANSWERS.value`:**
  ```json
  {
    "value": 3.14
  }
  ```

---

### 2.4. Dạng 4: Câu hỏi tự luận nộp tệp bài làm (File Upload Essay)
- Học sinh làm bài trên giấy/máy tính rồi tải tệp lên (mã nguồn `.cpp`, `.py`, tài liệu `.docx`, `.pdf`, ảnh `.png`,...).
- Giáo viên cấu hình danh sách đuôi tệp cho phép (`allowed_extensions`), dung lượng tối đa (`max_file_size_mb`), số lượng tệp tối đa (`max_files`).
- Chấm điểm: Chấm thủ công bởi giáo viên kèm tiêu chí chấm (`rubric`) và lời nhận xét (`feedback_md`).
- **Cấu hình `QUESTIONS.config`:**
  ```json
  {
    "allowed_extensions": ["docx", "pdf", "cpp", "py", "zip"],
    "max_file_size_mb": 10,
    "max_files": 1,
    "rubric_md": "Tiêu chí chấm điểm: Thuật toán đúng (0.5đ), Tối ưu thời gian (0.5đ)"
  }
  ```
- **Đáp án đúng `QUESTIONS.answer_key`:**
  ```json
  {
    "grading": "manual",
    "solution_md": "Mã nguồn tham khảo và lời giải chuẩn của giáo viên",
    "rubric": [
      {"criterion": "Tính đúng đắn", "max_points": 0.5},
      {"criterion": "Độ phức tạp O(N log N)", "max_points": 0.5}
    ]
  }
  ```
- **Bài nộp học sinh `ANSWERS.value`:**
  ```json
  {
    "file_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "file_name": "bai_lam_toan.docx",
    "s3_key": "submissions/2026/exam1/bai_lam_toan.docx",
    "file_size": 204800
  }
  ```
- Khóa ngoại `ANSWERS.file_id` trỏ trực tiếp đến `FILES.id`.
