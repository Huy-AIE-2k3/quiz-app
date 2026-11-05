# DANH MỤC QUẢN LÝ BÍ MẬT & DỊCH VỤ ĐÁM MÂY (SECRETS INVENTORY)

> **Tài liệu tham chiếu:** `ke-hoach-trien-khai-quiz.md` (Bước 0.2)  
> **Nguyên tắc cốt lõi:** Tuyệt đối không ghi giá trị bí mật vào tài liệu này. Mọi mật khẩu, token, API key phải do người dùng tự khởi tạo và lưu trữ an toàn trong công cụ quản lý mật khẩu cá nhân / biến môi trường đám mây.

---

## 1. NGUYÊN TẮC BẢO MẬT & QUẢN TRỊ BÍ MẬT

1. **Không có giá trị mặc định (Zero Default Secrets):** Mọi tham số nhạy cảm (CSDL, Token, S3 Key, Session Secret) đều phải do người vận hành trực tiếp chỉ định. Hệ thống được lập trình để từ chối khởi động (fail-fast) nếu thiếu biến.
2. **Nguyên tắc đặc quyền tối thiểu (Least Privilege):** Mỗi dịch vụ bên thứ ba chỉ được cấp quyền tối thiểu cần thiết để vận hành (ví dụ: Token Cloudflare R2 chỉ được thao tác trên đúng bucket chỉ định, không có quyền quản trị tài khoản Cloudflare).
3. **Bảo vệ 2 lớp (2FA Mandatory):** Mọi tài khoản dịch vụ (GitHub, Neon, Cloudflare, Render, Cron-job) bắt buộc kích hoạt xác thực hai yếu tố (2FA) qua ứng dụng Authenticator (TOTP) hoặc khóa bảo mật phần cứng (FIDO2).
4. **Cô lập theo môi trường:** Tuyệt đối không sử dụng chung CSDL, S3 bucket hoặc SECRET_KEY giữa môi trường phát triển (Development) và môi trường thực tế (Production).

---

## 2. BẢNG KIỂM KÊ DANH MỤC BIẾN MÔI TRƯỜNG

| Tên biến | Mức độ nhạy cảm | Môi trường áp dụng | Nơi lưu trữ an toàn | Mục đích & Yêu cầu định dạng |
| :--- | :---: | :---: | :---: | :--- |
| `APP_ENV` | Thấp | Dev, Prod | `.env`, Render | Xác định môi trường (`development`, `production`). |
| `DEBUG` | Thấp | Dev, Prod | `.env`, Render | Bật/tắt chế độ debug và tài liệu Swagger (`false` trên Production). |
| `DATABASE_URL` | **Tối mật** | Dev, Prod | `.env`, Render | Chuỗi kết nối Postgres cho ứng dụng (dùng qua PgBouncer/Pooled của Neon: `postgresql://user:pass@ep-...-pooler.ap-southeast-1.neon.tech/neondb?sslmode=require`). |
| `DATABASE_URL_DIRECT` | **Tối mật** | Dev, Prod, CI | `.env`, Render, GitHub Secrets | Chuỗi kết nối Postgres trực tiếp (không qua pooler) dành riêng cho Alembic migration (`postgresql://user:pass@ep-...ap-southeast-1.neon.tech/neondb?sslmode=require`). |
| `SECRET_KEY` | **Tối mật** | Dev, Prod | `.env`, Render | Chuỗi ngẫu nhiên có độ dài tối thiểu 32 ký tự, dùng ký token phiên và bảo mật hệ thống. Không chia sẻ. |
| `SESSION_TTL_HOURS` | Trung bình | Dev, Prod | `.env`, Render | Thời gian sống tối đa của phiên đăng nhập (mặc định 12 giờ cho ca thi). |
| `S3_ENDPOINT` | Thấp | Dev, Prod | `.env`, Render | Endpoint API tương thích S3 (Local MinIO: `http://127.0.0.1:9000`; Cloudflare R2: `https://<account_id>.r2.cloudflarestorage.com`). |
| `S3_BUCKET` | Thấp | Dev, Prod | `.env`, Render | Tên bucket lưu trữ (Local: `quiz-files`; R2: bucket riêng tư dành riêng cho Quiz). |
| `S3_ACCESS_KEY` | **Tối mật** | Dev, Prod | `.env`, Render | Access Key ID của tài khoản / R2 API Token. |
| `S3_SECRET_KEY` | **Tối mật** | Dev, Prod | `.env`, Render | Secret Access Key tương ứng với Access Key ID. |
| `S3_REGION` | Thấp | Dev, Prod | `.env`, Render | Vùng lưu trữ (`auto` với Cloudflare R2, hoặc `us-east-1` với MinIO). |
| `CORS_ORIGINS` | Trung bình | Dev, Prod | `.env`, Render | Danh sách domain frontend được phép gọi API (Dev: `http://localhost:5173`; Prod: `https://<ten-mien-pages>.pages.dev`). |
| `MAX_UPLOAD_MB` | Thấp | Dev, Prod | `.env`, Render | Giới hạn dung lượng tệp tải lên (ảnh đề thi, bài nộp học sinh), tối đa 10 MB. |
| `DATA_RETENTION_DAYS` | Thấp | Dev, Prod | `.env`, Render | Số ngày lưu trữ kết quả và tệp nộp trước khi tự động dọn dẹp (mặc định 90 ngày). |
| `POSTGRES_USER` | Trung bình | Dev (Docker) | `.env` | Tên tài khoản CSDL cục bộ (chỉ dùng cho Docker Compose nội bộ máy phát triển). |
| `POSTGRES_PASSWORD` | **Tối mật** | Dev (Docker) | `.env` | Mật khẩu tài khoản CSDL cục bộ (do lập trình viên tự đặt trong `.env`). |
| `POSTGRES_DB` | Thấp | Dev (Docker) | `.env` | Tên cơ sở dữ liệu cục bộ (`quiz_dev`). |
| `POSTGRES_PORT` | Thấp | Dev (Docker) | `.env` | Cổng máy chủ Postgres cục bộ (mặc định 5432). |

---

## 3. THIẾT LẬP CÁC DỊCH VỤ ĐÁM MÂY (HƯỚNG DẪN THỰC HIỆN)

### 3.1. Neon Postgres (CSDL Đám mây)
- **Mục tiêu:** Cung cấp PostgreSQL 16 quản lý bởi Neon với tính năng Serverless và Connection Pooling.
- **Vùng chọn (Region):** `ap-southeast-1` (Singapore) để tối ưu độ trễ với mạng Internet Việt Nam.
- **Cấu hình:**
  1. Tạo tài khoản Neon qua GitHub hoặc email riêng của dự án, bật 2FA.
  2. Tạo Project mới: Tên `quiz-app-db`, chọn Postgres 16, Region `Asia Pacific (Singapore)`.
  3. Lấy 2 chuỗi kết nối:
     - **Direct Connection:** Chọn `Connection string` $\to$ bỏ chọn pooling $\to$ sao chép vào `DATABASE_URL_DIRECT`. (Đảm bảo có `sslmode=require`).
     - **Pooled Connection:** Chọn `Connection string` $\to$ bật `Connection pooling` $\to$ sao chép vào `DATABASE_URL`.
  4. Giới hạn gói miễn phí: 0.5 GB dung lượng, 100 CU-giờ/tháng (đủ cho 50 người dùng đồng thời trong các kỳ thi nội bộ).

### 3.2. Cloudflare R2 (Lưu trữ tệp bài thi & đề thi)
- **Mục tiêu:** Lưu trữ ảnh câu hỏi (asset) và file nộp bài tự luận của học sinh, không phát sinh chi phí egress.
- **Cấu hình:**
  1. Đăng nhập Cloudflare Dashboard, kích hoạt R2 Object Storage.
  2. Tạo bucket mới: `quiz-files-prod` (chọn Region `WNAM` hoặc `APAC` nếu có).
  3. **Bảo mật:** Đảm bảo **Public Access** của bucket ở trạng thái **Disabled (Bị khóa)**. Mọi truy cập vào tệp phải thông qua URL ký có thời hạn (Presigned URL) do Backend sinh ra.
  4. Tạo API Token:
     - Chọn `Manage R2 API Tokens` $\to$ `Create API Token`.
     - Quyền: **Object Read & Write** (Chỉ cho phép đọc và ghi đối tượng, không cấp quyền Admin/Bucket deletion).
     - Áp dụng: Chỉ cấp quyền trên bucket `quiz-files-prod`.
     - Lưu lại `Access Key ID`, `Secret Access Key` và Endpoint URL (`https://<ACCOUNT_ID>.r2.cloudflarestorage.com`).
  - *(Dự phòng)*: Nếu tài khoản Cloudflare yêu cầu thẻ thanh toán để bật R2 mà giáo viên chưa có sẵn thẻ, có thể sử dụng Supabase Storage (miễn phí 1 GB, tương thích API S3) bằng cách điền endpoint S3 của Supabase vào các biến `S3_*`.

### 3.3. Cloudflare Pages (Frontend Hosting)
- **Mục tiêu:** Triển khai Single Page Application (React + Vite) trên mạng lưới CDN toàn cầu của Cloudflare.
- **Cấu hình:**
  1. Trong Cloudflare Dashboard $\to$ `Workers & Pages` $\to$ `Create Application` $\to$ `Pages` $\to$ `Connect to Git`.
  2. Chọn kho lưu trữ `quiz-app`.
  3. Cài đặt Build:
     - Framework preset: `Vite`
     - Root directory: `frontend`
     - Build command: `pnpm run build`
     - Build output directory: `dist`
  4. Cấu hình biến môi trường Build (nếu cần): `NODE_VERSION=20`.

### 3.4. Render (Backend Web Service)
- **Mục tiêu:** Chạy ứng dụng FastAPI trên container Linux miễn phí.
- **Cấu hình:**
  1. Đăng nhập Render.com, tạo `New Web Service` trỏ tới repo GitHub `quiz-app`.
  2. Cài đặt dịch vụ:
     - Root Directory: `backend`
     - Runtime: `Python 3`
     - Build Command: `pip install uv && uv sync --frozen` (hoặc cài dependencies qua `pip`)
     - Start Command: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`
     - Health Check Path: `/healthz`
  3. Nhập đầy đủ các biến môi trường trong mục `Environment Variables` trên Render (theo bảng ở Mục 2).

### 3.5. Dịch vụ Giữ thức (Ping / Uptime Monitor)
- **Mục tiêu:** Ngăn Render Free Tier chuyển sang chế độ ngủ (sleep) trong thời gian giáo viên và học sinh tổ chức thi.
- **Công cụ:** `cron-job.org` hoặc `uptimerobot.com`.
- **Cấu hình:**
  - Thiết lập HTTP GET định kỳ 5 phút/lần tới endpoint `https://<ten-backend-render>.onrender.com/healthz`.
  - Chỉ kích hoạt hoặc đặt lịch chạy trong khung giờ tổ chức thi để tiết kiệm tài nguyên.

---

## 4. QUY TRÌNH THAY ĐỔI & THU HỒI BÍ MẬT (SECRET ROTATION)

1. **Khi phát hiện hoặc nghi ngờ lộ khóa (Compromised Key):**
   - Đăng nhập ngay vào trang quản trị dịch vụ tương ứng (Neon/Cloudflare/Render).
   - Tạo khóa mới / token mới.
   - Cập nhật biến môi trường trên Render và Cloudflare Pages.
   - Kích hoạt khởi động lại (Restart/Redeploy) dịch vụ để nạp biến mới.
   - Xóa (Revoke/Delete) token hoặc khóa cũ.
2. **Xử lý sự cố commit nhầm bí mật vào Git:**
   - Pre-commit hook đã được cấu hình chặn commit `.env` và các định dạng khóa phổ biến.
   - Nếu xảy ra trường hợp ngoại lệ bị lọt vào commit cục bộ: **Tuyệt đối không push lên remote**. Chạy `git reset HEAD~1` để hủy commit, xóa bí mật và commit lại.
   - Nếu đã push lên GitHub: Coi như bí mật đó đã bị lộ công khai $\to$ Tiến hành thu hồi ngay lập tức trên trang quản trị dịch vụ đám mây, sau đó dùng `git filter-repo` hoặc BFG Repo-Cleaner để làm sạch lịch sử Git.

