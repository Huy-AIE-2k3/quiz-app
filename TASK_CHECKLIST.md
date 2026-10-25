# BẢNG THEO DÕI TIẾN ĐỘ & NGHIỆM THU TEST CASE (MATHRIX)

> **Căn cứ:** `TASKS.md` v1.0 & `QUIZ.md` v1.0  
> **Cập nhật lần cuối:** 25/10/2026  
> **Quy ước trạng thái:**  
> - `[x]` : Đã hoàn thành & Đạt kiểm thử (Passed)  
> - `[/]` : Đang triển khai (In Progress)  
> - `[ ]` : Chưa bắt đầu (Pending)  
> - `[!]` : Bị nghẽn / Cần lưu ý đặc biệt (Blocked)  

---

## TỔNG QUAN TIẾN ĐỘ THEO GIAI ĐOẠN

| Giai đoạn | Nội dung | Số Test Case | Đã Đạt | Tiến độ | Milestone | Trạng thái |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **P0** | **Thiết kế UI/UX với AI & Stitch** | **30** | **30** | **100%** | **M0: Duyệt Prototype** | 🟢 **HOÀN THÀNH** |
| **P1** | Khởi tạo hạ tầng & khung dự án | 28 | 7 | 25% | M1: FE–BE–DB nối thông | 🟡 **ĐANG TRIỂN KHAI** |
| **P2** | Tài khoản, lớp, học sinh | 28 | 0 | 0% | M2: Quản lý lớp & Auth | ⏳ Chờ bắt đầu |
| **P3** | Soạn đề (LaTeX, ảnh, 5 dạng câu) | 35 | 0 | 0% | M3: Đề thi hoàn chỉnh | ⏳ Chờ bắt đầu |
| **P4** | Làm bài, autosave, chống gián đoạn | 42 | 0 | 0% | M4: Thi chịu gián đoạn | ⏳ Chờ bắt đầu |
| **P5** | Chấm điểm, giám sát, công bố, CSV | 42 | 0 | 0% | M5: Vòng đời đề khép kín | ⏳ Chờ bắt đầu |
| **P6** | Kiểm thử chất lượng, bảo mật, tải | 21 | 0 | 0% | M6: Nghiệm thu 10 kịch bản | ⏳ Chờ bắt đầu |
| **P7** | Triển khai hosting, pilot, go-live | 35 | 0 | 0% | M7: Pilot lớp thật | ⏳ Chờ bắt đầu |
| **P8** | Vận hành & đóng dự án | 7 | 0 | 0% | M8: Bàn giao & tài liệu | ⏳ Chờ bắt đầu |
| **TỔNG** | **Toàn bộ dự án** | **268** | **30** | **11.2%** | **8 Cột mốc** | 🚀 **ĐANG TRIỂN KHAI** |

---

## CHI TIẾT GIAI ĐOẠN P0: THIẾT KẾ UI/UX VỚI AI & STITCH

> **Stitch Project ID:** `1234490079088282130` (`Quiz Toan Tin` / Mathrix)  
> **Design System:** `Cybernetic Prism` (`assets/626e24bb72a94145b979254c2b157864`)  
> **Tài liệu nguyên mẫu trực quan:** [stitch_ui_prototype.md](file:///home/leduchuy/.gemini/antigravity-ide/brain/347efaa9-f19b-4a1c-b758-18890445fc9d/stitch_ui_prototype.md)

### Bước 0.1 – Khảo sát giao diện tham khảo & thu thập yêu cầu customize từ người dùng
- [x] **T0.1.1 [M]** Trao đổi về giao diện tham khảo: Đã khảo sát ảnh mẫu trong `template-figma`, thống nhất phong cách dark mode gaming/edtech hiện đại.
- [x] **T0.1.2 [M]** Thu thập yêu cầu customize về màu sắc & font chữ: Bảng màu `#08090C` (nền đen sâu), `#00FF88` (neon emerald), hiệu ứng click đáp án màu vàng hổ phách `#F59E0B`, textbox đăng nhập lóe viền xanh chạy ngang, typography Outfit & Inter sắc nét cho Toán - Tin.
- [x] **T0.1.3 [M]** Thu thập yêu cầu customize về bố cục màn hình làm bài: Thiết kế 1 câu hỏi duy nhất tại mỗi thời điểm, sidebar ma trận 20 câu hỏi bên phải, vô hiệu hóa phím tắt hệ thống, bỏ hoàn toàn bàn phím ảo chiếm chỗ ở câu điền số.
- [x] **T0.1.4 [M]** Thu thập yêu cầu customize về trải nghiệm soạn đề giáo viên: Bố cục 3 cột (Danh sách câu hỏi - Trình soạn Markdown/LaTeX - Live Preview KaTeX).
- [x] **T0.1.5 [M]** Rà soát nhánh bất thường (mất mạng, hết giờ, server ngủ): Đã xác định vị trí banner cảnh báo và màn hình trấn an nộp bài an toàn không hé lộ đáp án.
- [x] **T0.1.6 [M]** Kiểm tra tiêu chí "không tài liệu kỹ thuật dài dòng": Không tạo file spec/SRS cồng kềnh; brief đi thẳng vào các prompt sinh màn hình trên Stitch.
- [x] **T0.1.7 [M]** Chốt các quyết định A.3 mục 15 spec: Chốt chế độ chấm Đúng/Sai, giới hạn 1 đáp án MCQ, 1 ô upload file tự luận với danh sách bên dưới, bỏ barem checklist ở màn hình chấm thi.

**DoD Bước 0.1:** ✅ **ĐẠT** (Người dùng đồng thuận định hướng và yêu cầu customize).

---

### Bước 0.2 – Khởi tạo dự án Stitch & sinh Design System bằng AI
- [x] **T0.2.1 [M]** Gọi lệnh tạo project trên Stitch: Tạo thành công project `Quiz Toan Tin` (ID: `1234490079088282130`).
- [x] **T0.2.2 [M]** Kiểm tra tính nhất quán của bảng màu trên Stitch: Tone Cybernetic Prism tối giản, viền neon emerald phát sáng tinh tế, không chói mắt.
- [x] **T0.2.3 [M]** Kiểm tra typography cho tiếng Việt và công thức Toán: KaTeX render hoàn hảo các công thức ma trận, logarit, phân thức hữu tỉ, đạo hàm.
- [x] **T0.2.4 [M]** Kiểm tra độ tương phản màu sắc (WCAG AA): Tỷ lệ tương phản chữ trắng/xanh neon trên nền đen đạt chuẩn ≥ 4.5:1.
- [x] **T0.2.5 [M]** Kiểm tra các thành phần cốt lõi (Buttons, Badges, Inputs, Cards): Đạt chuẩn bo góc, viền neon mỏng, card tách lớp không gian.
- [x] **T0.2.6 [M]** Tái sử dụng `designSystemId` cho project: ID `assets/626e24bb72a94145b979254c2b157864` được tái sử dụng đồng bộ cho tất cả các màn hình.
- [x] **T0.2.7 [M]** Kiểm tra tính sẵn sàng cho cả 2 môi trường Mobile và Desktop: Bố cục desktop chuẩn, tự thích ứng trên màn hình nhỏ.

**DoD Bước 0.2:** ✅ **ĐẠT** (Design System khởi tạo và áp dụng thành công).

---

### Bước 0.3 – Sinh giao diện trực quan phía HỌC SINH trên Stitch
- [x] **T0.3.1 [M]** Xem trực quan màn hình Đăng nhập: Giao diện tối giản (`signin_stitch.png`), textbox lóe sáng viền xanh neon, đăng nhập tài khoản học sinh nội bộ.
- [x] **T0.3.2 [M]** Xem màn hình Danh sách đề thi: Phân tab trực quan (`student_exam_list_stitch.png`), cột thông tin đặc tả chi tiết đề thi bên phải.
- [x] **T0.3.3 [M]** Xem màn hình Giới thiệu đề thi & Pop-up Xác nhận: Modal xác nhận tinh giản (`exam_confirmation_clean_stitch.png`), loại bỏ hoàn toàn 3 dòng rườm rà (thời gian server, cơ chế, giám sát).
- [x] **T0.3.4 [M]** Xem màn hình Làm bài thi trọng tâm (các dạng câu):
  - *Câu trắc nghiệm đơn:* `quiz_screen_stitch.png` (Hiệu ứng click đáp án vàng amber glow).
  - *Câu Đúng / Sai:* `quiz_true_false_clean.png` (4 mệnh đề a, b, c, d với lựa chọn Đúng/Sai tinh gọn, không HUD giám sát).
  - *Câu Trả lời ngắn / Điền số:* `quiz_short_answer_clean.png` (Bỏ hoàn toàn bàn phím ảo, ô textbox nhập số đơn giản).
  - *Câu Tự luận nộp file:* `quiz_essay_clean.png` (Chỉ 1 ô kéo thả file duy nhất, danh sách tệp đã tải hiển thị ngay phía dưới theo giới hạn giáo viên).
- [x] **T0.3.5 [M]** Kiểm tra biến thể lưới điều hướng câu hỏi: Ma trận 20 câu hỏi dạng thẻ lưới 4x5 ở sidebar phải, hiển thị trực quan trạng thái đã làm, gắn cờ xem lại, câu đang xem.
- [x] **T0.3.6 [M]** Xem banner cảnh báo mất mạng & đang đánh thức máy chủ: Bố trí cố định, không che khuất đề thi và nút làm bài.
- [x] **T0.3.7 [M]** Xem màn hình Đã nộp bài: Thông báo trấn an trang trọng (`submitted_stitch.png`), không hé lộ điểm hay đáp án trước khi công bố.
- [x] **T0.3.8 [M]** Xem màn hình Kết quả thi: Tích hợp với bảng điểm lớp và xem lại đề thi.

**DoD Bước 0.3:** ✅ **ĐẠT** (100% màn hình học sinh được tối giản và duyệt trực quan).

---

### Bước 0.4 – Sinh giao diện trực quan phía GIÁO VIÊN trên Stitch & duyệt Prototype (M0)
- [x] **T0.4.1 [M]** Xem Dashboard giáo viên trên Desktop: `dashboard_stitch.png` hiển thị đề đang mở, bài chờ chấm, KPI nhanh.
- [x] **T0.4.2 [M]** Xem màn hình Soạn đề thi Toán - Tin: `exam_editor_stitch.png` thiết kế 3 cột chuyên nghiệp với khung LaTeX KaTeX live preview.
- [x] **T0.4.3 [M]** Xem cấu hình 5 dạng câu hỏi trong trình soạn đề: Trực quan cho MCQ, Đúng/Sai, Điền số, Tự luận file.
- [x] **T0.4.4 [M]** Xem màn hình Giám sát trực tiếp phòng thi & Thống kê vi phạm: `exam_details_anticheat_stitch.png` đếm số lần chuyển tab, copy-paste, ảnh chụp màn hình và lịch sử học sinh.
- [x] **T0.4.5 [M]** Xem màn hình Chấm bài và duyệt file nộp: `manual_grading_no_rubric.png` bỏ hoàn toàn barem chi tiết rườm rà, hỗ trợ xem ảnh bài làm zoom/xoay + ô nhập điểm số trực tiếp + nhận xét nhanh.
- [x] **T0.4.6 [M]** Xem màn hình Bảng điểm & Xuất dữ liệu: `class_results_stitch.png` phổ điểm trực quan, công bố điểm và xuất CSV.
- [x] **T0.4.7 [M]** Thao tác duyệt toàn bộ luồng từ Giáo viên đến Học sinh: Đồng bộ phong cách Mathrix, không xung đột UI.
- [x] **T0.4.8 [M]** Rà soát nghiệm thu Milestone M0: Người dùng xác nhận *"Giao diện cơ bản đã ổn"*.

**DoD Bước 0.4 & Cột mốc M0:** ✅ **HOÀN THÀNH XUẤT SẮC** (Chính thức nghiệm thu Prototype M0, sẵn sàng chuyển giao sang P1).

---

## KHUNG THEO DÕI CÁC GIAI ĐOẠN TIẾP THEO (P1 – P8)

### P1. KHỞI TẠO HẠ TẦNG & KHUNG DỰ ÁN (Tuần 1, song song P0)
- [x] **Bước 1.1 – Repo, công cụ, CI, môi trường cục bộ:**
  - [x] **T1.1.1 [M]** Máy mới: `cp .env.example .env` → `make dev` khởi động toàn bộ DB, pgAdmin, BE, FE.
  - [x] **T1.1.2 [I]** Linter CI: `ruff check` và `eslint` được cấu hình trong GitHub Actions.
  - [x] **T1.1.3 [I]** Test CI: `pytest` và `vitest` được cấu hình trong GitHub Actions.
  - [x] **T1.1.4 [S]** Bảo mật: Đã cấu hình `.gitignore` chặn toàn bộ `.env`, key và credentials.
  - [x] **T1.1.5 [I]** Cache dependencies: `setup-uv` và `setup-node` caching sẵn sàng.
  - [x] **T1.1.6 [M]** Biến môi trường: `pydantic-settings` đọc `.env` có fallback và validate.
  - [x] **T1.1.7 [M]** Lockfile: Đã tạo `backend/uv.lock` và `frontend/package-lock.json`.
  - [x] **T1.1.8 [M]** Chạy đa nền tảng: Chạy qua `Makefile` và `docker-compose.yml` (PostgreSQL 16 + pgAdmin 4 Web Console).
  - **DoD Bước 1.1:** ✅ **ĐẠT** (Monorepo sẵn sàng, `make test` và `make lint` 100% xanh, pgAdmin web hoạt động).
- [ ] **Bước 1.2 – Khung Backend (FastAPI, config, log, time service):** T1.2.1 -> T1.2.7 (7 test cases: `GET /healthz`, format JSON error, timing NTP drift, structured log).
- [ ] **Bước 1.3 – Cơ sở dữ liệu (PostgreSQL, Alembic migration, Seed data):** T1.3.1 -> T1.3.7 (7 test cases: `alembic upgrade head`, `downgrade -1`, FK indexes, seed CLI).
- [ ] **Bước 1.4 – Khung Frontend (Vite/React, Tailwind/CSS, Router, Axios client):** T1.4.1 -> T1.4.7 (7 test cases: Build clean, 404 page, interceptor 401, AuthGuard).
- **Cột mốc M1:** Khung dự án nối thông FE – BE – DB, CI xanh.

---

### P2. TÀI KHOẢN, LỚP, HỌC SINH (Tuần 2)
- [ ] **Bước 2.1 – Xác thực & phiên Backend (JWT/Cookie, Role-based):** T2.1.1 -> T2.1.7 (7 test cases: Login đúng/sai, expired token, phân quyền teacher/student).
- [ ] **Bước 2.2 – CLI quản trị & Quản lý mật khẩu:** T2.2.1 -> T2.2.7 (7 test cases: CLI tạo admin, bcrypt hash, reset password, đổi mật khẩu lần đầu).
- [ ] **Bước 2.3 – Quản lý lớp, học sinh, ghi danh, nhập CSV:** T2.3.1 -> T2.3.7 (7 test cases: CRUD lớp, import CSV học sinh, bắt lỗi trùng SBD, phân trang).
- [ ] **Bước 2.4 – Frontend: Đăng nhập & Quản lý lớp/học sinh:** T2.4.1 -> T2.4.7 (7 test cases: Form đăng nhập, danh sách lớp, modal import CSV có preview).
- **Cột mốc M2:** Giáo viên quản lý lớp, import danh sách học sinh và đăng nhập trơn tru.

---

### P3. SOẠN ĐỀ THI (LaTeX, Ảnh, 5 dạng câu) (Tuần 2–3)
- [ ] **Bước 3.1 – Model & API đề thi (5 dạng câu, khóa sửa khi xuất bản):** T3.1.1 -> T3.1.7 (7 test cases: Tạo đề draft, CRUD câu hỏi, lock draft khi published).
- [ ] **Bước 3.2 – Render Markdown + LaTeX KaTeX an toàn (`MathText`):** T3.2.1 -> T3.2.7 (7 test cases: Render inline/block KaTeX, sanitize XSS HTML, render ma trận/hệ pt).
- [ ] **Bước 3.3 – Upload ảnh & Dịch vụ lưu trữ (Cloudflare R2 / S3):** T3.3.1 -> T3.3.7 (7 test cases: Presigned URL, giới hạn dung lượng ảnh, kiểm tra MIME type).
- [ ] **Bước 3.4 – Giao diện soạn đề 3 cột (Exam Editor):** T3.4.1 -> T3.4.7 (7 test cases: Kéo thả thứ tự câu, live preview KaTeX <5ms, cấu hình điểm từng câu).
- [ ] **Bước 3.5 – Xem trước đề thi, Xuất bản, Đóng đề, Lưu trữ:** T3.5.1 -> T3.5.7 (7 test cases: Chế độ Preview học sinh, validate đủ đáp án trước khi publish).
- **Cột mốc M3:** Tạo được đề thi hoàn chỉnh với công thức Toán sắc nét.

---

### P4. LÀM BÀI & CHỐNG GIÁN ĐOẠN (Tuần 3) — ƯU TIÊN CAO NHẤT
- [ ] **Bước 4.1 – Schema làm bài (che đáp án) & Bắt đầu bài idempotent:** T4.1.1 -> T4.1.7 (7 test cases: Start attempt không trả `correct_answer`, retry không sinh 2 attempt).
- [ ] **Bước 4.2 – Tự lưu đáp án từng câu (Autosave với `client_seq`):** T4.2.1 -> T4.2.7 (7 test cases: Save answer, debounce 500ms, `client_seq` giải quyết out-of-order).
- [ ] **Bước 4.3 – Nộp bài `finalize_attempt` (idempotent, server time, auto-submit):** T4.3.1 -> T4.3.7 (7 test cases: Submit đúng hạn, hết giờ tự khóa, retry an toàn).
- [ ] **Bước 4.4 – Client: Đồng hồ Server, Hàng đợi Offline, SaveIndicator:** T4.4.1 -> T4.4.7 (7 test cases: Mất mạng lưu IndexedDB, có mạng tự flush, cấm gian lận giờ client).
- [ ] **Bước 4.5 – Giao diện làm bài thi hoàn chỉnh (5 dạng câu, 1 ô nộp file):** T4.5.1 -> T4.5.7 (7 test cases: Thao tác chuột, 1 câu/màn hình, upload file tự luận).
- [ ] **Bước 4.6 – Chống gián đoạn: Reload tab, Nhiều tab, Ghi nhận rời tab:** T4.6.1 -> T4.6.7 (7 test cases: F5 khôi phục trạng thái, khóa tab thứ hai, log event blur).
- **Cột mốc M4:** Học sinh làm trọn vẹn bài thi, miễn nhiễm rớt mạng và reload.

---

### P5. CHẤM ĐIỂM, GIÁM SÁT, CÔNG BỐ, XUẤT CSV (Tuần 4)
- [ ] **Bước 5.1 – Thư viện chấm điểm thuần (Pure scoring functions):** T5.1.1 -> T5.1.7 (7 test cases: Chấm MCQ, Đúng/Sai 3 chế độ THPT, điền số làm tròn eps).
- [ ] **Bước 5.2 – Tự động chấm khi Finalize & Chấm tay tự luận:** T5.2.1 -> T5.2.7 (7 test cases: Auto score trắc nghiệm, gán điểm tự luận, chấm lại toàn bộ).
- [ ] **Bước 5.3 – Giám sát trực tiếp phòng thi & Can thiệp khẩn cấp:** T5.3.1 -> T5.3.7 (7 test cases: Bảng tiến độ realtime, nút cộng giờ, nút nộp bài hộ).
- [ ] **Bước 5.4 – Công bố kết quả & Màn hình kết quả học sinh:** T5.4.1 -> T5.4.7 (7 test cases: `score_only` vs `full`, mở xem giải chi tiết sau giờ thi).
- [ ] **Bước 5.5 – Xuất bảng điểm CSV & Lưu trữ an toàn:** T5.5.1 -> T5.5.7 (7 test cases: Xuất UTF-8-BOM tiếng Việt cho Excel, backup kết quả).
- [ ] **Bước 5.6 – Frontend quản trị giáo viên hoàn chỉnh:** T5.6.1 -> T5.6.7 (7 test cases: Giao diện chấm tự luận không barem, bảng phân tích vi phạm).
- **Cột mốc M5:** Hoàn tất toàn bộ chu trình đề thi và chấm điểm.

---

### P6. KIỂM THỬ CHẤT LƯỢNG, BẢO MẬT, TẢI (Tuần 4–5)
- [ ] **Bước 6.1 – Rà soát & Kiểm thử bảo mật (IDOR, Anti-cheat, SQLi, XSS):** T6.1.1 -> T6.1.7.
- [ ] **Bước 6.2 – Kiểm thử đồng thời & Tải (40–100 học sinh thi cùng lúc):** T6.2.1 -> T6.2.7 (Locust script mô phỏng nộp bài đồng thời).
- [ ] **Bước 6.3 – Kiểm thử End-to-End theo 10 kịch bản nghiệm thu:** T6.3.1 -> T6.3.7.
- **Cột mốc M6:** Đạt toàn bộ 10 kịch bản nghiệm thu của hệ thống.

---

### P7. TRIỂN KHAI HOSTING & PILOT (Tuần 5)
- [ ] **Bước 7.1 – Dịch vụ cơ sở dữ liệu: Neon Postgres & Cloudflare R2:** T7.1.1 -> T7.1.7.
- [ ] **Bước 7.2 – Triển khai Backend FastAPI lên Render / VPS:** T7.2.1 -> T7.2.7.
- [ ] **Bước 7.3 – Triển khai Frontend lên Cloudflare Pages:** T7.3.1 -> T7.3.7.
- [ ] **Bước 7.4 – Giữ server thức (Cron Ping), Tên miền & Giám sát:** T7.4.1 -> T7.4.7.
- [ ] **Bước 7.5 – Thi thử nghiệm (Pilot) với 1 lớp thật & Go-live:** T7.5.1 -> T7.5.7.
- **Cột mốc M7:** Hệ thống chạy trơn tru với dữ liệu và học sinh thật.

---

### P8. VẬN HÀNH & ĐÓNG DỰ ÁN
- [ ] **Bước 8.1 – Bàn giao, hướng dẫn giáo viên, hoàn tất tài liệu:** T8.1.1 -> T8.1.7.
- **Cột mốc M8:** Bàn giao dự án hoàn thiện.
