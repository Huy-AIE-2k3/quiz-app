# MATHRIX – Nền Tảng Khảo Thí Trực Tuyến Môn Toán & Tin Học

Hệ thống thi trắc nghiệm và tự luận nội bộ dành cho học sinh và giáo viên môn Toán & Tin học, tối ưu trải nghiệm làm bài mượt mà, render công thức KaTeX siêu tốc (<5ms) và quản trị trực quan.

---

## 1. Cấu Trúc Dự Án (Monorepo)

```
quiz-web/
├── backend/                 # Backend API (Python 3.12, FastAPI, SQLAlchemy, Alembic)
│   ├── app/
│   │   ├── main.py          # Entrypoint ứng dụng & /healthz
│   │   └── core/config.py   # Quản lý cấu hình Settings qua Pydantic
│   ├── tests/               # Unit & Integration tests (pytest)
│   └── pyproject.toml       # Quản lý thư viện qua uv
├── frontend/                # Frontend SPA (React 18, Vite, TypeScript, Tailwind CSS)
│   ├── src/
│   │   ├── App.tsx          # Giao diện chính
│   │   └── index.css        # Theme Cybernetic Prism dark mode & KaTeX styles
│   ├── vite.config.ts       # Cấu hình Vite & Vitest
│   └── package.json
├── docker/
│   └── pgadmin/
│       └── servers.json     # Cấu hình tự động kết nối DB cho pgAdmin
├── docker-compose.yml       # Container PostgreSQL 16 + pgAdmin 4 Web Console
├── Makefile                 # Các lệnh điều khiển toàn bộ dự án
├── .env.example             # Mẫu biến môi trường
└── README.md
```

---

## 2. Khởi Động Nhanh (Quick Start)

### Yêu cầu tiên quyết:
- **Python 3.12** & **uv** (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Node.js 20+** & **npm**
- **Docker** & **Docker Compose**
- **GNU Make**

### Bước 1: Thiết lập cấu hình môi trường
```bash
cp .env.example .env
```

### Bước 2: Khởi động toàn bộ hệ thống bằng 1 lệnh duy nhất
```bash
make dev
```
Lệnh này sẽ tự động:
1. Khởi chạy container **PostgreSQL 16** và **pgAdmin 4** (Docker).
2. Chờ PostgreSQL sẵn sàng (`healthcheck` passed).
3. Khởi chạy Backend **FastAPI** (`http://localhost:8000`).
4. Khởi chạy Frontend **Vite React** (`http://localhost:5173`).

---

## 3. Danh Sách Địa Chỉ Dịch Vụ Cục Bộ

| Dịch vụ | Địa chỉ truy cập | Thông tin đăng nhập / Ghi chú |
| :--- | :--- | :--- |
| **Frontend Web** | [http://localhost:5173](http://localhost:5173) | Giao diện học sinh & giáo viên |
| **Backend API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI tương tác trực tiếp |
| **Health Check API** | [http://localhost:8000/healthz](http://localhost:8000/healthz) | Trạng thái máy chủ (JSON) |
| **pgAdmin 4 Web** | [http://localhost:5050](http://localhost:5050) | Email: `admin@mathrix.edu.vn`<br/>Mật khẩu: `admin` |
| **PostgreSQL Database** | `localhost:5432` | DB: `quiz_db`<br/>User: `quiz_user`<br/>Password: `quiz_password` |

> 💡 **Mẹo với pgAdmin 4 Web Console:**
> Khi đăng nhập vào `http://localhost:5050`, database `Mathrix PostgreSQL (quiz_db)` đã được kết nối sẵn thông qua cấu hình `servers.json`. Bạn chỉ cần click mở để xem các bảng và dữ liệu.

---

## 4. Các Lệnh Thao Tác Thường Dùng (`Makefile`)

```bash
# Xem hướng dẫn tất cả các lệnh
make help

# Khởi chạy toàn bộ môi trường dev (DB + pgAdmin + Backend + Frontend)
make dev

# Chỉ khởi động PostgreSQL và pgAdmin qua Docker
make dev-db

# Dừng PostgreSQL và pgAdmin
make stop-db

# Chạy toàn bộ test (Backend pytest + Frontend vitest)
make test

# Chạy kiểm tra chuẩn code (Ruff + Mypy + TypeScript typecheck)
make lint

# Build bundle frontend cho production
make build

# Dọn dẹp cache tạm thời
make clean
```
