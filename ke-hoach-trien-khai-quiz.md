# KẾ HOẠCH TRIỂN KHAI: HỆ THỐNG QUIZ NỘI BỘ TOÁN – TIN
### Từ xây dựng UI/UX đến khi hosting và vận hành

> Phiên bản 1.0 · 04/11/2026 · Bám theo `quiz-toan-tin-spec.md` (đặc tả v1.0).
> Mỗi **bước nhỏ** gồm 4 phần cố định: **Tên bước → Yêu cầu cần đạt → Cách thức triển khai → Test case kiểm thử & yêu cầu cần đạt** (tối thiểu 4 test case/bước, bao phủ luồng chính, biên, lỗi, đồng thời, gián đoạn).

---

## PHẦN A. CÁCH ĐỌC & QUY ƯỚC CHUNG

### A.1 Tổng quan lộ trình

| GĐ | Nội dung | Ước tính (làm bán thời gian) | Sản phẩm bàn giao |
|---|---|---|---|
| 0 | Chuẩn bị môi trường, tài khoản dịch vụ, Antigravity + Stitch MCP + skill | 1–2 ngày | Repo chạy cục bộ, MCP Stitch kết nối được |
| 1 | UI/UX: luồng, design system, sinh hàng loạt màn hình bằng Stitch, rà slop, component React | 5–6 ngày | Bộ màn hình + thư viện component + `DESIGN.md` |
| 2 | Nền tảng: FastAPI, CSDL + migration, xác thực, đồng hồ server, khung frontend | 4 ngày | API khung + đăng nhập chạy được |
| 3 | Lớp, học sinh, ghi danh, nhập CSV | 3 ngày | Giáo viên quản lý được lớp |
| 4 | Soạn đề: 5 dạng câu, LaTeX, ảnh, vòng đời đề | 5 ngày | Tạo + xuất bản được đề hoàn chỉnh |
| 5 | Làm bài: bắt đầu, tự lưu, đồng hồ, offline, nộp, tự nộp, nộp file | 8 ngày | Học sinh làm trọn bài, chịu gián đoạn |
| 6 | Chấm điểm, công bố, giám sát, can thiệp, xuất CSV, dọn dữ liệu | 5 ngày | Vòng đời đề khép kín |
| 7 | Chất lượng: bảo mật, tải, hỗn loạn (chaos), E2E, thiết bị | 4 ngày | Báo cáo kiểm thử đạt chuẩn |
| 8 | Hosting, tên miền, giám sát, diễn tập, go-live | 3 ngày | Hệ thống chạy thật |
| | **Tổng** | **~38 ngày làm việc (≈ 6–7 tuần bán thời gian)** | |

> Đặc tả mục 13 ước 3–4 tuần chưa tính chi tiết UI/UX và kiểm thử sâu; con số trên là ước tính thận trọng sau khi thêm hai phần đó.

**Thứ tự phụ thuộc:** 0 → 1 → 2 → (3 ∥ 4) → 5 → 6 → 7 → 8. Giai đoạn 5 là rủi ro cao nhất nên viết test trước khi viết code (TDD) cho các hàm thời gian, ghi đáp án và finalize.

### A.2 Quy ước chung (áp dụng cho mọi bước)

| Hạng mục | Quy ước |
|---|---|
| ID | UUID v4 (`gen_random_uuid()` của Postgres), hiển thị rút gọn cho người dùng khi cần |
| Thời gian | Lưu `timestamptz` (UTC); API trả ISO-8601 có `Z`; hiển thị `Asia/Ho_Chi_Minh` ở frontend |
| **Nguồn thời gian nghiệp vụ** | Duy nhất một `Clock` của ứng dụng (`utcnow()`), truyền vào mọi truy vấn dưới dạng tham số `:now`. **Không trộn** `now()` của DB với đồng hồ ứng dụng cho cùng một phép so sánh (dễ lệch vài chục ms, khó kiểm thử). `created_at` mặc định của DB chỉ mang tính thông tin |
| Định dạng lỗi | `{"error":{"code":"...","message":"...","details":{...}}}`; mã HTTP: 400 dữ liệu hỏng, 401 chưa đăng nhập, 403 không đủ quyền, 404 không thấy, 409 xung đột trạng thái/phiên bản, 422 sai schema, 429 vượt giới hạn, 503 quá tải/DB chưa sẵn sàng |
| Idempotency | Mọi thao tác có thể bị gọi lặp (start, submit, finalize, save answer, import CSV commit) phải cho cùng kết quả khi gọi lại |
| Giao dịch | Một request ghi = một transaction; khóa hàng bằng `SELECT … FOR UPDATE/SHARE` khi cần thứ tự; không giữ transaction qua lời gọi mạng (S3) |
| Nhánh & commit | Trunk-based: nhánh ngắn `feat/<bước>`, commit kiểu Conventional Commits, PR phải xanh CI mới merge |
| CI tối thiểu | `ruff` + `pytest` (backend), `tsc --noEmit` + `eslint` + `vitest` (frontend), `alembic check`, quét bí mật (`gitleaks`) |
| ID test case | `TC-<số bước>-<thứ tự>`, ví dụ `TC-5.4-07` |
| Định nghĩa hoàn thành (DoD) | (1) mọi test case của bước đạt; (2) lint/type sạch; (3) có migration nếu đổi CSDL; (4) cập nhật tài liệu API/README; (5) không để `TODO` gây mất dữ liệu hoặc lộ đáp án |

### A.3 Các quyết định kỹ thuật bổ sung so với đặc tả (và lý do)

1. **SQLAlchemy đồng bộ (sync) + endpoint `def`** thay vì async: transaction dễ suy luận, đủ cho ≤ 50 người; FastAPI tự chạy endpoint `def` trong threadpool.
2. **Truyền `:now` từ `Clock` vào SQL finalize** (thay cho `now()` trong mẫu SQL ở đặc tả mục 9) để kiểm thử được bằng đồng hồ giả.
3. **Khóa hàng attempt để ghi đáp án và finalize tuần tự**: ghi đáp án dùng `FOR SHARE`, finalize dùng `FOR UPDATE` → đáp án đã được báo "đã lưu" trước thời điểm finalize chắc chắn nằm trong lần chấm (chi tiết ở bước 5.4 và 5.7).
4. **Ảnh trong đề lưu dạng `asset:<uuid>`** trong Markdown, server thay bằng URL ký có hạn khi trả dữ liệu (ảnh không công khai, hết hạn tự động).
5. **Đồng hồ client dùng `performance.now()` làm gốc (đơn điệu)** và đồng bộ lại khi tab hiện lại/online/máy thức dậy; không đếm bằng cách trừ dần mỗi giây.
6. **Giáo viên cộng giờ có thể vượt `close_at`** (ghi đè có chủ đích, có ghi vết); cộng giờ tự nhiên theo công thức đặc tả `min(start + duration + extra, close_at)` chỉ áp dụng lúc bắt đầu.
7. **Kết nối Neon qua pooler**: tắt prepared statement tự động của psycopg 3 (`prepare_threshold=None`), dùng khóa advisory kiểu transaction (`pg_try_advisory_xact_lock`) thay vì kiểu session.

### A.4 QUY TẮC BẢO MẬT CỐT LÕI: KHÔNG KHỞI TẠO MẶC ĐỊNH ĐỐI TƯỢNG NHẠY CẢM (TAKE NOTE QUAN TRỌNG)

> [!IMPORTANT]
> **NGUYÊN TẮC BẢO MẬT BẮT BUỘC: KHÔNG KHỞI TẠO MẶC ĐỊNH ĐỐI TƯỢNG NHẠY CẢM**  
> Mọi đối tượng nhạy cảm như **tài khoản, mật khẩu, thông tin đăng nhập, token bí mật... TUYỆT ĐỐI KHÔNG ĐƯỢC KHỞI TẠO MẶC ĐỊNH** trong mã nguồn, migration, file cấu hình hoặc tự động tạo khi ứng dụng khởi động. Tất cả thông tin này **phải do người dùng (quản trị viên/giáo viên) chủ động quyết định và khởi tạo**:
> 1. **Tài khoản Quản trị viên (Admin) đầu tiên:** Tuyệt đối không tạo tự động với mật khẩu/username mặc định trong code hay cấu hình môi trường. Bắt buộc phải do người dùng tạo thủ công qua lệnh CLI tương tác: `python -m app.cli create-admin` (yêu cầu người dùng tự nhập username và mật khẩu với chế độ ẩn ký tự, xác nhận mật khẩu và kiểm tra độ phức tạp tối thiểu 12 ký tự).
> 2. **Tài khoản Học sinh:** Mật khẩu phải do giáo viên trực tiếp cung cấp khi tạo hoặc nhập CSV; nếu dùng chức năng sinh ngẫu nhiên thì phải là một tùy chọn do giáo viên chủ động kích hoạt và bắt buộc tải bảng mật khẩu lưu trữ ngoài hệ thống. Tuyệt đối không dùng mật khẩu mặc định cố định (ví dụ `123456`, ngày sinh, mã lớp...).
> 3. **Dữ liệu mẫu / Seed:** Script seed môi trường dev (`python -m app.cli seed`) tuyệt đối không cài sẵn tài khoản/mật khẩu mặc định trong code hay migration production. Nếu cần tạo tài khoản kiểm thử cục bộ, script phải yêu cầu người phát triển nhập thông tin hoặc chỉ chạy trên môi trường test cô lập, không bao giờ chứa tài khoản mặc định trên production.

---

# GIAI ĐOẠN 0. CHUẨN BỊ

## Bước 0.1 — Dựng môi trường phát triển & khung monorepo

**Yêu cầu cần đạt**
- Một người mới clone repo làm theo `README` chạy được backend, frontend, Postgres cục bộ trong ≤ 15 phút.
- Có sẵn lint, test, pre-commit, CI chạy xanh với test "hello world".
- Không có bí mật nào nằm trong Git.

**Cách thức triển khai**
- **Công cụ:** Python 3.12 + `uv`; Node 20/22 LTS + `pnpm`; Docker (Windows nên dùng WSL2 + Docker Desktop); Git.
- **Cấu trúc:** đúng theo đặc tả 5.4 (`backend/`, `frontend/`, `design/`, `docs/`, `docker-compose.yml`, `.env.example`).
- **`docker-compose.yml`:** dịch vụ `db` (`postgres:16`, volume có tên, healthcheck `pg_isready`) và `minio` (S3 cục bộ để thử upload mà không đụng R2). Cổng chỉ bind `127.0.0.1`.
- **Backend:** `uv init`, thêm `fastapi uvicorn[standard] sqlalchemy>=2 alembic psycopg[binary] pydantic-settings argon2-cffi slowapi apscheduler boto3 python-multipart pillow`; dev: `pytest httpx ruff hypothesis freezegun`. Cấu hình `ruff` và `pytest` trong `pyproject.toml`.
- **Frontend:** `pnpm create vite` (React + TS); thêm `tailwindcss react-router-dom @tanstack/react-query react-hook-form zod @hookform/resolvers react-markdown remark-math rehype-katex rehype-sanitize katex @dnd-kit/core @dnd-kit/sortable`; dev: `vitest @testing-library/react @playwright/test eslint`.
- **Pre-commit:** `ruff`, `eslint`, `gitleaks`, chặn commit file `.env`.
- **CI (GitHub Actions):** job backend (service container Postgres 16 → `alembic upgrade head` → `pytest`), job frontend (`pnpm i --frozen-lockfile`, `tsc`, `eslint`, `vitest`, `vite build`).
- **Bắt lỗi cấu hình:** `Settings` (pydantic-settings) **thất bại ngay khi khởi động** nếu thiếu biến bắt buộc, in rõ tên biến thiếu, không in giá trị bí mật.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-0.1-01 | Clone sạch, chạy theo README | Máy/VM mới: `docker compose up -d`, `uv sync`, `pnpm i`, chạy 2 server | Cả hai chạy, `GET /healthz` trả 200, trang chủ Vite hiển thị |
| TC-0.1-02 | Thiếu biến môi trường | Xóa `DATABASE_URL` rồi chạy backend | Tiến trình thoát với thông báo "Thiếu biến: DATABASE_URL", mã thoát ≠ 0 |
| TC-0.1-03 | Commit nhầm bí mật | Thêm `.env` và file chứa chuỗi giống khóa AWS rồi `git commit` | Pre-commit/gitleaks chặn commit |
| TC-0.1-04 | CI | Mở PR có test cố tình sai | CI đỏ, không thể merge; sửa xong CI xanh |
| TC-0.1-05 | Dịch vụ phụ thuộc chưa sẵn sàng | Tắt container DB rồi gọi `/readyz` | `/readyz` trả 503; `/healthz` vẫn 200 (xem bước 2.1) |

---

## Bước 0.2 — Tạo tài khoản dịch vụ & quản lý bí mật

**Yêu cầu cần đạt**
- Có đủ tài khoản: GitHub, Neon, Cloudflare (Pages + R2), Render, dịch vụ ping (cron-job.org hoặc UptimeRobot).
- Bật xác thực 2 lớp cho mọi tài khoản; mỗi bí mật chỉ nằm ở nơi cần dùng.

**Cách thức triển khai**
- Tạo tài khoản bằng email riêng của dự án (để bàn giao/khôi phục dễ).
- **Neon:** tạo dự án, chọn vùng gần Việt Nam (Singapore); lấy 2 chuỗi: *direct* (cho migration) và *pooled* (cho ứng dụng). Giới hạn miễn phí cần nhớ: 0.5 GB/dự án, 100 CU-giờ/tháng.
- **Cloudflare:** tạo dự án Pages (kết nối GitHub); tạo bucket R2 **riêng tư**; tạo API token chỉ cấp quyền *Object Read & Write* trên đúng bucket đó. Lưu ý: R2 có thể yêu cầu thêm phương thức thanh toán khi bật; nếu không muốn, đổi sang Supabase Storage (cùng giao diện S3) và chỉ cần đổi 3 biến `S3_*`.
- **Render:** tạo Web Service (free) từ repo, chưa deploy.
- **Quản lý bí mật:** file `.env` cục bộ (gitignore); biến môi trường ở Render/Cloudflare; ghi danh sách biến (không ghi giá trị) trong `docs/secrets-inventory.md`.
- **Mẫu kiểm tra kết nối** (chạy cục bộ, không commit):
```bash
psql "$DATABASE_URL_DIRECT" -c "select 1"
python - <<'PY'
import boto3, os
s3 = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"],
    aws_access_key_id=os.environ["S3_ACCESS_KEY"],
    aws_secret_access_key=os.environ["S3_SECRET_KEY"], region_name="auto")
s3.put_object(Bucket=os.environ["S3_BUCKET"], Key="healthcheck.txt", Body=b"ok")
print(s3.get_object(Bucket=os.environ["S3_BUCKET"], Key="healthcheck.txt")["Body"].read())
s3.delete_object(Bucket=os.environ["S3_BUCKET"], Key="healthcheck.txt")
PY
```

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-0.2-01 | Kết nối Neon | `psql` với chuỗi direct và `sslmode=require` | Trả `1`; thử không có `sslmode=require` thì bị từ chối hoặc cảnh báo |
| TC-0.2-02 | Ghi/đọc/xóa object R2 | Chạy đoạn mã mẫu | In `b'ok'`, object bị xóa, không lỗi quyền |
| TC-0.2-03 | Bucket không công khai | Mở URL trực tiếp của object (không ký) bằng trình duyệt ẩn danh | 403/AccessDenied, không tải được |
| TC-0.2-04 | Token R2 đúng phạm vi | Dùng token để ghi vào bucket khác | Bị từ chối |
| TC-0.2-05 | 2FA & kiểm kê bí mật | Rà từng tài khoản; chạy `gitleaks detect` trên toàn lịch sử | Tất cả bật 2FA; gitleaks báo 0 phát hiện |

---

## Bước 0.3 — Cài Antigravity, skill và kết nối Stitch MCP

**Yêu cầu cần đạt**
- Antigravity thấy được Stitch MCP và gọi được ít nhất một thao tác (liệt kê/tạo project).
- Các skill thiết kế được nạp và xuất hiện trong danh sách skill của Antigravity.

**Cách thức triển khai**
- **Đăng nhập Google Cloud & bật API:**
```bash
gcloud auth login
gcloud auth application-default login
gcloud beta services mcp enable stitch.googleapis.com
```
- **Khai báo MCP** trong `mcp_config.json` của Antigravity (đường dẫn thay đổi theo bản App/CLI/IDE; mở mục MCP/Customizations trong Antigravity để biết đúng file). Có hai cách người dùng đã báo cáo chạy được, thử cách 1 trước và **đối chiếu tài liệu Stitch MCP chính thức** khi viết cấu hình:
  1. Proxy cục bộ: `npx @_davideast/stitch-mcp proxy` (bọc trong script nếu IDE không thừa kế PATH/biến môi trường).
  2. `mcp-remote` trỏ tới `https://stitch.googleapis.com/mcp`.
- **Cài skill** ở thư mục dự án (vào `.agents/skills/`):
```bash
npx skills add google-labs-code/stitch-skills --skill stitch-design
npx skills add google-labs-code/stitch-skills --skill stitch-loop
npx skills add google-labs-code/stitch-skills --skill design-md
npx skills add google-labs-code/stitch-skills --skill enhance-prompt
npx skills add google-labs-code/stitch-skills --skill react-components
npx skills add anthropics/skills -s frontend-design
npx skills add pbakaus/impeccable
```
- **Nguyên tắc nạp skill:** chỉ nạp bộ gọn ở trên; không cài thêm skill thiết kế khác để tránh chỉ dẫn mâu thuẫn. Ghi danh sách vào `docs/tooling.md`.
- **Lưu ý:** Impeccable làm việc trên **mã giao diện** trong dự án, không đọc trực tiếp thiết kế còn nằm trong Stitch; vì vậy luồng đúng là Stitch → xuất HTML/React → Impeccable rà soát (bước 1.4).
- **Phương án dự phòng nếu MCP lỗi:** dùng giao diện web Stitch, xuất HTML/ảnh thủ công vào `design/screens/`, phần còn lại của kế hoạch không đổi.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-0.3-01 | MCP nhận diện | Khởi động lại Antigravity, mở danh sách MCP | `stitch` hiển thị trạng thái đang chạy, không lỗi xác thực |
| TC-0.3-02 | Gọi thật | Nhờ agent "liệt kê các project Stitch của tôi" (hoặc tạo project `quiz-toantin`) | Trả danh sách/ID project; project xuất hiện trên web Stitch |
| TC-0.3-03 | Skill được nạp | Mở Customizations, hoặc hỏi agent liệt kê skill đang dùng | Thấy `stitch-design`, `stitch-loop`, `design-md`, `frontend-design`, `impeccable` |
| TC-0.3-04 | Hết hạn đăng nhập | Thu hồi/hết hạn token ADC rồi gọi lại | Lỗi xác thực rõ ràng; chạy lại `gcloud auth application-default login` thì hoạt động lại |
| TC-0.3-05 | Dự phòng | Tắt MCP, thực hiện quy trình xuất thủ công cho 1 màn hình | File HTML + PNG nằm đúng `design/screens/`, đặt tên theo quy ước ở bước 1.3 |

---

# GIAI ĐOẠN 1. UI/UX

## Bước 1.1 — Sơ đồ trang, luồng người dùng và bảng trạng thái giao diện

**Yêu cầu cần đạt**
- Mọi màn hình trong đặc tả mục 11 đều có trong sơ đồ trang; mỗi màn hình có đủ trạng thái: *đang tải, rỗng, lỗi, offline, hết hạn/đã nộp, không đủ quyền*.
- Không có màn hình "cụt" (luôn có đường đi tiếp hoặc quay lại).

**Cách thức triển khai**
- **Sản phẩm:** `docs/ux/sitemap.md`, `docs/ux/flows.md`, `docs/ux/state-matrix.md`.
- **Bảng route** (làm cơ sở cho React Router):

| Route | Vai trò | Màn hình |
|---|---|---|
| `/login` | chung | Đăng nhập |
| `/s/exams` | student | Danh sách đề |
| `/s/exams/:id` | student | Giới thiệu đề |
| `/s/attempts/:id` | student | Làm bài |
| `/s/attempts/:id/done` | student | Đã nộp |
| `/s/attempts/:id/result` | student | Kết quả (khi được công bố) |
| `/a` | admin | Bảng điều khiển |
| `/a/classes`, `/a/classes/:id` | admin | Lớp, chi tiết lớp, nhập CSV |
| `/a/students`, `/a/students/:id` | admin | Học sinh |
| `/a/exams`, `/a/exams/:id/edit` | admin | Danh sách đề, soạn đề |
| `/a/exams/:id/preview` | admin | Xem trước như học sinh |
| `/a/exams/:id/monitor` | admin | Giám sát trực tiếp |
| `/a/exams/:id/grading` | admin | Chấm bài |
| `/a/exams/:id/results` | admin | Kết quả đề |
| `/a/settings` | admin | Cài đặt |

- **Ma trận trạng thái:** mỗi màn hình × {loading, empty, error(code), offline, forbidden, expired/submitted}. Ánh xạ **mỗi mã lỗi API** (`attempt_closed`, `exam_not_open`, `result_not_released`, `rate_limited`…) tới một trạng thái UI cụ thể và thông điệp tiếng Việt.
- **Luồng quan trọng cần vẽ sơ đồ:** (1) học sinh làm bài từ đăng nhập đến nộp, kèm nhánh mất mạng, hết giờ, mở lại; (2) giáo viên soạn → xuất bản → giám sát → chấm → công bố; (3) nhập CSV 3 bước (tải lên → xem trước → xác nhận → tải bảng mật khẩu).
- **Nguyên tắc giao diện làm bài:** một cột chính, đồng hồ cố định phía trên, thanh điều hướng câu, thao tác chạm ≥ 44px, không có yếu tố gây xao nhãng, không hiển thị bất kỳ gợi ý đáp án nào.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-1.1-01 | Đủ màn hình | Đối chiếu danh sách mục 11 đặc tả với bảng route | 100% màn hình có route và có mục trong ma trận trạng thái |
| TC-1.1-02 | Phủ mã lỗi | Liệt kê mọi mã lỗi ở đặc tả 8.4 | Mỗi mã có ít nhất một trạng thái/thông điệp UI tương ứng |
| TC-1.1-03 | Không màn hình cụt | Đi tay qua 3 hành trình chính trên sơ đồ | Mỗi màn hình có ≥ 1 đường ra; sau "Đã nộp" có đường về danh sách đề |
| TC-1.1-04 | Nhánh gián đoạn | Soát luồng làm bài với: mất mạng, hết giờ lúc đang gõ, mở tab thứ hai, giáo viên mở lại bài | Mỗi nhánh có trạng thái UI và hành động người dùng được mô tả |
| TC-1.1-05 | Soát bởi người khác | Cho 1 giáo viên và 1 học sinh xem sơ đồ | Ghi nhận ≥ 90% họ hiểu luồng không cần giải thích; các góp ý được đưa vào bản sau |

---

## Bước 1.2 — Hệ thống thiết kế (design system) và `DESIGN.md`

**Yêu cầu cần đạt**
- Một bộ token thống nhất (màu, chữ, khoảng cách, bo góc, đổ bóng, z-index) dùng chung cho Stitch và Tailwind.
- Tất cả cặp màu chữ/nền đạt tương phản WCAG AA (≥ 4.5:1 chữ thường, ≥ 3:1 chữ lớn/biểu tượng).
- Phông chữ hiển thị đúng đầy đủ dấu tiếng Việt.

**Cách thức triển khai**
- **Định hướng thẩm mỹ:** công cụ học tập tiện dụng, tĩnh, tương phản cao, dày thông tin nhưng dễ đọc. Tránh những dấu hiệu "AI slop": nền gradient tím-xanh, kính mờ khắp nơi, lưới thẻ biểu tượng giống hệt nhau, bo góc quá lớn + bóng đổ nặng, emoji làm biểu tượng, số liệu giả, hoạt ảnh vô nghĩa.
- **Chữ:** dùng gói có tập ký tự tiếng Việt, tự host qua `@fontsource/*` (không phụ thuộc Google Fonts, tránh phải nới CSP). Gợi ý: một phông sans cho giao diện (ví dụ Be Vietnam Pro), một phông monospace cho mã (JetBrains Mono); công thức do KaTeX tự cung cấp phông.
- **Token** (ví dụ cấu trúc, giá trị cuối cùng do bước kiểm tra tương phản quyết định):
```css
:root {
  --bg: #FAFAF7;  --surface: #FFFFFF;  --ink: #1B1F24;  --ink-muted: #4B5360;
  --primary: #1F5FBF;  --primary-ink: #FFFFFF;
  --success: #1E7A46;  --warning: #8A5A00;  --danger: #B42318;
  --border: #D5D9E0;  --focus: #1F5FBF;
  --radius-sm: 6px; --radius-md: 10px;
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px; --space-6: 24px;
}
```
- **Trạng thái đồng hồ:** bình thường / cảnh báo (< 5 phút) / nguy cấp (< 1 phút). **Không chỉ dùng màu**: kèm biểu tượng và chữ ("Còn dưới 1 phút").
- **Sinh `DESIGN.md`:** dùng skill `design-md` (và chạy lệnh khởi tạo của Impeccable để lưu bối cảnh dự án) để mô tả hệ thống thiết kế bằng ngôn ngữ mà Stitch hiểu; ghi rõ nguyên tắc ở trên.
- **Xuất token sang Tailwind:** một file nguồn `design/tokens.json` → script sinh `tailwind.config.ts` (`theme.extend`) và `tokens.css`, để hai nơi không lệch nhau.
- **Script kiểm tra tương phản** (chạy trong CI):
```python
def lum(h):
    c = [int(h[i:i+2], 16)/255 for i in (1, 3, 5)]
    f = lambda v: v/12.92 if v <= 0.03928 else ((v+0.055)/1.055)**2.4
    return 0.2126*f(c[0]) + 0.7152*f(c[1]) + 0.0722*f(c[2])
def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la+0.05)/(lb+0.05)
PAIRS = [("--ink","--bg",4.5), ("--ink-muted","--bg",4.5), ("--primary-ink","--primary",4.5),
         ("--danger","--surface",4.5), ("--warning","--surface",4.5), ("--success","--surface",4.5)]
```

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-1.2-01 | Tương phản | Chạy script cho mọi cặp trong `PAIRS` (cả trạng thái hover/disabled) | Mọi cặp ≥ ngưỡng; CI đỏ nếu vi phạm |
| TC-1.2-02 | Dấu tiếng Việt | Hiển thị chuỗi "Ắ ằ ẳ ẵ ặ Ế ề ể ễ ệ Ố ồ ổ ỗ ộ Ứ ừ ử ữ ự Đ đ" ở các cỡ chữ 12/14/16/20px | Không rơi sang phông dự phòng, không chồng dấu/cắt dấu |
| TC-1.2-03 | Một nguồn token | Đổi `--primary` trong `tokens.json`, sinh lại | Tailwind và `DESIGN.md` cùng cập nhật; `grep` không còn mã màu cứng trong `src/` |
| TC-1.2-04 | Không phụ thuộc mạng ngoài | Chặn truy cập `fonts.googleapis.com`, tải trang mẫu | Chữ vẫn hiển thị đúng (do tự host) |
| TC-1.2-05 | Đồng hồ không chỉ dựa vào màu | Mô phỏng người mù màu đỏ-lục (DevTools) | Vẫn phân biệt được 3 trạng thái nhờ biểu tượng và nhãn chữ |

---

## Bước 1.3 — Sinh hàng loạt màn hình trên Stitch (một prompt, không phải gõ từng trang)

**Yêu cầu cần đạt**
- Toàn bộ ~18 màn hình (và biến thể trạng thái chính) được sinh ra từ **một prompt tổng** thông qua `stitch-loop`, dùng chung `DESIGN.md`.
- Có thể dừng/tiếp tục giữa chừng mà không sinh trùng.
- Mỗi màn hình được xuất ra `design/screens/<mã>.html` + `.png`.

**Cách thức triển khai**
- **Danh sách màn hình (`design/SITE.md`)** — là "hợp đồng" cho vòng lặp, mỗi dòng có mã, thiết bị mục tiêu, trạng thái cần có và `[ ]` chưa làm:

| Mã | Màn hình | Thiết bị | Biến thể cần sinh |
|---|---|---|---|
| S0 | Đăng nhập | mobile + desktop | lỗi sai mật khẩu, đang đăng nhập |
| S1 | Lỗi / mất kết nối / "đang đánh thức máy chủ" | mobile | 3 biến thể |
| ST1 | Danh sách đề của tôi | mobile | rỗng, có đề, đã nộp |
| ST2 | Giới thiệu đề | mobile | chưa mở, đang mở, đã đóng |
| ST3 | Làm bài | mobile (ưu tiên) + desktop | MCQ, Đúng/Sai, trả lời chữ, trả lời số, nộp file, cảnh báo < 5 phút, offline |
| ST4 | Hộp xác nhận nộp bài | mobile | còn câu chưa làm |
| ST5 | Đã nộp bài | mobile | tự nộp do hết giờ |
| ST6 | Kết quả | mobile | chỉ điểm, đầy đủ |
| AD1 | Bảng điều khiển | desktop | — |
| AD2 | Lớp + chi tiết lớp + nhập CSV 3 bước | desktop | — |
| AD3 | Học sinh | desktop | — |
| AD4 | Danh sách đề | desktop | — |
| AD5 | Soạn đề (danh sách câu + trình soạn + preview + thiết lập) | desktop | 5 dạng câu |
| AD6 | Xem trước như học sinh | desktop | dùng lại ST3 + dải thông báo |
| AD7 | Giám sát trực tiếp | desktop | — |
| AD8 | Chấm bài | desktop | theo học sinh / theo câu |
| AD9 | Kết quả đề + công bố | desktop | — |
| AD10 | Cài đặt | desktop | — |

- **Prompt tổng** (dán vào Antigravity, đã có skill và MCP):
```
Dùng stitch-loop với Stitch MCP. Bối cảnh: web làm bài kiểm tra Toán/Tin cho học sinh lớp nội bộ,
giao diện tiếng Việt. Đọc DESIGN.md làm nguồn thẩm mỹ duy nhất (không tự thêm phong cách khác).
Đọc design/SITE.md: đây là danh sách đầy đủ màn hình. Làm tuần tự từng dòng chưa đánh dấu [x],
không hỏi lại từng bước. Với mỗi màn hình: (1) dùng enhance-prompt viết prompt tối ưu có nêu
đủ trạng thái trong cột "Biến thể"; (2) sinh bằng Stitch vào project "quiz-toantin";
(3) xuất HTML + PNG vào design/screens/<mã>.html|png; (4) đánh dấu [x] trong SITE.md;
(5) ghi next-prompt.md cho màn hình kế tiếp. Ràng buộc: học sinh dùng điện thoại là chính;
đồng hồ cố định đầu trang làm bài; chạm ≥ 44px; không dùng emoji làm biểu tượng; không số liệu giả.
Khi xong, báo danh sách màn hình + liên kết project.
```
- **Thuật toán vòng lặp (baton):** đọc `next-prompt.md` → đọc `SITE.md` + `DESIGN.md` → sinh 1 màn hình → ghi kết quả → cập nhật `SITE.md` và `next-prompt.md`. Trạng thái nằm trong file, nên **dừng/tiếp tục an toàn** (idempotent): màn hình đã `[x]` không bị sinh lại.
- **Bắt lỗi:** lỗi MCP/hết hạn mức → agent dừng ở dòng hiện tại, ghi `status: blocked + lý do` vào `SITE.md`; chạy lại sau đó tiếp tục đúng chỗ. Stitch có hạn mức sinh theo gói — kiểm tra hạn mức trước khi chạy cả loạt và chạy theo lô (mỗi lô ~6 màn hình).
- **Đặt tên & lưu:** mã màn hình cố định (`ST3`), biến thể thêm hậu tố (`ST3-mcq`, `ST3-offline`); commit mỗi lô.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-1.3-01 | Đủ bộ màn hình | Sau khi chạy xong, đối chiếu `SITE.md` với `design/screens/` | 100% mã có `.html` và `.png`, không file mồ côi |
| TC-1.3-02 | Chạy lại không trùng | Chạy lại prompt tổng khi mọi dòng đã `[x]` | Không sinh thêm màn hình, thông báo "đã hoàn tất" |
| TC-1.3-03 | Dừng giữa chừng | Ngắt agent ở màn hình thứ 7 rồi chạy lại | Tiếp tục từ màn hình 8; màn 1–7 không bị ghi đè |
| TC-1.3-04 | Lỗi MCP/hạn mức | Tắt MCP khi đang chạy | Dòng hiện tại ghi `blocked` kèm lý do; không đánh dấu `[x]` sai |
| TC-1.3-05 | Nhất quán | So khớp header, nút chính, bảng màu giữa ≥ 5 màn hình | Dùng đúng token của `DESIGN.md`; không màn hình nào có phong cách riêng lạc quần |
| TC-1.3-06 | Đủ biến thể ST3 | Mở 7 biến thể của ST3 | Có đủ 5 dạng câu + cảnh báo thời gian + offline |

---

## Bước 1.4 — Rà soát chống "AI slop", trợ năng (a11y) và đáp ứng nhiều cỡ màn hình

**Yêu cầu cần đạt**
- Giao diện đạt chuẩn trợ năng cơ bản; không còn dấu hiệu "AI slop" mức nghiêm trọng.
- Dùng được ở 360px (điện thoại nhỏ), 768px, 1280px; thao tác được hoàn toàn bằng bàn phím.

**Cách thức triển khai**
- **Quét tự động:** chạy `npx impeccable detect` (quét mẫu slop, không cần LLM) trên `design/screens/*.html`; chạy `/critique` và `/audit` của Impeccable để lấy danh sách lỗi có thứ tự ưu tiên.
- **Vòng sửa tối đa 3 lượt:** đưa danh sách lỗi cho agent sửa bằng `/polish`, `/typeset`, `/layout`… (tên lệnh có thể khác theo phiên bản Impeccable cài); sau mỗi lượt chạy lại quét.
- **Danh sách soát thủ công (checklist slop):** nền gradient tím-xanh; kính mờ lạm dụng; lưới thẻ biểu tượng giống nhau; văn bản giả (lorem/số giả); emoji thay biểu tượng; bóng đổ nặng + bo góc lớn; phông mặc định không có lý do; hoạt ảnh không phục vụ chức năng; tiêu đề "hero" cho một ứng dụng thao tác.
- **Trợ năng:** `axe-core` (qua Playwright) quét từng trang; vòng focus nhìn thấy rõ; thứ tự Tab hợp lý; nút có tên truy cập; vùng `aria-live="polite"` cho chỉ báo lưu và cảnh báo thời gian (**chỉ thông báo khi đổi trạng thái hoặc mốc 5 phút/1 phút, không đọc từng giây**); biểu mẫu có nhãn gắn với ô nhập.
- **Đáp ứng:** chụp màn hình bằng Playwright ở 360/768/1280 px; kiểm tra không cuộn ngang.
- **Thử nhanh với người thật:** 2–3 học sinh và 1 giáo viên làm thử "5 giây nhìn + làm 1 nhiệm vụ" trên bản HTML.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-1.4-01 | Quét slop | `impeccable detect` trên toàn bộ màn hình | 0 phát hiện mức nghiêm trọng; mức nhẹ có ghi chú lý do giữ lại |
| TC-1.4-02 | a11y tự động | `axe-core` trên từng màn hình ở 3 cỡ | 0 lỗi mức serious/critical |
| TC-1.4-03 | Bàn phím | Làm hết luồng ST1→ST5 chỉ bằng Tab/Enter/Space/phím mũi tên | Hoàn thành được; focus luôn nhìn thấy; hộp thoại xác nhận bẫy focus và đóng bằng Esc |
| TC-1.4-04 | 360px | Chụp mọi màn hình học sinh ở 360×640 | Không cuộn ngang; nút ≥ 44px; không chữ bị cắt |
| TC-1.4-05 | Phóng chữ 200% | Tăng cỡ chữ trình duyệt lên 200% | Không mất nội dung/nút chính, đồng hồ vẫn thấy |
| TC-1.4-06 | Người dùng thật | 3 học sinh làm "tìm đề và bắt đầu làm" | ≥ 2/3 hoàn thành không cần hướng dẫn; góp ý được ghi lại và xử lý |

---

## Bước 1.5 — Chuyển thiết kế thành thư viện component React

**Yêu cầu cần đạt**
- Có thư viện component tái sử dụng, có kiểu (TypeScript), đủ trạng thái, dùng token (không mã màu cứng).
- Có trang `/dev/components` (chỉ bật ở môi trường dev) trưng bày mọi component và trạng thái.

**Cách thức triển khai**
- **Chuyển đổi:** dùng skill `react-components` để chuyển HTML của Stitch thành khung React, sau đó **tái cấu trúc thủ công** thành component dùng chung (đừng giữ nguyên mã sinh tự động: lặp, khó bảo trì).
- **Danh sách component:** `Button`, `Input`, `Textarea`, `Select`, `Checkbox/Radio`, `Card`, `Badge`, `Table`, `Tabs`, `Modal/ConfirmDialog`, `Toast`, `Skeleton`, `EmptyState`, `ErrorState`, `Banner` (offline/đang đánh thức máy chủ), `Timer`, `SaveIndicator`, `QuestionNav`, `FileDropzone`, `Pagination`.
- **Quy tắc:** mỗi component nhận `className` để mở rộng, hỗ trợ trạng thái `loading/disabled/error`, có `aria-*` đúng; **nút gửi form tự vô hiệu hóa khi đang gửi** (chống bấm đúp).
- **Chặn mã màu cứng:** quy tắc ESLint/`grep` trong CI cấm `#xxxxxx` và `rgb(` trong `src/` (trừ file token).
- **Hiệu năng:** tách mã theo route (`React.lazy`), KaTeX chỉ nạp ở màn hình cần dùng; ngân sách gói ban đầu ≤ 200 KB gzip cho trang đăng nhập/danh sách đề.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-1.5-01 | Trạng thái component | Vitest + Testing Library cho mỗi component: mặc định, loading, disabled, error | Render đúng, thuộc tính `aria` đúng, không cảnh báo React |
| TC-1.5-02 | Chống bấm đúp | Nhấn `Button type=submit` 2 lần liên tiếp khi `onSubmit` còn chạy | `onSubmit` chỉ được gọi 1 lần |
| TC-1.5-03 | Ảnh chụp so sánh | Playwright chụp `/dev/components` ở 360/1280 px và so với ảnh chuẩn | Lệch ≤ ngưỡng đặt trước; thay đổi cố ý phải cập nhật ảnh chuẩn |
| TC-1.5-04 | Không mã màu cứng | Chạy luật kiểm tra trong CI | 0 vi phạm |
| TC-1.5-05 | Ngân sách gói | `vite build` + phân tích kích thước | Trang đăng nhập ≤ 200 KB gzip; KaTeX không nằm trong gói đăng nhập |
| TC-1.5-06 | Timer & SaveIndicator | Test với dữ liệu: còn 10 phút / 4 phút / 50 giây / 0 | Đổi trạng thái đúng mốc; `aria-live` chỉ phát khi đổi mốc |

---

## Bước 1.6 — Thành phần hiển thị Markdown + LaTeX (`MathText`) an toàn

**Yêu cầu cần đạt**
- Một component duy nhất dùng cho **mọi nơi** hiển thị nội dung đề (câu hỏi, lựa chọn, mệnh đề, lời giải, preview).
- Công thức hỏng chỉ báo lỗi tại chỗ; **không thể chạy script/HTML thô**; ảnh chỉ nạp từ nguồn cho phép.

**Cách thức triển khai**
- **Pipeline:** `react-markdown` + `remark-math` + `rehype-katex` + `rehype-sanitize`.
  - `rehype-katex` với `{ throwOnError: false, strict: "ignore", trust: false, errorColor: "var(--danger)", maxExpand: 1000, maxSize: 20 }` để chặn công thức "nổ" (macro lồng vô hạn, kích thước khổng lồ).
  - `rehype-sanitize` với schema cho phép: văn bản, danh sách, bảng, `code/pre`, ảnh; **cấm** `script`, `style`, `iframe`, thuộc tính `on*`, URL `javascript:`/`data:` (trừ ảnh `blob:` ở trình soạn).
  - Thứ tự: sanitize **trước** khi KaTeX chèn HTML của nó, hoặc cấu hình sanitize cho phép lớp `katex*` — kiểm tra bằng test, không phỏng đoán.
- **Ảnh:** URL chỉ chấp nhận `asset:<uuid>` (server đã thay bằng URL ký R2) hoặc đúng miền R2; mọi miền khác bị bỏ (thay bằng khung "ảnh không hợp lệ").
- **Hiệu năng:** `React.memo` theo `content`; preview trong trình soạn debounce 200 ms; tải CSS/phông KaTeX bằng import động.
- **Bắt lỗi:** mỗi khối `MathText` bọc `ErrorBoundary` riêng; lỗi một công thức không làm hỏng cả câu hỏi.
- **Mã nguồn (môn Tin):** `pre/code` có cuộn ngang, phông monospace, không tô màu bằng thư viện thực thi mã.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-1.6-01 | Công thức hợp lệ | `$x^2+y^2=r^2$`, `$$\int_0^1 x\,dx$$`, ma trận, hệ phương trình | Hiển thị đúng; inline và khối đúng bố cục |
| TC-1.6-02 | Công thức sai cú pháp | `$\frac{1}{$`, `$\unknowncmd$` | Hiện báo lỗi tại chỗ màu `--danger`; phần còn lại của câu vẫn hiển thị; không ném lỗi ra ngoài |
| TC-1.6-03 | Chống XSS | `<script>alert(1)</script>`, `<img src=x onerror=alert(1)>`, `[a](javascript:alert(1))`, `$\href{javascript:alert(1)}{x}$` | Không có script nào chạy; HTML thô bị loại; liên kết nguy hiểm bị vô hiệu |
| TC-1.6-04 | Công thức "nổ" | Macro đệ quy, `$x^{x^{x^{…}}}$` lồng 500 tầng, công thức 20.000 ký tự | Bị chặn theo `maxExpand/maxSize` hoặc hiện lỗi; trình duyệt không treo (> 1 s) |
| TC-1.6-05 | Tiếng Việt trong công thức | `$\text{đa thức } P(x)$`, `**in đậm** tiếng Việt có dấu` | Hiển thị đúng dấu |
| TC-1.6-06 | Ảnh ngoài nguồn | `![x](https://evil.example/a.png)` | Không nạp ảnh; hiện khung thay thế |
| TC-1.6-07 | Khối mã Tin học | Đoạn Python 40 dòng, dòng dài 300 ký tự | Cuộn ngang trong khung, không phá bố cục mobile |

---

# GIAI ĐOẠN 2. NỀN TẢNG (BACKEND + CSDL + XÁC THỰC + KHUNG FRONTEND)

## Bước 2.1 — Khung ứng dụng FastAPI, middleware, xử lý lỗi thống nhất

**Yêu cầu cần đạt**
- Một `create_app()` duy nhất; mọi lỗi (kể cả lỗi không lường trước) trả về đúng định dạng lỗi chung, **không lộ stack trace**.
- Có `/healthz` (không đụng DB), `/readyz` (kiểm tra DB), `/api/v1/time`.
- Log có cấu trúc, có `request_id`, **không bao giờ** chứa mật khẩu/token.

**Cách thức triển khai**
- **Cấu trúc:** theo đặc tả 5.4 (`core/`, `db/`, `models/`, `schemas/`, `routers/`, `services/`). Router chỉ làm: xác thực → gọi service → trả schema. Logic nghiệp vụ nằm ở `services/` (hàm thuần/ít phụ thuộc, dễ test).
- **Middleware (thứ tự từ ngoài vào trong):** `RequestID` (đọc/sinh `X-Request-ID`) → `AccessLog` (method, path, status, thời gian ms, `user_id` nếu có) → `SecurityHeaders` (`X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` cho `/api`) → `CORS` (chỉ các origin trong `CORS_ORIGINS`, `allow_credentials=False` vì dùng header Bearer) → `GZip` (≥ 1 KB).
- **Giới hạn kích thước body:** mặc định 1 MB cho JSON (từ chối theo `Content-Length`, và chặn khi đọc stream nếu thiếu header); riêng route upload có giới hạn riêng (bước 4.3, 5.9).
- **Xử lý lỗi:**
```python
class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None): ...

@app.exception_handler(AppError)            -> JSON {"error": {...}} với status của lỗi
@app.exception_handler(RequestValidationError) -> 422 "validation_error" + details theo từng trường
@app.exception_handler(OperationalError)    -> 503 "db_unavailable" + header Retry-After: 2   # Neon vừa thức dậy / mất kết nối
@app.exception_handler(Exception)           -> 500 "internal_error" + request_id, log đầy đủ stack ở server
```
- **`/readyz`:** `SELECT 1` với timeout 2 giây; trả 503 nếu lỗi. **`/healthz`** không chạm DB (để cron ping giữ server thức mà không đánh thức DB không cần thiết; nút "Làm nóng hệ thống" mới gọi cả hai).
- **Log:** formatter JSON; bộ lọc che các khóa `password`, `authorization`, `token`, `answer_key`.
- **Cấu hình:** `Settings` (pydantic-settings) gom toàn bộ biến ở Phụ lục A đặc tả; thiếu biến bắt buộc → dừng khi khởi động (đã có ở 0.1).

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-2.1-01 | Lỗi nghiệp vụ | Router ném `AppError("x","y",409)` | 409, JSON đúng định dạng, có `request_id` trong header phản hồi |
| TC-2.1-02 | Lỗi không lường trước | Endpoint thử nghiệm `raise RuntimeError("boom")` | 500 `internal_error`; **không** có chuỗi "boom"/stack trong body; log server có đủ stack |
| TC-2.1-03 | Mất DB | Tắt DB giữa chừng rồi gọi endpoint cần DB | 503 `db_unavailable` + `Retry-After`; `/healthz` vẫn 200; `/readyz` 503 |
| TC-2.1-04 | Body quá lớn | POST JSON 2 MB tới endpoint thường | 413/400 với mã lỗi rõ ràng, server không tốn bộ nhớ đọc hết |
| TC-2.1-05 | CORS | Gửi `Origin` lạ và `Origin` hợp lệ (preflight `OPTIONS`) | Origin lạ không được cấp header CORS; origin hợp lệ qua |
| TC-2.1-06 | Không rò thông tin nhạy cảm vào log | Gọi login với mật khẩu `S3cretPwd!` và kiểm log | Không tìm thấy `S3cretPwd!` hay giá trị `Authorization` trong log |
| TC-2.1-07 | Sai schema | Gửi JSON thiếu trường bắt buộc | 422 `validation_error`, `details` chỉ rõ trường nào sai |

---

## Bước 2.2 — Thiết kế CSDL, mô hình SQLAlchemy và migration (Alembic)

**Yêu cầu cần đạt**
- Có đủ bảng theo đặc tả mục 7; ràng buộc nằm **trong CSDL** (không chỉ trong mã).
- Migration chạy lên/xuống được; `alembic check` sạch (mô hình khớp migration).
- Cấu hình kết nối chịu được việc Neon tự tạm dừng và pooler.

**Cách thức triển khai**
- **Quy ước kiểu dữ liệu:** `uuid` làm khóa; `timestamptz`; `numeric(6,2)` cho điểm; `jsonb` cho `config/answer_key/value`. Trạng thái dùng `varchar` + `CHECK` (không dùng `ENUM` của Postgres vì đổi giá trị khó khi migration).
- **Ràng buộc quan trọng:**
  - `users.username` lưu chữ thường + `CHECK (username = lower(username))`, `UNIQUE`.
  - `attempts`: `UNIQUE (exam_id, student_id)`; `CHECK (status IN ('in_progress','submitted'))`; chỉ mục **một phần** phục vụ sweeper: `CREATE INDEX ix_attempts_active_deadline ON attempts (deadline_at) WHERE status = 'in_progress';`
  - `answers`: `UNIQUE (attempt_id, question_id)`; `client_seq bigint NOT NULL DEFAULT 0`.
  - `questions`: `UNIQUE (exam_id, position) DEFERRABLE INITIALLY DEFERRED` (để đổi thứ tự nhiều câu trong một transaction không vướng ràng buộc); `CHECK (points >= 0)`.
  - `class_members`, `exam_classes`: khóa chính kép; `ON DELETE CASCADE` đúng chiều (xóa lớp → xóa liên kết, không xóa học sinh).
  - Thêm cột `classes.is_archived boolean default false` (bổ sung so với đặc tả, dùng ở bước 3.1).
  - Thêm cột `version integer not null default 1` cho `exams`, `questions`, `answers` (khóa lạc quan).
- **Engine & phiên:**
```python
engine = create_engine(
    settings.database_url,                    # chuỗi POOLED của Neon
    pool_size=5, max_overflow=5, pool_timeout=5,
    pool_pre_ping=True,                       # bỏ kết nối chết khi Neon đã tạm dừng
    pool_recycle=240,                         # < 300 giây tự tắt của Neon
    connect_args={"prepare_threshold": None}, # tránh prepared statement qua PgBouncer
)
def get_db():
    with Session(engine) as s:
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback(); raise
```
- **Migration:** dùng chuỗi **direct** (`DATABASE_URL_DIRECT`) trong `alembic/env.py`; `compare_type=True`; `naming_convention` cho khóa/chỉ mục để tên ổn định. Mỗi migration phải **tương thích ngược một phiên bản** (thêm cột có mặc định, không đổi tên cột trong một lần deploy) vì deploy có thể diễn ra khi còn tiến trình cũ.
- **Seed phát triển:** `python -m app.cli seed` (chỉ dùng cho môi trường dev/test, tuyệt đối không dùng trên production). Để tuân thủ nguyên tắc không khởi tạo mặc định đối tượng nhạy cảm: script seed chỉ tạo khung dữ liệu (2 lớp, 1 đề mẫu đủ 5 dạng câu) sau khi người dùng đã tự tạo tài khoản admin qua CLI, hoặc yêu cầu người dùng nhập thông tin tài khoản test tại thời điểm chạy; không lưu cứng bất kỳ mật khẩu mặc định nào trong code.
- **Tối ưu dữ liệu:** `answers.value` chỉ lưu giá trị gọn (không nhân đôi nội dung đề); dữ liệu quá hạn bị dọn ở bước 6.5 để giữ DB < 0.5 GB.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-2.2-01 | Lên/xuống/lên | `alembic upgrade head` → `downgrade base` → `upgrade head` trên DB trống | Cả 3 lệnh thành công, lược đồ cuối giống nhau |
| TC-2.2-02 | Lệch mô hình | Sửa model nhưng quên migration, chạy `alembic check` | Lệnh báo có thay đổi chưa migrate (CI đỏ) |
| TC-2.2-03 | Unique attempt | Chèn 2 attempt cùng `(exam_id, student_id)` | Lần 2 vi phạm ràng buộc `UNIQUE` |
| TC-2.2-04 | Username viết hoa | Chèn `Nam01` | Vi phạm `CHECK`; chèn `nam01` thành công |
| TC-2.2-05 | Đổi thứ tự câu | Hoán đổi `position` của câu 1 và 2 trong **một** transaction | Thành công nhờ ràng buộc `DEFERRABLE` |
| TC-2.2-06 | Trạng thái sai | Chèn `attempts.status = 'foo'` | Bị `CHECK` từ chối |
| TC-2.2-07 | Kết nối sau khi DB ngủ | Dừng/khởi động lại Postgres (hoặc chờ Neon suspend 5 phút), rồi gọi query | Truy vấn đầu tiên tự phục hồi nhờ `pool_pre_ping` (có thể chậm vài trăm ms), không văng lỗi ra người dùng |
| TC-2.2-08 | Chỉ mục sweeper | `EXPLAIN` truy vấn `WHERE status='in_progress' AND deadline_at < :t` trên 100k dòng giả lập | Dùng `ix_attempts_active_deadline`, không quét toàn bảng |

---

## Bước 2.3 — Xác thực: đăng nhập, phiên, phân quyền, giới hạn tốc độ

**Yêu cầu cần đạt**
- Đăng nhập bằng `username + password`, đúng là vào (không email/OTP).
- Token bất kỳ không thể suy ra từ CSDL; thu hồi được; hết hạn đúng cấu hình.
- Chống dò mật khẩu nhưng **không chặn oan cả lớp dùng chung một mạng Wi-Fi**.
- Đăng nhập đồng loạt 40 học sinh không làm tràn bộ nhớ máy chủ nhỏ.

**Cách thức triển khai**
- **Băm mật khẩu:** Argon2id (`argon2-cffi`) với tham số tối thiểu khuyến nghị (`time_cost=2, memory_cost=19456 KiB, parallelism=1`). Mỗi lần băm tốn ~19 MiB RAM: **giới hạn song song bằng `threading.BoundedSemaphore(3)`** quanh `verify/hash` để lúc cả lớp đăng nhập cùng lúc không vượt RAM của gói miễn phí (~512 MB). Dùng `check_needs_rehash` để nâng tham số về sau.
- **Chống dò thời gian (timing):** nếu username không tồn tại vẫn `verify` với một hash giả cố định, để thời gian phản hồi xấp xỉ nhau; thông báo lỗi chung "Sai tên đăng nhập hoặc mật khẩu". Chỉ **sau khi mật khẩu đúng** mới phân biệt `account_disabled` (tài khoản do giáo viên tạo, không có rủi ro dò tài khoản công khai).
- **Token:** `secrets.token_urlsafe(32)`; lưu `sha256(token)` ở `sessions.token_hash`; client gửi `Authorization: Bearer <token>`.
- **Hết hạn trượt:** `expires_at = now + SESSION_TTL_HOURS`; chỉ **cập nhật `last_seen_at/expires_at` tối đa mỗi 5 phút** mỗi phiên để tránh ghi DB ở mọi request.
- **Nhiều thiết bị:** **không** áp chính sách một-phiên-một-tài-khoản (học sinh mất điện có thể đổi sang điện thoại; giáo viên có thể thu hồi phiên khi nghi ngờ dùng chung).
- **Giới hạn tốc độ (`slowapi`, bộ nhớ trong vì chạy 1 worker):** theo cặp `IP + username` ≤ 10 lần sai/phút (chặn dò mật khẩu); theo IP ≤ 120 yêu cầu đăng nhập/phút (rộng, vì cả lớp có thể chung một IP NAT). Lấy IP thật từ `X-Forwarded-For` chỉ khi chạy sau proxy tin cậy (Render): cấu hình `--proxy-headers`.
- **Phụ thuộc phân quyền:**
```python
def current_user(token=Depends(bearer), db=Depends(get_db), clock=Depends(get_clock)) -> User: ...
def require_admin(u=Depends(current_user)):   # 403 nếu role != admin
def require_student(u=Depends(current_user)): # 403 nếu role != student
```
  Mọi router dưới `/admin` mount với `dependencies=[Depends(require_admin)]`, dưới `/student` mount với `require_student` — **không** tự kiểm tra rải rác từng hàm.
- **Admin đầu tiên (Bắt buộc do người dùng tự quyết định, không khởi tạo mặc định):** Tuyệt đối KHÔNG tự động tạo tài khoản admin với thông tin mặc định khi khởi động ứng dụng. Quản trị viên bắt buộc phải tự khởi tạo thông qua lệnh CLI tương tác: `python -m app.cli create-admin`. CLI yêu cầu người dùng tự gõ username và nhập mật khẩu bảo mật (chế độ ẩn ký tự `getpass`, nhập lại xác nhận, kiểm tra độ dài $\ge 12$ ký tự). Hệ thống từ chối khởi tạo nếu người dùng không tự cung cấp mật khẩu trực tiếp.
- **Khi giáo viên đổi/đặt lại mật khẩu hoặc khóa tài khoản:** xóa mọi `sessions` của người đó trong cùng transaction.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-2.3-01 | Đăng nhập đúng | `POST /auth/login` với tài khoản hợp lệ | 200, trả token + `role`; `/auth/me` dùng token trả đúng người dùng |
| TC-2.3-02 | Sai mật khẩu / không tồn tại | Hai lời gọi: user có thật + sai mật khẩu; user không có | Cùng mã lỗi và thông điệp; chênh lệch thời gian trung vị < 30% |
| TC-2.3-03 | Token không lưu thô | Đăng nhập rồi truy vấn bảng `sessions` | Không cột nào chứa token gốc; chỉ có hash 64 ký tự hex |
| TC-2.3-04 | Hết hạn & thu hồi | Dùng đồng hồ giả tăng 13 giờ; riêng ca khác: admin thu hồi phiên | Cả hai trường hợp → 401 ở request kế tiếp |
| TC-2.3-05 | Chống dò mật khẩu | 11 lần sai trong 1 phút cùng `IP+username` | Lần 11 → 429 `rate_limited`; **người dùng khác cùng IP vẫn đăng nhập được** |
| TC-2.3-06 | Cả lớp cùng IP | 40 đăng nhập đúng trong 10 giây từ cùng IP | Tất cả thành công; bộ nhớ tiến trình tăng không vượt ngưỡng đặt trước (ví dụ < 200 MB) nhờ semaphore |
| TC-2.3-07 | Phân quyền | Student gọi `/admin/*`; ẩn danh gọi `/student/*` | 403 và 401 tương ứng ở **mọi** route (kiểm tra tự động theo danh sách route OpenAPI) |
| TC-2.3-08 | Khóa tài khoản giữa chừng | Admin đặt `is_active=false` khi học sinh đang có phiên | Request kế tiếp của học sinh → 401; đăng nhập lại → `account_disabled` |
| TC-2.3-09 | Header sai | `Authorization: Bearer` rỗng, `Basic xxx`, token có ký tự lạ | 401, không lỗi 500 |
| TC-2.3-10 | Khởi tạo admin (Người dùng tự quyết) | Chạy CLI `create-admin` tương tác nhập thông tin; chạy lại lần 2 cùng username; khởi động server khi chưa có admin | Server khởi động an toàn khi chưa có admin (không tự sinh tài khoản mặc định); CLI tạo đúng tài khoản do người dùng nhập; lần 2 báo lỗi trùng lặp |

---

## Bước 2.4 — Dịch vụ thời gian (`Clock`) và các hàm thời hạn thuần

**Yêu cầu cần đạt**
- Mọi tính toán hạn nộp/hết giờ đi qua các hàm thuần, có thể kiểm thử bằng đồng hồ giả.
- Có giám sát độ lệch giữa đồng hồ ứng dụng và DB.

**Cách thức triển khai**
```python
class Clock(Protocol):
    def now(self) -> datetime: ...
class SystemClock:
    def now(self) -> datetime: return datetime.now(timezone.utc)

def compute_deadline(started_at, duration_minutes, extra_seconds, close_at):
    assert started_at.tzinfo is not None            # cấm datetime không múi giờ
    d = started_at + timedelta(minutes=duration_minutes, seconds=extra_seconds)
    return min(d, close_at) if close_at else d

def is_writable(now, deadline_at, grace_seconds) -> bool:
    return now <= deadline_at + timedelta(seconds=grace_seconds)

def remaining_seconds(now, deadline_at) -> int:
    return max(0, math.ceil((deadline_at - now).total_seconds()))
```
- `get_clock()` là dependency của FastAPI để test thay bằng `FakeClock`.
- `GET /api/v1/time` trả `{"server_now": "<ISO>", "epoch_ms": <int>}` (dùng cho đồng bộ đồng hồ client ở 5.5).
- **Giám sát lệch giờ:** trong `/readyz` (và khi khởi động) so sánh `Clock.now()` với `SELECT clock_timestamp()`; nếu lệch > 2 giây → ghi log cảnh báo `clock_skew`.
- **Quy tắc:** tuyệt đối không gọi `datetime.now()` hay `func.now()` trực tiếp trong logic hạn nộp; chỉ dùng `Clock`. Thêm test kiểu "grep" trong CI để cấm `datetime.now(`/`utcnow(` ngoài `core/time.py`.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-2.4-01 | Hạn bình thường | `start=10:00, 30 phút, extra=0, close_at=None` | `deadline=10:30:00` |
| TC-2.4-02 | Bị cắt bởi `close_at` | `start=10:00, 60 phút, close_at=10:20` | `deadline=10:20` |
| TC-2.4-03 | Cộng giờ | `extra_seconds=300` | `deadline` tăng đúng 5 phút; `extra` âm bị từ chối ở tầng API |
| TC-2.4-04 | Biên grace | `now = deadline + grace` và `now = deadline + grace + 1µs` | Trường hợp đầu `is_writable=True`, trường hợp sau `False` |
| TC-2.4-05 | Datetime không múi giờ | Truyền `datetime` naive | Ném lỗi rõ ràng (không âm thầm hiểu là giờ địa phương) |
| TC-2.4-06 | `remaining_seconds` biên | `now` đúng bằng `deadline`; `now` sau `deadline`; còn 0.2 giây | `0`; `0`; `1` (làm tròn lên) |
| TC-2.4-07 | Lệch giờ | Giả lập `Clock` nhanh 5 giây so với DB | Log `clock_skew` cảnh báo; `/readyz` vẫn 200 |
| TC-2.4-08 | Quét cấm | Chạy kiểm tra grep trong CI | Không có `datetime.now(` ngoài `core/time.py` |

---

## Bước 2.5 — Khung frontend: định tuyến, API client, xác thực, xử lý lỗi toàn cục

**Yêu cầu cần đạt**
- Một API client duy nhất, **phân biệt rõ lỗi mạng với lỗi HTTP**, có timeout, thử lại an toàn cho yêu cầu đọc.
- Bảo vệ route theo vai trò; mất phiên không làm mất dữ liệu đang làm dở.
- Hiển thị thân thiện khi máy chủ đang "ngủ".

**Cách thức triển khai**
- **API client (`lib/api.ts`):**
```ts
export class ApiError extends Error { constructor(public status:number, public code:string,
  message:string, public details?:unknown, public requestId?:string){ super(message) } }
export class NetworkError extends Error {}         // fetch ném TypeError / hết thời gian

async function request<T>(path:string, o:{method?:string, body?:unknown, timeoutMs?:number,
  idempotent?:boolean, keepalive?:boolean} = {}): Promise<T> { /* AbortController + Bearer + parse lỗi chung */ }
```
  - Mặc định `timeoutMs=15000`; **GET** và yêu cầu đánh dấu `idempotent` được thử lại tối đa 3 lần với backoff `1s, 2s, 4s` + nhiễu ngẫu nhiên ±20% khi gặp `NetworkError`, 502/503/504; **POST/PUT không idempotent không tự thử lại**.
  - `401` → xóa token, chuyển `/login` **kèm `returnTo`**; nhưng ở trang làm bài thì **giữ nguyên outbox** và hiện hộp thoại đăng nhập lại (bước 5.6) thay vì chuyển trang.
  - `429` → đọc `Retry-After`, hiện thông báo "Thao tác quá nhanh".
- **Phát hiện "máy chủ đang ngủ":** nếu yêu cầu đầu tiên sau khi tải trang chưa có phản hồi sau 3 giây, hiện `Banner` "Đang đánh thức máy chủ, có thể mất tới ~1 phút", đồng thời gọi `/healthz` mỗi 3 giây tối đa 90 giây; khi sống lại tự thử lại yêu cầu ban đầu. Quá 90 giây mới báo lỗi thật.
- **TanStack Query:** `staleTime` hợp lý (danh sách: 30 s); `refetchOnWindowFocus:false` ở trang làm bài; `retry` theo quy tắc trên.
- **Định tuyến & bảo vệ:** `RequireAuth(role)` bọc nhóm route; tải trạng thái người dùng bằng `/auth/me` khi khởi động (hiện skeleton, không nháy trang đăng nhập).
- **Xử lý lỗi toàn cục:** `ErrorBoundary` cấp ứng dụng với nút "Tải lại"; lắng nghe `vite:preloadError` (chunk cũ không còn sau khi deploy) → hộp thoại "Có bản cập nhật, bấm để tải lại" (đảm bảo outbox đã lưu trong `localStorage` trước khi tải lại).
- **Địa phương hóa:** hằng chuỗi tiếng Việt tập trung `lib/i18n/vi.ts`; định dạng ngày giờ bằng `Intl.DateTimeFormat('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })`.
- **Lưu token:** `localStorage` (bọc `try/catch`; nếu không dùng được thì lưu trong bộ nhớ và cảnh báo "Đóng tab sẽ phải đăng nhập lại"). Vì token nằm ở `localStorage`, **CSP chặt và sanitize nội dung** (1.6, 8.4) là lớp phòng vệ XSS bắt buộc.

**Test case kiểm thử và yêu cầu cần đạt** (dùng Vitest + MSW để giả lập máy chủ)

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-2.5-01 | Phân biệt lỗi | MSW trả 500 cho 1 request, ngắt kết nối cho request khác | Lỗi đầu là `ApiError(status=500)`, lỗi sau là `NetworkError` |
| TC-2.5-02 | Thử lại GET | Máy chủ lỗi 503 hai lần rồi 200 | GET thành công ở lần thứ 3; thời gian chờ tăng dần có nhiễu |
| TC-2.5-03 | Không thử lại POST | POST nhận `NetworkError` | Không tự gửi lại; lỗi được trả cho tầng gọi |
| TC-2.5-04 | Hết phiên | API trả 401 ở trang danh sách đề | Chuyển `/login?returnTo=…`; đăng nhập xong quay lại đúng trang |
| TC-2.5-05 | Server ngủ | Giả lập phản hồi chậm 20 giây rồi OK | Hiện banner sau 3 giây; sau khi sống lại, dữ liệu hiển thị, banner biến mất |
| TC-2.5-06 | Server chết hẳn | Không phản hồi quá 90 giây | Hiện trạng thái lỗi kèm nút "Thử lại"; không vòng lặp vô hạn |
| TC-2.5-07 | Chunk cũ | Giả lập `vite:preloadError` | Hộp thoại cập nhật hiện ra; sau tải lại dữ liệu nháp (outbox) vẫn còn |
| TC-2.5-08 | Bảo vệ route | Student mở `/a/classes`; admin mở `/s/exams` | Bị chuyển về trang mặc định đúng vai trò, không nháy nội dung bị cấm |
| TC-2.5-09 | `localStorage` bị chặn | Giả lập `setItem` ném lỗi | Ứng dụng vẫn đăng nhập được (lưu trong bộ nhớ), có cảnh báo |

---

# GIAI ĐOẠN 3. LỚP, HỌC SINH, GHI DANH, NHẬP CSV

## Bước 3.1 — API quản lý lớp

**Yêu cầu cần đạt**
- CRUD lớp đúng đặc tả 3.2; không xóa nhầm lớp đang có dữ liệu thi.
- Danh sách có phân trang, tìm kiếm, sắp xếp, **không bị N+1 truy vấn**.

**Cách thức triển khai**
- **Quy tắc dữ liệu:** `code` chuẩn hóa chữ hoa, regex `^[A-Z0-9_-]{2,20}$`, duy nhất (`409 class_code_taken`); `subject ∈ {toan, tin, both}`.
- **Xóa:** nếu lớp đã được giao đề → `409 class_in_use` và gợi ý "Lưu trữ" (`is_archived=true`: không cho thêm học sinh/giao đề mới, vẫn giữ dữ liệu cũ). Chỉ xóa cứng khi lớp chưa dính đề nào (xóa liên kết `class_members` theo cascade).
- **Danh sách:** `GET /admin/classes?limit=&offset=&q=&sort=` với `limit ≤ 100`; `sort` chỉ nhận từ danh sách trắng; `q` dùng `ILIKE` với ký tự đặc biệt `%`/`_` được thoát; số học sinh lấy bằng một truy vấn `LEFT JOIN … GROUP BY` (hoặc subquery), không đếm riêng cho từng lớp.
- **Khóa lạc quan:** `PATCH` kèm `version`; sai phiên bản → `409 version_conflict`.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-3.1-01 | Tạo lớp hợp lệ | `POST` với `code="10a1"` | 201; `code` lưu `10A1` |
| TC-3.1-02 | Trùng mã | Tạo lớp thứ hai mã `10a1` | 409 `class_code_taken` |
| TC-3.1-03 | Xóa lớp đang dùng | Lớp đã giao 1 đề rồi `DELETE` | 409 `class_in_use`; sau khi `is_archived=true` danh sách mặc định ẩn lớp |
| TC-3.1-04 | Tìm kiếm ký tự đặc biệt | `q=%` và `q=_` | Chỉ khớp văn bản thật chứa ký tự đó, không trả về toàn bộ |
| TC-3.1-05 | Phân trang biên | `limit=0`, `limit=101`, `offset` âm, `offset` vượt tổng | Lần lượt 422, 422, 422, danh sách rỗng hợp lệ |
| TC-3.1-06 | Hiệu năng truy vấn | Danh sách 50 lớp mỗi lớp 30 học sinh, đếm số câu lệnh SQL | ≤ 3 câu lệnh (không N+1) |
| TC-3.1-07 | Xung đột sửa đồng thời | Hai `PATCH` cùng `version=1` | Một thành công, một `409 version_conflict` |

---

## Bước 3.2 — API học sinh và ghi danh vào lớp

**Yêu cầu cần đạt**
- Tạo/sửa/khóa học sinh; mật khẩu sinh ra chỉ hiển thị **một lần**.
- Ghi danh là thao tác **idempotent** theo tập hợp; học sinh có thể thuộc nhiều lớp.

**Cách thức triển khai**
- **Tạo học sinh:** `username` chuẩn hóa chữ thường, regex `^[a-z0-9._-]{3,32}$`; `full_name` chuẩn hóa Unicode NFC, cắt khoảng trắng. **Mật khẩu do người dùng (giáo viên) chủ động nhập hoặc chủ động chọn "Tự sinh mật khẩu ngẫu nhiên an toàn"**; tuyệt đối không dùng mật khẩu mặc định cố định (như `123456`, ngày sinh...). Trả mật khẩu rõ **chỉ trong phản hồi tạo/đặt lại**, không bao giờ lưu rõ.
- **Ghi danh theo tập hợp (`PUT /admin/classes/{id}/members` body `{user_ids:[...]}`):**
  1. Khóa dòng lớp `SELECT … FOR UPDATE` để hai admin sửa cùng lúc không đè nhau.
  2. Xác thực toàn bộ id là *học sinh tồn tại và đang hoạt động*; nếu có id sai → `422` liệt kê các id sai (không ghi gì).
  3. Tính `thêm = mới − cũ`, `bớt = cũ − mới`; `INSERT … ON CONFLICT DO NOTHING` cho `thêm`, `DELETE` cho `bớt`; trả số lượng thêm/bớt.
- **Rút học sinh khỏi lớp khi đang làm bài:** bài đang làm **không bị hủy** (attempt thuộc về học sinh); chỉ ngăn bắt đầu đề mới của lớp đó. Ghi rõ trong tài liệu để giáo viên biết.
- **Khóa tài khoản:** `is_active=false` + xóa phiên đăng nhập trong cùng transaction.
- **Đặt lại mật khẩu:** sinh mật khẩu mới, băm, xóa phiên cũ, trả mật khẩu một lần.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-3.2-01 | Username trùng / sai định dạng | Tạo `Nam 01`, `ab`, `nam01` hai lần | Hai lỗi 422 định dạng; lần trùng → 409 `username_taken` |
| TC-3.2-02 | Mật khẩu một lần | Tạo không nhập mật khẩu rồi `GET` học sinh | Phản hồi tạo có `generated_password`; `GET` sau đó **không** có trường mật khẩu |
| TC-3.2-03 | Ghi danh idempotent | Gọi `PUT members` hai lần cùng danh sách | Lần 2 trả `added=0, removed=0`; không lỗi |
| TC-3.2-04 | Tập có id sai | Danh sách có 1 id không tồn tại và 1 id là admin | 422 liệt kê 2 id sai; không có thay đổi nào được ghi |
| TC-3.2-05 | Nhiều lớp | Học sinh thuộc lớp A và B, đề giao cho cả hai | `GET /student/exams` (bước 5.1) trả đề **một lần**, không trùng |
| TC-3.2-06 | Hai admin sửa đồng thời | Hai luồng `PUT members` song song với tập khác nhau | Kết quả cuối là tập của luồng chạy sau (tuần tự hóa), không có dữ liệu "nửa vời" |
| TC-3.2-07 | Rút khỏi lớp giữa kỳ thi | Rút học sinh khi đang `in_progress` | Học sinh vẫn lưu và nộp bài được; không thể bắt đầu đề khác của lớp đó |
| TC-3.2-08 | Khóa tài khoản | Khóa học sinh đang có phiên | Phiên bị xóa; request kế tiếp 401 |

---

## Bước 3.3 — Nhập học sinh hàng loạt bằng CSV

**Yêu cầu cần đạt**
- Chịu được file xuất từ Excel tiếng Việt (UTF-8 có BOM, hoặc Windows-1258; dấu phân tách `,` hoặc `;`).
- **Xem trước (dry-run) → xác nhận**; khi xác nhận là **tất cả hoặc không gì cả**.
- Xuất được bảng tên đăng nhập/mật khẩu để phát cho học sinh, không bị lỗi "CSV injection".

**Cách thức triển khai**
- **Giới hạn:** ≤ 1 MB, ≤ 500 dòng, bắt buộc có hàng tiêu đề.
- **Giải mã & phân tích:**
```python
def decode_csv(raw: bytes) -> str:
    for enc in ("utf-8-sig", "cp1258"):      # BOM của Excel; cp1258 = tiếng Việt Windows
        try: return raw.decode(enc)
        except UnicodeDecodeError: pass
    raise AppError("csv_encoding", "Không đọc được mã hóa tệp", 400)

dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")   # lỗi → dùng ","
```
  Tiêu đề được chuẩn hóa (bỏ dấu, chữ thường, `_`) và có bí danh: `ho_ten|họ tên|full_name`, `username|tên đăng nhập`, `mat_khau|mật khẩu|password`, `ma_lop|mã lớp|class`.
- **Hai pha:** `POST /admin/students/import?dry_run=true` → trả báo cáo từng dòng (`ok` / danh sách lỗi: `username_invalid`, `username_duplicate_in_file`, `username_taken`, `class_not_found`, `name_empty`); **không ghi gì**. `dry_run=false` → chạy lại đúng các kiểm tra rồi ghi trong **một transaction**; bất kỳ dòng lỗi nào → rollback toàn bộ, trả báo cáo. (Hai lần xác nhận liên tiếp không tạo trùng vì `username` duy nhất → lần 2 bị `409`, an toàn.)
- **Mật khẩu học sinh trong CSV (Không mật khẩu mặc định):** Cột mật khẩu trong CSV do giáo viên tự quyết định thiết lập cho từng học sinh. Nếu ô mật khẩu để trống, hệ thống chỉ sinh ngẫu nhiên khi giáo viên **chủ động bật tùy chọn 'Tự động tạo mật khẩu ngẫu nhiên an toàn cho các ô trống'** trên giao diện trước khi xác nhận (tuyệt đối không gán mật khẩu mặc định). Mật khẩu ngẫu nhiên dùng `secrets.choice` trên bảng ký tự không gây nhầm lẫn `ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789`, dài 8, đảm bảo có ít nhất một chữ và một số.
- **Băm:** Argon2 từng dòng tuần tự (qua semaphore ở 2.3); 40 học sinh ≈ vài giây, chấp nhận được. Trả về thời gian ước tính trong báo cáo dry-run.
- **Tệp mật khẩu cho giáo viên:** trả trong phản hồi xác nhận (một lần) kèm nút "Tải CSV"; làm sạch ô bắt đầu bằng `= + - @` hoặc ký tự điều khiển bằng cách thêm `'` ở đầu; ghi UTF-8 có BOM để Excel mở đúng tiếng Việt.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-3.3-01 | UTF-8 BOM + `;` | File Excel VN lưu "CSV UTF-8" | Đọc đúng tên có dấu, đúng cột |
| TC-3.3-02 | Windows-1258 | File lưu bằng mã hóa ANSI tiếng Việt | Giải mã đúng, tên "Nguyễn Văn Ánh" không vỡ chữ |
| TC-3.3-03 | Dry-run | Gửi `dry_run=true` với file có 3 dòng lỗi | Báo cáo đúng 3 dòng/lý do; số học sinh trong DB không đổi |
| TC-3.3-04 | Atomic | Dòng 30/40 trùng username đã tồn tại, `dry_run=false` | Rollback toàn bộ: **0** học sinh mới; báo cáo chỉ rõ dòng 30 |
| TC-3.3-05 | Trùng trong file | Hai dòng cùng `username` | Cả hai bị đánh dấu `username_duplicate_in_file` |
| TC-3.3-06 | Giới hạn | File 501 dòng; file 2 MB; file rỗng; file thiếu tiêu đề | Lần lượt 422/413/400/400 với mã lỗi rõ ràng |
| TC-3.3-07 | CSV injection | Tên `=HYPERLINK("http://x")` | Trong CSV xuất ra bị thêm `'` ở đầu, Excel không thực thi công thức |
| TC-3.3-08 | Ô có dấu phẩy/nháy | Tên `"Trần, Văn ""A"""` | Phân tích đúng thành `Trần, Văn "A"` |
| TC-3.3-09 | Mật khẩu hợp lệ | Sinh 1000 mật khẩu | Không có ký tự trong `0OIl1`; mỗi mật khẩu có ≥ 1 chữ và ≥ 1 số |
| TC-3.3-10 | Lớp không tồn tại | `ma_lop=ZZZ` | Dòng lỗi `class_not_found`; không tự tạo lớp |

---

## Bước 3.4 — Giao diện quản trị: lớp, học sinh, nhập CSV

**Yêu cầu cần đạt**
- Giáo viên hoàn thành: tạo lớp → thêm/nhập học sinh → ghi danh → tải bảng mật khẩu, không cần xem hướng dẫn.
- Lỗi từ server hiển thị **đúng chỗ** (đúng ô nhập / đúng dòng CSV).

**Cách thức triển khai**
- **Trang:** `ClassesPage`, `ClassDetailPage` (tab: Học sinh | Ghi danh | Nhập CSV), `StudentsPage`, `StudentDetail` (đặt lại mật khẩu, khóa).
- **Biểu mẫu:** `react-hook-form` + `zod` (cùng quy tắc username/mã lớp với server); lỗi `422` ánh xạ vào từng trường qua `details`; lỗi `409` hiện ngay dưới trường tương ứng.
- **Trình hướng dẫn nhập CSV (3 bước):** (1) kéo thả/chọn tệp, hiển thị tên + dung lượng; (2) gọi dry-run, hiển thị bảng: dòng hợp lệ (xanh), dòng lỗi (đỏ + lý do), tóm tắt; nút "Xác nhận" **bị vô hiệu** nếu còn lỗi; (3) gọi xác nhận, hiện mật khẩu và nút "Tải CSV" + cảnh báo "Mật khẩu chỉ hiển thị một lần".
- **Chống thao tác trùng:** nút gửi vô hiệu khi đang gọi; thao tác nguy hiểm (khóa, xóa, đặt lại mật khẩu) qua `ConfirmDialog` nêu rõ hậu quả.
- **Danh sách:** phân trang + tìm kiếm có debounce 300 ms; huỷ yêu cầu cũ (`AbortController`) khi gõ tiếp để không hiển thị kết quả cũ chồng lên mới.
- **Đồng bộ:** sau mỗi thay đổi dùng `invalidateQueries` đúng khóa; khi `409 version_conflict` hiện "Dữ liệu đã được người khác thay đổi — Tải lại".

**Test case kiểm thử và yêu cầu cần đạt** (Vitest/RTL + Playwright)

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-3.4-01 | Luồng đầy đủ (E2E) | Tạo lớp → nhập CSV 10 học sinh → ghi danh → tải CSV mật khẩu | Hoàn thành; CSV tải về mở được tiếng Việt; 10 học sinh thấy trong lớp |
| TC-3.4-02 | Lỗi theo trường | Nhập mã lớp trùng | Lỗi hiện ngay dưới ô "Mã lớp", không phải toast chung chung |
| TC-3.4-03 | Bấm đúp "Tạo" | Nhấn nhanh 2 lần | Chỉ 1 yêu cầu gửi đi; chỉ 1 lớp được tạo |
| TC-3.4-04 | Dry-run có lỗi | Tệp có 2 dòng lỗi | Nút "Xác nhận" bị vô hiệu; dòng lỗi nổi bật kèm lý do |
| TC-3.4-05 | Tìm kiếm gõ nhanh | Gõ "nguy" rồi "nguyen" thật nhanh với mạng chậm | Chỉ hiển thị kết quả của "nguyen"; không nhấp nháy kết quả cũ |
| TC-3.4-06 | Xung đột phiên bản | Sửa lớp ở hai tab | Tab sau nhận thông báo xung đột và có nút tải lại, không ghi đè |
| TC-3.4-07 | Mất mạng giữa lúc xác nhận nhập | Ngắt mạng khi bấm "Xác nhận" | Hiện lỗi mạng; **không** tự gửi lại; hướng dẫn kiểm tra danh sách trước khi thử lại |

---

# GIAI ĐOẠN 4. SOẠN ĐỀ

## Bước 4.1 — Lược đồ câu hỏi theo từng dạng và "góc nhìn học sinh" không lộ đáp án

**Yêu cầu cần đạt**
- Mỗi trong 5 dạng câu (`mcq`, `tf`, `short_text`, `short_number`, `file_upload`) có lược đồ `config` + `answer_key` được **kiểm tra chặt** khi tạo/sửa.
- Dữ liệu trả cho học sinh được tạo bằng **danh sách trắng (allow-list)**: thêm trường mới vào model không bao giờ tự động lộ ra học sinh.

**Cách thức triển khai**
- **Pydantic v2, union phân biệt theo `type`:** mỗi dạng một model riêng với `config` và `answer_key` có kiểu rõ ràng, thêm `model_validator` kiểm tra chéo:
  - `mcq`: 2–8 lựa chọn, `id` lựa chọn là mã đục (`o1…o8`, không dùng "A/B/C" để việc xáo trộn không làm lệch nhãn), `correct ∈ ids`, nội dung mỗi lựa chọn không rỗng.
  - `tf`: 1–8 mệnh đề; `answer_key` có đúng các khóa là `id` mệnh đề, giá trị `bool`; `scoring ∈ {thpt, proportional, all_or_nothing}`; nếu `thpt` mà số mệnh đề ≠ 4 thì tự chuyển `proportional` và báo cảnh báo trong phản hồi.
  - `short_text`: `accepted` 1–20 chuỗi không rỗng (chuẩn hóa NFC), `grading ∈ {auto, manual}`; nếu `manual` thì `accepted` có thể rỗng; `review_wrong` (bool, mặc định `false`: bật thì đáp án không khớp được đánh dấu "cần xem lại").
  - `short_number`: `values` 1–10 chuỗi **phân tích được** bằng `parse_number` (cùng hàm với lúc chấm, xem 6.1), `tolerance ≥ 0`, `tolerance_type ∈ {abs, rel}`.
  - `file_upload`: `max_files ∈ [1,5]`, `max_mb ∈ [1, MAX_UPLOAD_MB]`, `allowed_ext ⊆ {jpg,jpeg,png,pdf}`.
  - Chung: `points` là `Decimal` `0 < p ≤ 100`, tối đa 2 chữ số thập phân; `content_md ≤ 20 000` ký tự.
- **Hai nhóm schema đầu ra tách riêng file:** `schemas/admin_question.py` (đầy đủ) và `schemas/student_question.py`. Hàm dựng góc nhìn học sinh:
```python
STUDENT_CONFIG_KEYS = {
  "mcq": {"options"}, "tf": {"statements"}, "short_text": set(),
  "short_number": set(), "file_upload": {"max_files", "max_mb", "allowed_ext"},
}
def student_view(q, seed: int | None, shuffle_options: bool) -> dict:
    cfg = {k: v for k, v in q.config.items() if k in STUDENT_CONFIG_KEYS[q.type]}
    if q.type == "mcq" and shuffle_options:
        cfg["options"] = sorted(cfg["options"], key=lambda o: stable_key(seed, q.id, o["id"]))
    return {"id": str(q.id), "type": q.type, "content_md": q.content_md,
            "points": str(q.points), "config": cfg}          # KHÔNG có answer_key/explanation_md
```
- **Thay `asset:<uuid>` bằng URL ký** ngay trong `student_view` (bước 4.3).
- **Bắt lỗi:** khi dữ liệu cũ trong DB không khớp lược đồ (lỗi di trú), `student_view` ném `AppError("question_corrupt")`, ghi log; endpoint làm bài **không sập cả đề** mà đánh dấu câu đó `unavailable` để giáo viên xử lý (và câu này được tính "cần xem lại" khi chấm).

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-4.1-01 | Hợp lệ 5 dạng | Tạo mỗi dạng với dữ liệu chuẩn | 201; đọc lại giống dữ liệu gửi (đã chuẩn hóa) |
| TC-4.1-02 | Sai lược đồ | MCQ chỉ 1 lựa chọn; `correct` không thuộc lựa chọn; TF thiếu khóa đáp án; số `values=["abc"]`; `allowed_ext=["exe"]` | Mỗi trường hợp 422 với `details` chỉ đúng trường |
| TC-4.1-03 | Điểm biên | `points=0`, `-1`, `100.01`, `0.255`, `0.25` | Chỉ `0.25` (và giá trị hợp lệ khác) được nhận |
| TC-4.1-04 | **Không lộ đáp án (allow-list)** | Tạo câu mọi dạng rồi gọi `student_view`; thêm một trường bí mật `config.secret` | Đầu ra chỉ chứa khóa trong danh sách trắng; `secret`, `correct`, `accepted`, `values`, `tolerance`, `explanation_md` **không bao giờ** xuất hiện |
| TC-4.1-05 | Kiểm thuộc tính (property test) | Dùng `hypothesis` sinh câu hỏi ngẫu nhiên hợp lệ | Quét đệ quy đầu ra: không khóa nào thuộc tập cấm; mọi khóa nằm trong danh sách trắng |
| TC-4.1-06 | Dữ liệu hỏng | Chèn tay câu MCQ thiếu `options` vào DB | Endpoint làm bài vẫn trả các câu khác; câu hỏng được đánh dấu `unavailable`, có log |
| TC-4.1-07 | Xáo lựa chọn ổn định | Gọi `student_view` hai lần cùng `seed`; và hai `seed` khác nhau | Cùng seed → cùng thứ tự; khác seed → (thường) khác thứ tự; `id` lựa chọn không đổi |
| TC-4.1-08 | TF 3 mệnh đề + `thpt` | Tạo câu TF 3 mệnh đề chọn `thpt` | Phản hồi chứa cảnh báo, `scoring` lưu là `proportional` |

---

## Bước 4.2 — API đề thi, thiết lập đề và máy trạng thái vòng đời

**Yêu cầu cần đạt**
- Vòng đời `draft → published → closed → archived` chỉ chuyển qua các cạnh hợp lệ.
- Đề đã có người bắt đầu làm thì **khóa nội dung** (câu hỏi, đáp án, điểm, thời lượng, xáo trộn); vẫn cho sửa các trường không ảnh hưởng điểm.
- Nhân bản đề tạo bản độc lập hoàn toàn (kể cả ảnh).

**Cách thức triển khai**
- **Bảng chuyển trạng thái:**

| Từ → Đến | Điều kiện | Tác động |
|---|---|---|
| draft → published | Qua kiểm tra trước xuất bản (xem dưới) | Học sinh thấy đề theo cửa sổ `open_at/close_at` |
| published → draft | Chưa có attempt nào | Ẩn đề |
| published → closed | — | Gọi `finalize_all(exam_id, "teacher_closed")` (5.8); từ chối bắt đầu mới |
| closed → published | Chỉ khi `close_at` còn ở tương lai hoặc `NULL` | Mở lại cho phép bắt đầu mới |
| closed → archived | — | Ẩn khỏi danh sách chính; đủ điều kiện dọn dữ liệu (6.5) |
| (khác) | — | `409 invalid_transition` |

- **Kiểm tra trước xuất bản (`GET /admin/exams/{id}/validate` → danh sách vấn đề):** ≥ 1 câu hỏi; mọi câu qua lược đồ; tổng điểm > 0; ≥ 1 lớp được giao và không lớp nào đã lưu trữ; `duration_minutes ∈ [1, 300]`; `open_at < close_at` (nếu có); `close_at` chưa ở quá khứ. Xuất bản chạy lại chính hàm này trong transaction, không tin kết quả cũ.
- **Khóa nội dung:** `exams.locked_at` được đặt ở bước 5.2 (lúc có học sinh đầu tiên bắt đầu). Khi `locked_at IS NOT NULL`, các thao tác sửa/xóa/thêm/đổi thứ tự câu hỏi, sửa `duration_minutes`, `shuffle_*` → `409 exam_locked`. **Vẫn cho sửa:** `title`, `description_md`, `result_visibility`, `open_at`, `close_at` (đổi `close_at` chỉ ảnh hưởng người bắt đầu **sau** đó; hạn của attempt đang chạy đã cố định).
- **Khóa lạc quan:** `PATCH` kèm `version`; sai phiên bản → `409 version_conflict`.
- **Đổi thứ tự (`POST …/questions/reorder` body `{ordered_ids}`):** kiểm tra tập id đúng bằng tập câu hiện có; trong **một transaction** cập nhật `position = 1..n` (nhờ ràng buộc `DEFERRABLE` ở 2.2 nên không vướng giữa chừng).
- **Nhân bản (`POST …/duplicate`):** sao chép đề + câu hỏi sang bản `draft` mới (tên "… (bản sao)", không sao chép lớp được giao, `locked_at=NULL`). Với ảnh: gom mọi `asset:<uuid>` trong `content_md/config/explanation_md` bằng regex, **sao chép đối tượng ở R2 phía server** (`copy_object`) sang khóa mới, tạo hàng `files` mới, thay id trong văn bản theo bảng ánh xạ cũ→mới. Thực hiện: ghi DB trong transaction, sao chép S3 **trước khi commit**; nếu lỗi giữa chừng → rollback và xóa các đối tượng vừa sao chép (bù trừ).
- **Xóa đề:** chỉ khi `draft` hoặc chưa có attempt; còn lại phải qua "Xóa dữ liệu" (6.5).

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-4.2-01 | Cạnh hợp lệ/không hợp lệ | Thử mọi cặp trạng thái (bảng 5×5) | Chỉ các cạnh trong bảng thành công; còn lại `409 invalid_transition` |
| TC-4.2-02 | Xuất bản thiếu điều kiện | Đề không câu hỏi; đề không giao lớp; `open_at ≥ close_at` | Mỗi trường hợp bị từ chối, `validate` liệt kê đúng vấn đề |
| TC-4.2-03 | Khóa nội dung | Sau khi 1 học sinh bắt đầu, thử sửa điểm câu 1, xóa câu 2, đổi `duration` | Cả ba → `409 exam_locked`; sửa `title` và `result_visibility` vẫn thành công |
| TC-4.2-04 | Đổi `close_at` sau khi khóa | Gia hạn `close_at` thêm 1 giờ | Attempt đang chạy **không đổi** `deadline_at`; học sinh bắt đầu sau đó dùng `close_at` mới |
| TC-4.2-05 | Đổi thứ tự | Đảo 5 câu; gửi tập id thiếu 1 câu; gửi id trùng | Lần đầu thành công, `position` liên tục 1..5; hai lần sau `422` và không thay đổi gì |
| TC-4.2-06 | Nhân bản có ảnh | Đề 3 ảnh → nhân bản → xóa đề gốc (draft) | Bản sao vẫn hiển thị đủ 3 ảnh (đối tượng R2 độc lập); không còn tham chiếu `asset:` của đề gốc |
| TC-4.2-07 | Nhân bản lỗi giữa chừng | Giả lập `copy_object` lỗi ở ảnh thứ 2 | Không có đề mới nào được tạo; không còn đối tượng R2 mồ côi |
| TC-4.2-08 | Sửa đồng thời | Hai admin `PATCH` cùng `version` | Một thành công, một `409 version_conflict` |
| TC-4.2-09 | Mở lại đề đã đóng | `closed → published` khi `close_at` đã qua / còn hạn | Lần đầu bị từ chối; lần sau thành công |

---

## Bước 4.3 — Tải ảnh cho đề và phát ảnh an toàn

**Yêu cầu cần đạt**
- Giáo viên tải ảnh (jpg/png/webp ≤ 5 MB), nhận về mã `asset:<uuid>` để chèn vào Markdown.
- Tệp được **kiểm tra nội dung thật** và mã hóa lại; không tin phần mở rộng hay `Content-Type` do client khai.
- Ảnh không công khai; học sinh chỉ nhìn thấy ảnh thuộc đề của mình qua URL có hạn.

**Cách thức triển khai**
- **Phía client:** nén bằng `browser-image-compression` (cạnh dài ≤ 1600 px, mục tiêu ≤ 1 MB) trước khi tải để tiết kiệm băng thông và dung lượng R2.
- **Phía server (`POST /admin/assets`, multipart, bắt buộc `exam_id`):**
  1. Đọc theo từng khối 64 KB, **dừng ngay khi vượt 5 MB** (`413`), không nạp cả tệp vào bộ nhớ trước khi kiểm tra.
  2. Kiểm tra chữ ký (magic bytes) bằng Pillow: `Image.open` + `verify()`, mở lại; đặt `Image.MAX_IMAGE_PIXELS = 40_000_000` để chặn "bom giải nén"; chỉ chấp nhận định dạng thực sự là JPEG/PNG/WEBP; **từ chối SVG** (chứa script).
  3. **Mã hóa lại** sang WEBP (chất lượng ~85, cạnh dài ≤ 2000 px) — loại bỏ EXIF (vị trí GPS…) và mọi dữ liệu nhúng/polyglot.
  4. Ghi lên R2 ở khóa `exams/{exam_id}/img/{uuid}.webp`; chèn hàng `files(kind='question_image')`; trả `{asset: "asset:<uuid>", markdown: "![](asset:<uuid>)"}`.
  5. Thứ tự **S3 trước, DB sau**; nếu chèn DB lỗi → xóa đối tượng vừa ghi.
- **Phát ảnh:** trong `student_view`/`admin_view`, hàm `render_assets(md, exam_id, ttl)`:
```python
ASSET_RE = re.compile(r"asset:([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")
def render_assets(md, exam_id, db, ttl=6*3600):
    ids = set(ASSET_RE.findall(md))
    owned = {str(f.id): f for f in db.scalars(select(File).where(File.id.in_(ids), File.exam_id == exam_id))}
    def sub(m):
        f = owned.get(m.group(1))
        return presign_get(f.storage_key, ttl) if f else "about:blank"   # id không thuộc đề → vô hiệu
    return ASSET_RE.sub(sub, md)
```
  Việc chỉ tra theo `exam_id` ngăn một đề **trỏ sang ảnh của đề khác**. TTL 6 giờ đủ cho bài dài nhất (300 phút) cộng dư; tải lại trang luôn lấy URL mới.
- **Dọn ảnh mồ côi:** job hằng tuần xóa `files(kind='question_image')` không được tham chiếu trong bất kỳ văn bản câu hỏi nào và cũ hơn 7 ngày; khi xóa đề cũng xóa ảnh của đề.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-4.3-01 | Ảnh hợp lệ | Tải PNG 800 KB | 201; ảnh WEBP trên R2; chèn Markdown hiển thị được trong editor |
| TC-4.3-02 | Giả mạo định dạng | Đổi tên `virus.exe` → `a.png`; file PDF gắn `Content-Type: image/png` | `415/400 invalid_image`; không ghi gì lên R2 |
| TC-4.3-03 | Quá dung lượng | Tải 6 MB; và gửi luồng 50 MB không có `Content-Length` | `413` ngay khi vượt ngưỡng; bộ nhớ máy chủ không tăng đột biến |
| TC-4.3-04 | Bom giải nén | Ảnh PNG 30.000×30.000 px nén nhỏ | Bị từ chối (vượt `MAX_IMAGE_PIXELS`), server không treo |
| TC-4.3-05 | SVG / ảnh chứa script | Tải `a.svg` có `<script>` | Bị từ chối |
| TC-4.3-06 | Xóa EXIF | Ảnh JPEG có GPS trong EXIF | Ảnh lưu **không còn** EXIF (kiểm bằng `exiftool`/Pillow) |
| TC-4.3-07 | URL ký hết hạn | Lấy URL ký với TTL 5 giây, chờ 10 giây | Truy cập trả 403 |
| TC-4.3-08 | Tham chiếu chéo đề | Đề B chèn `asset:<id ảnh của đề A>` | Khi hiển thị, ảnh đó **không** được nạp (`about:blank`) |
| TC-4.3-09 | Lỗi DB sau khi ghi R2 | Giả lập lỗi chèn `files` | Đối tượng R2 vừa ghi bị xóa (bù trừ); trả 500 an toàn |
| TC-4.3-10 | Quyền | Student gọi `POST /admin/assets` | 403 |

---

## Bước 4.4 — Giao diện soạn đề (trình soạn câu hỏi, xem trước trực tiếp)

**Yêu cầu cần đạt**
- Giáo viên tạo đề đủ 5 dạng câu, nhập LaTeX, dán/tải ảnh, đặt điểm, sắp xếp câu, mà không mất dữ liệu khi lỡ đóng tab hay mất mạng.
- Khung xem trước hiển thị **giống hệt** học sinh sẽ thấy.

**Cách thức triển khai**
- **Bố cục 3 cột (desktop):** danh sách câu (kéo thả `@dnd-kit`, hỗ trợ bàn phím) | biểu mẫu câu hỏi | xem trước. Mobile: tab chuyển Soạn/Xem trước.
- **Biểu mẫu theo dạng câu:** `react-hook-form` + `zod` (union phân biệt theo `type`, cùng quy tắc với server); thành phần con riêng: `McqEditor` (thêm/xóa lựa chọn, chọn đáp án đúng bằng radio), `TfEditor` (bảng mệnh đề + công tắc Đúng/Sai), `ShortTextEditor` (danh sách đáp án chấp nhận + tùy chọn hoa/thường, bỏ dấu), `ShortNumberEditor` (giá trị đúng, sai số, loại sai số, **ô thử nhanh**: nhập thử "1,5" hoặc "3/2" để thấy kết quả chấm), `FileUploadEditor`.
- **Xem trước:** dùng **chính** `QuestionRenderer` + `MathText` của trang làm bài ở chế độ chỉ-đọc; debounce 200 ms; hiển thị tổng điểm và số lỗi công thức (đếm từ phần tử lỗi KaTeX).
- **Thanh công cụ LaTeX:** nút chèn mẫu (phân số, căn, mũ/chỉ số, tích phân, tổng, ma trận, hệ phương trình, ký hiệu Hy Lạp) tại vị trí con trỏ bằng `setRangeText`, đặt con trỏ vào chỗ trống đầu tiên.
- **Dán ảnh:** bắt `onPaste` với `clipboardData.files`, tải lên (4.3), chèn `![](asset:…)`; hiện thanh tiến trình; lỗi → thông báo tại chỗ, không chèn gì.
- **Lưu nháp tự động theo từng câu:** debounce 1,5 giây → `PATCH` kèm `version`; chỉ báo "Đã lưu nháp / Đang lưu / Chưa lưu được"; **không gửi khi đang gõ tiếng Việt bằng bộ gõ** (`compositionstart…compositionend`) để tránh lưu giữa chừng ký tự chưa hoàn tất. Chặn rời trang (`beforeunload`) khi còn thay đổi chưa lưu.
- **Xung đột `409 version_conflict`:** hộp thoại hai lựa chọn "Tải lại bản mới nhất" (mất thay đổi cục bộ — kèm nút sao chép nội dung đang soạn vào clipboard trước) hoặc "Ghi đè" (gửi lại với `version` mới nhất).
- **Đề đã khóa:** toàn bộ biểu mẫu chuyển chỉ-đọc, hiện dải thông báo và nút "Nhân bản để chỉnh sửa".

**Test case kiểm thử và yêu cầu cần đạt** (Playwright)

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-4.4-01 | Tạo đề đủ 5 dạng | Soạn mỗi dạng một câu, đặt điểm, lưu | Tổng điểm đúng; tải lại trang dữ liệu y nguyên |
| TC-4.4-02 | Xem trước = góc nhìn học sinh | So ảnh chụp phần câu hỏi trong xem trước và trong trang làm bài (cùng dữ liệu) | Giống nhau theo ngưỡng; **không** hiển thị đáp án đúng ở xem trước câu hỏi |
| TC-4.4-03 | Gõ tiếng Việt (Telex) | Gõ "Tính đạo hàm của hàm số" bằng bộ gõ trong ô nội dung | Văn bản đúng; không có yêu cầu lưu nào phát đi trong lúc đang `composition` |
| TC-4.4-04 | Dán ảnh | Dán ảnh từ clipboard | Hiện tiến trình, sau đó chèn Markdown; xem trước hiển thị ảnh |
| TC-4.4-05 | Kéo thả sắp xếp | Kéo câu 5 lên đầu bằng chuột và bằng bàn phím | Thứ tự mới được lưu; tải lại giữ nguyên; lỗi mạng khi lưu → hoàn tác giao diện + thông báo |
| TC-4.4-06 | Mất mạng khi soạn | Ngắt mạng, gõ tiếp, bật lại mạng | Chỉ báo "Chưa lưu được" → tự lưu lại khi có mạng; không mất chữ nào |
| TC-4.4-07 | Xung đột phiên bản | Sửa cùng một câu ở hai tab | Tab sau thấy hộp thoại xung đột với hai lựa chọn; nội dung không bị mất âm thầm |
| TC-4.4-08 | Công thức lỗi | Nhập `$\frac{1}{$` | Xem trước báo lỗi tại chỗ; bộ đếm lỗi công thức tăng; vẫn cho lưu nhưng cảnh báo khi xuất bản |
| TC-4.4-09 | Đề đã khóa | Mở đề đã có người làm | Biểu mẫu chỉ-đọc, nút "Nhân bản để chỉnh sửa" hoạt động |
| TC-4.4-10 | Ô thử số | Đáp án `0.5` sai số 0: thử `1/2`, `0,5`, `.5`, `0.50`, `1/3` | Bốn giá trị đầu "đúng", `1/3` "sai" |

---

## Bước 4.5 — Xuất bản, giao lớp và xem trước như học sinh

**Yêu cầu cần đạt**
- Xuất bản đề kèm giao lớp trong một thao tác rõ ràng, có hộp thoại tóm tắt hậu quả.
- Xem trước như học sinh **không tạo attempt và không khóa đề**.

**Cách thức triển khai**
- **Hộp thoại xuất bản:** hiển thị kết quả `validate` (lỗi chặn / cảnh báo), tóm tắt: số câu, tổng điểm, thời lượng, cửa sổ mở/đóng, các lớp được giao và **số học sinh bị ảnh hưởng**; nút "Xuất bản" chỉ bật khi không còn lỗi chặn; xác nhận gõ lại tên đề khi đề đã từng đóng/mở lại.
- **Cảnh báo công thức:** trước khi xuất bản, trình soạn đếm lỗi KaTeX của mọi câu (render ẩn) và hiện danh sách câu có lỗi để sửa.
- **`GET /admin/exams/{id}/preview`:** trả `student_view` cho mọi câu (cùng hàm với học sinh, bao gồm xáo trộn bằng seed ngẫu nhiên tạm), **không ghi bất kỳ hàng `attempts/answers` nào và không đặt `locked_at`**. Trang xem trước dùng lại giao diện làm bài ở chế độ "sandbox": đáp án chỉ lưu trong bộ nhớ trình duyệt, đồng hồ giả lập, có dải thông báo "Chế độ xem trước — không lưu".
- **Giao lớp:** `PUT /admin/exams/{id}/classes` theo tập hợp (giống ghi danh ở 3.2); sau khi `locked_at` đặt, chỉ cho **thêm** lớp, không rút lớp đã có học sinh làm.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-4.5-01 | Xem trước không tác dụng phụ | Mở xem trước, làm 3 câu | Bảng `attempts`, `answers` **không đổi**; `exams.locked_at` vẫn `NULL` |
| TC-4.5-02 | Xuất bản đúng | Đề hợp lệ giao 2 lớp | Học sinh của 2 lớp thấy đề (bước 5.1); học sinh lớp khác không thấy |
| TC-4.5-03 | Bị chặn khi thiếu điều kiện | Đề có câu MCQ không chọn đáp án đúng | Nút "Xuất bản" bị vô hiệu; danh sách lỗi trỏ đúng câu |
| TC-4.5-04 | Rút lớp sau khi khóa | Đề đã có học sinh của lớp A làm; thử rút lớp A | `409`; thêm lớp B vẫn được |
| TC-4.5-05 | Cảnh báo công thức | Một câu có công thức lỗi | Hộp thoại xuất bản liệt kê câu đó; cho phép bỏ qua có chủ đích (có xác nhận) |
| TC-4.5-06 | Xuất bản đồng thời | Hai tab cùng bấm "Xuất bản" | Một thành công, tab kia nhận trạng thái đã xuất bản (không lỗi 500, không bản ghi trùng) |

---

# GIAI ĐOẠN 5. LÀM BÀI (PHẦN RỦI RO CAO NHẤT)

> Quy tắc làm giai đoạn này: **viết test trước**, đặc biệt cho 5.2, 5.4, 5.7, 5.8. Mọi test về thời gian dùng `FakeClock`; mọi test về đồng thời chạy trên **PostgreSQL thật** (không dùng SQLite) với nhiều luồng/kết nối.

## Bước 5.1 — Danh sách đề của học sinh và trang giới thiệu đề

**Yêu cầu cần đạt**
- Học sinh chỉ thấy đề thuộc các lớp mình ghi danh, kèm trạng thái chính xác theo thời gian thực của server.
- Không có dữ liệu nào về điểm/đáp án trong phản hồi.

**Cách thức triển khai**
- **Truy vấn:** một câu `SELECT DISTINCT ON (e.id)` nối `exam_classes → class_members(user=:uid)` và `LEFT JOIN attempts(student=:uid)`; điều kiện hiển thị: `e.status='published' OR attempt tồn tại` (đề đã đóng vẫn hiện nếu học sinh từng làm); **ẩn** `draft` và `archived`.
- **Trạng thái tính ở server** bằng `Clock`: `upcoming` (chưa tới `open_at`), `open`, `closed` (quá `close_at` hoặc đề đã đóng, chưa làm), `in_progress`, `submitted`, `result_available` (`attempt.released=true`).
- **Trường trả về (allow-list):** `id, title, subject, duration_minutes, question_count, open_at, close_at, state, attempt_id`. Tuyệt đối không trả `total_score`, `result_visibility`, `answer_key`.
- **`GET /student/exams/{id}` (giới thiệu):** thêm `description_md` (đã `render_assets`), tổng điểm, hướng dẫn; kiểm tra quyền như trên, đề không thuộc lớp mình → `404` (không phải 403, tránh dò đề).
- **Ngay cả khi có lỗi:** nếu truy vấn lỗi tạm thời → `503` để frontend thử lại, không trả danh sách rỗng giả (tránh học sinh tưởng không có đề).

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-5.1-01 | Cách ly lớp | Học sinh A (lớp 1), B (lớp 2); đề giao lớp 1 | A thấy, B không thấy; B gọi `/student/exams/{id}` → 404 |
| TC-5.1-02 | Nhiều lớp | A thuộc cả lớp 1 và 2, đề giao cả hai | Đề xuất hiện **đúng 1 lần** |
| TC-5.1-03 | Trạng thái theo thời gian | Dùng `FakeClock` đặt trước `open_at`, trong cửa sổ, sau `close_at` | Lần lượt `upcoming`, `open`, `closed` |
| TC-5.1-04 | Trạng thái sau khi làm | Có attempt `in_progress`; đã `submitted`; đã `released` | `in_progress`, `submitted`, `result_available`; **không** có điểm trong JSON |
| TC-5.1-05 | Đề nháp / lưu trữ | Đề `draft`, `archived` (chưa làm) | Không xuất hiện |
| TC-5.1-06 | Đề đã đóng nhưng từng làm | Đề `closed`, học sinh đã nộp | Vẫn hiện với `submitted` |
| TC-5.1-07 | Lỗi tạm thời | Giả lập DB lỗi | 503; frontend hiển thị thử lại, không hiện "Chưa có đề" |

---

## Bước 5.2 — Bắt đầu làm bài (idempotent, an toàn khi bấm đúp / mở nhiều tab)

**Yêu cầu cần đạt**
- Mỗi cặp `(exam, student)` chỉ có **một** attempt dù bấm "Bắt đầu" nhiều lần, từ nhiều tab/thiết bị, đồng thời.
- `deadline_at` tính ở server theo `compute_deadline`; đề được khóa nội dung khi có người bắt đầu đầu tiên.

**Cách thức triển khai**
- **Thuật toán (một transaction):**
```python
def start_attempt(db, user, exam_id, clock):
    now = clock.now()
    exam = get_exam_visible_to(db, user, exam_id)             # 404 nếu không thuộc lớp / chưa xuất bản & chưa từng làm
    existing = db.scalar(select(Attempt).where(Attempt.exam_id==exam_id, Attempt.student_id==user.id))
    if existing:
        return resume_or_finalize(existing, now)              # đã có → trả lại (tiếp tục, hoặc nộp lười nếu quá hạn)
    if exam.status != "published": raise AppError("exam_not_open", status=409)
    if exam.open_at and now < exam.open_at: raise AppError("exam_not_open", status=409)
    if exam.close_at and now >= exam.close_at: raise AppError("exam_closed", status=409)
    deadline = compute_deadline(now, exam.duration_minutes, 0, exam.close_at)
    stmt = (pg_insert(Attempt).values(exam_id=exam_id, student_id=user.id, status="in_progress",
              started_at=now, deadline_at=deadline, shuffle_seed=secrets.randbits(62))
            .on_conflict_do_nothing(index_elements=["exam_id","student_id"]).returning(Attempt.id))
    row = db.execute(stmt).first()
    if row is None:                                            # thua cuộc đua → đọc bản đã được người khác tạo
        return resume_or_finalize(get_existing(db, exam_id, user.id), now)
    db.execute(update(Exam).where(Exam.id==exam_id, Exam.locked_at.is_(None)).values(locked_at=now))
    return get_attempt(db, row.id)
```
- **Kiểm tra quyền ghi danh** nằm trong `get_exam_visible_to` (EXISTS lớp chung giữa đề và học sinh; học sinh phải `is_active`).
- **`resume_or_finalize`:** attempt `submitted` → trả trạng thái đã nộp (200, không phải lỗi); `in_progress` nhưng `now > deadline + grace` → finalize lười (5.7) rồi trả đã nộp; còn lại trả attempt đang chạy.
- **Đồng thời:** ràng buộc `UNIQUE(exam_id, student_id)` + `ON CONFLICT DO NOTHING` là hàng rào cuối cùng, không dùng "kiểm tra rồi chèn" thuần ứng dụng.
- **Phía client:** nút "Bắt đầu" vô hiệu khi đang gọi; nhận được attempt (dù mới hay cũ) thì chuyển tới `/s/attempts/:id`.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-5.2-01 | Bắt đầu bình thường | Học sinh hợp lệ gọi `start` | 200; `deadline_at = now + duration` (hoặc `close_at` nếu sớm hơn); `locked_at` được đặt |
| TC-5.2-02 | **Đồng thời** | 10 luồng gọi `start` cùng lúc (PostgreSQL thật) | Chỉ **1** hàng `attempts`; mọi luồng nhận cùng `attempt_id`; không có lỗi 500 |
| TC-5.2-03 | Hai thiết bị | Điện thoại và laptop cùng bắt đầu | Cùng một attempt; hai nơi thấy cùng `deadline_at` |
| TC-5.2-04 | Cửa sổ thời gian | Trước `open_at`; đúng `open_at`; còn 1 giây tới `close_at`; sau `close_at` | `409 exam_not_open`; thành công; thành công với `deadline` chỉ còn 1 giây; `409 exam_closed` |
| TC-5.2-05 | Không thuộc lớp / tài khoản khóa | Học sinh lớp khác; học sinh `is_active=false` | 404; 401/403 theo thiết kế, không tạo attempt |
| TC-5.2-06 | Gọi lại sau khi nộp | `start` khi attempt đã `submitted` | 200 với trạng thái đã nộp; không tạo attempt mới, không đổi `deadline` |
| TC-5.2-07 | Gọi lại khi quá hạn chưa finalize | `in_progress`, `now = deadline + grace + 1s` | Được finalize lười, trả đã nộp với `submitted_at = deadline_at` |
| TC-5.2-08 | Khóa đề một lần | Hai học sinh bắt đầu | `locked_at` bằng thời điểm của người **đầu tiên**, không bị ghi đè |
| TC-5.2-09 | Đề chưa xuất bản | Gọi `start` đề `draft` | 404 (không lộ sự tồn tại) |

---

## Bước 5.3 — Nạp bài làm (tiếp tục sau gián đoạn) và xáo trộn ổn định

**Yêu cầu cần đạt**
- Mở lại bất kỳ lúc nào đều nhận đủ: câu hỏi (không đáp án), đáp án đã lưu, `deadline_at`, `server_now`.
- Thứ tự câu/lựa chọn đã xáo **không đổi** giữa các lần tải và giữa các thiết bị, nhưng khác nhau giữa các học sinh.

**Cách thức triển khai**
- **`GET /student/attempts/{id}`:** kiểm tra `attempt.student_id == user.id` (sai → `404`, không `403`); nếu `in_progress` và quá `deadline + grace` → finalize lười (sau khi nhả khóa) rồi trả `{status:"submitted", submitted_at}` không kèm câu hỏi.
- **Xáo trộn xác định, không phụ thuộc `hash()` của Python (thay đổi theo tiến trình):**
```python
def stable_key(seed: int, *parts: str) -> bytes:
    return hashlib.sha256(f"{seed}:{':'.join(parts)}".encode()).digest()

qs = sorted(questions, key=lambda q: stable_key(seed, str(q.id))) if exam.shuffle_questions \
     else sorted(questions, key=lambda q: q.position)
# mcq: sắp lựa chọn theo stable_key(seed, qid, option_id) nếu shuffle_options; mệnh đề tf GIỮ nguyên thứ tự a, b, c, d
```
- **Nhãn hiển thị** A/B/C/D do **client** gán theo vị trí hiển thị (id lựa chọn là mã đục `o1…`), nên xáo trộn không làm lệch nhãn.
- **Phản hồi:**
```json
{ "attempt": {"id":"…","status":"in_progress","deadline_at":"…Z","server_now":"…Z",
              "remaining_seconds": 1234, "grace_seconds": 10},
  "exam": {"title":"…","description_md":"…"},
  "questions": [ …student_view… ],
  "answers": { "<question_id>": {"value": {…}, "client_seq": 7} } }
```
  Kèm `Cache-Control: no-store`; nén gzip.
- **Tối ưu:** 2 truy vấn (attempt + câu hỏi/đáp án) bằng `selectinload`; `render_assets` gom mọi id ảnh của đề thành **một** truy vấn.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-5.3-01 | Thứ tự ổn định | Gọi `GET` 5 lần, và từ 2 phiên của cùng học sinh | Thứ tự câu và lựa chọn **y hệt** mỗi lần |
| TC-5.3-02 | Khác nhau giữa học sinh | 10 học sinh cùng đề bật xáo trộn | Có ≥ 2 thứ tự khác nhau (xác suất trùng hết ≈ 0) |
| TC-5.3-03 | **Không lộ đáp án** | Quét đệ quy toàn bộ JSON phản hồi với tập khóa cấm (`answer_key`, `correct`, `accepted`, `values`, `tolerance`, `explanation_md`) | 0 trùng khớp; đồng thời quét giá trị chuỗi không chứa đáp án đúng của câu số/chữ |
| TC-5.3-04 | Của người khác | Học sinh A gọi attempt của B | 404 |
| TC-5.3-05 | Tiếp tục sau khi đóng tab | Lưu 3 đáp án, `GET` lại | `answers` chứa đúng 3 đáp án + `client_seq` |
| TC-5.3-06 | Đã quá hạn | `now = deadline + grace + 1s` | Trả `submitted`; không có `questions`; DB attempt đã `submitted` với `submitted_at=deadline_at` |
| TC-5.3-07 | `remaining_seconds` | `now = deadline - 90,4 giây` | `remaining_seconds = 91` (làm tròn lên) |
| TC-5.3-08 | Số truy vấn | Đề 60 câu có 10 ảnh | ≤ 4 câu lệnh SQL cho toàn bộ request |
| TC-5.3-09 | Câu hỏng dữ liệu | Một câu `unavailable` (4.1) | Các câu còn lại hiển thị; câu hỏng có cờ, có log |

---

## Bước 5.4 — Lưu đáp án từng câu (chống ghi đè cũ, chống ghi sau hạn, tuần tự với finalize)

**Yêu cầu cần đạt**
- Mỗi lần học sinh đổi đáp án được lưu **riêng từng câu**; gói tin đến sai thứ tự hoặc từ tab cũ **không** ghi đè dữ liệu mới.
- Sau `deadline + grace` mọi ghi đều bị từ chối (`409 attempt_closed`).
- Đáp án đã được báo "đã lưu" trước thời điểm nộp **chắc chắn** có mặt trong lần chấm.

**Cách thức triển khai**
- **Endpoint:** `PUT /student/attempts/{id}/answers/{question_id}` body `{"value": {...}, "client_seq": 12}`.
- **Thuật toán (một transaction):**
```python
def save_answer(db, user, attempt_id, qid, value, client_seq, clock):
    now = clock.now()
    a = db.execute(select(Attempt)
          .where(Attempt.id == attempt_id, Attempt.student_id == user.id)
          .with_for_update(read=True)).scalar_one_or_none()     # SELECT … FOR SHARE
    if a is None: raise AppError("not_found", status=404)
    if a.status != "in_progress" or not is_writable(now, a.deadline_at, grace(a)):
        raise AttemptClosed(attempt_id)                          # sau khi rollback → finalize lười (xem dưới)
    q = get_question_of_exam(db, qid, a.exam_id)                 # 404 nếu không thuộc đề của attempt
    clean = validate_answer_value(q, value)                      # chuẩn hóa + kiểm tra theo dạng câu
    stmt = (pg_insert(Answer).values(attempt_id=a.id, question_id=qid, value=clean,
              client_seq=client_seq, updated_at=now)
            .on_conflict_do_update(index_elements=["attempt_id","question_id"],
              set_={"value": clean, "client_seq": client_seq, "updated_at": now,
                    "version": Answer.version + 1,
                    "score": None, "is_correct": None, "graded_by": None, "graded_at": None},  # an toàn khi mở lại bài (6.4)
              where=Answer.client_seq < client_seq)
            .returning(Answer.client_seq))
    meta = {"server_now": now, "deadline_at": a.deadline_at, "status": a.status}   # đúng đặc tả 3.8a
    if db.execute(stmt).first():
        return {"accepted": True,  "server_seq": client_seq, **meta}
    cur = db.scalar(select(Answer.client_seq).where(Answer.attempt_id==a.id, Answer.question_id==qid))
    return     {"accepted": False, "server_seq": cur, "reason": "stale", **meta}
```
- **Vì sao dùng `FOR SHARE` ở đây và `FOR UPDATE` ở finalize (5.7):** nhiều lần lưu chạy song song được (khóa chia sẻ), nhưng finalize phải **đợi các lần lưu đang dở commit xong**, và các lần lưu đến sau finalize thấy `status='submitted'` → `409`. Thứ tự khóa luôn là *attempt trước, answers sau* ở cả hai phía nên **không deadlock**.
- **Quá hạn nhưng chưa finalize:** `AttemptClosed` làm rollback; lớp bao ngoài endpoint, **sau khi nhả transaction**, gọi `finalize_attempt(attempt_id, "timeout")` (transaction mới, best-effort) rồi trả `409 attempt_closed`.
- **Phản hồi "stale" là 200 chứ không phải lỗi:** client hiểu "server đã có bản mới hơn hoặc bằng", bỏ mục đó khỏi hàng đợi (5.6).
- **Xác thực giá trị theo dạng câu:** `mcq` `{"choice": "<id>"|null}` (id phải thuộc lựa chọn); `tf` `{"<statement_id>": true|false|null}` (khóa ⊆ mệnh đề); `short_text` `{"text": str ≤ 500}` (NFC, bỏ ký tự điều khiển); `short_number` `{"text": str ≤ 40}`; tổng JSON ≤ 20 KB; `file_upload` **không** nhận qua endpoint này (dùng upload, 5.9).
- **Giới hạn tần suất theo attempt** (bộ đếm trong bộ nhớ, token bucket ~20 yêu cầu/10 giây): vượt → `429` + `Retry-After` (client có backoff, không mất dữ liệu vì còn trong outbox).
- **`server_seq` ban đầu:** khi nạp bài (5.3) client nhận `client_seq` hiện có của từng câu để khởi tạo bộ đếm cục bộ cao hơn.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-5.4-01 | Lưu bình thường | `seq=1` rồi `seq=2` cho cùng câu | Cả hai `accepted=true`; DB giữ giá trị của `seq=2`; `version` tăng |
| TC-5.4-02 | **Gói tin sai thứ tự** | Gửi `seq=5` rồi mới `seq=4` | `seq=4` trả `accepted=false, reason=stale, server_seq=5`; DB giữ giá trị `seq=5` |
| TC-5.4-03 | Gửi lặp cùng `seq` | Retry y hệt do mất phản hồi | Lần 2 trả `stale` (200) với `server_seq` = `seq` đã gửi; DB không đổi; client coi là đã xong |
| TC-5.4-04 | Hai tab cùng ghi một câu | Tab A `seq=7 "A"`, tab B `seq=8 "B"` đồng thời, thứ tự đến ngẫu nhiên | Giá trị cuối luôn là của `seq` lớn nhất (`"B"`), bất kể thứ tự đến |
| TC-5.4-05 | Biên hạn nộp | `now = deadline + grace` và `now = deadline + grace + 1µs` | Trường hợp đầu chấp nhận; trường hợp sau `409 attempt_closed` và attempt được finalize |
| TC-5.4-06 | Sau khi đã nộp | Lưu đáp án khi `status='submitted'` | `409 attempt_closed`; DB không đổi |
| TC-5.4-07 | **Đua với finalize** | 50 vòng: luồng A lưu đáp án, luồng B nộp bài, chạy đồng thời | Bất biến: *mọi* lần lưu trả `accepted=true` đều có giá trị đó trong kết quả chấm; mọi lần lưu bị từ chối là `409`; không deadlock; không có đáp án "ghi sau khi chấm" |
| TC-5.4-08 | Giá trị không hợp lệ | MCQ `choice="zz"`; TF khóa lạ; text 501 ký tự; JSON 30 KB; `file_upload` | Lần lượt `422`, không ghi gì |
| TC-5.4-09 | Câu thuộc đề khác | `question_id` của đề khác | 404 |
| TC-5.4-10 | Attempt người khác | Học sinh A ghi vào attempt của B | 404; không đổi dữ liệu của B |
| TC-5.4-11 | Giới hạn tần suất | 100 yêu cầu trong 1 giây cho cùng attempt | Một phần bị `429`; các phần được nhận đều đúng; không lỗi 500 |
| TC-5.4-12 | Xóa đáp án | `{"choice": null}` với `seq` cao hơn | Lưu thành công, câu được tính "chưa trả lời" khi chấm |

---

## Bước 5.5 — Đồng hồ đếm ngược phía client (đồng bộ với server, chịu được đổi giờ máy, ngủ máy)

**Yêu cầu cần đạt**
- Thời gian còn lại hiển thị luôn khớp `deadline_at` của server (sai lệch ≤ ~1 giây), kể cả khi học sinh chỉnh đồng hồ máy, tab bị trình duyệt làm chậm ở nền, hoặc máy ngủ rồi thức dậy.
- Hết giờ thì tự nộp đúng một lần; giáo viên cộng giờ thì đồng hồ cập nhật.

**Cách thức triển khai**
- **Không đếm bằng cách trừ dần mỗi giây** (dễ trôi khi tab bị làm chậm). Luôn **tính lại** từ mốc neo:
```ts
// lib/timer.ts
type Sample = { rtt: number; anchorPerf: number; anchorServerMs: number; anchorDate: number };
export class ServerClock {
  private samples: Sample[] = [];
  // gọi mỗi khi có phản hồi chứa server_now; tSend/tRecv lấy bằng performance.now() quanh lời gọi
  ingest(tSend: number, tRecv: number, serverNowMs: number) {
    const rtt = tRecv - tSend;
    this.samples.push({ rtt, anchorPerf: tRecv, anchorServerMs: serverNowMs + rtt / 2, anchorDate: Date.now() });
    this.samples = this.samples.slice(-5);
  }
  private best(): Sample {              // mẫu có RTT nhỏ nhất → sai số ước lượng nhỏ nhất
    return this.samples.reduce((a, b) => (b.rtt < a.rtt ? b : a));
  }
  nowMs(): number { const s = this.best(); return s.anchorServerMs + (performance.now() - s.anchorPerf); }
  needsResync(): boolean {              // phát hiện ngủ máy/đổi giờ: Date.now() và performance.now() chạy lệch nhau
    const s = this.best();
    const drift = (Date.now() - s.anchorDate) - (performance.now() - s.anchorPerf);
    return Math.abs(drift) > 2000;
  }
}
export const remainingMs = (deadlineMs: number, c: ServerClock) => Math.max(0, deadlineMs - c.nowMs());
```
  - Ước lượng bằng **trung điểm RTT** (`server_now + RTT/2`), giữ 5 mẫu gần nhất, dùng mẫu RTT nhỏ nhất.
  - `performance.now()` là đồng hồ đơn điệu nên **học sinh chỉnh giờ hệ thống giữa chừng không ảnh hưởng**.
  - Vì `performance.now()` có thể không chạy khi máy ngủ, `needsResync()` so với `Date.now()`; lệch > 2 giây thì buộc đồng bộ lại với server.
- **Khi nào đồng bộ:** lúc nạp bài (5.3), sau mỗi lần lưu thành công (phản hồi 5.4 có `server_now`, `deadline_at`, `status`), mỗi 30 giây bằng `GET /student/attempts/{id}/status` (endpoint nhẹ, bổ sung: trả `status, deadline_at, server_now`), và khi `visibilitychange→visible`, `focus`, `online`, `pageshow`.
- **Hiển thị:** `setInterval(250ms)` chỉ để **vẽ lại**; giá trị luôn tính bằng `remainingMs`. Định dạng `mm:ss` (hoặc `h:mm:ss`). Mốc cảnh báo ≤ 5 phút và ≤ 1 phút: đổi trạng thái màu + biểu tượng + nhãn chữ; `aria-live="polite"` **chỉ phát một lần ở mỗi mốc**.
- **Hết giờ (`remaining = 0`):** chuyển trạng thái `submitting`, khóa nhập liệu, gọi `submitOnce()` (5.6/5.7) có thử lại với backoff cho đến khi server xác nhận `submitted` hoặc `409 attempt_closed`. Server mới là bên quyết định cuối cùng (có `grace_seconds`).
- **Cộng giờ từ giáo viên:** lần đồng bộ kế tiếp nhận `deadline_at` mới → đồng hồ tự tăng; nếu client đang ở trạng thái `submitting` mà server trả `in_progress` với hạn mới thì **quay lại `ready`** (trường hợp lời gọi nộp chưa tới nơi).
- **Bắt lỗi:** nếu chưa có mẫu đồng bộ nào (mạng chết ngay khi nạp) dùng `deadline_at` + `server_now` từ lần nạp gần nhất lưu trong `sessionStorage` kèm `performance`-anchor mới; hiển thị dấu "≈" cạnh đồng hồ cho tới khi đồng bộ lại được.

**Test case kiểm thử và yêu cầu cần đạt** (Vitest với `vi.useFakeTimers` và mock `performance.now`/`Date.now`)

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-5.5-01 | Đồng hồ máy lệch | Đặt `Date.now()` nhanh 10 phút so với server | Thời gian còn lại vẫn tính đúng theo server (không phụ thuộc `Date.now()` ban đầu) |
| TC-5.5-02 | Học sinh chỉnh giờ hệ thống giữa bài | Giữa chừng dịch `Date.now()` +1 giờ, `performance.now()` đi bình thường | `needsResync()` = true → gọi đồng bộ; giá trị hiển thị không nhảy sai quá 1 giây |
| TC-5.5-03 | Tab ở nền bị làm chậm | Giả lập timer chỉ chạy mỗi 60 giây trong 10 phút | Khi tab hiện lại, thời gian còn lại giảm đúng 10 phút (không phải 10 tick) |
| TC-5.5-04 | Máy ngủ/thức | `performance.now()` đứng yên 30 phút, `Date.now()` +30 phút, kích hoạt `visibilitychange` | Đồng bộ lại; nếu đã quá hạn thì chuyển ngay sang `submitting` |
| TC-5.5-05 | Hết giờ | Đưa thời gian tới `deadline` | `submitOnce` được gọi **đúng 1 lần** dù timer vẽ lại nhiều lần; UI khóa nhập liệu |
| TC-5.5-06 | Cộng giờ | Server đổi `deadline_at` +5 phút ở lần đồng bộ sau | Đồng hồ tăng 5 phút; nếu đang `submitting` mà server còn `in_progress` thì quay về `ready` |
| TC-5.5-07 | RTT bất thường | Mẫu RTT 4 giây xen giữa các mẫu RTT 80 ms | Dùng mẫu RTT nhỏ nhất; sai số < 100 ms |
| TC-5.5-08 | Không có mạng khi nạp | Chặn mạng, dùng giá trị lưu trong `sessionStorage` | Đồng hồ chạy với dấu "≈"; khi có mạng lại thì đồng bộ chính xác và bỏ dấu "≈" |
| TC-5.5-09 | Trợ năng | Chạy qua các mốc 5:00, 1:00 | `aria-live` phát đúng 2 thông báo trong cả lượt chạy (không phát mỗi giây) |

---

## Bước 5.6 — Tự lưu chịu mất mạng: hàng đợi (outbox) bền vững, thử lại, nhiều tab

**Yêu cầu cần đạt**
- Mọi thay đổi đáp án đều đến được server **tối đa một lần ghi hiệu lực cho mỗi `client_seq`**, kể cả khi rớt mạng, F5, đóng/mở lại trình duyệt.
- Học sinh luôn thấy rõ trạng thái lưu: **Đã lưu / Đang lưu… / Chưa gửi được**.
- Hai tab cùng một bài không làm hỏng dữ liệu.

**Cách thức triển khai**
- **Cấu trúc:**
  - `AnswerStore`: trạng thái đáp án hiển thị (nguồn cho giao diện).
  - `AnswerOutbox` (bền vững): các thay đổi **chưa được server xác nhận**, khóa theo câu (gộp: chỉ giữ bản mới nhất cho mỗi câu), lưu ở `localStorage` khóa `quiz:v1:attempt:{id}:outbox` và bộ đếm `…:seq`. Mọi đọc/ghi bọc `try/catch`; nếu `QuotaExceededError`/bị chặn thì giữ trong bộ nhớ và hiện cảnh báo "Không lưu tạm được trên máy này".
- **Khi học sinh đổi đáp án:** `seq = ++seqByQuestion[qid]` (đã lưu bền) → ghi vào outbox → đặt lịch `flush` sau **800 ms** (debounce; chọn đáp án MCQ/TF gửi ngay sau 100 ms vì là thao tác rời rạc; ô gõ chữ/số chờ debounce và gửi ngay khi `blur`/`compositionend`).
- **Khởi tạo `seq`:** `max(server_seq của câu (từ 5.3), seq lưu cục bộ)`. Nhờ vậy dù `localStorage` bị xóa, `seq` mới vẫn lớn hơn `seq` đã có ở server.
- **Vòng `flush` (một vòng chạy tại một thời điểm, đồng thời tối đa 2 yêu cầu):**
  1. Lấy các mục trong outbox; gửi `PUT …/answers/{qid}` `{value, client_seq}` có `timeout 10s`.
  2. Phân loại kết quả:

| Kết quả | Hành động |
|---|---|
| 200 (`accepted` hoặc `stale`) | Nếu `server_seq ≥ seq` của mục → **xóa khỏi outbox**; nếu người dùng đã gõ tiếp (seq cao hơn) → giữ mục mới |
| `NetworkError` / timeout / 502 / 503 / 504 | Giữ nguyên, backoff `1s,2s,4s,8s,16s,30s` ±20% nhiễu; hiện "Chưa gửi được" (sau lần lỗi thứ 2) |
| 429 | Giữ nguyên, chờ `Retry-After` |
| 401 | **Tạm dừng**, hiện hộp thoại "Đăng nhập lại để tiếp tục" (không rời trang, không xóa outbox); sau đăng nhập → flush tiếp |
| 409 `attempt_closed` | Dừng hẳn, gọi `/status` xác nhận → chuyển sang màn "Đã nộp" |
| 404 | Dừng, báo lỗi nghiêm trọng "Không tìm thấy bài làm" |
| 422 | Đánh dấu lỗi **tại câu đó**, bỏ khỏi outbox (không thử lại vô hạn), người dùng sửa lại thì gửi lại |
| 500 khác | Thử lại tối đa 5 lần rồi chuyển sang nhịp chậm 30 giây (không bỏ) |

  3. Sự kiện `online`, `visibilitychange→visible` → flush ngay (bỏ qua thời gian chờ backoff).
- **Khi ẩn tab/đóng trang** (`visibilitychange→hidden`, `pagehide`): gửi các mục còn lại bằng `fetch(..., {keepalive: true})` (không dùng `sendBeacon` vì không đặt được header `Authorization`); không chờ kết quả, mục vẫn ở outbox cho tới khi được xác nhận lần sau.
- **Nạp lại trang:** sau khi nhận câu trả lời từ server (5.3), duyệt outbox: mục có `seq > server_seq` → giữ để gửi bù; mục `≤ server_seq` → bỏ. Giao diện hiển thị **đáp án từ outbox** nếu mới hơn server (học sinh thấy đúng cái mình đã chọn).
- **Nhiều tab cùng bài:** dùng **Web Locks API** `navigator.locks.request('quiz-attempt-'+id, {ifAvailable:true})`; tab không giành được khóa vào chế độ chỉ-đọc với dải thông báo "Bài này đang mở ở tab khác" + nút "Dùng tab này" (`{steal:true}`, tab cũ chuyển chỉ-đọc). Trình duyệt không hỗ trợ Web Locks → bỏ qua; `client_seq` vẫn bảo vệ dữ liệu ở server.
- **Chỉ báo lưu:** `saved` (outbox rỗng, không có yêu cầu bay) / `saving` (có debounce đang chờ hoặc yêu cầu đang bay) / `offline` (`navigator.onLine=false` hoặc lỗi mạng gần nhất) / `error`. Cảnh báo `beforeunload` **chỉ khi outbox khác rỗng**.
- **Bộ gõ tiếng Việt:** không đặt lịch flush giữa `compositionstart` và `compositionend`.

**Test case kiểm thử và yêu cầu cần đạt** (Vitest + MSW; Playwright cho các ca trình duyệt thật)

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-5.6-01 | Gõ nhanh nhiều ký tự | Gõ 20 ký tự trong 2 giây vào câu chữ | Chỉ 1–2 yêu cầu `PUT` (debounce); giá trị cuối đúng; `seq` tăng đơn điệu |
| TC-5.6-02 | Mất mạng rồi có lại | Ngắt mạng (`context.setOffline(true)`), trả lời 5 câu, bật lại | Chỉ báo `offline` → tự gửi cả 5 câu khi có mạng → `saved`; server có đủ 5 đáp án |
| TC-5.6-03 | F5 khi còn mục chưa gửi | Offline, trả lời 3 câu, tải lại trang, rồi bật mạng | Sau tải lại giao diện vẫn hiện 3 đáp án (từ outbox); sau đó được gửi lên server |
| TC-5.6-04 | `localStorage` bị xóa | Xóa dữ liệu trang rồi tiếp tục trả lời | `seq` mới = `server_seq + 1…` (không thấp hơn server) nên **không bị từ chối "stale"** oan |
| TC-5.6-05 | Thứ tự phản hồi đảo | MSW trả phản hồi của `seq=2` trước `seq=1` | Trạng thái cuối đúng `seq=2`, outbox rỗng, không ghi đè ngược |
| TC-5.6-06 | Lỗi 422 một câu | Server trả 422 cho câu 3 | Câu 3 hiện lỗi tại chỗ, không bị gửi lại vô hạn; các câu khác vẫn lưu bình thường |
| TC-5.6-07 | Hết phiên (401) | Server trả 401 giữa chừng | Hộp thoại đăng nhập lại; **outbox còn nguyên**; đăng nhập xong thì tự gửi tiếp |
| TC-5.6-08 | Bài đã bị đóng | Server trả 409 `attempt_closed` | Dừng gửi, chuyển sang màn "Đã nộp"; không vòng lặp thử lại |
| TC-5.6-09 | Hai tab | Mở cùng bài ở 2 tab | Tab thứ hai chỉ-đọc với nút "Dùng tab này"; sau khi bấm, tab đầu chỉ-đọc; không có ghi chéo |
| TC-5.6-10 | `localStorage` đầy/bị chặn | Giả lập `setItem` ném lỗi | Vẫn lưu lên server bình thường (bộ nhớ); hiện cảnh báo; mất tab khi offline thì chấp nhận mất mục chưa gửi |
| TC-5.6-11 | Ẩn tab/đóng trang | Gõ rồi đóng tab ngay | `fetch keepalive` được phát; mở lại bài thấy đáp án (từ server hoặc outbox) |
| TC-5.6-12 | Bộ gõ tiếng Việt | Gõ "Hà Nội" bằng Telex | Không có yêu cầu gửi giữa lúc đang soạn dấu; giá trị gửi là chuỗi đã hoàn chỉnh |
| TC-5.6-13 | Giới hạn tần suất 429 | Server trả 429 + `Retry-After: 3` | Không mất mục nào; gửi lại sau ≥ 3 giây |

---

## Bước 5.7 — Nộp bài và `finalize_attempt` (idempotent, chấm trong cùng giao dịch)

**Yêu cầu cần đạt**
- Nộp bài (thủ công, hết giờ, giáo viên đóng/nộp hộ) cùng đi qua **một hàm** `finalize_attempt`; gọi bao nhiêu lần, từ bao nhiêu nơi, kết quả vẫn một lần nộp và một lần chấm.
- `submitted_at = min(now, deadline_at)`.
- Phản hồi cho học sinh **không chứa điểm/đáp án**.

**Cách thức triển khai**
- **Endpoint:** `POST /student/attempts/{id}/submit` body tùy chọn `{"answers":[{question_id, value, client_seq}, …]}` = ảnh chụp outbox hiện có của client. Nhờ đó nếu mạng chập chờn, **một lời gọi duy nhất** vừa ghi nốt đáp án còn sót vừa nộp.
- **Thuật toán:**
```python
def finalize_attempt(db, attempt_id, reason, now, snapshot=None):
    a = db.execute(select(Attempt).where(Attempt.id == attempt_id).with_for_update()).scalar_one()   # FOR UPDATE
    if a.status == "submitted":
        return FinalizeResult(a, already=True)               # idempotent: không chấm lại
    if snapshot and reason == "manual" and is_writable(now, a.deadline_at, grace(a)):
        for item in snapshot: upsert_answer_guarded(db, a, item, now)       # cùng điều kiện client_seq như 5.4
    submitted_at = min(now, a.deadline_at)
    a.status, a.submitted_at, a.submit_reason = "submitted", submitted_at, reason
    ensure_answer_rows(db, a)                                # tạo hàng trống cho câu chưa trả lời
    results = grade_attempt(db, a)                           # 6.1: hàm thuần cho từng câu, bọc try/except theo câu
    persist_grades(db, a, results)                           # cập nhật answers + score_auto, grading_status
    return FinalizeResult(a, already=False)
```
  - `reason ∈ {manual, timeout, teacher_closed, teacher_forced}`. Nếu học sinh bấm nộp **sau** `deadline + grace` thì lớp ngoài chuyển thành `timeout` và **bỏ qua `snapshot`** (đáp án sau hạn không được nhận).
  - **Lỗi chấm một câu không được chặn việc nộp:** `grade_attempt` bắt ngoại lệ **theo từng câu**, để `score = NULL` (quy ước: NULL = chờ chấm tay) + `needs_review=true`, ghi log; attempt vẫn `submitted`, `grading_status='needs_manual'`.
  - **`ensure_answer_rows`:** tạo hàng `answers` (giá trị rỗng, điểm 0) cho câu chưa trả lời để các truy vấn chấm/giám sát/xuất CSV luôn đủ hàng.
- **Khóa:** `FOR UPDATE` trên attempt ⇒ (a) chờ các lần lưu đáp án đang dở (khóa `FOR SHARE` ở 5.4) commit xong rồi mới đọc đáp án để chấm; (b) hai lời gọi finalize đồng thời tuần tự hóa — kẻ đến sau thấy `submitted` và trả lại kết quả cũ.
- **Phản hồi cho học sinh:** `{"status":"submitted","submitted_at":"…Z","reason":"manual"}` — không điểm, không đáp án.
- **Phía client:** nút Nộp → `ConfirmDialog` (nêu số câu chưa làm) → trạng thái `submitting`: khóa nhập liệu, chờ flush tối đa 5 giây, gửi `submit` kèm `snapshot`; lỗi mạng → thử lại với backoff (an toàn vì idempotent); `200`/`409` đều dẫn tới màn "Đã nộp".

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-5.7-01 | Nộp bình thường | Nộp lúc còn thời gian | `status=submitted`, `submitted_at=now`, `reason=manual`, điểm tự chấm có mặt trong DB |
| TC-5.7-02 | **Gọi song song** | 20 luồng gọi `submit` cùng lúc; đếm số lần `grade_attempt` thực sự chạy (spy) | Chạy **đúng 1 lần**; cả 20 phản hồi đều `submitted`; không lỗi 500 |
| TC-5.7-03 | Nộp lặp lại | Gọi `submit` lần 2 sau khi đã nộp | 200 như cũ; điểm và `submitted_at` **không đổi** |
| TC-5.7-04 | Hết giờ | `finalize(..., "timeout")` khi `now = deadline + 40s` | `submitted_at = deadline_at` (không phải `now`) |
| TC-5.7-05 | Nộp trong grace | Bấm nộp ở `deadline + 5s` (grace 10s) | Được nhận; `submitted_at = deadline`; `snapshot` được áp dụng |
| TC-5.7-06 | Nộp sau grace | Bấm nộp ở `deadline + 11s` | Chuyển thành `timeout`; `snapshot` **bị bỏ qua**; chỉ các đáp án đã lưu trước đó được chấm |
| TC-5.7-07 | Snapshot bù đáp án | Server chưa có câu 4; `snapshot` chứa câu 4 | Câu 4 có trong kết quả chấm; `client_seq` cũ hơn server thì bị bỏ qua, không đè |
| TC-5.7-08 | Lỗi chấm một câu | Một câu dữ liệu hỏng làm `grade` ném lỗi | Attempt vẫn `submitted`; câu đó `score=NULL` + `needs_review`; `grading_status='needs_manual'`; log có stack |
| TC-5.7-09 | Câu chưa trả lời | Chỉ trả lời 2/10 câu | Có đủ 10 hàng `answers`; 8 câu điểm 0; tổng điểm đúng |
| TC-5.7-10 | Không lộ điểm | Quét JSON phản hồi `submit` | Không có `score`, `total_score`, `is_correct`, đáp án |
| TC-5.7-11 | Đua giữa nộp tay và hết giờ | Một luồng `manual`, một luồng `timeout` cùng thời điểm | Duy nhất một lý do được ghi; không chấm hai lần; không deadlock |
| TC-5.7-12 | Nộp hộ bởi giáo viên | `force-submit` (6.4) | `reason=teacher_forced`; cùng đường đi finalize |

---

## Bước 5.8 — Tự động nộp khi hết giờ: nộp lười (lazy), tiến trình quét (sweeper), kích hoạt khi giáo viên xem

**Yêu cầu cần đạt**
- Mọi attempt quá hạn **cuối cùng đều được nộp** với `submitted_at = deadline_at`, dù server đã ngủ, đã khởi động lại hay học sinh không bao giờ quay lại.
- Không bao giờ chấm hai lần; một attempt lỗi không làm hỏng cả lượt quét.

**Cách thức triển khai**
- **Bốn lớp bảo đảm, cùng gọi `finalize_attempt`:**
  1. **Client** (5.5) tự gọi `submit` khi hết giờ.
  2. **Nộp lười:** mọi request chạm tới attempt (`GET`, `PUT answers`, `start`, `status`, tải file…) mà `now > deadline + grace` → sau khi nhả khóa, gọi finalize với `reason="timeout"` rồi trả `submitted`/`409`.
  3. **Sweeper (APScheduler):** job nền mỗi **30 giây**.
  4. **Khi giáo viên mở giám sát/kết quả/chấm/xuất CSV:** gọi `finalize_expired(exam_id)` **trước** khi đọc số liệu (nên dù server vừa thức dậy, số liệu vẫn đúng).
- **`finalize_expired`:**
```python
def finalize_expired(db_factory, clock, exam_id=None, limit=50) -> int:
    now = clock.now(); done = 0
    with db_factory() as s:
        ids = s.scalars(text("""
            SELECT a.id FROM attempts a JOIN exams e ON e.id = a.exam_id
            WHERE a.status = 'in_progress'
              AND (a.deadline_at + make_interval(secs => e.grace_seconds) < :now
                   OR e.status IN ('closed','archived'))
              AND (:exam_id IS NULL OR a.exam_id = :exam_id)
            ORDER BY a.deadline_at LIMIT :n"""), {"now": now, "exam_id": exam_id, "n": limit}).all()
    for aid in ids:                                           # mỗi attempt MỘT transaction riêng
        try:
            with db_factory() as s, s.begin():
                reason = "teacher_closed" if is_exam_closed_early(s, aid, now) else "timeout"
                finalize_attempt(s, aid, reason, now); done += 1
        except Exception:
            log.exception("finalize_failed", attempt_id=str(aid))   # lỗi 1 attempt không dừng cả lượt
    return done
```
  `finalize_attempt` đã idempotent và có `FOR UPDATE`, nên hai sweeper (hoặc sweeper + request) chạy trùng vẫn an toàn; khóa tư vấn `pg_try_advisory_xact_lock(7301)` ở đầu lượt chỉ để **giảm làm việc trùng** (dùng loại *transaction-level* vì Neon pooler không giữ khóa mức phiên).
- **Lập lịch:** `BackgroundScheduler(timezone="UTC")`, job `interval=30s`, `max_instances=1`, `coalesce=True`, `misfire_grace_time=60`; bọc `try/except` để job không tự chết. **Chạy đúng 1 tiến trình** (`uvicorn --workers 1`). Khi khởi động (`lifespan`) chạy một lượt quét ngay để **bắt kịp** sau khi server ngủ/khởi động lại; nếu DB chưa sẵn sàng thì thử lại ở lượt sau.
- **Giáo viên đóng đề (4.2):** gọi `finalize_expired(exam_id)` lặp tới khi hết (giới hạn thời gian 20 giây/lượt); phần còn lại để sweeper hoàn tất (vì điều kiện `e.status IN ('closed','archived')` luôn coi attempt là "đến hạn").
- **Không đánh thức DB vô ích (tiết kiệm CU-giờ của Neon):** sweeper giữ trong bộ nhớ một giá trị `next_due` = `min(deadline_at + grace)` của các attempt đang chạy. Giá trị này được nạp bởi lượt quét lúc khởi động và được cập nhật (hạ xuống nếu nhỏ hơn) mỗi khi `start_attempt`, `extend`, `reopen` commit thành công. Mỗi nhịp 30 giây, nếu `now < next_due` (hoặc không có attempt nào đang chạy) thì **bỏ qua, không truy vấn DB**; khi tới hạn mới chạy `finalize_expired` rồi tính lại `next_due` từ DB. Hệ quả: lúc không có kỳ thi, compute Neon được tạm dừng sau 5 phút rảnh.
- **Giám sát:** log `sweeper_run{finalized, duration_ms}`; cảnh báo nếu một attempt tồn tại `in_progress` quá `deadline + 5 phút` (nghĩa là sweeper không chạy).
- **Lưu ý gói miễn phí:** khi server ngủ thì sweeper cũng ngủ — đây là lý do cần nộp lười, nộp-khi-giáo-viên-xem, quét-khi-khởi-động và ping giữ thức (8.5). **Thời hạn đúng nhờ `deadline_at` trong DB**, không phụ thuộc server có đang chạy.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-5.8-01 | Sweeper cơ bản | 3 attempt quá hạn, 2 còn hạn; chạy `finalize_expired` | Đúng 3 attempt `submitted` (`reason=timeout`, `submitted_at=deadline_at`); 2 còn lại không đổi |
| TC-5.8-02 | Server "ngủ" | Không chạy sweeper; gọi `GET attempt` sau hạn 1 giờ | Nộp lười: trả `submitted`, `submitted_at=deadline_at` (không phải lúc gọi) |
| TC-5.8-03 | Giáo viên mở giám sát | Có attempt quá hạn chưa ai chạm; gọi `GET /admin/exams/{id}/attempts` | Danh sách trả về đã hiển thị `submitted`; số liệu đúng ngay lần gọi đầu |
| TC-5.8-04 | Hai sweeper song song | Chạy 2 luồng `finalize_expired` trên cùng 100 attempt | Mỗi attempt chỉ chấm 1 lần (spy); tổng không lỗi |
| TC-5.8-05 | Một attempt hỏng | Chèn dữ liệu làm `finalize` của 1 attempt ném lỗi | 99 attempt còn lại vẫn được nộp; có log `finalize_failed` cho 1 attempt |
| TC-5.8-06 | Bắt kịp khi khởi động | Dừng server, tạo attempt quá hạn, khởi động | Lượt quét lúc khởi động nộp hết trong ≤ vài giây |
| TC-5.8-07 | Đề bị đóng | Giáo viên đóng đề khi 20 học sinh đang làm | Cả 20 `submitted` (`teacher_closed`) ngay hoặc sau ≤ 1 chu kỳ sweeper; học sinh thấy màn "Đã nộp" ở lần đồng bộ kế |
| TC-5.8-08 | Không nộp nhầm | Attempt `deadline` còn 1 giây | **Không** bị sweeper nộp; chỉ nộp khi `now > deadline + grace` |
| TC-5.8-09 | Lập lịch | Job chạy chậm 70 giây | `max_instances=1` + `coalesce` ⇒ không chồng lượt; không tích lũy lượt bù |
| TC-5.8-10 | Không đánh thức DB khi rảnh | Không có attempt đang chạy; chạy sweeper 20 nhịp liên tiếp, đếm câu lệnh gửi tới DB | 0 câu lệnh trong các nhịp rảnh; sau khi có attempt mới `start` thì `next_due` được hạ xuống đúng và nhịp tới hạn mới truy vấn |
| TC-5.8-11 | `next_due` sau cộng giờ/mở lại | `extend` làm lùi hạn; `reopen` bài đã nộp | `next_due` được cập nhật; không nộp sớm hơn hạn mới; bài mở lại vẫn được nộp đúng hạn |

---

## Bước 5.9 — Nộp tệp của học sinh (câu `file_upload`)

**Yêu cầu cần đạt**
- Học sinh tải/xóa/thay tệp **cho đến khi nộp**; tệp được lưu ngay (coi như tự lưu).
- Chặn đúng: quá số tệp, quá dung lượng, sai loại, tệp giả mạo, tải sau hạn.
- Tệp riêng tư; chỉ giáo viên xem được qua URL ký ngắn hạn.

**Cách thức triển khai**
- **Endpoint:** `POST /student/attempts/{id}/questions/{qid}/files` (multipart, trường `file`); `DELETE /student/attempts/{id}/files/{file_id}`.
- **Luồng tải lên (S3 ngoài giao dịch):**
  1. **Kiểm tra sơ bộ (DB, nhanh):** attempt thuộc học sinh, `in_progress`, `is_writable`; câu hỏi thuộc đề và là `file_upload`; số tệp hiện có `< max_files` → nếu không `409 file_limit`.
  2. **Đọc luồng theo khối 64 KB**, dừng ngay khi vượt `max_mb` (→ `413`); kiểm tra đuôi trong `allowed_ext` **và** chữ ký thật (PDF bắt đầu `%PDF-`; JPG/PNG bằng Pillow `verify()`); ảnh được **mã hóa lại** (bỏ EXIF, cạnh dài ≤ 2400 px, JPEG/WEBP ~85) để nhẹ hơn và sạch metadata.
  3. **Ghi lên R2:** khóa ngẫu nhiên `submissions/{exam_id}/{attempt_id}/{uuid}`, `ContentType` do server đặt.
  4. **Giao dịch DB:** `pg_advisory_xact_lock(hashtext(attempt_id||qid))` (tuần tự hóa các lần tải cùng câu) → đếm lại số tệp (kiểm tra lần hai) → chèn `files(kind='submission')` + cập nhật `answers.value = {"file_ids":[…]}` (server là nguồn sự thật cho dạng câu này; các yêu cầu `PUT answers` không được sửa dạng này). Nếu vượt giới hạn do đua → xóa đối tượng R2 vừa ghi, trả `409`.
  5. **Bù trừ:** lỗi ở bước 4 → xóa đối tượng R2; lỗi sau khi ghi R2 mà trước commit → cùng xử lý. Công việc dọn hằng đêm xóa các khóa R2 không có hàng `files` và cũ hơn 1 giờ.
- **Xóa tệp:** chỉ khi `in_progress` và còn hạn; xóa hàng DB (và cập nhật `answers.value`) trong transaction, **sau commit** mới xóa đối tượng R2 (lỗi xóa R2 chỉ để lại rác sẽ được dọn).
- **Tên tệp hiển thị:** `original_name` làm sạch (bỏ đường dẫn, ký tự điều khiển, cắt 100 ký tự); chỉ dùng để hiển thị, không bao giờ để xác định khóa lưu hay đường dẫn.
- **Tải về cho giáo viên (6.2):** URL ký TTL 5 phút với `ResponseContentDisposition: attachment` để trình duyệt không "thực thi/hiển thị" nội dung do học sinh nộp như một trang web.
- **Phía client:** `FileDropzone` dùng `XMLHttpRequest` để có **thanh tiến trình** và hủy; ảnh ≥ 2 MB nén phía client trước khi tải; **cần có mạng** (không đưa tệp vào outbox vì dung lượng lớn): ngoại tuyến → thông báo rõ "Cần có kết nối để tải tệp, bài làm chữ/số vẫn được lưu tạm"; sau mỗi thao tác tải/xóa **đọc lại danh sách tệp từ server** để hiển thị.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-5.9-01 | Tải hợp lệ | Ảnh 3 MB (`max_mb=10`) | 201; có hàng `files`, đối tượng R2, `answers.value.file_ids` cập nhật; xuất hiện trong danh sách |
| TC-5.9-02 | Vượt số tệp | `max_files=3`, tải tệp thứ 4 | `409 file_limit`; không có đối tượng R2 mồ côi |
| TC-5.9-03 | **Tải song song** | 5 yêu cầu cùng lúc khi còn chỗ cho 2 tệp | Đúng 2 thành công, 3 bị `409`; không vượt `max_files`; R2 không có tệp thừa |
| TC-5.9-04 | Quá dung lượng | 15 MB với `max_mb=10`; luồng không có `Content-Length` | `413` ngay khi vượt; không nạp cả tệp vào RAM |
| TC-5.9-05 | Sai loại / giả mạo | `.exe`; `.pdf` thực chất là ảnh; `.png` thực chất là script | `415 invalid_file`, không ghi gì |
| TC-5.9-06 | Sau hạn | Tải ở `deadline + grace + 1s` | `409 attempt_closed`; không tạo tệp |
| TC-5.9-07 | Sau khi nộp | Tải/xóa khi `submitted` | `409 attempt_closed` |
| TC-5.9-08 | Xóa & thay | Xóa tệp 1, tải tệp mới | Danh sách đúng; đối tượng R2 cũ bị xóa sau commit |
| TC-5.9-09 | Lỗi giữa chừng | Giả lập lỗi DB sau khi ghi R2 | Đối tượng R2 bị xóa bù; học sinh nhận lỗi rõ, có thể thử lại |
| TC-5.9-10 | Mất mạng giữa lúc tải | Ngắt mạng khi đang ở 60% | UI báo thất bại + nút "Thử lại"; không có tệp "nửa vời" trong danh sách |
| TC-5.9-11 | Quyền | Học sinh A tải vào attempt của B; xóa tệp của B | 404 |
| TC-5.9-12 | Tên tệp độc hại | `../../etc/passwd.png`, tên 300 ký tự, ký tự điều khiển | Tên hiển thị được làm sạch; khóa R2 là UUID ngẫu nhiên |

---

## Bước 5.10 — Lắp ráp giao diện làm bài (trải nghiệm học sinh hoàn chỉnh)

**Yêu cầu cần đạt**
- Học sinh làm trọn vẹn một bài trên điện thoại 360px: nhìn thấy đồng hồ và trạng thái lưu mọi lúc, chuyển câu dễ, nộp có xác nhận, nhận màn hình "Đã nộp" (không điểm).
- Máy trạng thái trang rõ ràng, không có trạng thái "treo".

**Cách thức triển khai**
- **Máy trạng thái trang (`useAttemptMachine`):** `loading → ready ⇄ readonly(other-tab) → submitting → submitted`; nhánh phụ `reauth` (401), `error`. Mỗi chuyển trạng thái có hành động xác định (khóa nhập liệu ở `submitting/submitted/readonly`).
- **Bố cục:** thanh trên cố định (tên đề, `Timer`, `SaveIndicator`); `QuestionNav` dạng lưới (trạng thái: chưa làm / đã làm / cần xem lại / đang xem) — mobile hiển thị dạng nút mở ngăn kéo; vùng câu hỏi hiển thị **từng câu** (tải nhanh, ít cuộn) hoặc tất cả câu cuộn dọc (cấu hình mặc định: từng câu); thanh dưới: Trước/Sau + nút Nộp bài.
- **Thành phần theo dạng câu:** `McqQuestion` (`role="radiogroup"`, nhãn A/B/C/D gán theo vị trí hiển thị), `TfQuestion` (bảng mệnh đề, mỗi hàng nhóm Đúng/Sai), `ShortTextQuestion`, `ShortNumberQuestion` (`type="text" inputmode="decimal" autocomplete="off" spellcheck="false"`; chấp nhận cả `,` và `.`, phân số `a/b`), `FileUploadQuestion` (5.9). Mọi nội dung hiển thị qua `MathText`.
- **Đánh dấu "cần xem lại":** chỉ lưu cục bộ (`localStorage`), **không gửi server** (không ảnh hưởng chấm điểm).
- **Hộp thoại nộp:** tóm tắt số câu đã làm/chưa làm/đánh dấu (tính từ `AnswerStore`); nút xác nhận → `submitting` (5.7).
- **Sự kiện rời tab:** `visibilitychange→hidden` → `POST /student/attempts/{id}/events {type:"blur"}` (debounce 2 giây, bỏ qua lỗi); server tăng `attempts.blur_count` nguyên tử (`UPDATE … SET blur_count = blur_count + 1 WHERE status='in_progress'`), giới hạn 1 lần/2 giây; chỉ để giáo viên tham khảo, **không phạt**.
- **Màn "Đã nộp":** hiển thị giờ nộp (giờ Việt Nam) và lý do nếu tự nộp ("Hết giờ, bài đã được tự động nộp"); nút "Về danh sách đề". **Không** hiển thị điểm; nếu mở `/result` khi chưa công bố → thông báo "Giáo viên chưa công bố kết quả".
- **Di động:** cỡ chạm ≥ 44px; chặn phóng/zoom ngoài ý muốn chỉ ở vùng điều khiển (không tắt zoom toàn trang để giữ trợ năng); không dùng `100vh` thuần (dùng `dvh`) để thanh địa chỉ trình duyệt không che nút Nộp.

**Test case kiểm thử và yêu cầu cần đạt** (Playwright, chạy trên Chromium + WebKit, viewport 360×640 và 1280×800)

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-5.10-01 | Luồng đầy đủ | Đăng nhập → chọn đề → bắt đầu → trả lời đủ 5 dạng câu → nộp | Màn "Đã nộp" không có điểm; DB có đủ đáp án và điểm tự chấm |
| TC-5.10-02 | Đóng tab giữa chừng | Trả lời 5 câu, đóng tab, mở lại sau 2 phút | Đáp án còn nguyên, đồng hồ đã giảm tương ứng, tiếp tục làm được |
| TC-5.10-03 | Mất mạng | Ngắt mạng, làm tiếp 3 câu, bật lại | Banner offline → tự đồng bộ → "Đã lưu"; server có đủ đáp án |
| TC-5.10-04 | Hết giờ khi đang gõ | Đặt đề 1 phút, gõ tới hết giờ | Tự nộp; câu đang gõ (đã gửi trước hạn) có trong bài; UI chuyển "Đã nộp (hết giờ)" |
| TC-5.10-05 | Giáo viên cộng giờ | Cộng 5 phút ở bước 6.4 khi học sinh còn 30 giây | Đồng hồ học sinh tăng ở lần đồng bộ kế (≤ 30 giây); không bị tự nộp |
| TC-5.10-06 | Xác nhận nộp | Còn 3 câu chưa làm, bấm Nộp | Hộp thoại nêu "3 câu chưa làm"; Hủy → quay lại làm tiếp, không nộp |
| TC-5.10-07 | Nộp bấm đúp | Bấm xác nhận nộp 2 lần | Một lời gọi hiệu lực; UI không lỗi |
| TC-5.10-08 | Bị giáo viên đóng đề | Giáo viên đóng đề khi đang làm | Lần đồng bộ kế: chuyển "Đã nộp"; hàng đợi chưa gửi không gây lỗi lặp |
| TC-5.10-09 | Thiết bị nhỏ | Chạy toàn luồng ở 360×640 với bàn phím ảo | Không cuộn ngang; nút Nộp luôn tiếp cận được; ô số hiện bàn phím số |
| TC-5.10-10 | Rời tab | Chuyển sang ứng dụng khác 3 lần | `blur_count = 3` (hiển thị ở giám sát); không ảnh hưởng điểm |
| TC-5.10-11 | Xem kết quả khi chưa công bố | Mở trực tiếp `/s/attempts/:id/result` | Thông báo chưa công bố; không có dữ liệu điểm trong phản hồi mạng |
| TC-5.10-12 | Hai thiết bị | Mở cùng bài ở điện thoại và laptop | Cùng đồng hồ/đáp án; ghi từ thiết bị nào cũng đúng nhờ `client_seq`; không tạo attempt thứ hai |

---

# GIAI ĐOẠN 6. CHẤM ĐIỂM, CÔNG BỐ, GIÁM SÁT, XUẤT DỮ LIỆU

> **Quy ước điểm (dùng xuyên suốt):** `answers.score = NULL` nghĩa là **đang chờ chấm tay**; `score = 0` là đã chấm và được 0 điểm. `attempts.total_score` luôn được **tính lại bằng SQL** (`COALESCE(SUM(answers.score),0)`) trong cùng transaction với mọi thay đổi điểm, không cộng dồn thủ công, để không bao giờ lệch. `grading_status = 'needs_manual'` khi còn ít nhất một câu `score IS NULL`, ngược lại `complete`.

## Bước 6.1 — Bộ máy chấm điểm (hàm thuần cho từng dạng câu)

**Yêu cầu cần đạt**
- Chấm đúng 4 dạng tự động (MCQ, TF, trả lời số, trả lời chữ) theo đặc tả 3.4; câu nộp tệp chuyển cho giáo viên.
- Hàm chấm **thuần** (không đụng DB, không đồng hồ), không bao giờ ném lỗi vì dữ liệu học sinh, kết quả luôn thuộc `[0, points]`.
- Chấm lại toàn đề (regrade) an toàn, không đè điểm giáo viên đã chấm tay.

**Cách thức triển khai**
- **Kiểu kết quả:** 
```python
@dataclass(frozen=True)
class Grade:
    score: Decimal | None        # None = chờ chấm tay
    is_correct: bool | None
    needs_review: bool = False
Q2 = Decimal("0.01")
def q2(x: Decimal) -> Decimal: return x.quantize(Q2, rounding=ROUND_HALF_UP)
```
- **MCQ:** `choice = (value or {}).get("choice")`; đúng khi `choice == key["correct"]` → điểm = `points`, ngược lại 0; không chọn → 0, `is_correct=False`.
- **TF:** `right = số mệnh đề mà value[sid] is key[sid]` (giá trị `None`/thiếu tính là sai); `n` = số mệnh đề.
  - `thpt` và `n == 4`: tỉ lệ `{0: 0, 1: 0.10, 2: 0.25, 3: 0.50, 4: 1.0}`; `thpt` mà `n ≠ 4` → coi như `proportional`.
  - `proportional`: `Decimal(right)/Decimal(n)`; `all_or_nothing`: 1 nếu `right == n` ngược lại 0.
  - Điểm = `q2(points × tỉ lệ)`; `is_correct = (right == n)`.
- **Số (`short_number`):**
```python
_NUM = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)(/[+-]?(\d+(\.\d*)?|\.\d+))?$")
def parse_number(raw: str) -> Decimal | None:
    s = unicodedata.normalize("NFKC", raw).strip().replace("−", "-").replace(" ", "").replace(",", ".")
    if len(s) > 40 or not _NUM.match(s): return None           # chặn chuỗi dài, "1e999999", "NaN", "Infinity"
    try:
        if "/" in s:
            a, b = s.split("/", 1); d = Decimal(b)
            return None if d == 0 else Decimal(a) / d
        return Decimal(s)
    except InvalidOperation: return None
def number_ok(x, target, tol, kind):                             # tol, target là Decimal
    return abs(x - target) <= (tol if kind == "abs" else abs(target) * tol)
```
  Đúng khi khớp **bất kỳ** giá trị trong `values`. **Lưu ý đã biết:** cả `,` và `.` đều được hiểu là dấu thập phân, nên "1.000" nghĩa là 1,000 chứ không phải một nghìn; trình soạn đề (4.4) cảnh báo khi đáp án ≥ 1000 để giáo viên viết rõ trong đề.
- **Chữ (`short_text`):**
```python
def norm_text(s: str, case_sensitive: bool, strip_accents: bool) -> str:
    s = re.sub(r"\s+", " ", unicodedata.normalize("NFC", s).strip())
    if strip_accents:
        s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
        s = unicodedata.normalize("NFC", s.replace("đ", "d").replace("Đ", "D"))   # 'đ' không phân rã bởi NFD
    return s if case_sensitive else s.casefold()
```
  `grading="manual"` → `Grade(None, None)`; `auto`: khớp một trong `accepted` (đã chuẩn hóa cùng quy tắc) → đúng; sai và `review_wrong=true` → `needs_review=True` (điểm vẫn 0, giáo viên có thể nâng lên).
- **Nộp tệp:** không có tệp → `Grade(Decimal(0), False)` (không có gì để chấm); có tệp → `Grade(None, None)`.
- **`grade_attempt`:** duyệt từng câu, mỗi câu bọc `try/except Exception` → `Grade(None, None, needs_review=True)` + log; không bao giờ làm hỏng cả bài.
- **Regrade (`POST /admin/exams/{id}/regrade?dry_run=`):** với mỗi attempt đã nộp (mỗi attempt một transaction, khóa `FOR UPDATE`), chỉ chấm lại các `answers` có `graded_by IS NULL`; **không đụng** câu giáo viên đã chấm/ghi đè; `dry_run=true` trả số bài/số câu sẽ đổi điểm để giáo viên xem trước. Ghi `audit_log`.
- **Cấm khóa đáp án khớp học sinh qua log:** log chấm chỉ ghi `question_id`, `type`, `score`, không ghi giá trị đáp án.

**Test case kiểm thử và yêu cầu cần đạt** (bảng dữ liệu `pytest.mark.parametrize` + `hypothesis`)

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-6.1-01 | MCQ | Đúng / sai / bỏ trống / `choice` không tồn tại | `points` / 0 / 0 / 0; không lỗi |
| TC-6.1-02 | TF `thpt` | 4 mệnh đề, đúng 0,1,2,3,4 ý; điểm câu 1,00 | 0 / 0,10 / 0,25 / 0,50 / 1,00 |
| TC-6.1-03 | TF khác chế độ | 3 mệnh đề + `thpt`; `proportional` đúng 2/3; `all_or_nothing` đúng 3/4 | Lần lượt: tỉ lệ theo `proportional`; `points×0,67` (làm tròn); 0 |
| TC-6.1-04 | TF thiếu mệnh đề | `value` chỉ trả lời 2/4 ý | Ý không trả lời tính sai; không ném lỗi |
| TC-6.1-05 | Số: định dạng | Đáp án `0.5`: `0,5`, `.5`, `0.50`, `1/2`, ` 0 , 5 `, `０．５` (toàn góc), `−0.5` | Các giá trị bằng 0,5 là đúng; `−0.5` sai; không giá trị nào gây lỗi |
| TC-6.1-06 | Số: sai số | `values=["3.14"]`, `abs 0.01`: `3.15`, `3.151`; `rel 1%`: `3.17`, `3.2` | `3.15` đúng, `3.151` sai; `3.17` đúng, `3.2` sai |
| TC-6.1-07 | Số: đầu vào độc hại | `1e999999`, `NaN`, `Infinity`, `1/0`, chuỗi 10.000 ký tự, `--5`, rỗng | `parse_number` trả `None` cho tất cả; thời gian < 5 ms; không ném lỗi |
| TC-6.1-08 | Số: chia | Đáp án `1/3`; trả lời `0.3333333333333333333333333333` và `1/3` | Khớp với `tolerance=0` cho `1/3`; `0.33` không khớp |
| TC-6.1-09 | Chữ: tiếng Việt | Đáp án `Đa thức`; trả lời `đa thức`, `DA THUC`, `  đa   thức `, `da thuc` | Khớp tùy theo `case_sensitive` và `strip_accents` (kiểm đủ 4 tổ hợp), đặc biệt `đ→d` |
| TC-6.1-10 | Chữ: Unicode | `ắ` ở dạng tổ hợp (NFD) vs dựng sẵn (NFC) | Hai dạng được coi là bằng nhau |
| TC-6.1-11 | Chữ: thủ công & "cần xem lại" | `grading=manual`; `auto + review_wrong` trả lời sai | `score=None`; `score=0, needs_review=True` |
| TC-6.1-12 | Nộp tệp | Không tệp / có tệp | `score=0` / `score=None` (chờ chấm) |
| TC-6.1-13 | Bất biến (property) | `hypothesis` sinh câu hỏi + đáp án ngẫu nhiên | `0 ≤ score ≤ points`; điểm có đúng ≤ 2 chữ số thập phân; chạy 2 lần cùng đầu vào cho cùng kết quả |
| TC-6.1-14 | Regrade bảo toàn chấm tay | Câu đã chấm tay 0,75; sửa khóa đáp án; regrade | Điểm 0,75 giữ nguyên; các câu tự động đổi theo khóa mới; `dry_run` không ghi gì |

---

## Bước 6.2 — Chấm tay và giao diện chấm bài

**Yêu cầu cần đạt**
- Giáo viên chấm nhanh bằng bàn phím, theo học sinh hoặc theo từng câu cho cả lớp; xem được tệp học sinh nộp.
- Sửa điểm an toàn khi hai người cùng thao tác; mọi thay đổi có vết.

**Cách thức triển khai**
- **API:**
  - `GET /admin/exams/{id}/grading?mode=student|question&filter=pending|all&cursor=…` (trả mục kế tiếp theo con trỏ, kèm tiến độ `đã chấm/tổng`); gọi `finalize_expired(exam_id)` trước.
  - `GET /admin/attempts/{id}` (bài làm đầy đủ: câu hỏi + **khóa đáp án** + đáp án học sinh + điểm; URL ký 5 phút cho từng tệp nộp).
  - `PUT /admin/answers/{id}/grade` body `{score, comment?, version}`.
- **Xử lý `grade`:** (1) khóa `attempts … FOR UPDATE` (tuần tự hóa với regrade/finalize); (2) attempt phải `submitted`; (3) `0 ≤ score ≤ points`, tối đa 2 chữ số thập phân (`422` nếu không); (4) kiểm tra `version` (khóa lạc quan); (5) ghi `score`, `teacher_comment`, `graded_by`, `graded_at`, `is_correct = (score == points)`, `version+1`; (6) tính lại `total_score` và `grading_status` bằng SQL; (7) ghi `audit_log` (điểm cũ → mới). Sửa điểm câu **tự động** cũng được và từ đó được bảo vệ khỏi regrade (`graded_by` khác NULL).
- **Hiển thị bài làm của học sinh:** nội dung do học sinh gõ (chữ/số) hiển thị dạng **văn bản thuần đã escape** (không qua Markdown/HTML) để học sinh không thể chèn mã vào trang giáo viên.
- **Giao diện:** hai chế độ (theo học sinh / theo câu); phím tắt `←/→` (người trước/sau), `Enter` (lưu & sang bài kế), nút điểm nhanh `0`, `½`, `Tối đa`, ô điểm số tự do; lọc "chưa chấm"; thanh tiến độ; hiển thị tệp (ảnh phóng to/xoay, PDF mở tab mới); lưu khi rời ô (blur) với chỉ báo trạng thái; xung đột `409` → tải lại bản mới và hiện điểm của người kia.
- **Tối ưu:** tải trước (prefetch) bài kế tiếp; phân trang theo con trỏ; ảnh nộp tải lười.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-6.2-01 | Chấm một câu | Nhập 0,5 cho câu `file_upload` (điểm 1) | `score=0.50`, `graded_by` = admin; `total_score` tăng 0,5; nếu là câu cuối thì `grading_status='complete'` |
| TC-6.2-02 | Điểm không hợp lệ | `-1`, `1.01` (vượt điểm câu), `0.555`, `abc` | Tất cả `422`; DB không đổi |
| TC-6.2-03 | Đồng thời | Hai admin chấm cùng câu với `version` giống nhau | Một thành công; một `409 version_conflict`; tổng điểm đúng |
| TC-6.2-04 | Chấm khi chưa nộp | Gọi `grade` cho attempt `in_progress` | `409` |
| TC-6.2-05 | Ghi đè điểm tự động | Sửa điểm một câu MCQ từ 0 lên 1 | Lưu được; regrade (6.1) không đổi lại; có dòng `audit_log` (0 → 1) |
| TC-6.2-06 | An toàn hiển thị | Học sinh gõ `<img src=x onerror=alert(1)>` và `**in đậm**` | Trang chấm hiển thị đúng chuỗi ký tự thô; không có script chạy, không render Markdown |
| TC-6.2-07 | Tệp nộp | Mở ảnh 3 MB và PDF | Ảnh xem được, PDF tải/mở; URL hết hạn sau 5 phút; học sinh không truy cập được URL của người khác |
| TC-6.2-08 | Phím tắt & tiến độ | Chấm 10 bài liên tiếp chỉ bằng bàn phím | Tiến độ cập nhật; mỗi bài có đúng 1 lần lưu; không chấm nhầm bài |
| TC-6.2-09 | Quyền | Student gọi các endpoint `/admin/…` chấm | 403 |

---

## Bước 6.3 — Công bố kết quả cho học sinh (có kiểm soát)

**Yêu cầu cần đạt**
- Mặc định học sinh **không thấy** điểm/đáp án. Giáo viên công bố cho cả lớp hoặc từng học sinh, mức `score_only` hoặc `full`, và **thu hồi** được.
- Việc ẩn/hiện được thực thi ở **backend**, không chỉ ở giao diện.

**Cách thức triển khai**
- **API giáo viên:** `POST /admin/exams/{id}/release` body `{scope: "all" | {student_ids:[…]}, visibility: "score_only" | "full"}`; `POST …/unrelease` (cùng `scope`). Chỉ tác động attempt **đã nộp** (bài `in_progress` chưa nộp không bị ảnh hưởng; phản hồi nêu "đã công bố N bài, còn M bài chưa nộp"). Nếu còn câu `score IS NULL` thì **cảnh báo** (cho phép công bố có chủ đích: câu chưa chấm hiện "chờ chấm").
- **API học sinh `GET /student/attempts/{id}/result`:** thứ tự kiểm tra: sở hữu (không phải → 404) → `released` (chưa → `403 result_not_released`) → dựng phản hồi bằng **allow-list**:
  - `score_only`: `{total_score, max_score, scaled_10?}`.
  - `full`: thêm từng câu: nội dung, đáp án của học sinh, **đáp án đúng**, điểm câu, nhận xét giáo viên, `explanation_md`.
  - Luôn kèm `Cache-Control: no-store`.
- **Thang 10:** nếu đề bật `scale_to_10`, thêm `scaled_10 = round(total/max×10, 2)` (cột bổ sung trong migration).
- **Danh sách đề của học sinh (5.1):** `state=result_available` chỉ khi `released=true`.
- **Nhật ký:** mỗi lần công bố/thu hồi ghi `audit_log` (ai, khi nào, phạm vi, mức).
- **Giao diện giáo viên:** trên trang "Kết quả đề": bảng điểm, bộ lọc, nút "Công bố…" mở hộp thoại chọn phạm vi + mức + xác nhận số học sinh bị tác động; cột trạng thái công bố từng học sinh.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-6.3-01 | Mặc định ẩn | Học sinh gọi `result` khi chưa công bố | `403 result_not_released`; thân phản hồi không có số điểm; trang kết quả hiện thông báo chờ |
| TC-6.3-02 | `score_only` | Công bố mức `score_only` | Phản hồi chỉ có `total_score/max_score`; **không** có đáp án đúng, câu hỏi, lời giải |
| TC-6.3-03 | `full` | Công bố `full` | Có đáp án đúng, điểm từng câu, lời giải; vẫn không có dữ liệu của học sinh khác |
| TC-6.3-04 | Phạm vi một học sinh | Công bố cho A, không cho B | A thấy, B vẫn 403 |
| TC-6.3-05 | Thu hồi | Công bố rồi `unrelease` | Lần gọi kế tiếp trả 403; trang danh sách quay lại `submitted` |
| TC-6.3-06 | Bài chưa nộp | Công bố "cả lớp" khi 3 học sinh còn đang làm | 3 bài đó không bị công bố; phản hồi nêu đúng số lượng; khi họ nộp xong vẫn **không** tự công bố |
| TC-6.3-07 | Câu chưa chấm | Công bố khi còn 1 câu `score IS NULL` | Có cảnh báo trước khi xác nhận; câu đó hiển thị "chờ chấm", tổng điểm tính phần đã chấm |
| TC-6.3-08 | Bộ nhớ đệm | Công bố rồi thu hồi, bấm "Quay lại" trên trình duyệt | Không hiển thị kết quả cũ từ bộ nhớ đệm (`no-store`) |
| TC-6.3-09 | Rò rỉ | Quét mọi phản hồi `/student/*` trước khi công bố | Không có số điểm/đáp án đúng ở **bất kỳ** endpoint nào |

---

## Bước 6.4 — Giám sát trực tiếp và can thiệp của giáo viên

**Yêu cầu cần đạt**
- Giáo viên thấy theo thời gian gần thực (≤ 10 giây) mỗi học sinh: Chưa vào / Đang làm / Đã nộp, thời gian còn lại, số câu đã trả lời, lần lưu cuối, số lần rời tab.
- Can thiệp được: **cộng giờ, mở lại bài, nộp hộ, thu hồi phiên, "làm nóng hệ thống"** — tất cả idempotent hoặc có xác nhận, đều ghi vết.

**Cách thức triển khai**
- **Danh sách giám sát `GET /admin/exams/{id}/attempts`:** (1) `finalize_expired(exam_id)`; (2) lấy **toàn bộ học sinh của các lớp được giao** (`LEFT JOIN attempts`) nên học sinh chưa vào cũng hiện; (3) `answered_count` tính trong Python từ **một** truy vấn `(attempt_id, question_id, value)` bằng hàm `is_answered(type, value)` (không đếm SQL phức tạp); (4) `remaining_seconds` từ `Clock`; (5) hỗ trợ `ETag` → trả `304` khi không đổi.
- **Cộng giờ `POST /admin/attempts/{id}/extend {seconds}`:** `seconds ∈ [30, 7200]`; khóa attempt; chỉ khi `in_progress`: `deadline_at += seconds`, `extra_seconds += seconds` (**cố ý không bị chặn bởi `close_at`**, vì đây là ghi đè của giáo viên; ghi vết); đã nộp → `409` và gợi ý "Mở lại bài".
- **Mở lại `POST /admin/attempts/{id}/reopen {seconds=300}`:** chỉ khi `submitted`; đặt `status='in_progress'`, `submitted_at=NULL`, `submit_reason=NULL`, `deadline_at = now + seconds`, `released=false`; **giữ nguyên đáp án**; điểm cũ không còn hợp lệ nên khi học sinh sửa một câu thì upsert ở 5.4 tự đặt `score/is_correct/graded_*` về NULL (đã bổ sung), và lần `finalize` kế tiếp chấm lại toàn bộ.
- **Nộp hộ `POST …/force-submit`:** gọi `finalize_attempt(…, "teacher_forced")`.
- **Thu hồi phiên `POST /admin/students/{id}/revoke-sessions`:** xóa `sessions` của học sinh.
- **Làm nóng `POST /admin/system/warmup`:** chạy `SELECT 1`, một truy vấn nhỏ có JOIN thật, gọi `HEAD` R2, trả thời gian từng thành phần (ms) để giáo viên biết hệ thống đã sẵn sàng.
- **Giao diện:** bảng cập nhật bằng polling 10 giây (`refetchInterval`) **chỉ khi tab đang hiện** (`document.visibilityState`); tô nổi học sinh `in_progress` mà "lần lưu cuối" > 3 phút (nghi mất kết nối) hoặc còn < 5 phút; menu hành động có `ConfirmDialog` nêu hậu quả; tóm tắt phía trên (X chưa vào / Y đang làm / Z đã nộp).

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-6.4-01 | Danh sách đầy đủ | Lớp 30 học sinh, 10 đã vào, 5 đã nộp | 30 dòng; trạng thái và đếm đúng; học sinh chưa vào hiện "Chưa vào" |
| TC-6.4-02 | Cộng giờ | Cộng 300 giây cho một học sinh đang làm | Chỉ attempt đó tăng `deadline_at` đúng 300 giây; người khác không đổi; học sinh thấy thêm giờ ở lần đồng bộ kế |
| TC-6.4-03 | Cộng giờ vượt `close_at` | `close_at` sắp tới, cộng 10 phút | Được phép, ghi vết "ghi đè"; học sinh làm tới hạn mới |
| TC-6.4-04 | Cộng giờ sai trạng thái/giá trị | Attempt đã nộp; `seconds=0`, `-5`, `99999` | `409`; `422`; `422`; không thay đổi |
| TC-6.4-05 | Mở lại bài | Mở lại bài đã nộp, học sinh sửa 1 câu rồi nộp lại | Đáp án cũ còn; điểm cũ được chấm lại từ đầu; `released=false` |
| TC-6.4-06 | Nộp hộ lặp | `force-submit` hai lần | Lần 2 trả kết quả như cũ (idempotent); chỉ một lần chấm |
| TC-6.4-07 | Thu hồi phiên | Thu hồi phiên của học sinh A | Request kế tiếp của A là 401; A đăng nhập lại và **vẫn tiếp tục đúng bài** (đáp án còn, đồng hồ không đổi) |
| TC-6.4-08 | Polling hiệu quả | Mở trang, để tab ở nền 2 phút | Không có yêu cầu polling khi tab ẩn; khi hiện lại thì cập nhật ngay; phản hồi `304` khi không đổi |
| TC-6.4-09 | Làm nóng | Bấm nút khi server vừa thức | Trả thời gian từng thành phần; lần bấm thứ hai nhanh hơn rõ rệt |
| TC-6.4-10 | Phát hiện nghi mất kết nối | Học sinh `in_progress` không lưu 4 phút | Dòng được tô nổi với nhãn "Lần lưu cuối 4 phút trước" |
| TC-6.4-11 | Ghi vết | Thực hiện cộng giờ, mở lại, nộp hộ | Mỗi thao tác có 1 dòng `audit_log` (ai/khi nào/giá trị) |

---

## Bước 6.5 — Xuất CSV, xóa dữ liệu theo đề và dọn dẹp tự động (lưu ngắn hạn)

**Yêu cầu cần đạt**
- Xuất bảng điểm CSV mở đúng trong Excel tiếng Việt, an toàn trước "CSV injection".
- Xóa dữ liệu một đề (bài làm, đáp án, tệp nộp) **nhất quán giữa DB và R2**; dọn dữ liệu quá hạn lưu trữ tự động mà không xóa nhầm.
- Dung lượng DB luôn dưới hạn mức gói miễn phí.

**Cách thức triển khai**
- **Xuất CSV `GET /admin/exams/{id}/export.csv`:** gọi `finalize_expired` trước; `StreamingResponse` sinh từng dòng (không nạp cả bảng); mã hóa `utf-8-sig` (BOM), xuống dòng CRLF; cột: `ma_lop, username, ho_ten, trang_thai, nop_luc (giờ VN), ly_do_nop, so_lan_roi_tab, tong_diem, thang_10, diem_cau_1…diem_cau_N, cau_cho_cham_tay`; ô bắt đầu bằng `= + - @` hoặc ký tự điều khiển được thêm `'`; tên tệp theo RFC 5987 (`filename*=UTF-8''…`) và có bản dự phòng ASCII.
- **Xóa dữ liệu đề `DELETE /admin/exams/{id}/data`:** yêu cầu đề `closed/archived` và `confirm_title` trùng tên đề (chống bấm nhầm); thứ tự:
  1. Trong **một transaction**: gom khóa R2 của `files(kind='submission', exam_id)`; xóa `answers`, `files` (submission), `attempts` của đề; ghi `audit_log`; **commit**.
  2. **Sau commit**, xóa đối tượng R2 theo lô 1000 (`delete_objects`). Lỗi xóa R2 chỉ để lại rác (sẽ được dọn ở bước dưới), **không làm DB quay lui**.
  3. Idempotent: gọi lại khi đã xóa trả `200` với số lượng 0.
- **Dọn dẹp định kỳ (APScheduler, 02:00 giờ VN):**
  - Dữ liệu bài làm của đề `archived` quá `DATA_RETENTION_DAYS`, hoặc đề `closed` quá `DATA_RETENTION_DAYS` kể từ lúc đóng, theo quy trình xóa ở trên (**không xóa đề và câu hỏi**).
  - Tệp R2 `submissions/…` không có hàng `files` và cũ hơn 1 giờ; ảnh đề không được tham chiếu và cũ hơn 7 ngày; `sessions` hết hạn; `audit_log` quá 180 ngày.
  - **Tuần đầu chạy ở chế độ `dry_run`** (chỉ ghi log "sẽ xóa N"), sau đó bật thật bằng biến môi trường.
  - Có cờ `retention_hold` (bổ sung) để giữ lại một đề không bị dọn.
- **Theo dõi dung lượng:** trang Cài đặt hiển thị `pg_database_size`, tổng `files.size_bytes`; cảnh báo màu khi DB > 80% của 0,5 GB; chú thích "Nên xuất CSV trước khi xóa".

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-6.5-01 | CSV mở trong Excel | Xuất đề có tên "Nguyễn Văn Ánh" và mở bằng Excel (Windows) | Tiếng Việt đúng, cột đúng, không cần chọn bảng mã |
| TC-6.5-02 | CSV injection | Họ tên `=cmd|' /C calc'!A0`, `@SUM(1)`, `+1+1` | Trong tệp xuất ô bị thêm `'`; Excel hiển thị văn bản, không thực thi |
| TC-6.5-03 | Đề lớn | 40 học sinh × 60 câu | Xuất < 3 giây; bộ nhớ không tăng theo kích thước (stream) |
| TC-6.5-04 | Xóa dữ liệu chuẩn | Xóa dữ liệu đề có 40 bài + 25 tệp nộp | DB: 0 attempt/answer/file của đề, đề và câu hỏi còn nguyên; R2: 25 đối tượng bị xóa |
| TC-6.5-05 | Xác nhận tên đề | Gửi `confirm_title` sai; đề đang `published` | `422`; `409`; không xóa gì |
| TC-6.5-06 | Lỗi R2 khi xóa | Giả lập R2 lỗi sau commit | DB vẫn đã xóa; có log; lượt dọn đêm sau xóa nốt đối tượng mồ côi |
| TC-6.5-07 | Idempotent | Gọi xóa 2 lần liên tiếp | Lần 2 trả `deleted=0`, không lỗi |
| TC-6.5-08 | Retention `dry_run` | Bật `dry_run`, có 2 đề quá hạn | Chỉ ghi log danh sách; dữ liệu không đổi; tắt `dry_run` thì xóa đúng 2 đề, **không** xóa đề còn hạn hoặc có `retention_hold` |
| TC-6.5-09 | Dọn rác | Tạo tệp R2 mồ côi 2 giờ tuổi và 10 phút tuổi | Chỉ tệp 2 giờ bị xóa |
| TC-6.5-10 | Cảnh báo dung lượng | Giả lập DB 0,45 GB | Trang Cài đặt hiện cảnh báo vượt 80% |

---

# GIAI ĐOẠN 7. CHẤT LƯỢNG: BẢO MẬT, TẢI, HỖN LOẠN, E2E, THIẾT BỊ

## Bước 7.1 — Rà soát bảo mật có hệ thống

**Yêu cầu cần đạt**
- Không có endpoint nào thiếu kiểm tra quyền; không có đường nào trả đáp án/điểm cho học sinh trước khi công bố; không lỗ hổng phổ biến (XSS, IDOR, injection, upload độc hại).

**Cách thức triển khai**
- **Ma trận quyền tự động:** tệp `tests/expected_access.yaml` khai báo mỗi route cần vai trò gì (`public`, `student`, `admin`). Bài test lặp qua **toàn bộ route** từ OpenAPI × {ẩn danh, student, admin}; kiểm tra mã trả về (`401/403/2xx` hợp lệ). **Route không có trong tệp YAML làm test thất bại** (buộc phân loại mọi endpoint mới).
- **Kiểm tra IDOR:** với mọi endpoint nhận `id` của tài nguyên thuộc người dùng (attempt, file, kết quả) thử bằng id của người khác → phải 404.
- **Bộ dò rò rỉ đáp án dùng chung:** `assert_no_leak(json)` (quét đệ quy khóa cấm + giá trị khớp đáp án đúng) được gọi **tự động** trong fixture cho mọi phản hồi của `/student/*`.
- **Nội dung do người dùng nhập:** Markdown đề (1.6), đáp án học sinh hiển thị cho giáo viên (6.2), tên tệp, `full_name`: kiểm thử XSS lưu trữ (stored XSS) bằng Playwright với payload chuẩn.
- **Upload:** bộ tệp độc hại (đổi đuôi, polyglot, SVG, ảnh khổng lồ, ZIP bom đổi tên `.png`).
- **Tiêm SQL:** mọi truy vấn qua ORM/tham số; thêm test đưa `' OR 1=1 --` vào các tham số tìm kiếm/sắp xếp và kiểm tra `sort` chỉ nhận từ danh sách trắng.
- **Cấu hình:** kiểm tra header phản hồi (`nosniff`, `Referrer-Policy`, CSP ở frontend), CORS chỉ đúng origin, HTTPS-only (HSTS do Cloudflare), cookie không dùng.
- **Chuỗi cung ứng & bí mật:** `pip-audit`, `pnpm audit --prod`, `gitleaks` trong CI; khóa phiên bản phụ thuộc (`uv.lock`, `pnpm-lock.yaml`).
- **Nhật ký:** soát log mẫu không chứa mật khẩu, token, đáp án.
- **Kế hoạch ứng phó:** quy trình thu hồi tất cả phiên (`DELETE FROM sessions`), xoay `SECRET_KEY` và khóa R2.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-7.1-01 | Ma trận quyền | Chạy bài test tự động trên mọi route | 100% route được phân loại; student chạm `/admin/*` → 403; ẩn danh → 401; route mới chưa khai báo làm CI đỏ |
| TC-7.1-02 | IDOR | Học sinh A dùng id attempt/file/result của B ở **mọi** endpoint có id | Luôn 404; không dữ liệu của B |
| TC-7.1-03 | Rò rỉ trước công bố | Chạy toàn bộ kịch bản học sinh (đăng nhập → làm → nộp → xem) với `assert_no_leak` | 0 vi phạm ở mọi phản hồi |
| TC-7.1-04 | XSS lưu trữ | Giáo viên chèn payload vào đề; học sinh chèn payload vào câu chữ; tên tệp chứa `<svg onload=…>` | Không script nào chạy ở phía học sinh lẫn giáo viên; payload hiện dạng chữ hoặc bị loại |
| TC-7.1-05 | Upload độc hại | Bộ 8 tệp độc hại (exe đổi tên, polyglot GIF/JS, SVG, ảnh bom, ZIP đổi tên…) | Tất cả bị từ chối; không có đối tượng nào được ghi lên R2 |
| TC-7.1-06 | Tiêm SQL | `q=' OR 1=1 --`, `sort=name;DROP TABLE users` | Kết quả rỗng/`422`; bảng không đổi |
| TC-7.1-07 | Dò mật khẩu | Script thử 200 mật khẩu cho 1 tài khoản | Bị `429` sau ≤ 10 lần/phút; tài khoản không bị khóa vĩnh viễn |
| TC-7.1-08 | Header & CORS | `curl -I` các route chính; request với `Origin` lạ | Có `nosniff`, `Referrer-Policy`; không `Access-Control-Allow-Origin` cho origin lạ |
| TC-7.1-09 | Phụ thuộc & bí mật | Chạy `pip-audit`, `pnpm audit`, `gitleaks` | 0 lỗ hổng mức cao/nghiêm trọng chưa có ngoại lệ được ghi lý do; 0 bí mật |
| TC-7.1-10 | Log sạch | Quét log của một phiên thi mô phỏng | Không có mật khẩu/token/đáp án |

---

## Bước 7.2 — Kiểm thử tải và đồng thời

**Yêu cầu cần đạt**
- Hệ thống chịu **40 học sinh đồng thời** (gấp > 6 lần yêu cầu) làm bài và nộp đồng loạt mà không mất đáp án, không lỗi 5xx ngoài ý muốn, trong giới hạn bộ nhớ của gói miễn phí.

**Cách thức triển khai**
- **Công cụ:** `locust` (Python). Kịch bản `StudentUser`: đăng nhập → `start` → `GET attempt` → 30 lần `PUT answers` với thời gian nghĩ 3–10 giây (`client_seq` tăng đúng) → `submit`; `TeacherUser`: polling giám sát mỗi 10 giây.
```python
class StudentUser(HttpUser):
    wait_time = between(3, 10)
    def on_start(self): self.token = login(self); self.attempt = start(self); self.seq = {}
    @task(30)
    def answer(self):
        q = random.choice(self.questions); self.seq[q] = self.seq.get(q, 0) + 1
        self.client.put(f"/student/attempts/{self.attempt}/answers/{q}",
                        json={"value": make_value(q), "client_seq": self.seq[q]}, name="PUT answer")
```
- **Môi trường:** chạy trên **cấu hình giống thật** (Render free + Neon free), từ máy ngoài mạng; thử cả cục bộ (Docker) để so sánh.
- **Kịch bản:** (A) tăng dần 0→40 người trong 60 giây; (B) **bão nộp bài**: 40 người cùng `submit` trong 2 giây (mô phỏng hết giờ đồng loạt); (C) **bão đăng nhập**: 40 người đăng nhập trong 10 giây (Argon2 tốn CPU/RAM); (D) chạy 30 phút liên tục để tìm rò rỉ bộ nhớ.
- **Điều chỉnh có căn cứ:** giới hạn số luồng của threadpool (`anyio` limiter ≈ 2× `pool_size`) để yêu cầu **xếp hàng** thay vì cạn pool và nhận `503`; `pool_timeout=5s` trả `503` + `Retry-After` (client có backoff). Nếu bão đăng nhập (C) chậm do CPU nhỏ của gói miễn phí, áp dụng **quy trình vận hành**: học sinh đăng nhập trước giờ thi 5–10 phút (phiên sống 12 giờ) — đưa vào checklist; chỉ nâng cấp gói khi đo thực tế vẫn không đạt.
- **Kiểm chứng bất biến sau tải:** truy vấn đối chiếu: mỗi attempt `submitted` đúng 1 lần; mọi đáp án phản hồi `accepted=true` có trong DB; tổng điểm khớp tính lại; không có deadlock trong log Postgres.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-7.2-01 | Tăng dần 40 người | Kịch bản A, 20 phút | p95 `PUT answer` < 500 ms khi server nóng; lỗi 5xx = 0; `409` chỉ ở ca cố ý |
| TC-7.2-02 | Bão nộp bài | Kịch bản B | 40/40 attempt `submitted` đúng 1 lần; p95 `submit` < 3 s; không deadlock |
| TC-7.2-03 | Bão đăng nhập | Kịch bản C trên gói miễn phí | Đo p95; nếu > 5 s → ghi nhận và áp dụng quy trình "đăng nhập trước"; RAM đỉnh < 400 MB, không bị OOM |
| TC-7.2-04 | Chạy dài | Kịch bản D 30 phút | RAM không tăng đơn điệu (> 10%/10 phút); số kết nối DB ≤ 10 |
| TC-7.2-05 | Toàn vẹn sau tải | Chạy các truy vấn đối chiếu | 0 bất thường: không attempt trùng, không đáp án mất, tổng điểm khớp |
| TC-7.2-06 | Cạn pool | Giả lập 100 yêu cầu đồng thời vượt pool | Phần dư xếp hàng hoặc nhận `503` có `Retry-After`; **không** có yêu cầu nào làm hỏng dữ liệu; client tự thử lại thành công |
| TC-7.2-07 | Giáo viên giám sát khi tải cao | Polling giám sát trong lúc 40 người làm | p95 < 1 s; không làm chậm `PUT answer` quá 20% so với lúc không giám sát |
| TC-7.2-08 | Neon vừa thức | Dừng truy cập DB > 5 phút rồi chạy tải | Truy vấn đầu chậm vài trăm ms rồi bình thường; không lỗi ra người dùng |

---

## Bước 7.3 — Kiểm thử hỗn loạn (chaos): mô phỏng sự cố thật của lớp học

**Yêu cầu cần đạt**
- Mỗi sự cố ở danh sách dưới đây đều có kết quả đã biết trước và **không làm mất đáp án đã được báo "Đã lưu"**; thời gian luôn theo server; bài hết giờ tự được nộp.

**Cách thức triển khai**
- **Công cụ:** Playwright (`context.setOffline`, CDP `Network.emulateNetworkConditions`, `page.clock`), **Toxiproxy** (độ trễ, mất kết nối, reset giữa chừng) đặt giữa client–API và API–DB, `docker kill/restart` cho backend/Postgres.
- **Kịch bản tự động hóa (mỗi kịch bản là một test E2E có kiểm chứng bằng truy vấn DB):**
  1. Mất điện máy học sinh: đóng cứng context (không `beforeunload`) khi còn đáp án trong outbox → mở lại bằng context mới (không `localStorage`).
  2. Rớt mạng 2 phút khi đang làm, trả lời tiếp, có mạng lại.
  3. Quá hạn trong lúc mất mạng; học sinh không quay lại; sweeper/nộp lười xử lý.
  4. Khởi động lại backend giữa đề (`docker restart`) khi 10 học sinh đang làm.
  5. Postgres dừng 20 giây (mô phỏng Neon thức dậy/chuyển đổi) rồi chạy lại.
  6. Mạng chập chờn: Toxiproxy `reset_peer` ngẫu nhiên 30% yêu cầu + độ trễ 2 giây.
  7. Đồng hồ máy học sinh nhanh/chậm 15 phút, và đổi giờ giữa chừng.
  8. Hai thiết bị cùng bài, ghi xen kẽ đáp án.
  9. Trình duyệt di động hủy tab nền (mô phỏng bằng đóng/mở lại cùng URL).
  10. Giáo viên đóng đề giữa lúc học sinh đang tải tệp 8 MB.
- **Bất biến kiểm chứng sau mỗi kịch bản:** (I1) mọi đáp án từng nhận `accepted=true` còn trong DB; (I2) mỗi attempt tối đa một lần `submitted`; (I3) `submitted_at ≤ deadline_at` (trừ nộp tay trong grace → vẫn ≤ deadline do `min`); (I4) không đáp án nào có `updated_at > deadline_at + grace`; (I5) không rò đáp án.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-7.3-01 | Mất điện, mất cả `localStorage` | Kịch bản 1 | Đáp án đã "Đã lưu" còn đủ; chỉ mất các thay đổi chưa gửi (đã được nêu trong tài liệu vận hành); đồng hồ đúng; làm tiếp được |
| TC-7.3-02 | Rớt mạng 2 phút | Kịch bản 2 | Banner offline → tự đồng bộ toàn bộ → "Đã lưu"; DB đủ đáp án |
| TC-7.3-03 | Quá hạn khi offline | Kịch bản 3 | Bài tự nộp với đáp án đã lưu **trước** thời điểm mất mạng; đáp án gõ khi offline sau hạn bị từ chối (`409`) và UI hiển thị "Hết giờ — bài đã nộp" |
| TC-7.3-04 | Backend khởi động lại | Kịch bản 4 | Học sinh thấy tối đa vài giây "đang kết nối lại", không lỗi mất dữ liệu; sweeper chạy bù khi khởi động |
| TC-7.3-05 | Postgres dừng 20 giây | Kịch bản 5 | API trả `503`; client thử lại; sau khi DB sống lại mọi mục trong outbox được gửi; **không** có `500` lộ ra người dùng |
| TC-7.3-06 | Mạng chập chờn | Kịch bản 6 | Mọi đáp án cuối cùng đến server; không đáp án trùng lặp hay ghi đè ngược; số lần thử lại có giới hạn hợp lý |
| TC-7.3-07 | Lệch/đổi giờ máy | Kịch bản 7 | Thời gian còn lại sai khác < 1,5 giây so với server ở mọi thời điểm |
| TC-7.3-08 | Hai thiết bị xen kẽ | Kịch bản 8 | Giá trị cuối mỗi câu là của `client_seq` lớn nhất; không có "giá trị nhảy ngược" |
| TC-7.3-09 | Hủy tab nền | Kịch bản 9 | Mở lại thấy đáp án đầy đủ và đồng hồ đúng; không tạo attempt mới |
| TC-7.3-10 | Đóng đề khi đang tải tệp | Kịch bản 10 | Tải tệp bị `409`, UI báo rõ; không có tệp "nửa vời" trong DB/R2; bài đã nộp với phần đã lưu |
| TC-7.3-11 | Bất biến | Chạy bộ kiểm chứng I1–I5 sau mỗi kịch bản | 0 vi phạm |

---

## Bước 7.4 — Bộ kiểm thử E2E tự động và quy trình CI

**Yêu cầu cần đạt**
- Có bộ E2E chạy tự động trên mỗi PR (nhóm nhanh) và hằng đêm (đủ bộ), ổn định (ít "test chập chờn"), cô lập dữ liệu giữa các test.

**Cách thức triển khai**
- **Cấu trúc `e2e/`:** `fixtures/` (tạo admin, lớp, học sinh, đề qua API/CLI seed; mỗi test **tự tạo dữ liệu riêng** với hậu tố ngẫu nhiên để chạy song song), `pages/` (Page Object cho các màn hình), `specs/` (theo luồng: `auth`, `class-mgmt`, `exam-editor`, `take-exam`, `resilience`, `grading`, `release`, `export`).
- **Cấu hình Playwright:** `retries: 1` (chỉ trên CI), `trace: 'on-first-retry'`, `video` khi lỗi, `workers` theo CPU, `projects` cho Chromium + WebKit + Mobile Chrome (viewport 360×640).
- **Đồng hồ:** test về hạn chót dùng đề thời lượng 1–2 phút hoặc `page.clock` kết hợp **đồng hồ server giả** (biến môi trường `TEST_CLOCK_OFFSET` chỉ bật ở môi trường test) để không phải chờ thật.
- **CI (GitHub Actions):** PR → nhóm "smoke" (≈ 10 phút: đăng nhập, tạo đề, làm bài, nộp, chấm, công bố); hằng đêm → toàn bộ + chaos (7.3) + tải ngắn (7.2 rút gọn); lưu `trace`/ảnh chụp khi lỗi làm artifact.
- **Cổng chất lượng trước khi deploy lên chính thức:** unit + tích hợp + smoke E2E phải xanh trên nhánh `main`.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-7.4-01 | Cô lập dữ liệu | Chạy toàn bộ bộ test 2 lần **đồng thời** trên cùng một DB | Cả hai lần xanh, không test nào đọc dữ liệu của test khác |
| TC-7.4-02 | Độ ổn định | Chạy bộ smoke 20 lần liên tiếp | Tỉ lệ thất bại ngẫu nhiên < 2%; test chập chờn bị cô lập và sửa/loại |
| TC-7.4-03 | Thời gian | Đo thời gian bộ smoke | ≤ 10 phút; bộ đầy đủ ≤ 30 phút |
| TC-7.4-04 | Chẩn đoán lỗi | Cố ý làm một test thất bại | Artifact có trace, video, ảnh chụp, log server tương ứng (theo `request_id`) |
| TC-7.4-05 | Cổng deploy | PR làm hỏng luồng nộp bài | CI đỏ, không thể merge/deploy |
| TC-7.4-06 | Đồng hồ giả | Test hết giờ dùng `TEST_CLOCK_OFFSET` | Chạy < 1 phút; biến này **không** có tác dụng ở môi trường production (kiểm bằng test cấu hình) |

---

## Bước 7.5 — Ma trận thiết bị, trình duyệt, bộ gõ tiếng Việt và trợ năng

**Yêu cầu cần đạt**
- Chạy đúng trên các thiết bị học sinh thực tế (điện thoại Android/iOS, laptop), kể cả máy yếu, bộ gõ tiếng Việt, chế độ tối tự động của trình duyệt, màn hình ngang/dọc.

**Cách thức triển khai**
- **Ma trận tối thiểu:** Chrome/Edge/Firefox (Windows/macOS), Safari iOS 16+, Chrome Android, Samsung Internet. Thử trên thiết bị thật hoặc dịch vụ thiết bị (ít nhất 1 iPhone + 1 Android tầm thấp).
- **Hiệu năng máy yếu:** DevTools throttle CPU 6×; đề 60 câu có 10 công thức mỗi câu → thời gian hiển thị câu đầu < 2 giây, chuyển câu < 300 ms; chỉ render **câu đang xem** (và tải trước câu kế).
- **Bộ gõ:** Telex, VNI, và bàn phím ảo Gboard/iOS với dự đoán từ; ô đáp án đặt `autocorrect="off" autocapitalize="off" spellcheck="false"`; kiểm tra sự kiện `composition*` ở mọi ô nhập (đã áp dụng ở 4.4, 5.6).
- **Tránh chế độ tối cưỡng bức làm sai tương phản:** khai báo `<meta name="color-scheme" content="light">` và `color-scheme: light` trong CSS; kiểm tra Samsung Internet/Chrome Android "Auto Dark".
- **Bàn phím ảo:** dùng `visualViewport` để khung nhập không bị che; nút Nộp luôn thao tác được.
- **Trợ năng:** thử nhanh với trình đọc màn hình (VoiceOver iOS, NVDA); thứ tự đọc, nhãn trường, `aria-live` của đồng hồ.
- **Tài liệu hỗ trợ:** `docs/ops/device-notes.md` ghi các lưu ý đã biết (ví dụ trình duyệt dựng sẵn trong ứng dụng Zalo/Facebook có thể hạn chế `localStorage`/tải tệp → hướng dẫn "Mở bằng Chrome/Safari").

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-7.5-01 | Luồng đầy đủ trên ma trận | Làm trọn một bài trên mỗi trình duyệt/thiết bị trong ma trận | Hoàn thành trên **100%** mục; lỗi nào phát hiện được ghi vào `device-notes.md` hoặc sửa |
| TC-7.5-02 | Máy yếu | CPU throttle 6× với đề 60 câu | Câu đầu hiển thị < 2 s; chuyển câu < 300 ms; không treo tab |
| TC-7.5-03 | Telex/VNI/bàn phím ảo | Gõ "Trường Đại học Bách khoa Hà Nội" vào ô chữ và đáp án ngắn | Văn bản đúng; không mất/đảo dấu; không tự sửa từ ngoài ý muốn |
| TC-7.5-04 | Chế độ tối tự động | Bật Auto Dark ở Chrome Android/Samsung Internet | Giao diện giữ chế độ sáng, tương phản không bị phá |
| TC-7.5-05 | Bàn phím ảo che nút | Mở bàn phím ở ô cuối trang trên iPhone nhỏ | Ô nhập và nút Nộp vẫn cuộn tới/nhìn thấy được |
| TC-7.5-06 | Trình duyệt trong ứng dụng | Mở liên kết trong trình duyệt Zalo/Messenger | Nếu `localStorage` bị hạn chế, hiện cảnh báo rõ + hướng dẫn mở bằng trình duyệt ngoài; không mất dữ liệu âm thầm |
| TC-7.5-07 | Xoay màn hình | Xoay ngang/dọc giữa lúc làm bài | Bố cục thích ứng; đáp án và đồng hồ không đổi |
| TC-7.5-08 | Trình đọc màn hình | Làm 3 câu bằng VoiceOver/NVDA | Nhãn câu hỏi/lựa chọn đọc đúng; đồng hồ chỉ thông báo ở mốc 5 phút/1 phút |

---

# GIAI ĐOẠN 8. HOSTING, TÊN MIỀN, GIÁM SÁT VÀ GO-LIVE

> **Mô hình triển khai:** Frontend tĩnh trên **Cloudflare Pages** → API **FastAPI trên Render (free web service, 1 worker)** → **Neon Postgres (free)** + **Cloudflare R2** (tệp/ảnh). Điều kiện các gói miễn phí thay đổi thường xuyên: **kiểm tra lại trang chính thức của từng nhà cung cấp ngay trước khi triển khai** và ghi lại phiên bản đã kiểm tra vào `docs/ops/hosting-notes.md`.

## Bước 8.1 — Triển khai cơ sở dữ liệu production trên Neon

**Yêu cầu cần đạt**
- CSDL production chạy ổn định, tách quyền (ứng dụng không có quyền sở hữu schema), có kế hoạch sao lưu độc lập, và **không tự đốt hết hạn mức CU-giờ miễn phí**.

**Cách thức triển khai**
- **Tạo dự án:** vùng gần Việt Nam (Singapore). Hạn mức miễn phí cần theo dõi: 0,5 GB lưu trữ và 100 CU-giờ/tháng cho mỗi dự án; compute tự tạm dừng sau 5 phút không có truy vấn.
- **Hai chuỗi kết nối:** *pooled* (host có `-pooler`) cho ứng dụng (`DATABASE_URL`), *direct* cho migration/sao lưu (`DATABASE_URL_DIRECT`); luôn `sslmode=require`.
- **Phân quyền:** chủ sở hữu (`neondb_owner`) chỉ dùng cho migration. Tạo vai trò ứng dụng:
```sql
CREATE ROLE quiz_app LOGIN PASSWORD '<mật khẩu dài ngẫu nhiên>';
GRANT CONNECT ON DATABASE neondb TO quiz_app;
GRANT USAGE ON SCHEMA public TO quiz_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO quiz_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO quiz_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO quiz_app;
```
- **Tương thích pooler:** kết nối của ứng dụng dùng `prepare_threshold=None` (2.2) và khóa tư vấn kiểu *transaction* (`pg_advisory_xact_lock`); chạy **toàn bộ bộ test tích hợp** một lần trên nhánh Neon qua chuỗi *pooled* để chắc chắn không có hành vi lạ.
- **Tiết kiệm CU-giờ:** (a) `/healthz` không chạm DB nên cron ping không đánh thức DB; (b) **sweeper không được truy vấn DB mỗi 30 giây vô điều kiện** (nếu làm vậy compute sẽ không bao giờ tạm dừng và vượt hạn mức): xem cơ chế `next_due` ở bước 5.8 — chỉ truy vấn DB khi có attempt đang chạy sắp đến hạn.
- **Môi trường thử (staging):** dùng **nhánh Neon** (sao chép khi ghi) từ production cho diễn tập 8.7; xóa nhánh sau khi xong.
- **Sao lưu độc lập** (khoảng khôi phục theo thời điểm của gói miễn phí rất ngắn, chỉ vài giờ): workflow GitHub Actions chạy mỗi tuần **và** thủ công trước mỗi kỳ thi:
```bash
pg_dump -Fc "$DATABASE_URL_DIRECT" | gzip | age -r "$BACKUP_PUBKEY" > quiz-$(date +%F).dump.gz.age
aws s3 cp quiz-*.age "s3://$S3_BACKUP_BUCKET/db/" --endpoint-url "$S3_ENDPOINT"
```
  Mã hóa bằng khóa công khai (`age`), giữ khóa riêng **ngoài** hệ thống; giữ 8 bản gần nhất; bucket sao lưu riêng, không công khai.
- **Chạy migration:** bằng chuỗi *direct* và vai trò chủ sở hữu, trước khi triển khai mã mới (xem 8.3); mọi migration tương thích ngược một phiên bản.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-8.1-01 | Kết nối từ backend thật | Triển khai bản thử, gọi `/readyz` | 200 qua chuỗi pooled; truy vấn đầu sau khi DB ngủ chậm ≤ vài giây rồi bình thường |
| TC-8.1-02 | Tách quyền | Với vai trò `quiz_app` chạy `DROP TABLE users`, `ALTER TABLE …`, `CREATE TABLE …` | Bị từ chối; CRUD thông thường hoạt động |
| TC-8.1-03 | Tương thích pooler | Chạy bộ test tích hợp trên nhánh Neon qua chuỗi pooled | 100% test đạt, không lỗi "prepared statement" |
| TC-8.1-04 | Sweeper không đốt CU-giờ | Để hệ thống rảnh (không attempt đang chạy) 30 phút rồi xem lịch sử hoạt động compute | Compute tạm dừng sau ~5 phút; không bị đánh thức định kỳ bởi sweeper |
| TC-8.1-05 | Sao lưu & mã hóa | Chạy workflow sao lưu | Tệp `.age` có trên bucket sao lưu; **không** giải mã được nếu không có khóa riêng |
| TC-8.1-06 | Khôi phục | Khôi phục bản sao lưu vào nhánh/DB mới | Số lượng hàng các bảng chính khớp bản gốc; ứng dụng chạy được trên DB đã khôi phục |
| TC-8.1-07 | Theo dõi hạn mức | Sau 1 tuần dùng thử, xem mức tiêu thụ CU-giờ và dung lượng | CU-giờ < 25% hạn mức tháng; dung lượng < 30% hạn mức; đã ghi vào `hosting-notes.md` |

---

## Bước 8.2 — Cấu hình lưu trữ tệp/ảnh trên Cloudflare R2

**Yêu cầu cần đạt**
- Bucket riêng tư, quyền tối thiểu, tự dọn dữ liệu cũ; sự cố R2 **không làm hỏng việc làm bài** (chỉ ảnh/tệp bị ảnh hưởng).

**Cách thức triển khai**
- **Bucket:** `quiz-files` (riêng tư), một bucket riêng `quiz-backups` cho sao lưu; mỗi bucket một **API token chỉ cấp quyền Object Read & Write cho đúng bucket đó**.
- **Máy khách S3 với thời gian chờ ngắn** (không để một lần R2 chậm treo cả request làm bài):
```python
s3 = boto3.client("s3", endpoint_url=S3_ENDPOINT, region_name="auto",
    aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"},
                  connect_timeout=3, read_timeout=10, retries={"max_attempts": 3, "mode": "standard"}))
```
  Tạo URL ký (`generate_presigned_url`) là phép tính cục bộ, không gọi mạng.
- **Quy tắc vòng đời (lifecycle):** `submissions/` hết hạn sau 120 ngày (chốt chặn phụ cho job dọn ở 6.5); hủy tải lên dở dang (multipart) sau 1 ngày.
- **CORS:** hiển thị `<img>` không cần CORS; không cho phép tải lên trực tiếp từ trình duyệt (mọi tải lên đi qua backend) nên **không bật CORS ghi**.
- **Chịu lỗi:** lỗi R2 → backend trả `502 storage_unavailable`; các luồng không cần R2 (lưu đáp án, nộp bài, đồng hồ) **không phụ thuộc R2**; ở frontend ảnh lỗi hiện khung "Ảnh tạm thời không tải được — Thử lại" (`onError` + nút tải lại), không làm hỏng câu hỏi.
- **Hạn mức:** kiểm tra hạn mức lưu trữ/số thao tác miễn phí hiện hành của R2 và ghi vào `hosting-notes.md`; thiết lập cảnh báo dung lượng.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-8.2-01 | Riêng tư | Truy cập URL đối tượng không ký | 403 |
| TC-8.2-02 | URL ký | Lấy URL ký 5 phút; dùng đúng hạn và sau hạn | Hoạt động trong hạn; 403 sau hạn; sửa tham số `Key` → 403 |
| TC-8.2-03 | Quyền token | Dùng token bucket `quiz-files` để ghi vào `quiz-backups` | Bị từ chối |
| TC-8.2-04 | **R2 ngừng hoạt động** | Chặn truy cập R2 từ backend (staging), cho một học sinh làm bài 5 phút | Lưu đáp án/nộp bài bình thường; ảnh hiển thị khung lỗi có nút thử lại; tải tệp báo lỗi rõ; không lỗi 500 trong luồng làm bài |
| TC-8.2-05 | R2 chậm | Thêm độ trễ 8 giây (Toxiproxy) | Hết thời gian chờ ở ≤ 10 giây, trả `502`; các request khác không bị ảnh hưởng |
| TC-8.2-06 | Lifecycle | Tạo đối tượng thử với quy tắc 1 ngày (môi trường thử) | Đối tượng bị xóa đúng hạn |

---

## Bước 8.3 — Triển khai backend lên Render

**Yêu cầu cần đạt**
- Triển khai lặp lại được bằng một thao tác; khởi động thất bại nhanh và rõ ràng khi thiếu cấu hình; có thể quay lui; **không có triển khai trong khung giờ thi**.

**Cách thức triển khai**
- **Dockerfile (nhỏ gọn, chạy bằng người dùng không phải root):**
```dockerfile
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini .
RUN useradd -m app && chown -R app /app
USER app
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1 --proxy-headers --forwarded-allow-ips='*'"]
```
  `--workers 1` bắt buộc (job nền + bộ đếm giới hạn tần suất trong bộ nhớ). Migration chạy ở đầu lệnh khởi động (gói miễn phí không có bước tiền-triển-khai riêng — nếu có thể dùng bước đó thì ưu tiên); `alembic/env.py` lấy `pg_advisory_lock` quanh migration để hai tiến trình không chạy trùng.
- **Dịch vụ:** Web Service gói miễn phí, vùng Singapore, **Auto-Deploy tắt**; triển khai bằng *deploy hook* do workflow CI gọi sau khi `main` xanh. **Quy tắc vận hành: không triển khai trong khung giờ thi hoặc trong 30 phút trước đó** (khi đó chặn workflow bằng biến `DEPLOY_FREEZE`).
- **Biến môi trường:** theo Phụ lục A đặc tả; `CORS_ORIGINS` đúng bằng domain Pages (https, không dấu `/` cuối); `DATABASE_URL` (pooled, vai trò `quiz_app`); `DATABASE_URL_DIRECT` (chủ sở hữu, chỉ cho migration — nếu muốn tách quyền chặt hơn thì chạy migration từ CI thay vì lúc khởi động); `SECRET_KEY`, `S3_*`. **Lưu ý bảo mật (Không mật khẩu mặc định):** Tuyệt đối không đặt biến `ADMIN_PASSWORD` mặc định trên môi trường; tài khoản Admin đầu tiên được tạo qua SSH/Shell của Render bằng lệnh tương tác `python -m app.cli create-admin` do chính người dùng tự nhập và xác nhận.
- **Health check path:** `/healthz`.
- **Quay lui:** dùng tính năng rollback bản triển khai trước của Render; vì migration tương thích ngược một phiên bản nên bản cũ vẫn chạy được trên schema mới.
- **Khởi động nguội:** log các mốc (import xong, migration xong, DB sẵn sàng, scheduler chạy, lượt quét bắt kịp) để đo thời gian; mục tiêu < 60 giây.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-8.3-01 | Triển khai từ đầu | Tạo dịch vụ mới, đặt biến, triển khai; chạy `create-admin` qua shell | Health check xanh; `/readyz` 200; migration đã chạy; tạo admin do người dùng nhập và đăng nhập thành công |
| TC-8.3-02 | Thiếu cấu hình | Xóa `SECRET_KEY` rồi triển khai | Dịch vụ **không** lên; log nêu rõ tên biến thiếu; không lộ giá trị bí mật |
| TC-8.3-03 | Khởi động nguội | Để dịch vụ ngủ (≥ 15 phút), gọi lần đầu | Phản hồi thành công sau ≤ ~60 giây; trang đăng nhập hiện "đang đánh thức máy chủ" rồi vào được; lượt quét bắt kịp chạy |
| TC-8.3-04 | Triển khai khi đang có bài | Staging: 3 học sinh đang làm, kích hoạt triển khai | Học sinh thấy "đang kết nối lại" tối đa vài chục giây; đáp án trong outbox được gửi bù; không mất dữ liệu (đây là lý do tồn tại quy tắc "không triển khai giờ thi") |
| TC-8.3-05 | Quay lui | Triển khai bản lỗi cố ý rồi rollback | Bản cũ chạy lại; schema vẫn tương thích; dữ liệu nguyên vẹn |
| TC-8.3-06 | Chỉ một worker | Kiểm tra số tiến trình/log scheduler | Duy nhất 1 scheduler; không job nào chạy trùng |
| TC-8.3-07 | Chặn triển khai giờ thi | Chạy workflow với `DEPLOY_FREEZE=1` | Workflow dừng với thông báo rõ, không gọi deploy hook |

---

## Bước 8.4 — Triển khai frontend lên Cloudflare Pages

**Yêu cầu cần đạt**
- SPA chạy trên tên miền `*.pages.dev` với HTTPS; tải lại ở đường dẫn sâu không lỗi 404; CSP chặt nhưng không làm hỏng KaTeX/ảnh R2; xử lý được tình huống "bản mới vừa triển khai".

**Cách thức triển khai**
- **Cài đặt dự án Pages:** thư mục gốc `frontend`, lệnh build `pnpm build`, thư mục xuất `dist`, biến `VITE_API_BASE_URL=https://<api>.onrender.com/api/v1`, `NODE_VERSION`.
- **`public/_redirects`:** `/* /index.html 200` (SPA fallback).
- **`public/_headers`:**
```
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: no-referrer
  X-Frame-Options: DENY
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://*.r2.cloudflarestorage.com; font-src 'self' data:; connect-src 'self' https://<api>.onrender.com; frame-ancestors 'none'; base-uri 'none'; form-action 'self'
/assets/*
  Cache-Control: public, max-age=31536000, immutable
/index.html
  Cache-Control: no-cache
```
  `style-src 'unsafe-inline'` cần vì KaTeX dùng thuộc tính `style` nội tuyến; **đổi `img-src` cho khớp đúng host mà URL ký R2 sử dụng** (kiểm tra bằng một URL ký thật). Vì token đăng nhập nằm ở `localStorage`, CSP chặt là lớp phòng vệ XSS quan trọng.
- **Backend CORS:** chỉ `https://<tên>.pages.dev` (và tên miền riêng nếu có). Bản xem trước của nhánh (Preview) trỏ tới API staging, không dùng API production.
- **Bản mới triển khai khi có người đang làm bài:** tệp băm cũ (`/assets/xyz-OLD.js`) có thể không còn → `vite:preloadError` (2.5) hiện hộp thoại tải lại; vì outbox đã ở `localStorage` nên không mất đáp án. Kết hợp quy tắc không triển khai giờ thi.
- **Hiệu năng:** chia mã theo route; KaTeX chỉ nạp khi cần; kiểm Lighthouse (di động, 4G chậm).

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-8.4-01 | Đường dẫn sâu | Mở trực tiếp và F5 tại `/s/attempts/<id>` | Trang tải đúng (không 404 của Pages) |
| TC-8.4-02 | CSP không vi phạm | Playwright lắng nghe `securitypolicyviolation` khi duyệt mọi màn hình (có công thức KaTeX, ảnh R2, xem trước) | 0 vi phạm; công thức và ảnh hiển thị đủ |
| TC-8.4-03 | CORS | Gọi API từ domain Pages và từ origin lạ | Domain Pages thành công (kể cả preflight); origin lạ bị chặn |
| TC-8.4-04 | Header & cache | `curl -I` `/`, `/assets/*.js` | Có đủ header bảo mật; `index.html` `no-cache`; tài sản băm `immutable` |
| TC-8.4-05 | Bản mới giữa phiên | Mở bài làm ở trình duyệt, triển khai bản mới, điều hướng sang chunk mới | Hộp thoại "Có bản cập nhật"; sau tải lại đáp án/đồng hồ nguyên vẹn |
| TC-8.4-06 | Hiệu năng di động | Lighthouse (Moto G, 4G chậm) trang đăng nhập | LCP < 2,5 s; điểm Performance ≥ 85, Accessibility ≥ 95 |
| TC-8.4-07 | Nội dung hỗn hợp | Kiểm tra tab Network | Không có yêu cầu HTTP (mixed content) |

---

## Bước 8.5 — Giữ máy chủ thức, giám sát và cảnh báo

**Yêu cầu cần đạt**
- Khi tới giờ thi máy chủ đã "nóng"; sự cố được phát hiện **trước** khi học sinh báo; giáo viên thấy trạng thái hệ thống ở một chỗ.

**Cách thức triển khai**
- **Ping giữ thức bằng cron-job.org:** `GET https://<api>/healthz` **mỗi 10 phút, chỉ trong khung giờ thi** (từ 30 phút trước giờ thi đến 30 phút sau giờ kết thúc; lập lịch theo từng đợt). Không ping 24/7 để giữ giờ chạy miễn phí an toàn (một dịch vụ chạy liên tục khoảng 744 giờ/tháng, sát hạn mức 750 giờ dùng chung cho mọi dịch vụ miễn phí trong tài khoản). Một công cụ ping duy nhất để tránh chồng lấn.
- **Cảnh báo:** cron-job.org gửi email (hoặc Telegram qua webhook) khi hai lần ping liên tiếp thất bại; cảnh báo nội bộ khi sweeper không chạy (attempt `in_progress` quá `deadline + 5 phút`).
- **Nút "Làm nóng hệ thống" (6.4):** quy trình: bấm 10 phút trước giờ thi.
- **Trang "Trạng thái hệ thống" cho giáo viên (`GET /admin/system/status`):** thời điểm lần quét gần nhất, số attempt đang chạy, độ trễ DB (ms), R2 sẵn sàng, độ lệch đồng hồ, dung lượng DB/tệp, phiên bản bản dựng.
- **Theo dõi lỗi (tùy chọn):** Sentry cho backend và frontend với `send_default_pii=False` và `before_send` **xóa nội dung đáp án, mật khẩu, token**; gắn `request_id`.
- **Ghi nhật ký:** log cấu trúc JSON ra stdout (Render giữ log ngắn hạn); các sự kiện quan trọng (`login`, `start`, `submit`, `finalize`, `extend`, `reopen`, `release`) đã có trong `audit_log`.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-8.5-01 | Máy chủ nóng đúng giờ | Đặt lịch ping 08:30–10:30; truy cập lúc 09:00 sau một đêm máy chủ ngủ | Phản hồi < 1 s (không có khởi động nguội) |
| TC-8.5-02 | Cảnh báo sự cố | Dừng dịch vụ trong khung giờ thi | Nhận email/Telegram trong ≤ 20 phút (2 lần ping lỗi) |
| TC-8.5-03 | Sweeper dừng | Giả lập job quét ngừng chạy với attempt quá hạn 6 phút | Phát sinh cảnh báo/ghi log mức ERROR và hiện đỏ ở trang trạng thái |
| TC-8.5-04 | Trang trạng thái | Mở trang khi hệ thống khỏe và khi chặn R2 | Chỉ báo từng thành phần đúng (xanh/đỏ); giá trị độ trễ hợp lý |
| TC-8.5-05 | Không rò dữ liệu qua Sentry | Gây lỗi có chứa đáp án/mật khẩu trong ngữ cảnh | Sự kiện gửi đi không chứa các giá trị đó |
| TC-8.5-06 | Hạn mức giờ chạy | Sau 1 tuần vận hành, xem bảng điều khiển Render | Số giờ chạy phù hợp kế hoạch (nhỏ hơn nhiều hạn mức 750 giờ) |

---

## Bước 8.6 — Tên miền dễ nhớ và cách học sinh truy cập

**Yêu cầu cần đạt**
- Học sinh vào được hệ thống bằng một địa chỉ ngắn dễ nhớ, trên mạng nhà trường lẫn 4G; có phương án nâng cấp lên tên miền riêng không gián đoạn.

**Cách thức triển khai**
- **Miễn phí:** đặt tên dự án Pages ngắn, không dấu, dễ đọc (ví dụ `quiz-toantin.pages.dev`; nếu bị trùng thì thêm hậu tố ngắn). Học sinh chỉ biết địa chỉ này; API ở `onrender.com` không cần nhớ.
- **Tên miền riêng (tùy chọn, có phí):** mua tên miền, thêm vào Pages (*Custom domains*), trỏ DNS theo hướng dẫn của Cloudflare (tên miền gốc cần dùng nameserver Cloudflare; tên miền phụ có thể dùng CNAME); chứng chỉ HTTPS tự cấp. Khi chuyển: **thêm** domain mới vào `CORS_ORIGINS` (giữ cả hai trong giai đoạn chuyển), đặt chuyển hướng từ `*.pages.dev` sang domain mới sau khi ổn định.
- **Phân phối:** tạo mã QR (thư viện `qrcode`) + liên kết rút gọn để chiếu/in dán ở lớp; thêm hướng dẫn một trang "Cách đăng nhập" cho học sinh (tên đăng nhập/mật khẩu do giáo viên phát, mở bằng Chrome/Safari, không dùng trình duyệt trong ứng dụng).
- **Kiểm tra truy cập mạng nhà trường:** một số mạng chặn tên miền lạ; thử `pages.dev` trên mạng trường thật trước ngày thi; nếu bị chặn → dùng tên miền riêng hoặc xin mở danh sách trắng.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-8.6-01 | HTTPS & chứng chỉ | Mở địa chỉ bằng nhiều trình duyệt | HTTPS hợp lệ, không cảnh báo chứng chỉ |
| TC-8.6-02 | Truy cập từ mạng thật | Mở trên Wi-Fi nhà trường và 4G của ≥ 3 loại điện thoại | Tải được trang đăng nhập trên mọi mạng; nếu bị chặn thì ghi lại và áp dụng phương án khác |
| TC-8.6-03 | Mã QR | Quét QR bằng iPhone và Android | Mở đúng trang đăng nhập (không qua trung gian lạ) |
| TC-8.6-04 | Chuyển sang tên miền riêng | Thêm domain mới, giữ cả hai trong CORS | Cả hai địa chỉ đăng nhập/làm bài được; sau khi bật chuyển hướng, địa chỉ cũ chuyển sang địa chỉ mới |
| TC-8.6-05 | Độ dễ nhớ | Hỏi 5 học sinh nhắc lại địa chỉ sau 1 phút | ≥ 4/5 gõ lại đúng |

---

## Bước 8.7 — Nghiệm thu người dùng (UAT) và diễn tập toàn bộ (dress rehearsal)

**Yêu cầu cần đạt**
- Toàn bộ vòng đời một kỳ thi được chạy thử với người thật trên hạ tầng thật (hoặc staging giống hệt), và **10 kịch bản nghiệm thu của đặc tả (mục 12.2)** đều đạt.

**Cách thức triển khai**
- **Chuẩn bị:** tạo nhánh Neon staging (hoặc dùng production với lớp "Thử nghiệm"), 1 lớp thử gồm 6–10 học sinh thật/cộng tác viên, 1 giáo viên; đề thử đủ 5 dạng câu, có công thức, có ảnh, thời lượng 15 phút, có câu nộp tệp.
- **Kịch bản diễn tập (theo đúng thứ tự thật):** giáo viên nhập CSV học sinh → soạn đề → xuất bản → "Làm nóng" → học sinh đăng nhập sớm → bắt đầu đồng loạt → **chủ động gây sự cố** (ngắt mạng, đóng tab, tắt điện thoại, mở 2 tab) → có học sinh để hết giờ → giáo viên cộng giờ/mở lại/nộp hộ → chấm tay → công bố → xuất CSV → xóa dữ liệu.
- **Thu thập số liệu:** thời gian đăng nhập đồng loạt, độ trễ lưu, số lần thử lại, lỗi ghi log, phản hồi của người dùng (bảng góp ý 1 trang).
- **Tiêu chí ký nghiệm thu:** 10/10 kịch bản đạt; 0 lỗi nghiêm trọng (mất dữ liệu, rò đáp án, sai thời gian); các lỗi nhẹ có kế hoạch sửa; giáo viên tự thực hiện được vòng đời mà không cần hỗ trợ.
- **Vòng lặp sửa lỗi:** phân loại (chặn go-live / sau go-live), sửa, chạy lại **đúng các kịch bản liên quan**.

**Test case kiểm thử và yêu cầu cần đạt** (đối chiếu đặc tả 12.2)

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-8.7-01 | (12.2#1) Đóng tab rồi mở lại | Làm 5 câu, đóng tab, mở lại sau 2 phút | Đáp án còn nguyên, đồng hồ đã giảm tương ứng |
| TC-8.7-02 | (12.2#2) Ngắt mạng | Ngắt mạng, trả lời tiếp, bật lại | Banner mất kết nối → tự đồng bộ → "Đã lưu" |
| TC-8.7-03 | (12.2#3) Đóng máy tới quá giờ | Tắt hẳn thiết bị đến sau hạn | Bài tự nộp với đáp án đã lưu; giáo viên thấy `timeout` |
| TC-8.7-04 | (12.2#4) Chỉnh đồng hồ máy | Chỉnh đồng hồ sớm/trễ | Thời gian còn lại vẫn đúng theo server |
| TC-8.7-05 | (12.2#5) Hai tab | Mở 2 tab cùng bài | Không tạo hai attempt; đáp án mới nhất được giữ |
| TC-8.7-06 | (12.2#6) Server ngủ | Để server ngủ rồi cho học sinh vào | "Đang đánh thức máy chủ", vào được, bài không mất |
| TC-8.7-07 | (12.2#7) Chưa công bố | Học sinh thử mở đường dẫn kết quả sau khi nộp | Không điểm/đáp án cho tới khi công bố |
| TC-8.7-08 | (12.2#8) Cộng giờ | Cộng 5 phút cho một học sinh | Chỉ học sinh đó có thêm giờ |
| TC-8.7-09 | (12.2#9) Nhiều người cùng làm | 6–10 học sinh làm và nộp đồng thời | Không lỗi, không mất đáp án |
| TC-8.7-10 | (12.2#10) Tệp không hợp lệ | Tải tệp 15 MB / `.exe` | Bị từ chối kèm thông báo rõ |
| TC-8.7-11 | Giáo viên tự vận hành | Giáo viên chưa từng dùng thực hiện trọn vòng đời theo tài liệu | Hoàn thành không cần trợ giúp; mọi điểm vướng được ghi lại để sửa tài liệu/giao diện |

---

## Bước 8.8 — Go-live, vận hành, sao lưu/khôi phục và quy trình sự cố

**Yêu cầu cần đạt**
- Có checklist trước/trong/sau kỳ thi; sổ tay xử lý sự cố (runbook) đã được diễn tập; đã thử khôi phục từ bản sao lưu và quay lui triển khai.

**Cách thức triển khai**
- **Checklist trước kỳ thi** (mở rộng Phụ lục C của đặc tả):
  1. Đã xuất bản đề và xem thử bằng tài khoản học sinh thật; `result_visibility = hidden`.
  2. Học sinh đã được ghi danh đúng lớp; mật khẩu đã phát; **học sinh đăng nhập trước 5–10 phút**.
  3. Đã chạy sao lưu thủ công trong 24 giờ trước; lịch ping giữ thức đã đặt đúng khung giờ.
  4. Bấm "Làm nóng hệ thống" 10 phút trước giờ; trang Trạng thái toàn xanh.
  5. **Không có triển khai nào** từ 30 phút trước đến hết giờ thi (`DEPLOY_FREEZE`).
  6. Đã thử một bài làm đầy đủ (đóng tab, tắt mạng) trên điện thoại và máy tính.
  7. Có số điện thoại/kênh liên lạc khi sự cố; bản in ngắn của runbook.
- **Runbook (triệu chứng → hành động):**

| Triệu chứng | Chẩn đoán nhanh | Hành động |
|---|---|---|
| Nhiều học sinh vào trang chậm/"đang đánh thức" | Trang Trạng thái; server ngủ | Bấm "Làm nóng"; yêu cầu học sinh chờ ≤ 1 phút, **không** tải lại liên tục |
| Một học sinh không đăng nhập được | Có `account_disabled` hay `rate_limited`? | Kiểm tra tài khoản; đặt lại mật khẩu; chờ 1 phút nếu bị giới hạn |
| Học sinh báo mất điện/hỏng máy | Giám sát: "Lần lưu cuối" | Cho đăng nhập ở thiết bị khác (bài tiếp tục nguyên trạng); cộng giờ bù nếu cần |
| Học sinh báo "Chưa gửi được" kéo dài | Mạng của em đó hay hệ thống? | Nếu chỉ một em: bảo giữ nguyên trang, kiểm tra mạng; nếu nhiều em: xem trạng thái hệ thống/DB |
| Đồng hồ học sinh khác kỳ vọng | `deadline_at` trên giám sát | Đồng hồ theo server là đúng; cộng giờ nếu sự cố do hệ thống |
| Cần kéo dài giờ cho cả lớp | — | Chọn nhiều dòng trên giám sát → "Cộng giờ" (gọi lần lượt từng attempt, mỗi lần có ghi vết) |
| Công bố nhầm | — | "Thu hồi công bố" ngay; kiểm tra `audit_log` ai đã xem (nếu cần) |
| R2 lỗi | Trạng thái R2 đỏ | Học sinh vẫn làm bài/nộp được; ảnh/tệp tạm thời bị ảnh hưởng; báo học sinh chờ |
| DB lỗi/`503` | Trạng thái DB; hạn mức Neon | Chờ tự phục hồi (≤ vài phút); nếu hết CU-giờ → phương án B (nâng cấp gói hoặc chuyển nhà cung cấp theo kế hoạch dự phòng) |
| Hết giờ chạy miễn phí của Render | Bảng điều khiển Render | Nâng cấp gói trả phí tạm thời hoặc đợi tháng sau; **không** ảnh hưởng dữ liệu |

- **Sau kỳ thi:** (1) mở trang Giám sát để hệ thống nộp nốt bài quá hạn; (2) chấm tay; (3) **xuất CSV** và lưu bản sao ngoài hệ thống; (4) công bố có chủ đích; (5) sao lưu; (6) dọn dữ liệu khi đã xong (hoặc để job dọn theo lịch lưu ngắn hạn).
- **Diễn tập khôi phục:** mỗi quý khôi phục bản sao lưu mới nhất vào nhánh/DB mới và đối chiếu số lượng hàng, chạy `alembic current`, đăng nhập thử. Mục tiêu: **RPO ≤ 1 tuần (hoặc tới lần sao lưu trước kỳ thi), RTO ≤ 60 phút**.
- **Quay lui:** thao tác rollback ở Render; nếu migration lỗi thì khôi phục DB từ bản sao lưu trước kỳ thi.
- **Bảo mật vận hành:** mật khẩu admin ≥ 12 ký tự, bật 2FA ở mọi dịch vụ; xoay `SECRET_KEY` và khóa R2 mỗi học kỳ; hạn chế dữ liệu cá nhân (chỉ họ tên + username), xóa theo lịch lưu trữ ngắn hạn.

**Test case kiểm thử và yêu cầu cần đạt**

| ID | Tình huống | Cách thực hiện | Kết quả cần đạt |
|---|---|---|---|
| TC-8.8-01 | Diễn tập khôi phục | Khôi phục bản sao lưu vào DB mới và chạy ứng dụng trỏ vào đó | Số hàng khớp; đăng nhập và mở đề cũ được; thời gian thực hiện ≤ 60 phút |
| TC-8.8-02 | Diễn tập quay lui | Triển khai bản lỗi cố ý rồi rollback theo runbook | Hệ thống hoạt động lại ≤ 10 phút; dữ liệu nguyên vẹn |
| TC-8.8-03 | Diễn tập sự cố | Chèn 5 sự cố (server ngủ, 1 học sinh mất điện, R2 lỗi, công bố nhầm, cần cộng giờ cả lớp) trong buổi thử | Giáo viên xử lý đúng theo runbook, mỗi sự cố ≤ 5 phút; runbook được cập nhật theo điểm vướng |
| TC-8.8-04 | Kỳ thi thật đầu tiên | Chạy với lớp thật, theo checklist | 0 bài mất dữ liệu; 0 rò đáp án; mọi bài hết giờ tự nộp; số liệu hiệu năng nằm trong ngưỡng ở 7.2 |
| TC-8.8-05 | Quy trình sau thi | Thực hiện đủ 6 bước sau kỳ thi | CSV đầy đủ, bản sao lưu có mặt, kết quả công bố đúng phạm vi, dữ liệu dọn theo lịch |
| TC-8.8-06 | Xoay bí mật | Xoay `SECRET_KEY` và khóa R2 ở môi trường thử | Hệ thống hoạt động lại sau khi cập nhật biến; phiên cũ bị vô hiệu như thiết kế; ảnh/tệp vẫn truy cập được |

---

# PHỤ LỤC

## Phụ lục A. Cổng chất lượng giữa các giai đoạn

| Hết giai đoạn | Điều kiện để sang giai đoạn kế tiếp |
|---|---|
| 0 | `README` chạy lại được trên máy mới; MCP Stitch gọi được (hoặc đã chọn phương án dự phòng) |
| 1 | 100% màn hình trong `SITE.md` đã sinh; `impeccable detect` + `axe` không lỗi nghiêm trọng; thư viện component có test; `MathText` qua bộ XSS |
| 2 | Đăng nhập/phân quyền hoạt động; `alembic check` sạch; test ma trận quyền sơ bộ xanh |
| 3 | Giáo viên nhập CSV 40 học sinh, ghi danh, tải bảng mật khẩu bằng giao diện |
| 4 | Tạo và xuất bản đề đủ 5 dạng câu; bộ dò rò rỉ đáp án xanh |
| 5 | **Toàn bộ test 5.x xanh, gồm test đồng thời trên PostgreSQL thật**; chaos sơ bộ (mất mạng, F5, hết giờ) đạt |
| 6 | Vòng đời đề khép kín: chấm → công bố → xuất CSV → xóa dữ liệu |
| 7 | Báo cáo tải/chaos/bảo mật/thiết bị đạt ngưỡng; E2E smoke xanh trên `main` |
| 8 | 10 kịch bản nghiệm thu đạt; diễn tập khôi phục/quay lui thành công; kỳ thi đầu tiên theo checklist |

## Phụ lục B. Đối chiếu đặc tả ↔ bước kế hoạch

| Mục đặc tả | Bước thực hiện |
|---|---|
| 3.1 Xác thực | 2.3, 7.1 |
| 3.2 Lớp & học sinh, nhập CSV | 3.1–3.4 |
| 3.3 Quản lý đề, 3.6 Thiết lập đề | 4.2, 4.5 |
| 3.4 Các dạng câu hỏi | 4.1, 4.4, 5.9, 6.1 |
| 3.5 LaTeX & ảnh | 1.6, 4.3, 4.4 |
| 3.7 Luồng làm bài | 5.1–5.3, 5.10 |
| 3.8 Chống gián đoạn | 5.4–5.8, 7.3 |
| 3.9 Chấm điểm | 6.1, 6.2 |
| 3.10 Công bố kết quả | 6.3 |
| 3.11 Theo dõi trực tiếp | 6.4 |
| 3.12 Xuất & dọn dữ liệu | 6.5, 8.1 |
| 4. Phi chức năng | 7.2, 7.5, 8.4 |
| 5. Kiến trúc & techstack | 0.1–0.3, 2.1–2.5 |
| 6. Hosting & tên miền | 8.1–8.6 |
| 7. Thiết kế dữ liệu | 2.2 |
| 8. Thiết kế API | 2.1–2.3, 3.x–6.x |
| 9. Đồng thời & toàn vẹn | 5.2, 5.4, 5.7, 5.8, 5.9, 7.2, 7.3 |
| 10. Bảo mật | 7.1 và rải rác ở 1.6, 4.3, 5.9 |
| 11. Danh sách màn hình | 1.1, 1.3–1.5 |
| 12. Kiểm thử & nghiệm thu | 7.1–7.5, 8.7 |
| 13. Lộ trình | A.1 |
| 14. Rủi ro | Phụ lục D |

## Phụ lục C. Khác biệt/bổ sung so với đặc tả v1.0 (cần cập nhật đặc tả khi thực hiện)

**Bổ sung API:**
- `GET /student/attempts/{id}/status` (đồng bộ đồng hồ nhẹ — 5.5).
- `GET /admin/exams/{id}/validate`, `GET /admin/exams/{id}/preview`, `PUT /admin/exams/{id}/classes` (4.2, 4.5).
- `POST /admin/students/import?dry_run=true` (3.3).
- `POST /admin/system/warmup`, `GET /admin/system/status`, `POST /admin/students/{id}/revoke-sessions` (6.4, 8.5).
- `POST /admin/exams/{id}/regrade?dry_run=` (6.1).

**Thay đổi lược đồ CSDL:** `classes.is_archived`; cột `version` ở `exams/questions/answers`; `exams.scale_to_10`; `exams.retention_hold`; ràng buộc `UNIQUE (exam_id, position) DEFERRABLE`; chỉ mục một phần `ix_attempts_active_deadline`; quy ước `answers.score IS NULL` = chờ chấm tay.

**Thay đổi hành vi so với đặc tả:**
- Truyền `:now` từ `Clock` vào SQL finalize thay vì `now()` của DB (A.3 #2).
- Ghi đáp án dùng `FOR SHARE`, finalize dùng `FOR UPDATE` (A.3 #3).
- Ảnh đề lưu `asset:<uuid>` và được thay bằng URL ký khi phát (A.3 #4).
- Giáo viên cộng giờ có thể vượt `close_at` (A.3 #6).
- Sweeper chỉ truy vấn DB khi có attempt đang chạy sắp đến hạn (5.8, 8.1).
- `submit` nhận thêm ảnh chụp outbox của client (5.7).

## Phụ lục D. Rủi ro còn lại và phương án dự phòng

| Rủi ro | Dấu hiệu | Phương án |
|---|---|---|
| Render free ngủ/ khởi động nguội đúng lúc thi | Trang chờ > 30 giây | Ping theo khung giờ thi, nút "Làm nóng"; nếu vẫn vướng: gói trả phí nhẹ cho backend hoặc VM luôn bật (Oracle Always Free) |
| Neon hết CU-giờ/dung lượng | DB trả `503` kéo dài, cảnh báo 80% | Dọn dữ liệu cũ, kiểm tra sweeper; nâng gói hoặc chuyển Postgres khác (dùng `pg_dump/pg_restore`, mã không phụ thuộc Neon) |
| R2 yêu cầu thanh toán/đổi điều kiện | Không bật được bucket | Đổi sang Supabase Storage (chỉ đổi biến `S3_*`) |
| Mạng nhà trường chặn tên miền | `TC-8.6-02` thất bại | Tên miền riêng, hoặc xin mở danh sách trắng, hoặc dùng 4G |
| Stitch MCP không ổn định/hết hạn mức | Lỗi xác thực/hạn mức ở 1.3 | Dùng giao diện web Stitch + xuất thủ công; hoặc sinh giao diện trực tiếp bằng code theo `DESIGN.md` |
| Học sinh quen dùng trình duyệt trong ứng dụng (Zalo…) | Cảnh báo `localStorage` ở 7.5 | Hướng dẫn mở bằng Chrome/Safari; mã QR dẫn tới liên kết mở trình duyệt ngoài |
| Tiến độ chậm | Quá 1,5× ước tính ở một giai đoạn | Cắt [V2] (đã nêu ở đặc tả 1.3); giữ nguyên Giai đoạn 5 và 7.3 (không cắt phần chống gián đoạn) |

## Phụ lục E. Khung workflow CI/CD (rút gọn)

```yaml
# .github/workflows/ci.yml
name: ci
on: [pull_request, push]
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres: { image: postgres:16, env: { POSTGRES_PASSWORD: pw }, ports: ["5432:5432"],
                  options: >- --health-cmd pg_isready --health-interval 5s --health-retries 10 }
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: cd backend && uv sync --frozen && uv run ruff check . && uv run alembic upgrade head && uv run alembic check && uv run pytest -q
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - run: cd frontend && pnpm i --frozen-lockfile && pnpm tsc --noEmit && pnpm lint && pnpm vitest run && pnpm build
  e2e-smoke:
    needs: [backend, frontend]
    runs-on: ubuntu-latest
    steps: [ { uses: actions/checkout@v4 }, { run: "docker compose -f docker-compose.ci.yml up -d && pnpm --dir e2e playwright test --grep @smoke" } ]
  deploy:                       # chỉ nhánh main, chỉ khi không bị đóng băng
    if: github.ref == 'refs/heads/main' && vars.DEPLOY_FREEZE != '1'
    needs: [backend, frontend, e2e-smoke]
    runs-on: ubuntu-latest
    steps: [ { run: "curl -fsS -X POST \"$RENDER_DEPLOY_HOOK\"" } ]    # Pages tự build từ nhánh main
```
