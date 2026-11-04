# Quiz Backend API

Hệ thống Quiz nội bộ môn Toán & Tin học (FastAPI + SQLAlchemy + Alembic).

## Hướng dẫn cài đặt & chạy cục bộ

1. Yêu cầu: Python >= 3.12, `uv`.
2. Đồng bộ môi trường ảo và dependencies:
   ```bash
   uv sync
   ```
3. Chạy test:
   ```bash
   uv run pytest
   ```
4. Chạy lint:
   ```bash
   uv run ruff check .
   ```
5. Khởi động server phát triển:
   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```
