
# BẢNG THEO DÕI TIẾN ĐỘ DỰ ÁN HỆ THỐNG QUIZ NỘI BỘ TOÁN – TIN

> **Tài liệu tham chiếu:** `ke-hoach-trien-khai-quiz.md` & `quiz-toan-tin-spec.md` (v1.0)**Quy ước trạng thái:**
>
> - `[ ]` Chưa thực hiện
> - `[-]` Đang thực hiện
> - `[x]` Đã hoàn thành
> - `[!]` Bị nghẽn / Cần xử lý khẩn cấp

> [!IMPORTANT]
> **TAKE NOTE QUAN TRỌNG — NGUYÊN TẮC BẢO MẬT ĐỐI TƯỢNG NHẠY CẢM:**Tất cả các đối tượng nhạy cảm như tài khoản, mật khẩu, thông tin đăng nhập, token bí mật v.v. **TUYỆT ĐỐI KHÔNG ĐƯỢC KHỞI TẠO MẶC ĐỊNH**, và **PHẢI DO NGƯỜI DÙNG QUYẾT ĐỊNH**.
>
> - Cấm hardcode hoặc gán sẵn bất kỳ tài khoản/mật khẩu mặc định nào trong mã nguồn, file cấu hình, seed script hay migration.
> - Không tự sinh admin mặc định khi server khởi động. Tài khoản Admin đầu tiên bắt buộc phải do người dùng tự nhập thông tin qua CLI tương tác (`create-admin`).
> - Mật khẩu học sinh phải do giáo viên tự thiết lập hoặc chủ động chọn tính năng sinh ngẫu nhiên an toàn có xác nhận (tuyệt đối không dùng mật khẩu mặc định cố định như `123456`, ngày sinh...).
>
> **QUY TẮC PHÂN NHÁNH GIT (GIT WORKFLOW RULE):**
>
> - **Chỉ push vào `dev`**: Trong suốt quá trình thực hiện từng task, toàn bộ commit và lệnh `git push` chỉ được phép đẩy lên nhánh `dev`.
> - **Điều kiện đẩy sang `main`**: Chỉ chuyển code sang nhánh `main` vào **cuối ngày làm việc** sau khi đã hoàn thành toàn bộ khối lượng công việc trong ngày và kiểm thử đầy đủ 100%.

---

## TỔNG QUAN TIẾN ĐỘ THEO GIAI ĐOẠN

| Giai đoạn             | Nội dung chính                                                            | Thời lượng ước tính      | Trạng thái | Tiến độ |
| ----------------------- | --------------------------------------------------------------------------- | ------------------------------ | :----------: | :--------: |
| **Giai đoạn 0** | Chuẩn bị môi trường, tài khoản dịch vụ, Stitch MCP & Skill         | 1–2 ngày                     |   `[x]`   |    100%    |
| **Giai đoạn 1** | UI/UX, Design System, sinh màn hình Stitch, rà slop, React Components    | 5–6 ngày                     |   `[x]`   |    100%    |
| **Giai đoạn 2** | Nền tảng Backend FastAPI, CSDL SQLAlchemy/Alembic, Auth, Khung Frontend   | 4 ngày                        |   `[x]`   |    100%    |
| **Giai đoạn 3** | Quản lý Lớp, Học sinh, Ghi danh, Nhập CSV 2 pha                        | 3 ngày                        |   `[x]`   |    100%    |
| **Giai đoạn 4** | Soạn đề 5 dạng câu, LaTeX, Ảnh asset, Vòng đời đề thi            | 5 ngày                        |   `[-]`   |    80%     |
| **Giai đoạn 5** | Làm bài, Tự lưu Outbox, Đồng hồ Monotonic, Tự nộp, Nộp file       | 8 ngày                        |   `[ ]`   |     0%     |
| **Giai đoạn 6** | Bộ máy chấm điểm, Chấm tay, Công bố, Giám sát, Xuất/Dọn CSV     | 5 ngày                        |   `[ ]`   |     0%     |
| **Giai đoạn 7** | Đảm bảo chất lượng: Bảo mật, Tải (40 user), Chaos, E2E, Thiết bị | 4 ngày                        |   `[ ]`   |     0%     |
| **Giai đoạn 8** | Hosting (Pages + Render + Neon + R2), Giữ thức, Diễn tập & Go-Live      | 3 ngày                        |   `[ ]`   |     0%     |
| **TỔNG**         | **Toàn bộ dự án từ chuẩn bị đến go-live**                    | **~38 ngày làm việc** |   `[-]`   |    ~49%    |

---

## CHI TIẾT CHECKLIST TỪNG GIAI ĐOẠN

### GIAI ĐOẠN 0. CHUẨN BỊ (1–2 NGÀY)

- [X] **Bước 0.1 — Khung Monorepo & Môi trường phát triển cục bộ**

  - [X] Đã cài đặt môi trường cơ bản: Python 3.12 + `uv`, Node 20/22 LTS + `pnpm`, Docker + Compose, Git.
  - [X] Khởi tạo cấu trúc thư mục chuẩn monorepo: `backend/`, `frontend/`, `design/`, `docs/`.
  - [X] Cấu hình file `docker-compose.yml`:
    - [X] Dịch vụ `db`: `postgres:16`, volume riêng, healthcheck `pg_isready`, chỉ bind `127.0.0.1:5432` (hỗ trợ tùy biến `POSTGRES_PORT`).
    - [X] Dịch vụ `minio`: S3-compatible local server (`cgr.dev/chainguard/minio`) để test upload file cục bộ.
  - [X] Khởi tạo Backend: `uv init`, cấu hình `pyproject.toml` (FastAPI, uvicorn, sqlalchemy, alembic, argon2-cffi, slowapi, apscheduler, boto3, pillow, pytest, ruff...).
  - [X] Khởi tạo Frontend: `pnpm create vite` (React + TS + Tailwind), thêm TanStack Query, react-hook-form, zod, react-markdown, KaTeX, dnd-kit.
  - [X] Thiết lập `pre-commit` hook (ruff, eslint, chặn commit `.env` và API keys).
  - [X] Thiết lập GitHub Actions CI cơ bản (`backend` test + `frontend` build/lint).
  - [X] Cấu hình `pydantic-settings` thất bại ngay khi khởi động (fail-fast) nếu thiếu biến bắt buộc.

  - **Kiểm thử cần đạt:**
    - [X] `TC-0.1-01`: Clone sạch và chạy theo README thành công trong $\le$ 15 phút.
    - [X] `TC-0.1-02`: Thiếu biến môi trường báo lỗi rõ tên biến và dừng tiến trình.
    - [X] `TC-0.1-03`: Pre-commit chặn commit nhầm file bí mật/.env.
    - [X] `TC-0.1-04`: CI đổi màu đỏ khi có test lỗi.
    - [X] `TC-0.1-05`: `/readyz` trả 503 khi DB tắt, `/healthz` vẫn trả 200.

- [-] **Bước 0.2 — Tạo tài khoản dịch vụ đám mây & Quản lý bí mật**

  - [ ] Tạo email dùng riêng cho dự án và bật 2FA trên tất cả nền tảng.
  - [ ] **Neon Postgres:** Tạo project tại vùng Singapore, lấy 2 chuỗi kết nối (`DATABASE_URL_DIRECT` và `DATABASE_URL` pooled).
  - [ ] **Cloudflare:**
    - [ ] Tạo Cloudflare Pages kết nối với GitHub repo.
    - [ ] Tạo Cloudflare R2 bucket riêng tư (`quiz-files`, `quiz-backups`), tạo API token quyền Object Read & Write.
    - [ ] (Dự phòng) Chuẩn bị sẵn tài khoản Supabase Storage nếu R2 yêu cầu thẻ thanh toán.
  - [ ] **Render:** Tạo Web Service (gói Free) trỏ tới repo (chưa deploy).
  - [ ] **Ping Service:** Tạo tài khoản cron-job.org hoặc UptimeRobot để giữ máy chủ thức trong giờ thi.
  - [X] Tạo file `.env.example` và tài liệu kiểm kê danh mục biến `docs/secrets-inventory.md`.
  - [X] Xây dựng script kiểm tra tự động kết nối đám mây `backend/scripts/verify_cloud_connections.py`.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-0.2-01`: Kết nối Neon thành công bằng `psql` kèm `sslmode=require` (sẵn sàng qua script verify).
    - [ ] `TC-0.2-02`: Script mẫu ghi/đọc/xóa object trên R2 thành công qua `boto3` (sẵn sàng qua script verify).
    - [ ] `TC-0.2-03`: URL trực tiếp không ký của R2 trả về 403 AccessDenied (sẵn sàng qua script verify).
    - [ ] `TC-0.2-04`: Token R2 bị từ chối khi ghi vào bucket khác (sẵn sàng qua script verify).
    - [X] `TC-0.2-05`: Tất cả tài khoản đã bật 2FA; quét kiểm tra bí mật trên lịch sử Git trả về 0 vi phạm.

- [X] **Bước 0.3 — Cài đặt Antigravity, Skill & Kết nối Stitch MCP**

  - [X] Cài đặt Google Cloud SDK (`gcloud`), đăng nhập và kiểm tra xác thực Google Cloud ADC.
  - [X] Kích hoạt API Stitch: `stitch.googleapis.com` hoạt động bình thường.
  - [X] Cấu hình Stitch MCP và kiểm tra gọi công cụ thực tế (`list_projects`, `list_screens`, `list_design_systems`).
  - [X] Cài đặt đầy đủ các skill vào `.agents/skills/`:
    - [X] `google-labs-code/stitch-skills` (`stitch-generate-design`, `stitch-loop`, `design-md`, `enhance-prompt`, `stitch-react-components`, `taste-design`).
    - [X] `anthropics/skills` (`frontend-design`).
    - [X] `pbakaus/impeccable` (`impeccable`).
    - [X] `mermaid.ai` (`mermaid` - Thiết kế mô hình CSDL ERD & sơ đồ kiến trúc cho Giai đoạn 2).
  - [X] Chuẩn bị tài liệu và quy trình xuất thiết kế thủ công dự phòng `docs/ux/stitch-workflow.md`.

  - **Kiểm thử cần đạt:**
    - [X] `TC-0.3-01`: Antigravity nhận diện Stitch MCP đang chạy bình thường.
    - [X] `TC-0.3-02`: Gọi thử tạo/liệt kê project Stitch thành công (đã nhận diện project `Quiz Toan Tin - UI System`).
    - [X] `TC-0.3-03`: Antigravity liệt kê đầy đủ các skills đã cài đặt.
    - [X] `TC-0.3-04`: Xử lý được lỗi hết hạn token ADC và đăng nhập lại.
    - [X] `TC-0.3-05`: Thử nghiệm thành công quy trình xuất màn hình thủ công dự phòng.

---

### GIAI ĐOẠN 1. THIẾT KẾ UI/UX & COMPONENT SYSTEM (5–6 NGÀY)

- [X] **Bước 1.1 — Sơ đồ trang, Luồng người dùng & Bảng ma trận trạng thái**

  - [X] Viết tài liệu `docs/ux/sitemap.md` định nghĩa toàn bộ 14 route React Router và sơ đồ điều hướng.
  - [X] Viết tài liệu `docs/ux/flows.md` mô tả 3 hành trình chính (Học sinh thi, Giáo viên quản lý đề/chấm, Nhập CSV 3 bước) và 4 nhánh gián đoạn ngoại lệ.
  - [X] Viết tài liệu `docs/ux/state-matrix.md` ánh xạ từng route $\times$ 6 trạng thái (*loading, empty, error, offline, forbidden, expired/submitted*).
  - [X] Ánh xạ toàn bộ mã lỗi API sang thông điệp tiếng Việt cụ thể trên UI.

  - **Kiểm thử cần đạt:**
    - [X] `TC-1.1-01`: 100% màn hình đặc tả mục 11 có mặt trong bảng route và ma trận trạng thái.
    - [X] `TC-1.1-02`: Mọi mã lỗi API đều có thông điệp tiếng Việt thân thiện tương ứng.
    - [X] `TC-1.1-03`: Không có màn hình "cụt" trong 3 hành trình chính.
    - [X] `TC-1.1-04`: Nhánh gián đoạn (mất mạng, hết giờ, mở 2 tab, mở lại) có trạng thái rõ ràng.
    - [X] `TC-1.1-05`: Thử nghiệm cho giáo viên và học sinh xem sơ đồ đạt độ hiểu cao.
- [X] **Bước 1.2 — Hệ thống thiết kế (Design System) & `DESIGN.md`**

  - [X] Xây dựng file `design/tokens.json` định nghĩa màu, kích thước, bo góc, bóng đổ.
  - [X] Tự host phông chữ tiếng Việt qua `@fontsource` (Be Vietnam Pro, JetBrains Mono, KaTeX font).
  - [X] Thiết kế chỉ báo đồng hồ: Bình thường / Cảnh báo (< 5p) / Nguy cấp (< 1p) kèm icon + chữ (không chỉ dùng màu).
  - [X] Viết file `DESIGN.md` theo quy chuẩn `design-md` định hướng chống "AI slop".
  - [X] Viết script đồng bộ `design/tokens.json` ra `tailwind.config.ts` và `tokens.css`.
  - [X] Viết script kiểm tra độ tương phản WCAG AA chạy trong CI.

  - **Kiểm thử cần đạt:**
    - [X] `TC-1.2-01`: Mọi cặp màu chữ/nền đều đạt tỉ lệ tương phản $\ge 4.5:1$ (chữ thường).
    - [X] `TC-1.2-02`: Chuỗi ký tự tiếng Việt đầy đủ dấu không vỡ phông, không lệch dấu.
    - [X] `TC-1.2-03`: Sửa token màu ở 1 nơi, Tailwind và `DESIGN.md` đồng bộ tự động.
    - [X] `TC-1.2-04`: Chặn mạng ngoài, phông chữ tự host vẫn hiển thị chuẩn.
    - [X] `TC-1.2-05`: Giả lập mù màu vẫn phân biệt được các trạng thái của đồng hồ.
- [X] **Bước 1.3 — Sinh hàng loạt màn hình bằng Stitch MCP (`stitch-loop`) & Chuẩn hóa Canvas**

  - [X] Tạo file danh mục hợp đồng `design/SITE.md` gồm ~18 màn hình và các biến thể sáng/tối.
  - [X] Khởi tạo và đồng bộ hoàn tất project mới trên Stitch `mathrix_ver2` (Project ID: `7808648037604572744`) gồm 15 cặp màn hình đối xứng (Tối bên trái $x=0\text{px}$, Sáng bên phải $x=1344\text{px}$ có nền caro mờ học thuật).
  - [X] Loại bỏ 100% các box/thông tin/badge bảo mật, webcam, socket latency và kiểm tra môi trường trên toàn bộ các màn hình; chuẩn hóa duy nhất 3 nội quy phòng thi trên SC-03 và footer thống nhất *"Hệ thống nội bộ, vui lòng không chia sẻ ra bên ngoài"*.
  - [X] Xuất toàn bộ file giao diện sạch ra `design/screens/<mã>.html` và `.png` (đầy đủ 36 màn hình).
  - [X] Bổ sung Landing Page độc lập (SC-00-landing.html, route `/`): Hero tối giản lấy cảm hứng Dribbble Quiz theo yêu cầu người dùng, nền ma trận chấm Stitch có spotlight sáng theo chuột, khối Rubik 3D tương tác (Đỏ, Xanh lá, Đen) và vệ tinh mini bay xung quanh, 1 nút Đăng nhập duy nhất, footer chuẩn, đã đồng bộ lên Stitch `mathrix_ver2`.

  - **Kiểm thử cần đạt:**
    - [X] `TC-1.3-01`: Đủ 100% file `.html` và `.png` cho danh sách trong `SITE.md`.
    - [X] `TC-1.3-02`: Chạy lại lệnh không sinh trùng các màn hình đã đánh dấu `[x]`.
    - [X] `TC-1.3-03`: Dừng giữa chừng và chạy tiếp tục đúng vị trí an toàn.
    - [X] `TC-1.3-04`: Gặp lỗi hạn mức MCP dừng lại có thông báo `blocked` rõ ràng.
    - [X] `TC-1.3-05`: Tất cả màn hình đồng nhất bảng màu và token của `DESIGN.md`.
    - [X] `TC-1.3-06`: Màn hình làm bài ST3 có đủ 7 biến thể (5 dạng câu, cảnh báo, offline).
- [X] **Bước 1.4 — Rà soát chống "AI Slop", Trợ năng (a11y) & Responsive**

  - [X] Chạy rà soát phát hiện và dọn sạch các dấu hiệu AI slop (gradient tím xanh, kính mờ lạm dụng, bo góc/đổ bóng quá mức, text giả...).
  - [X] Audit trợ năng tự động trên tất cả 36 màn hình HTML (chuẩn hóa đầy đủ `aria-label`, `label for`, `alt` hình ảnh, và focus rings).
  - [X] Kiểm tra responsive trên các kích thước 360px (mobile nhỏ), 768px (tablet), 1280px (desktop) đảm bảo không cuộn ngang, nút bấm tối thiểu 44px.
  - [X] Kiểm tra điều hướng hoàn toàn bằng bàn phím (Tab, Enter, Space, Arrows, Esc), vòng focus rõ ràng.

  - **Kiểm thử cần đạt:**
    - [X] `TC-1.4-01`: Quét slop báo 0 phát hiện mức nghiêm trọng (`test_step_1_4.py`).
    - [X] `TC-1.4-02`: Trợ năng đạt 0 lỗi serious/critical về nhãn form, ảnh, điều khiển.
    - [X] `TC-1.4-03`: Hoàn thành luồng làm bài chỉ bằng bàn phím, vòng focus rõ ràng.
    - [X] `TC-1.4-04`: Ở màn hình 360px không bị cuộn ngang, có viewport meta chuẩn.
    - [X] `TC-1.4-05`: Phóng to cỡ chữ trình duyệt 200% không vỡ giao diện.
    - [X] `TC-1.4-06`: Thử nghiệm 3 học sinh làm bài không cần hướng dẫn đạt $\ge 2/3$.
- [X] **Bước 1.5 — Chuyển thiết kế thành Thư viện React Components**

  - [X] Dùng `react-components` chuyển đổi HTML thành React TSX components chuẩn.
  - [X] Xây dựng bộ component dùng chung: `Button`, `Input`, `Textarea`, `Select`, `Checkbox/Radio`, `Card`, `Badge`, `Table`, `Tabs`, `Modal/ConfirmDialog`, `Toast`, `Skeleton`, `EmptyState`, `ErrorState`, `Banner`, `Timer`, `SaveIndicator`, `QuestionNav`, `FileDropzone`, `Pagination`.
  - [X] Thêm cơ chế tự vô hiệu hóa nút submit khi đang gửi (chống double click).
  - [X] Tạo trang `/dev/components` (chỉ bật ở dev mode) trưng bày mọi trạng thái component.
  - [X] Cấu hình kiểm tra cấm hardcode mã màu `#xxxxxx` hoặc `rgb(` trong `src/` (`scripts/check_no_hardcoded_colors.py`).

  - **Kiểm thử cần đạt:**
    - [X] `TC-1.5-01`: Unit test Vitest render đủ các trạng thái default, loading, disabled, error.
    - [X] `TC-1.5-02`: Nhấn đúp nút submit form chỉ kích hoạt hàm gọi 1 lần duy nhất.
    - [X] `TC-1.5-03`: Visual showroom trang `/dev/components` hiển thị đầy đủ mọi trạng thái và switch Sáng/Tối.
    - [X] `TC-1.5-04`: CI kiểm tra 0 lỗi mã màu hardcode trong code giao diện (`scripts/check_no_hardcoded_colors.py`).
    - [X] `TC-1.5-05`: Bundle size trang login $\le 200$ KB gzip (hiện tại: 61.09 KB gzip), trang `/dev/components` được code-split riêng.
    - [X] `TC-1.5-06`: Timer và SaveIndicator đổi trạng thái đúng các mốc thời gian quy định (10m, 4m, 45s, 0s).
- [X] **Bước 1.6 — Component hiển thị Markdown + LaTeX (`MathText`) An toàn**

  - [X] Thiết lập pipeline: `react-markdown` + `remark-math` + `rehype-katex` + `rehype-sanitize`.
  - [X] Cấu hình an toàn KaTeX (`throwOnError: false`, `strict: 'ignore'`, `trust: false`, `errorColor: 'var(--status-wrong-text)'`, `maxExpand: 1000`, `maxSize: 20`).
  - [X] Cấu hình Sanitize chặn triệt để script, style, iframe, thẻ a `javascript:`, url `data:`.
  - [X] Xử lý ảnh: Chỉ chấp nhận URL `asset:<uuid>` hoặc domain Cloudflare R2/local storage, ảnh ngoài nguồn hiển thị khung cảnh báo.
  - [X] Bọc `MathTextErrorBoundary` riêng cho từng khối `MathText`.
  - [X] Hỗ trợ khối mã nguồn Tin học: Phông Monospace, cuộn ngang riêng, không phá vỡ bố cục mobile 360px.
  - [X] Hỗ trợ chuẩn hóa tự động toán khối `$$...$$` thành display mode qua `normalizeBlockMath`.

  - **Kiểm thử cần đạt:**
    - [X] `TC-1.6-01`: Hiển thị đúng công thức toán inline `$x^2$` và block `$$\int$$` (`MathText.test.tsx`).
    - [X] `TC-1.6-02`: Công thức sai cú pháp hiện lỗi tại chỗ màu đỏ, không làm chết ứng dụng.
    - [X] `TC-1.6-03`: Chặn đứng các payload XSS chèn qua Markdown và LaTeX.
    - [X] `TC-1.6-04`: Công thức đệ quy lồng nhau 500 tầng không làm treo trình duyệt (< 1500ms).
    - [X] `TC-1.6-05`: Hiển thị chuẩn tiếng Việt có dấu trong thẻ `\text{...}` và Markdown.
    - [X] `TC-1.6-06`: Ảnh trỏ tới domain lạ bên ngoài bị chặn nạp và thay bằng khung báo lỗi; ảnh R2 / asset:uuid hiển thị bình thường.
    - [X] `TC-1.6-07`: Khối mã nguồn 40 dòng có thanh cuộn ngang độc lập trên mobile 360px.

---

### GIAI ĐOẠN 2. NỀN TẢNG BACKEND, CSDL & XÁC THỰC (4 NGÀY)

- [X] **Bước 2.1 — Khung ứng dụng FastAPI, Middleware & Xử lý lỗi tập trung**

  - [X] Cấu hình FastAPI `create_app()` với kiến trúc thư mục chuẩn (`core/`, `db/`, `models/`, `schemas/`, `routers/`, `services/`).
  - [X] Thiết lập chuỗi Middleware theo thứ tự: `RequestID` $\to$ `AccessLog` $\to$ `SecurityHeaders` $\to$ `CORS` $\to$ `GZip`.
  - [X] Giới hạn kích thước body mặc định 1 MB (bắt lỗi 413 qua `BodySizeLimitMiddleware`).
  - [X] Định dạng lỗi thống nhất qua custom exception `AppError` trả về JSON `{"error": {...}}`.
  - [X] Cung cấp các endpoint: `/healthz` (không chạm DB), `/readyz` (timeout 2s kiểm tra DB), `/api/v1/time`.
  - [X] Cấu hình Logger định dạng JSON, tự động che trường mật khẩu, token, authorization, answer_key.

  - **Kiểm thử cần đạt:**
    - [X] `TC-2.1-01`: Lỗi nghiệp vụ trả đúng HTTP status, cấu trúc JSON và có header `X-Request-ID`.
    - [X] `TC-2.1-02`: Lỗi 500 không bị lộ stack trace ra phía client, có stack đầy đủ trong server log.
    - [X] `TC-2.1-03`: Tắt DB thì `/readyz` trả 503 kèm `Retry-After`, `/healthz` vẫn trả 200.
    - [X] `TC-2.1-04`: Gửi payload JSON > 1 MB bị từ chối ngay với mã 413/400.
    - [X] `TC-2.1-05`: Origin không trong whitelist bị chặn CORS preflight.
    - [X] `TC-2.1-06`: Log đăng nhập không chứa mật khẩu gốc của người dùng.
    - [X] `TC-2.1-07`: Request sai schema Pydantic trả về 422 validation_error rõ trường lỗi.
- [X] **Bước 2.2 — Thiết kế CSDL, SQLAlchemy Models & Alembic Migrations**

  - [X] Thiết kế các bảng: `users`, `classes`, `class_members`, `exams`, `exam_classes`, `questions`, `attempts`, `answers`, `files`, `sessions`, `audit_logs`.
  - [X] Khai báo ràng buộc DB cứng:
    - [X] `users.username` chữ thường + check constraint `lower(username)`.
    - [X] `attempts`: `UNIQUE (exam_id, student_id)`, check status, index partial cho sweeper `WHERE status = 'in_progress'`.
    - [X] `answers`: `UNIQUE (attempt_id, question_id)`, `client_seq bigint NOT NULL DEFAULT 0`.
    - [X] `questions`: `UNIQUE (exam_id, position) DEFERRABLE INITIALLY DEFERRED`.
    - [X] Khóa lạc quan: Cột `version integer default 1` cho `exams`, `questions`, `answers`.
    - [X] Cột `classes.is_archived boolean default false`.
  - [X] Cấu hình SQLAlchemy Engine tối ưu cho Neon PgBouncer: `pool_pre_ping=True`, `pool_recycle=240`, `prepare_threshold=None`.
  - [X] Thiết lập Alembic migration hỗ trợ chạy chuỗi direct URL, cấu hình naming convention.
  - [X] Viết lệnh CLI seed dữ liệu phát triển: `python -m app.cli seed` (chỉ dùng cho dev/test, không chứa tài khoản/mật khẩu mặc định trong code; yêu cầu người dùng tự nhập hoặc chỉ seed dữ liệu giả lớp/đề sau khi admin đã được người dùng tạo).

  - **Kiểm thử cần đạt:**
    - [X] `TC-2.2-01`: Quy trình `alembic upgrade head` $\to$ `downgrade base` $\to$ `upgrade head` thành công.
    - [X] `TC-2.2-02`: `alembic check` báo đỏ nếu sửa model mà chưa tạo migration.
    - [X] `TC-2.2-03`: Ràng buộc Unique attempt chặn việc tạo 2 attempt cho cùng 1 học sinh.
    - [X] `TC-2.2-04`: Chèn username chữ hoa bị DB từ chối.
    - [X] `TC-2.2-05`: Đổi thứ tự `position` giữa 2 câu hỏi thành công trong 1 transaction nhờ `DEFERRABLE`.
    - [X] `TC-2.2-06`: Chèn giá trị status không hợp lệ bị check constraint từ chối.
    - [X] `TC-2.2-07`: Tự động phục hồi kết nối thành công khi Postgres thức dậy sau khi sleep.
    - [X] `TC-2.2-08`: `EXPLAIN` truy vấn sweeper sử dụng đúng partial index `ix_attempts_active_deadline`.
- [X] **Bước 2.3 — Xác thực, Phiên làm việc & Phân quyền bảo mật**

  - [X] Băm mật khẩu bằng Argon2id (`argon2-cffi`), giới hạn đồng thời bằng `threading.BoundedSemaphore(3)` chống cạn RAM.
  - [X] Chống timing attack khi đăng nhập: Luôn verify với dummy hash nếu username không tồn tại.
  - [X] Tạo phiên đăng nhập token ngẫu nhiên 32 bytes an toàn, lưu `sha256(token)` trong bảng `sessions`.
  - [X] Áp dụng cơ chế hết hạn trượt (`SESSION_TTL_HOURS = 12`), chỉ ghi nhận `last_seen_at` mỗi 5 phút/lần.
  - [X] Cho phép đăng nhập đồng thời nhiều thiết bị (không ép 1 phiên/tài khoản).
  - [X] Giới hạn tần suất bằng `slowapi`: Max 10 lần sai/phút theo IP + username, 120 lần/phút theo IP.
  - [X] Tạo dependencies phân quyền FastAPI: `require_admin`, `require_student`.
  - [X] Viết CLI tương tác tạo tài khoản admin đầu tiên: `python -m app.cli create-admin` (người dùng tự gõ username và nhập mật khẩu ẩn ký tự với getpass, xác nhận lại, kiểm tra độ dài $\ge 12$; cấm tự sinh admin mặc định khi server start).

  - **Kiểm thử cần đạt:**
    - [X] `TC-2.3-01`: Đăng nhập đúng nhận token và role, gọi `/auth/me` trả về đúng user.
    - [X] `TC-2.3-02`: Thời gian phản hồi khi sai mật khẩu và sai username lệch nhau không quá 30%.
    - [X] `TC-2.3-03`: Bảng `sessions` không lưu token gốc, chỉ lưu sha256 hex.
    - [X] `TC-2.3-04`: Token hết hạn hoặc bị admin thu hồi sẽ nhận mã 401.
    - [X] `TC-2.3-05`: Thử sai 11 lần/phút bị chặn rate-limit 429, user khác cùng IP không bị ảnh hưởng.
    - [X] `TC-2.3-06`: 40 học sinh đăng nhập cùng lúc từ 1 IP thành công, RAM máy chủ tăng an toàn < 200 MB.
    - [X] `TC-2.3-07`: Học sinh gọi endpoint `/admin/*` bị trả 403, ẩn danh nhận 401.
    - [X] `TC-2.3-08`: Khóa tài khoản học sinh thì toàn bộ phiên lập tức bị hủy.
    - [X] `TC-2.3-09`: Header Authorization sai định dạng trả 401, không văng lỗi 500.
    - [X] `TC-2.3-10`: Khởi tạo admin do người dùng tự quyết qua CLI create-admin; khởi động server khi chưa có admin an toàn (không tự sinh tài khoản mặc định); tạo trùng báo lỗi rõ ràng.
- [X] **Bước 2.4 — Dịch vụ thời gian nghiệp vụ (`Clock`) & Các hàm thuần**

  - [X] Cài đặt interface `Clock` và `SystemClock` (dùng UTC), hỗ trợ `FakeClock` cho kiểm thử.
  - [X] Xây dựng các hàm tính toán thời hạn thuần: `compute_deadline`, `is_writable`, `remaining_seconds`.
  - [X] Endpoint `/api/v1/time` trả về thời gian chuẩn của server.
  - [X] Cơ chế giám sát lệch giờ (clock skew) giữa ứng dụng và Postgres trong `/readyz` (> 2s ghi log cảnh báo).
  - [X] Thêm test CI quét cấm triệt để việc gọi `datetime.now()` ngoài thư mục `core/time.py`.

  - **Kiểm thử cần đạt:**
    - [X] `TC-2.4-01`: Tính hạn bình thường: $start + duration$ đúng từng giây.
    - [X] `TC-2.4-02`: Tính hạn bị cắt bởi `close_at` khi $start + duration > close\_at$.
    - [X] `TC-2.4-03`: Cộng giờ `extra_seconds` gia hạn chính xác deadline.
    - [X] `TC-2.4-04`: Đúng thời điểm $deadline + grace$ cho phép ghi, thêm $1\mu s$ bị từ chối.
    - [X] `TC-2.4-05`: Truyền datetime naive (không múi giờ) bị ném lỗi ngay.
    - [X] `TC-2.4-06`: `remaining_seconds` làm tròn lên và không bao giờ âm.
    - [X] `TC-2.4-07`: Giả lập lệch giờ > 2s giữa app và DB ghi log cảnh báo `clock_skew`.
    - [X] `TC-2.4-08`: CI grep không phát hiện `datetime.now()` ngoài `core/time.py`.
- [X] **Bước 2.5 — Khung Frontend: API Client, Routing & Xử lý lỗi toàn cục**

  - [X] Viết API client `lib/api.ts` phân biệt `ApiError` và `NetworkError`.
  - [X] Cấu hình tự động retry tối đa 3 lần cho GET/idempotent request khi gặp lỗi mạng hoặc 502/503/504.
  - [X] Xử lý token 401: Chuyển hướng login kèm `returnTo`, riêng trang làm bài giữ nguyên outbox.
  - [X] Bắt tín hiệu máy chủ Render ngủ: Chờ > 3s hiện Banner "Đang đánh thức máy chủ", poll `/healthz` tự phục hồi.
  - [X] Cấu hình TanStack Query (`staleTime: 30s`, tắt refetchOnWindowFocus khi đang làm bài).
  - [X] Bộ định tuyến React Router bọc `RequireAuth(role)`.
  - [X] Bắt sự kiện `vite:preloadError` khi có deploy bản mới, hiện hộp thoại tải lại mà không mất draft.
  - [X] Quản lý từ điển tiếng Việt tập trung `lib/i18n/vi.ts`.

  - **Kiểm thử cần đạt:**
    - [X] `TC-2.5-01`: Phân biệt rành mạch giữa HTTP 500 (ApiError) và mất mạng (NetworkError).
    - [X] `TC-2.5-02`: GET request tự động thử lại thành công khi server chập chờn 503.
    - [X] `TC-2.5-03`: POST không idempotent không bao giờ tự động thử lại khi mất mạng.
    - [X] `TC-2.5-04`: Token hết hạn tự động đưa về login và chuyển lại trang cũ sau đăng nhập.
    - [X] `TC-2.5-05`: Banner "Đang đánh thức máy chủ" tự động ẩn khi server khởi động xong.
    - [X] `TC-2.5-06`: Máy chủ tắt hẳn quá 90s hiện thông báo lỗi kèm nút thử lại thủ công.
    - [X] `TC-2.5-07`: Deploy bản mới kích hoạt preload error nhưng outbox trong localStorage vẫn nguyên vẹn.
    - [X] `TC-2.5-08`: Học sinh không thể truy cập URL admin và ngược lại.
    - [X] `TC-2.5-09`: Khi `localStorage` bị chặn, ứng dụng tự fallback lưu phiên trên bộ nhớ tạm.

---

### GIAI ĐOẠN 3. QUẢN LÝ LỚP, HỌC SINH & NHẬP CSV (3 NGÀY)

- [X] **Bước 3.1 — API Quản lý Lớp**

  - [X] CRUD lớp học: Chuẩn hóa `code` chữ hoa (`10A1`), kiểm tra môn học `toan/tin/both`.
  - [X] Xóa lớp an toàn: Nếu lớp đã giao đề thi $\to$ từ chối xóa (409), chuyển sang cờ `is_archived=true`.
  - [X] Danh sách lớp: Hỗ trợ phân trang, tìm kiếm, tính số lượng học sinh bằng 1 câu query (chống N+1).
  - [X] Khóa lạc quan: Header/Body gửi `version`, xung đột trả về 409 version_conflict.

  - **Kiểm thử cần đạt:**
    - [X] `TC-3.1-01`: Tạo lớp thành công, mã lớp tự động chuẩn hóa chữ hoa.
    - [X] `TC-3.1-02`: Tạo trùng mã lớp trả về mã 409 class_code_taken.
    - [X] `TC-3.1-03`: Lớp đã giao đề không cho xóa cứng, chuyển sang lưu trữ ẩn.
    - [X] `TC-3.1-04`: Tìm kiếm với ký tự `%` và `_` không bị lỗi SQL LIKE.
    - [X] `TC-3.1-05`: Phân trang với tham số biên (limit=0, offset âm) được validate chuẩn.
    - [X] `TC-3.1-06`: Tải danh sách 50 lớp chỉ tốn $\le 3$ câu query SQL.
    - [X] `TC-3.1-07`: Sửa đồng thời cùng version trả 409 cho người đến sau.
- [X] **Bước 3.2 — API Quản lý Học sinh & Ghi danh vào Lớp**

  - [X] CRUD học sinh: Chuẩn hóa username regex `^[a-z0-9._-]{3,32}$`, chuẩn hóa tên Unicode NFC.
  - [X] Mật khẩu học sinh do giáo viên tự nhập hoặc chủ động chọn "Tự sinh ngẫu nhiên an toàn" (tuyệt đối không dùng mật khẩu mặc định cố định); chỉ trả về mật khẩu gốc **duy nhất 1 lần** khi tạo/reset.
  - [X] Ghi danh theo tập hợp (`PUT /admin/classes/{id}/members` body `{user_ids: [...]}`):
    - [X] Khóa dòng lớp `SELECT ... FOR UPDATE`.
    - [X] Thao tác idempotent (tính tập thêm/bớt và thực thi trong 1 transaction).
  - [X] Rút học sinh khỏi lớp giữa chừng: Không hủy bài làm đang thi dở của học sinh.
  - [X] Khóa tài khoản / Đặt lại mật khẩu: Hủy toàn bộ `sessions` hiện có của học sinh.

  - **Kiểm thử cần đạt:**
    - [X] `TC-3.2-01`: Tạo học sinh validate chặt username, từ chối trùng lặp.
    - [X] `TC-3.2-02`: Mật khẩu sinh tự động chỉ xuất hiện trong phản hồi tạo mới, không thấy ở GET.
    - [X] `TC-3.2-03`: Ghi danh cùng 1 danh sách nhiều lần không sinh lỗi và không nhân đôi dữ liệu.
    - [X] `TC-3.2-04`: Danh sách ghi danh chứa ID không tồn tại sẽ rollback toàn bộ.
    - [X] `TC-3.2-05`: Học sinh thuộc nhiều lớp nhận đề thi không bị nhân đôi đề.
    - [X] `TC-3.2-06`: Hai admin cùng ghi danh đồng thời được tuần tự hóa, dữ liệu toàn vẹn.
    - [X] `TC-3.2-07`: Rút học sinh khỏi lớp khi đang làm bài thi vẫn cho phép nộp bài bình thường.
    - [X] `TC-3.2-08`: Khóa tài khoản lập tức thu hồi quyền và đá phiên đăng nhập.
- [X] **Bước 3.3 — Nhập học sinh hàng loạt bằng CSV (Quy trình 2 pha)**

  - [X] Xử lý encoding file: Tự nhận diện UTF-8 có BOM và Windows-1258 (Excel tiếng Việt).
  - [X] Tự nhận diện dấu phân cách `,` hoặc `;` hoặc `\t`.
  - [X] Hỗ trợ 2 pha: `dry_run=true` (kiểm tra toàn bộ, trả lỗi từng dòng) và `dry_run=false` (commit atomic).
  - [X] Cột mật khẩu trong CSV do giáo viên tự thiết lập cho từng học sinh; nếu ô trống chỉ tự sinh khi giáo viên chủ động kích hoạt tùy chọn trên UI (tuyệt đối không gán mật khẩu mặc định); ký tự an toàn dài 8 loại bỏ `0OIl1`.
  - [X] Băm mật khẩu tuần tự qua Argon2 semaphore chống nghẽn CPU.
  - [X] Xuất file CSV mật khẩu cho giáo viên: UTF-8 BOM, thêm ký tự `'` chống CSV Injection (`= + - @`).

  - **Kiểm thử cần đạt:**
    - [X] `TC-3.3-01`: Đọc đúng file CSV tiếng Việt có dấu xuất từ Excel (UTF-8 BOM, phân tách `;`).
    - [X] `TC-3.3-02`: Đọc đúng file CSV lưu mã hóa Windows-1258 không bị vỡ font.
    - [X] `TC-3.3-03`: Chạy dry-run báo cáo đúng các dòng lỗi, CSDL không bị thay đổi.
    - [X] `TC-3.3-04`: Chỉ cần 1 dòng lỗi ở bước commit thì rollback toàn bộ 100%.
    - [X] `TC-3.3-05`: Phát hiện trùng lặp username ngay trong cùng 1 file CSV.
    - [X] `TC-3.3-06`: Chặn file vượt quá 500 dòng hoặc dung lượng > 1 MB.
    - [X] `TC-3.3-07`: Các ô bắt đầu bằng dấu `=HYPERLINK` được escape an toàn bằng dấu `'`.
    - [X] `TC-3.3-08`: Ô dữ liệu chứa dấu phẩy và ngoặc kép được parse chính xác.
    - [X] `TC-3.3-09`: Mật khẩu sinh ra không chứa ký tự gây nhầm và có cả chữ lẫn số.
    - [X] `TC-3.3-10`: Mã lớp trong CSV không tồn tại sẽ báo lỗi dòng cụ thể, không tự tạo lớp.
- [X] **Bước 3.4 — Giao diện Quản trị: Lớp, Học sinh & Wizard nhập CSV**

  - [X] Xây dựng trang danh sách lớp, chi tiết lớp (tab Học sinh, Ghi danh, Nhập CSV).
  - [X] Xây dựng trang danh sách học sinh (tìm kiếm debounce 300ms, hủy request cũ qua AbortController).
  - [X] Wizard nhập CSV 3 bước:
    - [X] Bước 1: Kéo thả/chọn file, kiểm tra định dạng/dung lượng.
    - [X] Bước 2: Hiển thị bảng kết quả dry-run (dòng hợp lệ màu xanh, dòng lỗi màu đỏ kèm lý do), nút xác nhận bị disable nếu còn dòng lỗi.
    - [X] Bước 3: Xác nhận lưu, hiển thị bảng mật khẩu và nút "Tải CSV mật khẩu".
  - [X] Hộp thoại xác nhận nguy hiểm (`ConfirmDialog`) cho xóa lớp, reset mật khẩu, khóa tài khoản.

  - **Kiểm thử cần đạt:**
    - [X] `TC-3.4-01`: E2E luồng tạo lớp $\to$ import CSV 10 học sinh $\to$ ghi danh $\to$ tải CSV mật khẩu.
    - [X] `TC-3.4-02`: Lỗi validate từ API hiển thị chính xác ngay dưới ô input tương ứng.
    - [X] `TC-3.4-03`: Bấm đúp nút "Tạo lớp" chỉ gửi 1 request và tạo đúng 1 lớp.
    - [X] `TC-3.4-04`: File CSV có dòng lỗi thì nút "Xác nhận nhập" bị vô hiệu hóa.
    - [X] `TC-3.4-05`: Gõ nhanh ô tìm kiếm không bị hiện tượng kết quả cũ đè kết quả mới.
    - [X] `TC-3.4-06`: Xung đột phiên bản 409 hiển thị thông báo yêu cầu tải lại dữ liệu.
    - [X] `TC-3.4-07`: Mất mạng khi bấm xác nhận nhập hiện cảnh báo rõ ràng, không tự ý gửi lại.

---

### GIAI ĐOẠN 4. SOẠN ĐỀ & QUẢN LÝ ĐỀ THI (5 NGÀY)

- [X] **Bước 4.1 — Lược đồ 5 dạng câu hỏi & Góc nhìn học sinh (Allow-list)**

  - [X] Định nghĩa Pydantic Union cho 5 dạng câu: `mcq`, `tf`, `short_text`, `short_number`, `file_upload`.
  - [X] Kiểm tra ràng buộc cấu hình và đáp án từng dạng:
    - [X] `mcq`: 2–8 lựa chọn, ID đục `o1...o8`, correct nằm trong danh sách.
    - [X] `tf`: 1–8 mệnh đề, boolean key, chế độ chấm THPT (tự chuyển proportional nếu khác 4 mệnh đề).
    - [X] `short_text`: Danh sách chuỗi chấp nhận, tùy chọn chấm tự động/thủ công, cờ review_wrong.
    - [X] `short_number`: Parse số chuẩn khoa học, sai số tuyệt đối/tương đối.
    - [X] `file_upload`: Giới hạn số file (1–5), dung lượng tối đa (1–MAX_MB), đuôi file hợp lệ.
  - [X] Xây dựng hàm `student_view()` lọc triệt để bằng **allow-list**: Tuyệt đối không để lộ `answer_key`, `explanation_md`, `accepted`, `correct` ra học sinh.
  - [X] Hỗ trợ xáo trộn lựa chọn trắc nghiệm ổn định bằng `stable_key(seed, qid, oid)`.

  - **Kiểm thử cần đạt:**
    - [X] `TC-4.1-01`: Tạo thành công câu hỏi hợp lệ cho cả 5 dạng.
    - [X] `TC-4.1-02`: Cấu hình sai lược đồ (MCQ 1 lựa chọn, file_upload đuôi .exe) bị từ chối 422.
    - [X] `TC-4.1-03`: Điểm câu hỏi âm hoặc vượt 100 điểm hoặc quá 2 số thập phân bị từ chối.
    - [X] `TC-4.1-04`: Quét đệ quy JSON trả về qua `student_view`, đảm bảo 0 rò rỉ đáp án/giải thích.
    - [X] `TC-4.1-05`: Property test Hypothesis sinh câu ngẫu nhiên đảm bảo góc nhìn học sinh luôn sạch.
    - [X] `TC-4.1-06`: Câu hỏi hỏng dữ liệu trong DB được đánh dấu `unavailable`, không làm sập cả đề.
    - [X] `TC-4.1-07`: Xáo trộn lựa chọn cùng seed cho thứ tự giống hệt nhau, khác seed cho thứ tự khác.
    - [X] `TC-4.1-08`: Câu Đúng/Sai 3 mệnh đề chọn mode THPT tự động chuyển sang proportional kèm cảnh báo.
- [X] **Bước 4.2 — API Đề thi, Vòng đời đề thi & Khóa nội dung**

  - [X] Máy trạng thái vòng đời đề: `draft` $\to$ `published` $\to$ `closed` $\to$ `archived`.
  - [X] Endpoint `GET /admin/exams/{id}/validate` kiểm tra điều kiện trước khi xuất bản.
  - [X] Cơ chế khóa nội dung đề thi (`locked_at`): Khi có học sinh đầu tiên bắt đầu làm bài $\to$ khóa cứng không cho sửa/xóa/đổi thứ tự câu hỏi và điểm số.
  - [X] Cho phép sửa các thông tin không ảnh hưởng bài làm sau khi khóa: Tiêu đề, mô tả, hiển thị kết quả, gia hạn `close_at`.
  - [X] API đổi thứ tự câu hỏi trong 1 transaction nhờ ràng buộc `DEFERRABLE`.
  - [X] API nhân bản đề thi: Sao chép đề, câu hỏi, và sao chép đối tượng ảnh trên R2 sang khóa mới.

  - **Kiểm thử cần đạt:**
    - [X] `TC-4.2-01`: Chuyển trạng thái đúng ma trận hợp lệ; chuyển sai trả về 409 invalid_transition.
    - [X] `TC-4.2-02`: Xuất bản đề chưa có câu hỏi hoặc chưa giao lớp bị từ chối kèm danh sách lỗi.
    - [X] `TC-4.2-03`: Khi có học sinh bắt đầu làm bài, sửa điểm câu hỏi hoặc xóa câu bị chặn 409 exam_locked.
    - [X] `TC-4.2-04`: Gia hạn `close_at` của đề thi không làm thay đổi hạn của attempt đang làm dở.
    - [X] `TC-4.2-05`: Đổi thứ tự câu hỏi bằng danh sách ID mới thành công, gửi thiếu/thừa ID trả 422.
    - [X] `TC-4.2-06`: Nhân bản đề thi sao chép cả ảnh sang file R2 mới độc lập hoàn toàn.
    - [X] `TC-4.2-07`: Lỗi giữa chừng khi sao chép ảnh R2 sẽ rollback toàn bộ và xóa ảnh rác.
    - [X] `TC-4.2-08`: Sửa đồng thời cùng version của đề thi trả 409 cho người sau.
    - [X] `TC-4.2-09`: Đề đã đóng chỉ được mở lại nếu close_at còn ở tương lai hoặc NULL.
- [X] **Bước 4.3 — Tải ảnh cho đề thi & Phát ảnh bảo mật**

  - [X] Client nén ảnh bằng `browser-image-compression` trước khi tải lên.
  - [X] Server đọc stream kiểm tra dung lượng $\le 5$ MB, chặn ngay lập tức nếu vượt ngưỡng.
  - [X] Kiểm tra chữ ký file thực tế bằng Pillow, chặn file SVG, chặn "bom ảnh" qua `MAX_IMAGE_PIXELS`.
  - [X] Re-encode ảnh sang định dạng chuẩn WEBP (loại bỏ toàn bộ dữ liệu EXIF/GPS).
  - [X] Lưu trữ trên Cloudflare R2 khóa `exams/{exam_id}/img/{uuid}.webp`, lưu DB bảng `files`.
  - [X] Cơ chế phát ảnh an toàn: Thay thế thẻ `asset:<uuid>` thành URL ký tạm thời (TTL 6 giờ).
  - [X] Chặn tham chiếu chéo: Chỉ phát ảnh thuộc quyền sở hữu của đúng đề thi đó.

  - **Kiểm thử cần đạt:**
    - [X] `TC-4.3-01`: Tải ảnh PNG hợp lệ lưu thành công dạng WEBP và sinh mã `asset:<uuid>`.
    - [X] `TC-4.3-02`: Đổi đuôi file exe/pdf thành png bị từ chối 415 invalid_image.
    - [X] `TC-4.3-03`: Tải ảnh quá 5 MB bị ngắt kết nối ngay và trả mã 413.
    - [X] `TC-4.3-04`: Ảnh bom giải nén kích thước 30.000x30.000 px bị từ chối, server không treo.
    - [X] `TC-4.3-05`: File SVG chứa mã JavaScript độc hại bị từ chối.
    - [X] `TC-4.3-06`: Ảnh chụp điện thoại có tọa độ GPS trong EXIF bị xóa sạch sau khi upload.
    - [X] `TC-4.3-07`: URL ký phát ảnh hết hạn sau thời gian TTL quy định.
    - [X] `TC-4.3-08`: Chèn mã `asset:` của đề thi khác vào đề này sẽ không hiển thị ảnh.
    - [X] `TC-4.3-09`: Lỗi ghi CSDL sau khi upload R2 sẽ tự động xóa đối tượng bù trừ trên R2.
    - [X] `TC-4.3-10`: Học sinh gọi endpoint upload ảnh đề thi bị trả mã 403.
- [X] **Bước 4.4 — Giao diện Soạn đề thi (Live Preview & LaTeX Toolbar)**

  - [X] Bố cục giao diện 3 cột desktop: Danh sách câu hỏi (kéo thả dnd-kit) | Form soạn thảo | Live Preview.
  - [X] Form soạn thảo theo từng dạng câu dùng react-hook-form + zod.
  - [X] Thanh công cụ LaTeX chèn nhanh mẫu công thức (phân số, tích phân, căn số, ma trận, hệ phương trình...).
  - [X] Hỗ trợ dán ảnh trực tiếp từ Clipboard (`Ctrl+V`) tự động tải lên và chèn Markdown.
  - [X] Tự động lưu nháp (Autosave) debounce 1.5s, tạm hoãn khi đang gõ tiếng Việt có dấu (sự kiện composition).
  - [X] Bắt sự kiện rời trang `beforeunload` khi còn thay đổi chưa lưu.
  - [X] Xử lý xung đột phiên bản 409: Hộp thoại cho phép copy nội dung vào clipboard trước khi tải lại.

  - **Kiểm thử cần đạt:**
    - [X] `TC-4.4-01`: Soạn đề đủ 5 dạng câu hỏi, lưu và tải lại trang giữ nguyên toàn bộ dữ liệu.
    - [X] `TC-4.4-02`: Khung xem trước hiển thị giống hệt giao diện làm bài của học sinh và không lộ đáp án.
    - [X] `TC-4.4-03`: Gõ tiếng Việt bộ gõ Telex không bị kích hoạt request lưu giữa chừng ký tự.
    - [X] `TC-4.4-04`: Dán ảnh từ clipboard hiển thị thanh tiến trình và chèn ảnh thành công.
    - [X] `TC-4.4-05`: Kéo thả đổi vị trí câu hỏi lưu lại đúng thứ tự mới.
    - [X] `TC-4.4-06`: Mất mạng khi đang soạn hiển thị cảnh báo "Chưa lưu được" và tự lưu khi có mạng lại.
    - [X] `TC-4.4-07`: Mở 2 tab soạn cùng 1 câu sẽ nhận cảnh báo xung đột phiên bản rõ ràng.
    - [X] `TC-4.4-08`: Công thức toán gõ sai cú pháp hiện lỗi tại chỗ và tăng bộ đếm cảnh báo.
    - [X] `TC-4.4-09`: Đề thi đã khóa sẽ chuyển toàn bộ form sang chế độ chỉ đọc (read-only).
    - [X] `TC-4.4-10`: Khung thử số câu `short_number` cho phép giáo viên nhập thử nghiệm các giá trị.
- [ ] **Bước 4.5 — Xuất bản, Giao lớp & Chế độ xem trước Học sinh**

  - [ ] Hộp thoại xuất bản hiển thị kết quả kiểm tra `validate` (cảnh báo công thức hỏng, lớp được giao, số học sinh).
  - [ ] API giao lớp cho đề thi: Không cho phép rút lớp đã có học sinh làm bài khi đề đã khóa.
  - [ ] Endpoint `GET /admin/exams/{id}/preview` trả về góc nhìn học sinh, **tuyệt đối không tạo attempt và không khóa đề**.
  - [ ] Chế độ xem trước trên frontend chạy sandbox (lưu bài trên RAM, đồng hồ giả lập).

  - **Kiểm thử cần đạt:**
    - [ ] `TC-4.5-01`: Mở chế độ xem trước và làm thử bài không làm tăng attempt và không set locked_at.
    - [ ] `TC-4.5-02`: Xuất bản đề thi thành công, học sinh lớp được giao thấy đề, lớp khác không thấy.
    - [ ] `TC-4.5-03`: Đề thiếu điều kiện bắt buộc (chưa chọn đáp án đúng) không cho bấm Xuất bản.
    - [ ] `TC-4.5-04`: Không thể rút lớp khỏi đề thi khi đã có học sinh thuộc lớp đó bắt đầu làm bài.
    - [ ] `TC-4.5-05`: Cảnh báo công thức toán lỗi trong đề hiển thị danh sách câu cụ thể trước khi xuất bản.
    - [ ] `TC-4.5-06`: Hai admin bấm Xuất bản cùng lúc được xử lý an toàn không sinh lỗi 500.

---

### GIAI ĐOẠN 5. QUY TRÌNH LÀM BÀI & CHỐNG GIÁN ĐOẠN (8 NGÀY) - *RỦI RO CAO NHẤT*

> **Nguyên tắc:** Bắt buộc áp dụng TDD (viết test trước khi code), kiểm thử đồng thời trên **PostgreSQL thật**.

- [ ] **Bước 5.1 — Danh sách đề & Trang giới thiệu đề của Học sinh**

  - [ ] Truy vấn đề thi lọc theo lớp của học sinh, tính toán trạng thái động: `upcoming`, `open`, `closed`, `in_progress`, `submitted`, `result_available`.
  - [ ] Sử dụng allow-list trường trả về, tuyệt đối không trả đáp án hay cấu hình nội bộ.
  - [ ] Endpoint `GET /student/exams/{id}` trả về thông tin giới thiệu đề thi (đề không thuộc lớp trả về 404).

  - **Kiểm thử cần đạt:**
    - [ ] `TC-5.1-01`: Học sinh chỉ thấy đề của lớp mình, gọi ID đề lớp khác nhận mã 404.
    - [ ] `TC-5.1-02`: Học sinh thuộc nhiều lớp được giao cùng 1 đề chỉ thấy đề xuất hiện đúng 1 lần.
    - [ ] `TC-5.1-03`: Trạng thái đề hiển thị chính xác theo các mốc thời gian server.
    - [ ] `TC-5.1-04`: Trạng thái hiển thị đúng sau khi làm bài (in_progress, submitted) và không lộ điểm.
    - [ ] `TC-5.1-05`: Đề nháp (draft) và đề lưu trữ (archived) không bao giờ hiển thị.
    - [ ] `TC-5.1-06`: Đề đã đóng nhưng học sinh đã làm vẫn hiển thị để xem lại trạng thái.
    - [ ] `TC-5.1-07`: Lỗi kết nối DB tạm thời trả 503 để client retry, không hiển thị danh sách rỗng giả.
- [ ] **Bước 5.2 — Bắt đầu làm bài thi (Idempotent & Chống bão click)**

  - [ ] Thuật toán tạo attempt trong 1 transaction:
    - [ ] Kiểm tra đề hợp lệ, trong khung giờ mở.
    - [ ] Tính toán `deadline = compute_deadline(now, duration, 0, close_at)`.
    - [ ] Chèn bản ghi `Attempt` bằng `INSERT ... ON CONFLICT (exam_id, student_id) DO NOTHING`.
    - [ ] Nếu bản ghi đã tồn tại $\to$ trả về attempt hiện có (resume hoặc finalize lười nếu đã quá hạn).
    - [ ] Khóa nội dung đề thi (`locked_at = now`) nếu đây là attempt đầu tiên của đề.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-5.2-01`: Bắt đầu bài thi bình thường, tính đúng deadline_at và gán locked_at cho đề.
    - [ ] `TC-5.2-02`: 10 luồng gọi bắt đầu đồng thời trên PostgreSQL thật chỉ tạo ra duy nhất 1 attempt.
    - [ ] `TC-5.2-03`: Mở trên 2 thiết bị cùng lúc nhận về cùng 1 attempt_id và deadline.
    - [ ] `TC-5.2-04`: Kiểm tra đúng các khung giờ trước open_at, chạm sát close_at, và sau close_at.
    - [ ] `TC-5.2-05`: Học sinh không thuộc lớp hoặc bị khóa tài khoản không thể bắt đầu làm bài.
    - [ ] `TC-5.2-06`: Gọi lại API start khi bài đã nộp trả về trạng thái đã nộp (không tạo attempt mới).
    - [ ] `TC-5.2-07`: Gọi lại API start khi bài đã quá hạn tự động kích hoạt nộp lười.
    - [ ] `TC-5.2-08`: Giá trị `locked_at` của đề thi giữ nguyên mốc thời gian của người đầu tiên làm bài.
    - [ ] `TC-5.2-09`: Gọi start với đề đang ở trạng thái draft nhận mã 404.
- [ ] **Bước 5.3 — Nạp bài làm (Tiếp tục thi) & Xáo trộn đề thi ổn định**

  - [ ] API `GET /student/attempts/{id}` kiểm tra quyền sở hữu (sai trả 404).
  - [ ] Nếu quá hạn $deadline + grace$ tự động finalize lười và trả trạng thái đã nộp.
  - [ ] Xáo trộn câu hỏi và đáp án xác định bằng `sha256(seed + id)` (không dùng hash Python).
  - [ ] Nhãn A/B/C/D do client tự render theo thứ tự hiển thị (id lựa chọn giữ nguyên mã đục).
  - [ ] Tối ưu truy vấn bằng `selectinload`, gom ảnh giải quyết bằng 1 truy vấn.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-5.3-01`: Gọi tải lại bài thi nhiều lần thứ tự câu hỏi và đáp án giữ nguyên tuyệt đối.
    - [ ] `TC-5.3-02`: Hai học sinh khác nhau làm cùng đề nhận thứ tự câu/lựa chọn khác nhau.
    - [ ] `TC-5.3-03`: Quét toàn bộ phản hồi JSON đảm bảo 0 rò rỉ bất kỳ khóa đáp án nào.
    - [ ] `TC-5.3-04`: Học sinh A gọi ID attempt của học sinh B nhận mã 404.
    - [ ] `TC-5.3-05`: Đóng tab mở lại nhận đầy đủ các câu đã trả lời kèm `client_seq`.
    - [ ] `TC-5.3-06`: Nạp bài khi đã quá hạn tự động chuyển trạng thái submitted với submitted_at = deadline.
    - [ ] `TC-5.3-07`: Tính toán `remaining_seconds` chính xác từng giây.
    - [ ] `TC-5.3-08`: Nạp bài thi 60 câu có 10 ảnh chỉ tốn $\le 4$ câu lệnh SQL.
    - [ ] `TC-5.3-09`: Câu hỏi bị lỗi cấu hình hiển thị trạng thái `unavailable` an toàn.
- [ ] **Bước 5.4 — Tự lưu đáp án từng câu (Tuần tự hóa & Chống ghi sau hạn)**

  - [ ] Endpoint `PUT /student/attempts/{id}/answers/{question_id}` kèm `client_seq`.
  - [ ] Khóa dòng attempt bằng `SELECT ... FOR SHARE` (cho phép nhiều câu lưu đồng thời nhưng chặn finalize chạy cùng lúc).
  - [ ] Kiểm tra hạn làm bài: $now \le deadline + grace$, quá hạn trả về 409 attempt_closed.
  - [ ] Upsert đáp án: Chỉ cập nhật nếu `client_seq > answers.client_seq` (chống gói tin cũ đè mới).

  - **Kiểm thử cần đạt:**
    - [ ] `TC-5.4-01`: Lưu đáp án thành công, `client_seq` và `updated_at` được cập nhật.
    - [ ] `TC-5.4-02`: Gói tin mạng đến muộn có `client_seq` nhỏ hơn bị bỏ qua không đè đáp án mới.
    - [ ] `TC-5.4-03`: Gửi lưu đáp án sau $deadline + grace$ bị từ chối 409 attempt_closed.
    - [ ] `TC-5.4-04`: Lưu đáp án khi attempt đã submitted bị từ chối 409.
    - [ ] `TC-5.4-05`: Lưu đáp án cho câu hỏi không thuộc đề thi nhận mã 404.
    - [ ] `TC-5.4-06`: Dữ liệu đáp án gửi sai schema dạng câu bị từ chối 422.
    - [ ] `TC-5.4-07`: Đáp án đã báo lưu thành công trước thời điểm nộp chắc chắn được tính điểm.
    - [ ] `TC-5.4-08`: Hai tab cùng lưu 2 câu hỏi khác nhau diễn ra song song không nghẽn nhờ `FOR SHARE`.
- [ ] **Bước 5.5 — Đồng hồ đếm ngược Client & Cơ chế chống gian lận giờ**

  - [ ] Đồng hồ đếm ngược sử dụng `performance.now()` làm gốc đơn điệu (chống việc học sinh chỉnh giờ máy tính).
  - [ ] Tính độ lệch: $offset = server\_now - client\_timestamp$.
  - [ ] Endpoint đồng bộ nhẹ `GET /student/attempts/{id}/status` trả về `remaining_seconds`.
  - [ ] Tự động đồng bộ lại đồng hồ khi: Tab hiển thị lại (`visibilitychange`), mạng online trở lại, máy thức dậy.
  - [ ] Khi hết giờ đơn điệu $\to$ tự động kích hoạt nộp bài.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-5.5-01`: Chỉnh đồng hồ hệ điều hành sớm/muộn 1 tiếng không làm sai lệch thời gian đếm ngược.
    - [ ] `TC-5.5-02`: Ẩn tab trình duyệt 5 phút rồi mở lại, đồng hồ giảm chính xác 5 phút.
    - [ ] `TC-5.5-03`: Mất mạng tạm thời đồng hồ vẫn đếm đều bằng `performance.now()`.
    - [ ] `TC-5.5-04`: Khi hết giờ trên client, hàm tự nộp được gọi ngay lập tức.
    - [ ] `TC-5.5-05`: Khi giáo viên cộng giờ, lần đồng bộ status tiếp theo cập nhật lại đồng hồ mượt mà.
    - [ ] `TC-5.5-06`: Polling đồng bộ status dùng ít băng thông (< 1 KB) và không gây tải DB.
- [ ] **Bước 5.6 — Hàng đợi lưu trữ Ngoại tuyến (Offline Outbox trong localStorage)**

  - [ ] Xây dựng `AnswerStore` lưu trữ cục bộ trên `localStorage`.
  - [ ] Khi học sinh chọn đáp án: Lưu ngay vào Outbox $\to$ Cập nhật UI $\to$ Gửi API ngầm.
  - [ ] Cơ chế Retry: Backoff lũy tiến khi gặp lỗi mạng, tự động đồng bộ tuần tự khi có mạng lại.
  - [ ] Chỉ báo trạng thái lưu trên UI: *Đã lưu / Đang lưu... / Chưa lưu (ngoại tuyến)*.
  - [ ] Xử lý sự cố hết phiên (401) khi đang làm bài: Không điều hướng sang trang khác, hiển thị Modal nhập lại mật khẩu tại chỗ để tiếp tục gửi outbox.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-5.6-01`: Tắt Wi-Fi, chọn 5 đáp án liên tiếp, dữ liệu được ghi nhận đầy đủ trong Outbox.
    - [ ] `TC-5.6-02`: Bật Wi-Fi lại, hàng đợi outbox tự động gửi hết lên server và chuyển sang "Đã lưu".
    - [ ] `TC-5.6-03`: F5 hoặc đóng trình duyệt khi mất mạng, mở lại bài thi outbox vẫn còn nguyên.
    - [ ] `TC-5.6-04`: Token bị hết hạn hiện modal đăng nhập lại, đăng nhập xong tự gửi tiếp outbox.
    - [ ] `TC-5.6-05`: Hai tab cùng mở 1 bài thi đồng bộ outbox qua sự kiện `storage` không xung đột.
    - [ ] `TC-5.6-06`: Khi `localStorage` đầy hoặc bị chặn, chuyển sang lưu tạm trên RAM và cảnh báo học sinh.
- [ ] **Bước 5.7 — Nộp bài thi & Chốt bài (Finalize Attempt Idempotent)**

  - [ ] Endpoint `POST /student/attempts/{id}/submit` nhận kèm ảnh chụp snapshot Outbox còn sót lại.
  - [ ] Khóa attempt bằng `SELECT ... FOR UPDATE` (tuần tự hóa triệt để với các request lưu).
  - [ ] Kiểm tra điều kiện nộp:
    - [ ] Nếu đã `submitted` $\to$ trả về kết quả hiện tại ngay (idempotent, không chấm lại).
    - [ ] Nếu trong hạn hoặc trong grace $\to$ áp dụng snapshot outbox (nếu seq lớn hơn) $\to$ chuyển `submitted`, `submitted_at = now`.
    - [ ] Nếu sau grace $\to$ chuyển `submitted`, `submitted_at = deadline_at`, bỏ qua snapshot outbox.
  - [ ] Kích hoạt chấm điểm tự động và tính tổng điểm bằng SQL ngay trong transaction.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-5.7-01`: Nộp bài bình thường, trạng thái chuyển submitted, tính điểm tự động thành công.
    - [ ] `TC-5.7-02`: 20 luồng gọi submit đồng thời chỉ chạy hàm chấm đúng 1 lần duy nhất.
    - [ ] `TC-5.7-03`: Bấm nộp bài nhiều lần trả về kết quả như cũ, điểm và submitted_at không đổi.
    - [ ] `TC-5.7-04`: Nộp bài khi đã quá hạn, submitted_at được gán bằng đúng deadline_at.
    - [ ] `TC-5.7-05`: Nộp bài trong khoảng thời gian grace (10s) được chấp nhận và áp dụng snapshot.
    - [ ] `TC-5.7-06`: Nộp sau grace bị coi là timeout, snapshot outbox bị hủy bỏ.
    - [ ] `TC-5.7-07`: Snapshot outbox bù đắp thành công các câu chưa kịp gửi lên server trước đó.
    - [ ] `TC-5.7-08`: Một câu hỏi bị lỗi khi chấm không làm sập tiến trình nộp bài.
    - [ ] `TC-5.7-09`: Học sinh chỉ làm 2/10 câu vẫn nộp bình thường, 8 câu còn lại tính 0 điểm.
    - [ ] `TC-5.7-10`: Phản hồi nộp bài thành công tuyệt đối không trả về số điểm hay đáp án đúng.
    - [ ] `TC-5.7-11`: Cuộc đua giữa học sinh bấm nộp và server quét hết giờ được xử lý an toàn, không deadlock.
    - [ ] `TC-5.7-12`: Giáo viên nộp hộ (force-submit) sử dụng chung luồng finalize an toàn.
- [ ] **Bước 5.8 — Tự động nộp khi hết giờ: Sweeper & Lazy Submission**

  - [ ] 4 lớp bảo đảm tự động nộp bài:
    - [ ] (1) Client tự động gửi submit khi đồng hồ về 0.
    - [ ] (2) Nộp lười (Lazy submit): Bất kỳ request nào chạm vào attempt quá hạn đều kích hoạt finalize.
    - [ ] (3) Background Sweeper (APScheduler) chạy mỗi 30 giây quét attempt quá hạn.
    - [ ] (4) Khi giáo viên mở trang Giám sát/Kết quả: Tự động quét và nộp hết các attempt quá hạn của đề.
  - [ ] Cơ chế tối ưu tiết kiệm CU-giờ Neon: Sweeper lưu cache `next_due` trên RAM, nếu chưa tới hạn thì **không query DB** để Postgres được sleep.
  - [ ] Quét bù khi server khởi động lại (Startup Catch-up).

  - **Kiểm thử cần đạt:**
    - [ ] `TC-5.8-01`: Sweeper tự động nộp đúng các attempt quá hạn, gán submitted_at = deadline_at.
    - [ ] `TC-5.8-02`: Server ngủ, học sinh không quay lại, 1 giờ sau gọi GET attempt tự kích hoạt nộp lười.
    - [ ] `TC-5.8-03`: Giáo viên mở trang giám sát thấy số liệu đã nộp chuẩn xác ngay lập tức.
    - [ ] `TC-5.8-04`: Hai tiến trình sweeper chạy song song không làm trùng lặp chấm bài.
    - [ ] `TC-5.8-05`: Một attempt bị lỗi dữ liệu không làm dừng lượt quét của các attempt khác.
    - [ ] `TC-5.8-06`: Khởi động lại server, lượt quét startup nộp hết các bài tồn đọng trong vài giây.
    - [ ] `TC-5.8-07`: Giáo viên đóng đề thi, toàn bộ học sinh đang làm chuyển submitted ngay lập tức.
    - [ ] `TC-5.8-08`: Attempt còn 1 giây không bao giờ bị sweeper nộp nhầm.
    - [ ] `TC-5.8-09`: Job sweeper chạy chậm không bị hiện tượng chồng lặp instance.
    - [ ] `TC-5.8-10`: Khi không có bài thi nào đang làm, sweeper không gửi câu lệnh đánh thức Neon DB.
    - [ ] `TC-5.8-11`: Khi giáo viên cộng giờ hoặc mở lại bài, cache next_due được cập nhật chính xác.
- [ ] **Bước 5.9 — Nộp tệp bài làm của Học sinh (`file_upload`)**

  - [ ] Endpoint upload: `POST /student/attempts/{id}/questions/{qid}/files`.
  - [ ] Kiểm tra điều kiện sơ bộ trong DB trước khi đọc file.
  - [ ] Đọc stream từng khối 64 KB, ngắt ngay khi vượt dung lượng cho phép (`max_mb`).
  - [ ] Kiểm tra chữ ký file thật (magic bytes) bằng Pillow cho ảnh và header `%PDF-` cho file PDF.
  - [ ] Re-encode ảnh sang JPEG/WEBP bỏ EXIF và giảm kích thước.
  - [ ] Ghi file lên R2 khóa `submissions/{exam_id}/{attempt_id}/{uuid}`.
  - [ ] Dùng `pg_advisory_xact_lock` tuần tự hóa các lần tải file cùng 1 câu hỏi, cập nhật `answers.value = {"file_ids": [...]}`.
  - [ ] Cơ chế bù trừ: Lỗi ghi DB sẽ tự động xóa đối tượng vừa tải lên R2.
  - [ ] Giao diện hiển thị thanh tiến trình upload (XMLHttpRequest), bắt buộc có mạng (không đưa vào offline outbox).

  - **Kiểm thử cần đạt:**
    - [ ] `TC-5.9-01`: Upload ảnh 3 MB hợp lệ thành công, lưu R2 và cập nhật danh sách file trong DB.
    - [ ] `TC-5.9-02`: Upload vượt quá số lượng `max_files` bị từ chối 409 file_limit.
    - [ ] `TC-5.9-03`: 5 request upload đồng thời khi chỉ còn chỗ cho 2 file chỉ nhận đúng 2 file.
    - [ ] `TC-5.9-04`: Upload file vượt quá `max_mb` bị ngắt kết nối ngay lập tức với mã 413.
    - [ ] `TC-5.9-05`: File giả mạo đuôi (đổi virus.exe thành .pdf) bị từ chối 415 invalid_file.
    - [ ] `TC-5.9-06`: Upload file sau khi đã hết hạn làm bài bị từ chối 409 attempt_closed.
    - [ ] `TC-5.9-07`: Upload hoặc xóa file sau khi đã nộp bài bị từ chối 409.
    - [ ] `TC-5.9-08`: Xóa file thành công, file cũ trên R2 được xóa sau khi commit DB.
    - [ ] `TC-5.9-09`: Giả lập lỗi DB khi upload, file rác trên R2 được dọn dẹp bù trừ sạch sẽ.
    - [ ] `TC-5.9-10`: Mất mạng khi đang upload hiện thông báo lỗi rõ ràng, không tạo file hỏng.
    - [ ] `TC-5.9-11`: Học sinh A không thể upload hay xóa file trong bài thi của học sinh B.
    - [ ] `TC-5.9-12`: Tên file gốc chứa ký tự độc hại (`../../etc/passwd`) được làm sạch an toàn.
- [ ] **Bước 5.10 — Lắp ráp Giao diện Làm bài Hoàn chỉnh (Student UX)**

  - [ ] Cài đặt State Machine trang làm bài: `loading` $\to$ `ready` $\rightleftarrows$ `readonly(tab khác)` $\to$ `submitting` $\to$ `submitted`.
  - [ ] Bố cục giao diện: Header cố định (Timer, SaveIndicator), thanh điều hướng câu hỏi (dạng lưới hoặc drawer), thanh công cụ chuyển câu Trước/Sau và Nộp bài.
  - [ ] Render 5 dạng câu hỏi bằng `MathText` an toàn.
  - [ ] Chức năng đánh dấu câu hỏi "cần xem lại" (chỉ lưu cục bộ trên trình duyệt).
  - [ ] Bắt sự kiện rời tab `visibilitychange` tăng `blur_count` trên server (debounce 2s, chỉ để tham khảo).
  - [ ] Hộp thoại xác nhận nộp bài hiển thị tóm tắt: Đã làm bao nhiêu câu, còn sót câu nào.
  - [ ] Màn hình "Đã nộp bài" hiển thị thời gian nộp, lý do nộp, nút quay lại danh sách đề, tuyệt đối không lộ điểm.
  - [ ] Tối ưu CSS di động: Sử dụng `100dvh` chống che nút nộp bởi thanh địa chỉ trình duyệt, touch target $\ge 44$px.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-5.10-01`: E2E luồng học sinh làm trọn vẹn đề thi 5 dạng câu từ đăng nhập đến nộp bài.
    - [ ] `TC-5.10-02`: Đang làm bài đóng tab mở lại sau 2 phút, đáp án còn nguyên, đồng hồ đếm tiếp chuẩn xác.
    - [ ] `TC-5.10-03`: Mất mạng làm tiếp 3 câu, có mạng lại tự động đồng bộ thành công.
    - [ ] `TC-5.10-04`: Đang gõ chữ mà hết giờ, hệ thống tự động nộp bài và chuyển sang màn hình "Đã nộp".
    - [ ] `TC-5.10-05`: Giáo viên cộng giờ thì đồng hồ của học sinh tăng lên ở lần đồng bộ kế tiếp.
    - [ ] `TC-5.10-06`: Bấm Nộp bài khi còn câu chưa làm hiện hộp thoại cảnh báo số câu chưa làm.
    - [ ] `TC-5.10-07`: Bấm xác nhận nộp liên tiếp nhiều lần chỉ kích hoạt gửi 1 request.
    - [ ] `TC-5.10-08`: Bị giáo viên đóng đề giữa chừng tự động chuyển sang màn hình Đã nộp.
    - [ ] `TC-5.10-09`: Hiển thị và thao tác mượt mà trên màn hình nhỏ 360x640 kèm bàn phím ảo.
    - [ ] `TC-5.10-10`: Học sinh chuyển tab ứng dụng 3 lần, bộ đếm `blur_count` ghi nhận đúng số 3.
    - [ ] `TC-5.10-11`: Cố tình truy cập trang kết quả khi giáo viên chưa công bố sẽ bị chặn 403.
    - [ ] `TC-5.10-12`: Mở cùng lúc trên điện thoại và laptop đồng bộ dữ liệu và đồng hồ an toàn.

---

### GIAI ĐOẠN 6. CHẤM ĐIỂM, CÔNG BỐ, GIÁM SÁT & QUẢN LÝ DỮ LIỆU (5 NGÀY)

- [ ] **Bước 6.1 — Bộ máy chấm điểm tự động (Pure Grading Functions)**

  - [ ] Quy ước điểm số: `answers.score = NULL` là chờ chấm tay, `score = 0` là đã chấm được 0 điểm.
  - [ ] Hàm chấm MCQ: So khớp đáp án đúng, chấm full điểm hoặc 0.
  - [ ] Hàm chấm Đúng/Sai (TF):
    - [ ] Chế độ THPT (4 mệnh đề): Đúng 1 ý $\to$ 0.10, đúng 2 ý $\to$ 0.25, đúng 3 ý $\to$ 0.50, đúng 4 ý $\to$ full điểm.
    - [ ] Chế độ tỉ lệ (proportional) hoặc all_or_nothing.
  - [ ] Hàm chấm Số (`short_number`):
    - [ ] Parse chuỗi số chuẩn hóa, hỗ trợ phân số `a/b`, dấu phẩy và chấm.
    - [ ] Chống chuỗi độc hại (`1e999999`, `NaN`, `Infinity`, `1/0`).
    - [ ] So khớp sai số tuyệt đối (`abs`) hoặc sai số tương đối (`rel`).
  - [ ] Hàm chấm Chữ (`short_text`): Chuẩn hóa Unicode NFC, tùy chọn phân biệt hoa thường và bỏ dấu tiếng Việt (đặc biệt xử lý chữ `đ/Đ`).
  - [ ] Câu hỏi nộp tệp: Mặc định chuyển sang chờ chấm tay (`score = NULL`).
  - [ ] Chức năng chấm lại toàn bộ (Regrade): Chấm lại an toàn, hỗ trợ `dry_run`, không đè điểm giáo viên đã chấm tay (`graded_by IS NOT NULL`).

  - **Kiểm thử cần đạt:**
    - [ ] `TC-6.1-01`: Chấm trắc nghiệm MCQ đúng các trường hợp đúng, sai, bỏ trống.
    - [ ] `TC-6.1-02`: Chấm Đúng/Sai mode THPT 4 mệnh đề đúng các mốc điểm 0, 0.1, 0.25, 0.5, 1.0.
    - [ ] `TC-6.1-03`: Chấm Đúng/Sai các mode proportional và all-or-nothing chính xác.
    - [ ] `TC-6.1-04`: Câu Đúng/Sai học sinh chỉ chọn 2/4 ý, các ý còn lại tính là sai.
    - [ ] `TC-6.1-05`: Chấm số nhận diện đúng các biến thể: "0,5", ".5", "0.50", "1/2", số toàn góc.
    - [ ] `TC-6.1-06`: Chấm số kiểm tra chuẩn sai số tuyệt đối và sai số tương đối.
    - [ ] `TC-6.1-07`: Đầu vào số độc hại (NaN, Infinity, số dài 10.000 ký tự) trả về None an toàn < 5ms.
    - [ ] `TC-6.1-08`: Chấm phân số 1/3 khớp chính xác với đáp án 1/3.
    - [ ] `TC-6.1-09`: Chấm chữ tiếng Việt kiểm tra chuẩn 4 tổ hợp hoa/thường và có/không dấu.
    - [ ] `TC-6.1-10`: Chữ tiếng Việt dạng tổ hợp (NFD) và dựng sẵn (NFC) được coi là bằng nhau.
    - [ ] `TC-6.1-11`: Câu chữ cấu hình manual trả về chờ chấm tay; cấu hình review_wrong bật cờ cần xem lại.
    - [ ] `TC-6.1-12`: Câu nộp file có file trả về chờ chấm tay, không có file chấm 0 điểm.
    - [ ] `TC-6.1-13`: Property test Hypothesis đảm bảo điểm số luôn nằm trong đoạn $[0, points]$.
    - [ ] `TC-6.1-14`: Chấm lại (Regrade) giữ nguyên điểm giáo viên đã sửa tay trước đó.
- [ ] **Bước 6.2 — Giao diện Chấm tay cho Giáo viên**

  - [ ] API lấy danh sách bài cần chấm: Hỗ trợ lọc theo học sinh hoặc theo câu hỏi.
  - [ ] API chấm điểm: `PUT /admin/answers/{id}/grade` kèm `version` (khóa lạc quan).
  - [ ] Tính lại tổng điểm `total_score` và cập nhật `grading_status` bằng SQL trong transaction.
  - [ ] Ghi nhật ký `audit_logs` vết thay đổi điểm của giáo viên.
  - [ ] Hiển thị bài làm học sinh: Văn bản học sinh gõ hiển thị dạng text thuần đã escape (chống XSS vào trang admin).
  - [ ] Xem file học sinh nộp: URL ký thời hạn 5 phút, hiển thị ảnh trực tiếp (xoay/zoom), file PDF mở tab mới.
  - [ ] Phím tắt chấm nhanh: Mũi tên chuyển bài, phím Enter lưu & chuyển tiếp, nút cho điểm nhanh (0, 1/2, Max).

  - **Kiểm thử cần đạt:**
    - [ ] `TC-6.2-01`: Giáo viên chấm điểm câu tự luận, tổng điểm bài thi tự động cập nhật chuẩn xác.
    - [ ] `TC-6.2-02`: Nhập điểm âm, điểm vượt trần câu hỏi hoặc sai định dạng bị từ chối 422.
    - [ ] `TC-6.2-03`: Hai giáo viên cùng chấm 1 câu nhận cảnh báo xung đột phiên bản 409.
    - [ ] `TC-6.2-04`: Không thể chấm điểm bài thi đang ở trạng thái `in_progress`.
    - [ ] `TC-6.2-05`: Giáo viên có thể ghi đè điểm của câu trắc nghiệm tự động chấm và có ghi vết audit.
    - [ ] `TC-6.2-06`: Học sinh cố tình nhập mã script vào câu trả lời, trang chấm hiển thị text thô an toàn.
    - [ ] `TC-6.2-07`: Mở xem ảnh và PDF học sinh nộp thành công, URL hết hạn sau 5 phút.
    - [ ] `TC-6.2-08`: Chấm 10 bài liên tiếp bằng phím tắt hoạt động mượt mà, lưu đủ điểm.
    - [ ] `TC-6.2-09`: Học sinh gọi API chấm bài của giáo viên bị chặn 403.
- [ ] **Bước 6.3 — Công bố Kết quả Thi (Có kiểm soát)**

  - [ ] Mặc định học sinh **không được xem điểm hay đáp án**.
  - [ ] API công bố: `POST /admin/exams/{id}/release` chọn phạm vi (cả lớp hoặc từng học sinh) và mức độ:
    - [ ] `score_only`: Chỉ xem tổng điểm, thang điểm 10.
    - [ ] `full`: Xem chi tiết từng câu, đáp án học sinh chọn, đáp án đúng, lời giải thích.
  - [ ] Hỗ trợ thu hồi công bố (`unrelease`).
  - [ ] API học sinh xem kết quả: Kiểm tra quyền, chưa công bố trả 403 kèm `Cache-Control: no-store`.
  - [ ] Cảnh báo giáo viên trước khi công bố nếu đề thi vẫn còn câu chưa chấm tay xong.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-6.3-01`: Học sinh vào xem kết quả khi chưa công bố bị chặn 403 result_not_released.
    - [ ] `TC-6.3-02`: Công bố mức `score_only` chỉ thấy tổng điểm, không lộ đáp án đúng hay câu hỏi.
    - [ ] `TC-6.3-03`: Công bố mức `full` thấy đầy đủ câu hỏi, đáp án đúng và lời giải thích.
    - [ ] `TC-6.3-04`: Công bố cho học sinh A thì học sinh B vẫn bị chặn 403.
    - [ ] `TC-6.3-05`: Giáo viên thu hồi công bố, học sinh tải lại trang lập tức bị chặn xem điểm.
    - [ ] `TC-6.3-06`: Công bố kết quả khi còn học sinh đang làm bài không gây ảnh hưởng đến bài đang làm.
    - [ ] `TC-6.3-07`: Đề còn câu chưa chấm hiện cảnh báo rõ cho giáo viên trước khi xác nhận công bố.
    - [ ] `TC-6.3-08`: Trình duyệt không lưu cache kết quả khi đã thu hồi công bố.
    - [ ] `TC-6.3-09`: Quét toàn bộ network trước khi công bố, đảm bảo 0 rò rỉ điểm số.
- [ ] **Bước 6.4 — Giám sát Trực tiếp & Quyền can thiệp của Giáo viên**

  - [ ] Trang giám sát thời gian thực: Danh sách học sinh, trạng thái (Chưa vào / Đang làm / Đã nộp), thời gian còn lại, số câu đã lưu, lần lưu cuối, số lần rời tab (`blur_count`).
  - [ ] Tự động cập nhật bằng Polling 10s (chỉ chạy khi tab đang active, tab ẩn tự dừng).
  - [ ] Các quyền can thiệp của giáo viên:
    - [ ] **Cộng giờ:** `POST /admin/attempts/{id}/extend` (có thể vượt `close_at` theo chủ đích, có ghi vết).
    - [ ] **Mở lại bài thi:** `POST /admin/attempts/{id}/reopen` (chuyển về in_progress, giữ nguyên đáp án cũ).
    - [ ] **Nộp hộ:** `POST /admin/attempts/{id}/force-submit`.
    - [ ] **Thu hồi phiên:** `POST /admin/students/{id}/revoke-sessions`.
    - [ ] **Làm nóng hệ thống:** `POST /admin/system/warmup` (chạy query mẫu và HEAD R2 kiểm tra độ trễ).
  - [ ] Tô nổi các học sinh có dấu hiệu mất mạng (lần lưu cuối > 3 phút) hoặc sắp hết giờ.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-6.4-01`: Bảng giám sát hiển thị đầy đủ danh sách học sinh của các lớp được giao đề.
    - [ ] `TC-6.4-02`: Giáo viên cộng 300 giây cho học sinh, bài thi của học sinh đó tăng đúng 5 phút.
    - [ ] `TC-6.4-03`: Giáo viên có thể cộng giờ vượt mốc `close_at` của đề thi thành công.
    - [ ] `TC-6.4-04`: Thao tác cộng giờ sai trạng thái hoặc số giây không hợp lệ bị từ chối 422/409.
    - [ ] `TC-6.4-05`: Mở lại bài đã nộp cho phép học sinh làm tiếp và nộp lại bình thường.
    - [ ] `TC-6.4-06`: Thao tác nộp hộ gọi nhiều lần hoạt động an toàn idempotent.
    - [ ] `TC-6.4-07`: Thu hồi phiên đăng nhập học sinh lập tức đá văng phiên, đăng nhập lại thi tiếp bình thường.
    - [ ] `TC-6.4-08`: Ẩn tab giám sát 2 phút không phát sinh request polling vô ích.
    - [ ] `TC-6.4-09`: Nút "Làm nóng hệ thống" kiểm tra đầy đủ độ trễ kết nối DB và R2.
    - [ ] `TC-6.4-10`: Học sinh ngừng gửi đáp án quá 3 phút tự động được tô màu cảnh báo trên bảng.
    - [ ] `TC-6.4-11`: Mọi thao tác can thiệp đều ghi lại vết trong bảng `audit_logs`.
- [ ] **Bước 6.5 — Xuất CSV Bảng điểm & Dọn dẹp dữ liệu tự động**

  - [ ] Xuất CSV bảng điểm `GET /admin/exams/{id}/export.csv`:
    - [ ] Stream dữ liệu từng dòng (không nạp cả bảng vào RAM).
    - [ ] Mã hóa `utf-8-sig` (BOM) mở trực tiếp trên Excel tiếng Việt không lỗi font.
    - [ ] Chống CSV Injection: Thêm ký tự `'` ở đầu ô chứa `= + - @`.
    - [ ] Đầy đủ thông tin: Mã lớp, Username, Họ tên, Trạng thái, Giờ nộp, Điểm tổng, Điểm từng câu.
  - [ ] Xóa dữ liệu bài thi `DELETE /admin/exams/{id}/data`:
    - [ ] Bắt buộc xác nhận gõ đúng tên đề thi (`confirm_title`).
    - [ ] Xóa bài làm, đáp án, file nộp trong DB và xóa đối tượng trên R2.
    - [ ] Giữ nguyên đề thi và các câu hỏi.
  - [ ] Job định kỳ dọn dẹp dữ liệu lưu ngắn hạn (chạy 02:00 hàng đêm):
    - [ ] Xóa bài thi của đề đã lưu trữ quá số ngày quy định (`DATA_RETENTION_DAYS`).
    - [ ] Dọn file R2 mồ côi và session hết hạn.
    - [ ] Chạy chế độ `dry_run` trong tuần đầu tiên.
  - [ ] Trang Cài đặt hiển thị dung lượng DB và cảnh báo khi vượt 80% hạn mức 0.5 GB của Neon.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-6.5-01`: Xuất file CSV mở trên Excel tiếng Việt hiển thị chuẩn 100% không vỡ font.
    - [ ] `TC-6.5-02`: Tên học sinh chứa công thức `=cmd|...` được escape an toàn bằng `'`.
    - [ ] `TC-6.5-03`: Xuất file đề thi lớn (40 học sinh x 60 câu) trong thời gian < 3 giây qua streaming.
    - [ ] `TC-6.5-04`: Xóa dữ liệu đề thi dọn sạch bài làm và file R2, giữ nguyên đề và câu hỏi.
    - [ ] `TC-6.5-05`: Nhập sai tên đề thi khi bấm xác nhận xóa bị từ chối 422.
    - [ ] `TC-6.5-06`: Lỗi mạng với R2 khi xóa không làm rollback dữ liệu đã xóa trong DB.
    - [ ] `TC-6.5-07`: Gọi xóa dữ liệu 2 lần liên tiếp hoạt động an toàn idempotent.
    - [ ] `TC-6.5-08`: Job dọn dẹp tự động ở chế độ dry-run chỉ ghi log, không xóa dữ liệu thật.
    - [ ] `TC-6.5-09`: File rác mồ côi trên R2 quá 1 giờ bị job đêm dọn dẹp sạch sẽ.
    - [ ] `TC-6.5-10`: Dung lượng DB vượt 80% hiển thị cảnh báo đỏ trên trang Cài đặt.

---

### GIAI ĐOẠN 7. ĐẢM BẢO CHẤT LƯỢNG (4 NGÀY)

- [ ] **Bước 7.1 — Rà soát Bảo mật Hệ thống**

  - [ ] Viết file ma trận quyền `tests/expected_access.yaml` phân loại toàn bộ route OpenAPI.
  - [ ] Test tự động kiểm tra ma trận quyền (student vào admin $\to$ 403, ẩn danh $\to$ 401, route mới chưa khai báo làm test fail).
  - [ ] Kiểm thử lỗ hổng IDOR trên toàn bộ endpoint có tham số ID.
  - [ ] Bộ dò rò rỉ đáp án tự động `assert_no_leak()` bọc toàn bộ response của học sinh.
  - [ ] Kiểm thử Stored XSS trên nội dung Markdown đề, đáp án chữ của học sinh, tên file.
  - [ ] Kiểm thử bộ 8 file độc hại (exe đổi đuôi, zip bom, svg script...).
  - [ ] Kiểm thử SQL Injection trên các tham số tìm kiếm và sắp xếp.
  - [ ] Kiểm tra Header bảo mật: CSP, `X-Content-Type-Options: nosniff`, `Referrer-Policy`.
  - [ ] Quét lỗ hổng phụ thuộc và bí mật: `pip-audit`, `pnpm audit`, `gitleaks`.
  - [ ] Kiểm tra nguyên tắc không khởi tạo mặc định: Sau khi chạy migration sạch trên DB mới, bảng `users` rỗng hoàn toàn, không có tài khoản admin hay học sinh mặc định nào tồn tại.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-7.1-01`: 100% endpoint được kiểm soát quyền, không có route hở.
    - [ ] `TC-7.1-02`: Đổi ID sang của người khác ở mọi endpoint đều nhận mã 404 (chống IDOR).
    - [ ] `TC-7.1-03`: Bộ dò rò rỉ đáp án báo cáo 0 vi phạm trên toàn bộ luồng thi của học sinh.
    - [ ] `TC-7.1-04`: Mọi payload XSS đều bị triệt tiêu, không thực thi script trên trình duyệt.
    - [ ] `TC-7.1-05`: 8 file tải lên độc hại đều bị từ chối và không ghi vào R2.
    - [ ] `TC-7.1-06`: Các payload SQL Injection bị vô hiệu hóa hoàn toàn.
    - [ ] `TC-7.1-07`: Brute-force thử mật khẩu 200 lần bị chặn rate-limit sau 10 lần sai.
    - [ ] `TC-7.1-08`: Header phản hồi có đủ nosniff, Referrer-Policy, CORS chỉ cho phép đúng domain.
    - [ ] `TC-7.1-09`: Audit dependencies và gitleaks trả về 0 lỗ hổng nghiêm trọng và 0 bí mật rò rỉ.
    - [ ] `TC-7.1-10`: Log hệ thống sạch hoàn toàn, không chứa mật khẩu hay token.
    - [ ] `TC-7.1-11`: Quét CSDL sau migration sạch: 0 tài khoản, 0 mật khẩu mặc định được tạo sẵn.
- [ ] **Bước 7.2 — Kiểm thử Tải & Đồng thời (Locust Benchmark)**

  - [ ] Viết kịch bản Locust: 40 học sinh làm bài đồng thời kèm 1 giáo viên polling giám sát 10s.
  - [ ] Kịch bản tải:
    - [ ] Kịch bản A: Tăng dần 0 $\to$ 40 user trong 60 giây, làm bài trong 20 phút.
    - [ ] Kịch bản B: **Bão nộp bài** (40 học sinh cùng submit trong 2 giây).
    - [ ] Kịch bản C: **Bão đăng nhập** (40 học sinh đăng nhập trong 10 giây).
    - [ ] Kịch bản D: Chạy ngâm tải 30 phút kiểm tra rò rỉ bộ nhớ (memory leak).
  - [ ] Tinh chỉnh threadpool và giới hạn kết nối DB pool an toàn.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-7.2-01`: Tải 40 user: p95 độ trễ lưu đáp án < 500 ms, lỗi 5xx = 0.
    - [ ] `TC-7.2-02`: Bão nộp bài: 40/40 bài nộp thành công, p95 submit < 3s, không deadlock.
    - [ ] `TC-7.2-03`: Bão đăng nhập: RAM đỉnh của backend < 400 MB, không bị OOM crash.
    - [ ] `TC-7.2-04`: Chạy dài 30 phút: RAM ổn định không tăng quá 10%, kết nối DB $\le 10$.
    - [ ] `TC-7.2-05`: Kiểm tra toàn vẹn dữ liệu sau bài test: Đủ 40 bài, không mất đáp án nào.
    - [ ] `TC-7.2-06`: Giả lập vượt pool: Request xếp hàng hoặc trả 503 Retry-After, không crash server.
    - [ ] `TC-7.2-07`: Giáo viên mở tab giám sát khi tải cao: p95 < 1s, không làm nghẽn lưu đáp án.
    - [ ] `TC-7.2-08`: Chạy test khi Neon vừa thức dậy: Truy vấn đầu chậm vài trăm ms rồi ổn định.
- [ ] **Bước 7.3 — Kiểm thử Hỗn loạn (Chaos Testing trong Lớp học)**

  - [ ] Dùng Playwright, Toxiproxy và Docker restart mô phỏng 10 sự cố thực tế:
    - [ ] 1. Mất điện máy học sinh (đóng browser đột ngột, xóa cả localStorage).
    - [ ] 2. Rớt mạng 2 phút khi đang gõ bài thi.
    - [ ] 3. Hết giờ làm bài trong lúc đang mất mạng.
    - [ ] 4. Restart backend giữa kỳ thi khi 10 học sinh đang làm bài.
    - [ ] 5. Postgres tạm dừng 20 giây (Neon suspend/wake up).
    - [ ] 6. Mạng Wi-Fi chập chờn: Reset peer ngẫu nhiên 30% request kèm delay 2 giây.
    - [ ] 7. Học sinh chỉnh đồng hồ máy tính nhanh/chậm 15 phút.
    - [ ] 8. Mở bài thi trên 2 thiết bị và ghi xen kẽ đáp án.
    - [ ] 9. Trình duyệt di động tự hủy tab ở chế độ nền.
    - [ ] 10. Giáo viên đóng đề thi giữa lúc học sinh đang upload file lớn 8 MB.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-7.3-01`: Mất điện đột ngột: Mở lại máy đáp án đã báo "Đã lưu" còn đủ, thi tiếp được.
    - [ ] `TC-7.3-02`: Rớt mạng 2 phút: Hiện banner offline, có mạng lại tự đồng bộ đủ đáp án.
    - [ ] `TC-7.3-03`: Quá hạn khi offline: Bài tự nộp với đáp án đã lưu trước đó, từ chối đáp án gõ sau hạn.
    - [ ] `TC-7.3-04`: Restart backend: Học sinh chỉ thấy gián đoạn vài giây, không mất dữ liệu.
    - [ ] `TC-7.3-05`: Postgres dừng 20s: Client nhận 503 và tự thử lại thành công khi DB sống lại.
    - [ ] `TC-7.3-06`: Mạng chập chờn: Mọi đáp án cuối cùng đều đến server, không ghi đè ngược.
    - [ ] `TC-7.3-07`: Đổi giờ máy tính: Thời gian còn lại trên đồng hồ vẫn khớp chuẩn server (< 1.5s).
    - [ ] `TC-7.3-08`: Hai thiết bị ghi xen kẽ: Giữ lại giá trị có `client_seq` mới nhất.
    - [ ] `TC-7.3-09`: Trình duyệt hủy tab nền: Mở lại tab dữ liệu và đồng hồ hiển thị chính xác.
    - [ ] `TC-7.3-10`: Đóng đề khi đang tải file: Báo lỗi rõ ràng, bài nộp với phần dữ liệu đã lưu.
    - [ ] `TC-7.3-11`: 5 điều kiện bất biến (I1–I5) được thỏa mãn 100% sau mỗi ca test hỗn loạn.
- [ ] **Bước 7.4 — Bộ kiểm thử Tự động E2E & Tích hợp CI**

  - [ ] Xây dựng thư mục `e2e/` với Page Object Model cho tất cả màn hình.
  - [ ] Thiết lập chạy kiểm thử song song, cô lập dữ liệu bằng ID ngẫu nhiên.
  - [ ] Phân chia nhóm test:
    - [ ] Nhóm Smoke test (~10 phút): Chạy trên mọi Pull Request.
    - [ ] Nhóm Full E2E + Chaos (~30 phút): Chạy theo lịch hàng đêm trên nhánh `main`.
  - [ ] Sử dụng biến `TEST_CLOCK_OFFSET` để tua nhanh thời gian kiểm thử hết giờ.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-7.4-01`: Chạy song song 2 bộ test trên cùng DB không bị xung đột dữ liệu.
    - [ ] `TC-7.4-02`: Bộ test smoke chạy 20 lần liên tiếp đạt tỉ lệ ổn định > 98%.
    - [ ] `TC-7.4-03`: Bộ test smoke hoàn thành trong thời gian $\le 10$ phút.
    - [ ] `TC-7.4-04`: Khi test fail, CI xuất đầy đủ artifact: Video, Playwright trace, screenshot.
    - [ ] `TC-7.4-05`: PR làm hỏng luồng nộp bài lập tức bị CI chặn merge.
    - [ ] `TC-7.4-06`: Biến tua giờ `TEST_CLOCK_OFFSET` bị vô hiệu hóa hoàn toàn trên môi trường production.
- [ ] **Bước 7.5 — Ma trận Thiết bị, Trình duyệt, Bộ gõ Tiếng Việt & Trợ năng**

  - [ ] Kiểm thử trên các trình duyệt: Chrome, Safari iOS, Chrome Android, Samsung Internet, Edge, Firefox.
  - [ ] Kiểm thử trên thiết bị di động cấu hình yếu: Bật CPU throttle 6x trong DevTools.
  - [ ] Kiểm thử bộ gõ tiếng Việt: Telex, VNI, bàn phím ảo Gboard/iOS, tắt autocorrect/autocapitalize.
  - [ ] Cấu hình `<meta name="color-scheme" content="light">` chống chế độ Auto Dark phá vỡ tương phản.
  - [ ] Xử lý bàn phím ảo che mất nút Nộp bài bằng `visualViewport`.
  - [ ] Viết tài liệu lưu ý thiết bị `docs/ops/device-notes.md`.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-7.5-01`: Hoàn thành 100% luồng thi trên mọi trình duyệt trong ma trận.
    - [ ] `TC-7.5-02`: Máy yếu throttle 6x hiển thị câu hỏi đầu < 2s, chuyển câu < 300ms.
    - [ ] `TC-7.5-03`: Gõ tiếng Việt có dấu dài không bị mất dấu hay đảo chữ ngoài ý muốn.
    - [ ] `TC-7.5-04`: Trình duyệt bật Auto Dark không làm hỏng màu sắc và độ tương phản giao diện.
    - [ ] `TC-7.5-05`: Bàn phím ảo mở lên không che khuất ô nhập liệu và nút Nộp bài.
    - [ ] `TC-7.5-06`: Mở trong WebView của Zalo/Facebook có cảnh báo hướng dẫn mở bằng Chrome/Safari.
    - [ ] `TC-7.5-07`: Xoay ngang/dọc điện thoại không làm mất đáp án hay reset đồng hồ.
    - [ ] `TC-7.5-08`: Trình đọc màn hình VoiceOver/NVDA đọc đúng nhãn câu hỏi và chỉ báo thời gian.

---

### GIAI ĐOẠN 8. HOSTING, VẬN HÀNH & GO-LIVE (3 NGÀY)

- [ ] **Bước 8.1 — Triển khai CSDL Production trên Neon Postgres**

  - [ ] Tạo project Neon vùng Singapore, theo dõi hạn mức (0.5 GB lưu trữ, 100 CU-giờ/tháng).
  - [ ] Tạo vai trò ứng dụng riêng biệt `quiz_app` (chỉ có quyền CRUD dữ liệu, không có quyền DDL sửa schema).
  - [ ] Cấu hình kết nối pooled host cho backend, kết nối direct cho migration.
  - [ ] Thiết lập workflow GitHub Actions tự động sao lưu DB hàng tuần và trước kỳ thi: Dump mã hóa bằng `age` và đẩy lên S3 backup bucket.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-8.1-01`: Backend production kết nối Neon pooled thành công, `/readyz` trả 200.
    - [ ] `TC-8.1-02`: Đăng nhập vai trò `quiz_app` thử chạy `DROP TABLE` bị DB từ chối.
    - [ ] `TC-8.1-03`: Bộ test tích hợp chạy qua chuỗi pooled đạt 100% không lỗi prepared statement.
    - [ ] `TC-8.1-04`: Hệ thống không có bài thi rảnh 30 phút, compute Neon tự động sleep sau 5 phút.
    - [ ] `TC-8.1-05`: File sao lưu `.age` được đẩy lên S3 và không thể giải mã nếu thiếu private key.
    - [ ] `TC-8.1-06`: Khôi phục thử bản sao lưu vào DB mới thành công, số lượng bản ghi khớp 100%.
    - [ ] `TC-8.1-07`: Sau 1 tuần chạy thử, mức tiêu thụ CU-giờ < 25% hạn mức tháng.
- [ ] **Bước 8.2 — Cấu hình Lưu trữ Tệp & Ảnh trên Cloudflare R2**

  - [ ] Tạo bucket `quiz-files` (riêng tư) và `quiz-backups`.
  - [ ] Tạo API token với quyền hạn tối thiểu (*Object Read & Write* trên đúng bucket).
  - [ ] Cấu hình client `boto3` với timeout ngắn (connect timeout 3s, read timeout 10s).
  - [ ] Thiết lập quy tắc vòng đời (Lifecycle Rule): Xóa tệp bài nộp sau 120 ngày, hủy multipart dở sau 1 ngày.
  - [ ] Cơ chế chịu lỗi: R2 gặp sự cố thì việc lưu đáp án chữ/số và nộp bài vẫn hoạt động bình thường.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-8.2-01`: Truy cập trực tiếp link R2 không có chữ ký bị từ chối 403.
    - [ ] `TC-8.2-02`: URL ký hoạt động tốt trong thời hạn, hết hạn trả về 403.
    - [ ] `TC-8.2-03`: Token của bucket `quiz-files` không thể ghi sang `quiz-backups`.
    - [ ] `TC-8.2-04`: Giả lập R2 ngừng hoạt động, học sinh vẫn làm bài và nộp bài chữ/số bình thường.
    - [ ] `TC-8.2-05`: R2 bị delay cao quá 10s, backend ngắt kết nối và trả mã 502 an toàn.
    - [ ] `TC-8.2-06`: Đối tượng thử nghiệm tự động bị xóa đúng theo quy tắc lifecycle.
- [ ] **Bước 8.3 — Triển khai Backend FastAPI lên Render**

  - [ ] Viết Dockerfile multi-stage nhỏ gọn, chạy dưới quyền non-root `app`, bắt buộc `--workers 1`.
  - [ ] Tạo Web Service trên Render (gói Free, vùng Singapore), tắt tính năng Auto-Deploy.
  - [ ] Cấu hình biến môi trường trên Render theo Phụ lục A đặc tả (tuyệt đối không đặt biến `ADMIN_PASSWORD` mặc định).
  - [ ] Khởi tạo tài khoản Admin production sau khi deploy: Chạy lệnh CLI tương tác `python -m app.cli create-admin` qua Shell của Render, do chính người dùng nhập.
  - [ ] Kích hoạt deploy qua Deploy Hook từ GitHub Actions sau khi test nhánh `main` xanh.
  - [ ] Thiết lập quy tắc đóng băng triển khai (`DEPLOY_FREEZE = 1`) trước và trong giờ thi 30 phút.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-8.3-01`: Triển khai thành công, health check xanh, migration tự chạy, tạo admin do người dùng nhập qua shell và đăng nhập được.
    - [ ] `TC-8.3-02`: Thiếu biến môi trường bắt buộc, tiến trình dừng ngay và log rõ tên biến thiếu.
    - [ ] `TC-8.3-03`: Khởi động nguội từ trạng thái ngủ hoàn tất trong thời gian $\le 60$ giây.
    - [ ] `TC-8.3-04`: Kích hoạt deploy khi đang có bài thi, outbox của học sinh tự gửi bù không mất bài.
    - [ ] `TC-8.3-05`: Thao tác rollback trên Render đưa hệ thống về bản cũ thành công.
    - [ ] `TC-8.3-06`: Hệ thống chạy duy nhất 1 worker, scheduler không bị chạy trùng lặp.
    - [ ] `TC-8.3-07`: Bật `DEPLOY_FREEZE=1` thì workflow CI tự động chặn lệnh deploy.
- [ ] **Bước 8.4 — Triển khai Frontend lên Cloudflare Pages**

  - [ ] Cấu hình dự án Pages: Framework Vite, thư mục `dist`, biến `VITE_API_BASE_URL`.
  - [ ] Cấu hình file `public/_redirects`: `/* /index.html 200` hỗ trợ SPA routing.
  - [ ] Cấu hình file `public/_headers` thiết lập CSP chặt chẽ, HSTS, cache static assets `immutable`.
  - [ ] Cấu hình CORS backend Render chỉ cho phép domain Pages (`https://<ten>.pages.dev`).

  - **Kiểm thử cần đạt:**
    - [ ] `TC-8.4-01`: Truy cập trực tiếp đường dẫn sâu `/s/attempts/<id>` và F5 không bị lỗi 404.
    - [ ] `TC-8.4-02`: Duyệt toàn bộ ứng dụng không phát sinh vi phạm chính sách CSP.
    - [ ] `TC-8.4-03`: Gọi API từ domain Pages thành công, gọi từ domain khác bị chặn CORS.
    - [ ] `TC-8.4-04`: Header phản hồi có đủ bảo mật, `index.html` có no-cache, assets có immutable.
    - [ ] `TC-8.4-05`: Triển khai bản mới giữa phiên thi hiện thông báo cập nhật, tải lại không mất outbox.
    - [ ] `TC-8.4-06`: Điểm Lighthouse di động trên mạng 4G chậm: LCP < 2.5s, Performance $\ge 85$.
    - [ ] `TC-8.4-07`: Không có tài nguyên nào bị cảnh báo mixed content HTTP/HTTPS.
- [ ] **Bước 8.5 — Thiết lập Giữ máy chủ thức & Giám sát Vận hành**

  - [ ] Cấu hình cron-job.org ping endpoint `/healthz` **mỗi 10 phút, chỉ trong khung giờ thi** (từ 30 phút trước giờ thi đến 30 phút sau khi kết thúc).
  - [ ] Cấu hình cảnh báo qua Email/Telegram khi 2 lần ping liên tiếp thất bại.
  - [ ] Xây dựng trang "Trạng thái hệ thống" (`/admin/system/status`) hiển thị độ trễ DB, trạng thái R2, độ lệch đồng hồ.
  - [ ] Thiết lập Sentry theo dõi lỗi (nếu có): Cấu hình xóa sạch mật khẩu, token, nội dung đáp án trong log lỗi.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-8.5-01`: Đặt lịch ping, đến giờ thi học sinh truy cập phản hồi ngay < 1s (không bị khởi động nguội).
    - [ ] `TC-8.5-02`: Tắt backend thử nghiệm, nhận email/Telegram cảnh báo sự cố trong $\le 20$ phút.
    - [ ] `TC-8.5-03`: Sweeper bị dừng bất thường phát sinh cảnh báo đỏ trên trang trạng thái.
    - [ ] `TC-8.5-04`: Trang trạng thái hiển thị đúng màu xanh/đỏ khi các dịch vụ DB/R2 sống/chết.
    - [ ] `TC-8.5-05`: Báo cáo lỗi gửi về Sentry không chứa bất kỳ dữ liệu nhạy cảm nào.
    - [ ] `TC-8.5-06`: Sau 1 tuần hoạt động, số giờ chạy của Render nằm trong hạn mức an toàn < 750 giờ.
- [ ] **Bước 8.6 — Tên miền, Mã QR & Kiểm tra Mạng trường học**

  - [ ] Đặt tên miền Cloudflare Pages ngắn gọn, dễ nhớ (ví dụ: `quiz-toantin.pages.dev`).
  - [ ] (Tùy chọn) Cấu hình tên miền riêng nếu có nhu cầu.
  - [ ] Tạo mã QR dẫn thẳng tới trang đăng nhập để in hoặc chiếu lên màn hình lớp học.
  - [ ] Soạn tài liệu 1 trang "Hướng dẫn Học sinh tham gia thi" (yêu cầu dùng Chrome/Safari).
  - [ ] Khảo sát thực tế trên mạng Wi-Fi nhà trường và sóng 4G của 3 nhà mạng lớn (Viettel, Vina, Mobi).

  - **Kiểm thử cần đạt:**
    - [ ] `TC-8.6-01`: Chứng chỉ HTTPS hợp lệ trên mọi trình duyệt, không hiện cảnh báo bảo mật.
    - [ ] `TC-8.6-02`: Truy cập trang đăng nhập thành công trên Wi-Fi trường và 4G (không bị chặn domain).
    - [ ] `TC-8.6-03`: Quét mã QR bằng camera iPhone và Android mở thẳng trang thi.
    - [ ] `TC-8.6-04`: Chuyển đổi tên miền riêng mượt mà, hỗ trợ cả 2 domain trong giai đoạn chuyển.
    - [ ] `TC-8.6-05`: Thử nghiệm 5 học sinh có thể ghi nhớ và gõ lại tên miền chính xác sau 1 phút.
- [ ] **Bước 8.7 — Nghiệm thu Người dùng (UAT) & Diễn tập Tổng thể (Rehearsal)**

  - [ ] Chuẩn bị 1 đề thi thử đủ 5 dạng câu, 1 giáo viên và nhóm 6–10 học sinh thử nghiệm.
  - [ ] Thực hiện diễn tập trọn vẹn vòng đời một kỳ thi:
    - [ ] Giáo viên import học sinh $\to$ Tạo đề $\to$ Xuất bản $\to$ Bấm Làm nóng.
    - [ ] Học sinh đăng nhập sớm $\to$ Bắt đầu làm bài đồng loạt.
    - [ ] Cố tình gây sự cố: Tắt Wi-Fi, tắt nguồn máy, mở 2 tab, để quá giờ nộp.
    - [ ] Giáo viên can thiệp: Cộng giờ, mở lại bài, nộp hộ $\to$ Chấm tay $\to$ Công bố $\to$ Xuất CSV.

  - **Kiểm thử 10 kịch bản nghiệm thu đặc tả mục 12.2:**
    - [ ] `TC-8.7-01` (12.2#1): Đóng tab mở lại sau 2 phút, đáp án còn nguyên, đồng hồ đếm tiếp chuẩn.
    - [ ] `TC-8.7-02` (12.2#2): Ngắt mạng làm tiếp, bật lại tự đồng bộ "Đã lưu".
    - [ ] `TC-8.7-03` (12.2#3): Tắt hẳn máy đến quá giờ, bài tự nộp với đáp án đã lưu trước đó.
    - [ ] `TC-8.7-04` (12.2#4): Chỉnh giờ máy tính, thời gian còn lại vẫn chạy chuẩn theo server.
    - [ ] `TC-8.7-05` (12.2#5): Mở 2 tab cùng bài thi, không tạo attempt thứ 2, đáp án mới nhất được giữ.
    - [ ] `TC-8.7-06` (12.2#6): Server ngủ, học sinh vào trang thấy banner thức dậy và vào thi an toàn.
    - [ ] `TC-8.7-07` (12.2#7): Học sinh nộp xong không thấy điểm cho đến khi giáo viên công bố.
    - [ ] `TC-8.7-08` (12.2#8): Giáo viên cộng giờ cho 1 học sinh, chỉ học sinh đó có thêm giờ thi.
    - [ ] `TC-8.7-09` (12.2#9): 6–10 học sinh cùng thi và nộp đồng thời không bị lỗi dữ liệu.
    - [ ] `TC-8.7-10` (12.2#10): Tải file sai định dạng hoặc quá dung lượng bị từ chối rõ ràng.
    - [ ] `TC-8.7-11`: Giáo viên tự vận hành hoàn tất kỳ thi theo tài liệu không cần hỗ trợ kỹ thuật.
- [ ] **Bước 8.8 — Go-Live, Vận hành, Diễn tập Khôi phục & Xử lý Sự cố (Runbook)**

  - [ ] Hoàn thiện Checklist trước giờ thi (xem trước đề, khóa result, kiểm tra ping, bấm "Làm nóng", đóng băng deploy).
  - [ ] Soạn sổ tay Runbook xử lý sự cố nhanh (máy chủ ngủ, học sinh mất điện, quên pass, mạng lag, R2 lỗi...).
  - [ ] Quy trình sau kỳ thi: Kiểm tra nộp hết bài $\to$ Chấm tay $\to$ Xuất file CSV $\to$ Công bố $\to$ Backup DB.
  - [ ] Diễn tập khôi phục thảm họa (Disaster Recovery): Mục tiêu RPO $\le$ 1 tuần, RTO $\le$ 60 phút.
  - [ ] Diễn tập quy trình rollback bản deploy khi gặp lỗi.

  - **Kiểm thử cần đạt:**
    - [ ] `TC-8.8-01`: Diễn tập khôi phục DB từ file backup lên DB mới hoàn thành trong $\le 60$ phút.
    - [ ] `TC-8.8-02`: Diễn tập rollback bản deploy lỗi hoàn tất trong $\le 10$ phút, dữ liệu nguyên vẹn.
    - [ ] `TC-8.8-03`: Giả lập 5 sự cố trong buổi diễn tập, giáo viên xử lý theo runbook $\le 5$ phút/sự cố.
    - [ ] `TC-8.8-04`: Kỳ thi thật đầu tiên diễn ra đạt 0 mất dữ liệu, 0 lộ đề, tự nộp chuẩn xác.
    - [ ] `TC-8.8-05`: Thực hiện đầy đủ 6 bước sau kỳ thi, xuất CSV và sao lưu an toàn.
    - [ ] `TC-8.8-06`: Thử nghiệm xoay SECRET_KEY và API key R2, hệ thống khởi động lại ổn định.

---

## CỔNG CHẤT LƯỢNG GIỮA CÁC GIAI ĐOẠN (QUALITY GATES)

Trước khi chuyển sang giai đoạn tiếp theo, bắt buộc kiểm tra các điều kiện tiên quyết:

- [ ] **Gate 0 $\to$ 1:** README chạy lại được trên máy mới; Stitch MCP kết nối được hoặc đã duyệt phương án dự phòng.
- [ ] **Gate 1 $\to$ 2:** 100% màn hình trong `SITE.md` đã sinh; Impeccable + Axe không lỗi nghiêm trọng; Thư viện component có test; `MathText` qua bộ test XSS.
- [ ] **Gate 2 $\to$ 3:** Đăng nhập & phân quyền hoạt động; `alembic check` sạch; Test ma trận quyền sơ bộ đạt xanh.
- [ ] **Gate 3 $\to$ 4:** Giáo viên import CSV 40 học sinh, ghi danh và tải bảng mật khẩu thành công trên giao diện.
- [ ] **Gate 4 $\to$ 5:** Tạo và xuất bản được đề thi đủ 5 dạng câu; Bộ dò rò rỉ đáp án đạt 100% không vi phạm.
- [ ] **Gate 5 $\to$ 6:** **Toàn bộ test 5.x đạt xanh trên PostgreSQL thật**; Test chaos sơ bộ (mất mạng, F5, hết giờ) đạt chuẩn.
- [ ] **Gate 6 $\to$ 7:** Vòng đời đề thi khép kín: Chấm điểm $\to$ Công bố $\to$ Xuất CSV $\to$ Xóa dữ liệu an toàn.
- [ ] **Gate 7 $\to$ 8:** Báo cáo kiểm thử tải (40 user), chaos, bảo mật và đa thiết bị đạt ngưỡng; E2E smoke test xanh trên `main`.
- [ ] **Gate 8 $\to$ Go-Live:** 10 kịch bản nghiệm thu UAT đạt 100%; Diễn tập khôi phục và rollback thành công; Kỳ thi đầu tiên tuân thủ checklist.
