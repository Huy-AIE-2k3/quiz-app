# Hệ thống Quiz Nội bộ Toán – Tin

Hệ thống web kiểm tra trực tuyến nội bộ dành cho học sinh môn Toán & Tin học.

---

## 1. Yêu cầu môi trường
* **Python:** 3.12+ và công cụ [`uv`](https://docs.astral.sh/uv/)
* **Node.js:** 20 hoặc 22 LTS và [`pnpm`](https://pnpm.io/)
* **Docker & Docker Compose**
* **Git**

---

## 2. Hướng dẫn khởi chạy nhanh (Dưới 15 phút)

### Bước 1: Khởi động dịch vụ nền cục bộ (PostgreSQL & MinIO S3)
```bash
docker compose up -d
```
* PostgreSQL sẽ lắng nghe tại: `127.0.0.1:5432`
* MinIO S3 Console sẽ mở tại: `http://127.0.0.1:9001` (API: `9000`)

### Bước 2: Thiết lập biến môi trường
Tạo file `.env` từ mẫu:
```bash
cp .env.example .env
```
*(Tùy chỉnh mật khẩu cục bộ nếu cần. Lưu ý: Không lưu mật khẩu thật lên Git)*.

### Bước 3: Khởi chạy Backend API (FastAPI)
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```
* API Health check: [http://127.0.0.1:8000/healthz](http://127.0.0.1:8000/healthz)
* API Readiness check: [http://127.0.0.1:8000/readyz](http://127.0.0.1:8000/readyz)

### Bước 4: Khởi chạy Frontend (React + Vite)
Mở một terminal mới:
```bash
cd frontend
pnpm install
pnpm dev
```
* Truy cập giao diện tại: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## 3. Kiểm thử & Đảm bảo chất lượng (Lint & Test)

### Backend
```bash
cd backend
# Chạy lint kiểm tra cú pháp
uv run ruff check .
# Chạy toàn bộ test
uv run pytest
```

### Frontend
```bash
cd frontend
# Kiểm tra TypeScript & ESLint
pnpm run lint
# Chạy unit test với Vitest
pnpm run test
# Build kiểm tra sản phẩm
pnpm run build
```

---

## 4. Cấu trúc thư mục Monorepo
```
├── backend/          # FastAPI, SQLAlchemy, Alembic, Pydantic
├── frontend/         # Vite, React, TypeScript, TailwindCSS
├── design/           # Design System tokens, tài liệu giao diện & Stitch screens
├── docs/             # Tài liệu kiến trúc, UX flows, sitemap, runbook
├── .github/          # GitHub Actions CI/CD workflows
├── docker-compose.yml# Dịch vụ DB Postgres & MinIO local
└── .env.example      # Mẫu khai báo biến môi trường an toàn
```

