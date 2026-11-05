# Mathrix - CONTRACT SITEMAP & DESIGN SPECIFICATION (SITE.md)

> **Dự án:** Hệ thống Quiz nội bộ Toán – Tin (Mathrix)  
> **Stitch Project ID:** `15546240290050457859`  
> **Stitch Project Title:** `Quiz Toan Tin - UI System`  
> **Device Type:** `DESKTOP` (Màn hình máy tính chuẩn phòng thi / giảng đường)  
> **Design Theme Archetype:** Modern Academic Technical Assessment (Emerald Precision)  
> **Brand Identity:** **Mathrix** (Tuyệt đối không slogan)  
> **Design System Token Source:** `design/tokens.json` / `DESIGN.md` / `frontend/src/tokens.css`  

---

## 1. NGUYÊN TẮC THIẾT KẾ TOÀN CỤC (GLOBAL DESIGN CONTRACT)

1. **Bảng màu Emerald Precision:**
   - **Canvas Dark:** `#090D16` | **Surface Card Dark:** `#111726` | **Border Dark:** `#1E293B`
   - **Canvas Light:** `#F8FAFC` | **Surface Card Light:** `#FFFFFF` | **Border Light:** `#E2E8F0`
   - **Brand Emerald Primary:** `#10B981` (Hover: `#34D399` / Light Mode: `#059669`)
   - **Typography:**
     - Văn bản: `Be Vietnam Pro`, `Plus Jakarta Sans`
     - Số & Nhãn: `Space Grotesk`
     - Mã nguồn & Ô số: `JetBrains Mono` (`tabular-nums`)
     - Công thức Toán: `KaTeX_Main`, `serif`
2. **Quy tắc Chống AI Slop:**
   - Không viền mờ nhạt, không dùng gradient lòe loẹt tím/hồng.
   - Bo góc tối đa 8px–12px (`rounded-lg`, `rounded-xl`).
   - Mọi card trắc nghiệm là **Selectable Option Card** với viền rõ ràng và phím tắt `[A]`, `[B]`, `[C]`, `[D]`.
   - Timer 3 trạng thái đạt chuẩn chống mù màu: Có Icon + Chữ + Màu (Bình thường / Cảnh báo / Khẩn cấp).
3. **Quy tắc Chống màn hình cụt:**
   - Mọi màn hình đều có breadcrumb hoặc nút thoát về trang chủ vai trò (`/s/exams` hoặc `/a`).
   - Màn hình nộp bài có 2 lối ra: Về danh sách đề thi hoặc Xem chi tiết kết quả.

---

## 2. DANH MỤC HỢP ĐỒNG 18 MÀN HÌNH & BIẾN THỂ (SCREEN INVENTORY)

| STT | Mã màn hình | Route tương ứng | Nhóm phân quyền | Tên màn hình | File HTML | File PNG | Trạng thái |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- | :---: |
| 1 | `SC-01` | `/login` | Public | Đăng nhập Hệ thống | `design/screens/SC-01-login.html` | `design/screens/SC-01-login.png` | `[x]` |
| 2 | `SC-02` | `/s/exams` | Học sinh | Danh sách Đề thi của tôi | `design/screens/SC-02-student-exams.html` | `design/screens/SC-02-student-exams.png` | `[x]` |
| 3 | `SC-03` | `/s/exams/:id` | Học sinh | Giới thiệu Đề & Quy chế thi | `design/screens/SC-03-exam-lobby.html` | `design/screens/SC-03-exam-lobby.png` | `[x]` |
| 4 | `SC-04` | `/s/attempts/:id` | Học sinh | Phòng thi - Không gian làm bài | `design/screens/SC-04-assessment-workspace.html` | `design/screens/SC-04-assessment-workspace.png` | `[x]` |
| 5 | `SC-04-VAR-OFFLINE` | `/s/attempts/:id#offline` | Học sinh | Phòng thi - Cảnh báo mất mạng & Outbox | `design/screens/SC-04-offline-state.html` | `design/screens/SC-04-offline-state.png` | `[x]` |
| 6 | `SC-05` | `/s/attempts/:id/done` | Học sinh | Nộp bài thành công | `design/screens/SC-05-exam-submitted.html` | `design/screens/SC-05-exam-submitted.png` | `[x]` |
| 7 | `SC-06` | `/s/attempts/:id/result` | Học sinh | Kết quả & Lời giải chi tiết | `design/screens/SC-06-exam-result.html` | `design/screens/SC-06-exam-result.png` | `[x]` |
| 8 | `SC-07` | `/a` | Giáo viên / Admin | Bảng điều khiển Quản trị | `design/screens/SC-07-admin-dashboard.html` | `design/screens/SC-07-admin-dashboard.png` | `[x]` |
| 9 | `SC-08` | `/a/classes` | Giáo viên / Admin | Quản lý Lớp học | `design/screens/SC-08-admin-classes.html` | `design/screens/SC-08-admin-classes.png` | `[x]` |
| 10 | `SC-09` | `/a/classes/:id` | Giáo viên / Admin | Chi tiết Lớp học & Wizard CSV 3 bước | `design/screens/SC-09-class-detail-csv.html` | `design/screens/SC-09-class-detail-csv.png` | `[x]` |
| 11 | `SC-10` | `/a/students` | Giáo viên / Admin | Tra cứu & Danh sách Học sinh | `design/screens/SC-10-admin-students.html` | `design/screens/SC-10-admin-students.png` | `[x]` |
| 12 | `SC-11` | `/a/exams` | Giáo viên / Admin | Quản lý Đề thi | `design/screens/SC-11-admin-exams.html` | `design/screens/SC-11-admin-exams.png` | `[x]` |
| 13 | `SC-12` | `/a/exams/:id/edit` | Giáo viên / Admin | Soạn thảo Đề thi 5 dạng câu | `design/screens/SC-12-exam-editor.html` | `design/screens/SC-12-exam-editor.png` | `[x]` |
| 14 | `SC-13` | `/a/exams/:id/preview` | Giáo viên / Admin | Xem trước Đề thi (Mô phỏng HS) | `design/screens/SC-13-exam-preview.html` | `design/screens/SC-13-exam-preview.png` | `[x]` |
| 15 | `SC-14` | `/a/exams/:id/monitor` | Giáo viên / Admin | Giám sát Trực tiếp phòng thi | `design/screens/SC-14-exam-monitor.html` | `design/screens/SC-14-exam-monitor.png` | `[x]` |
| 16 | `SC-15` | `/a/exams/:id/grading` | Giáo viên / Admin | Chấm bài Tự luận (Dual Pane) | `design/screens/SC-15-exam-grading.html` | `design/screens/SC-15-exam-grading.png` | `[x]` |
| 17 | `SC-16` | `/a/exams/:id/results` | Giáo viên / Admin | Báo cáo Phổ điểm & Xuất CSV | `design/screens/SC-16-exam-analytics.html` | `design/screens/SC-16-exam-analytics.png` | `[x]` |
| 18 | `SC-17` | `/a/settings` | Giáo viên / Admin | Cài đặt Hệ thống Quản trị | `design/screens/SC-17-admin-settings.html` | `design/screens/SC-17-admin-settings.png` | `[x]` |

---

## 3. ĐẶC TẢ CHI TIẾT & PROMPT SINH GIAO DIỆN TỪNG MÀN HÌNH

### SC-01: Đăng nhập Hệ thống (`/login`)
- **Bố cục:** Minimal Centered Card, chiều rộng 420px, giữa màn hình dark canvas `#090D16`.
- **Thành phần:**
  - Header: Logo biểu tượng hình học Toán - Tin kèm chữ **Mathrix** (Không có slogan).
  - Form: Tên đăng nhập (Username), Mật khẩu (Password kèm nút ẩn/hiện mắt).
  - Nút bấm: "Đăng nhập" (Màu Emerald `#10B981`, font chữ đậm, bo góc 8px).
  - Thông báo chân card: "Hệ thống khảo thí nội bộ. Vui lòng liên hệ giáo viên phụ trách để nhận thông tin tài khoản."
- **Prompt Stitch:**
  > Modern academic assessment login screen for "Mathrix" (NO slogan). Centered minimalist card layout on deep navy canvas (#090D16). Card surface #111726 with subtle 1px border #1E293B. Top brand header featuring geometric mathematical logo and bold typography "Mathrix". Input fields for Username and Password with clear labels, focus state glowing emerald ring (#10B981), and eye toggle icon. Primary call-to-action button "Đăng nhập" in solid emerald (#10B981) with crisp text. Security advisory footer at bottom. High contrast WCAG AA compliant.

---

### SC-02: Danh sách Đề thi của tôi (`/s/exams`)
- **Bố cục:** Student Standard Shell (Header chứa Logo Mathrix, Tên học sinh "Nguyễn Văn An", Lớp "12A1", Avatar tối giản, Nút Đăng xuất).
- **Thành phần:**
  - Tiêu đề: "Đề thi của tôi" + Thanh tìm kiếm đề thi + Bộ lọc Môn (Tất cả / Toán học / Tin học).
  - 3 Tab trạng thái: "Đang diễn ra (1)" - "Sắp tới (2)" - "Đã hoàn thành (8)".
  - Bento Card danh sách đề thi:
    - Badge môn: `TOÁN HỌC` (Xanh Emerald) hoặc `TIN HỌC` (Xanh Cyan).
    - Tên đề: "Khảo sát Chuyên đề Tích phân & Hình học Oxyz - Đợt 1".
    - Metadata: Số câu (50 câu), Thời gian (90 phút), Ca thi: 08:00 - 10:00 05/11/2026.
    - Trạng thái & Nút hành động: "Vào thi ngay" (Emerald) hoặc "Xem kết quả" (Secondary button).
- **Prompt Stitch:**
  > Student dashboard for "Mathrix" academic testing system. Dark mode theme (#090D16 canvas, #111726 cards). Clean top navigation bar with Mathrix logo, student info "Nguyễn Văn An - Lớp 12A1", notification badge, and logout. Main content has tabs: "Đang diễn ra (1)", "Sắp tới (2)", "Đã hoàn thành (8)". Bento grid of exam cards with distinct tags: emerald tag "TOÁN HỌC", cyan tag "TIN HỌC". Each card shows exam title, duration (90 min), question count (50 questions), deadline countdown, and a distinct primary CTA "Vào thi ngay". Strict anti-AI slop: no blurry drop-shadows, sharp 1px borders (#1E293B).

---

### SC-03: Giới thiệu Đề & Quy chế thi (`/s/exams/:id`)
- **Bố cục:** Focused Container (max-w 800px, căn giữa).
- **Thành phần:**
  - Breadcrumb: `Đề thi của tôi > Khảo sát Chuyên đề Giải tích & C++17`.
  - Hộp thông tin đề thi: Tiêu đề lớn font `Space Grotesk`, huy hiệu môn thi, giáo viên ra đề.
  - Bento Specs: 3 ô thông số (90 Phút / 50 Câu hỏi / 1 Lần thi duy nhất).
  - Hộp Quy chế thi nghiêm ngặt (Warning border amber `#F59E0B`):
    - 1. Không rời khỏi toàn màn hình hoặc đổi tab trình duyệt (hệ thống ghi log vi phạm).
    - 2. Kết quả được tự động lưu mỗi khi chọn đáp án (có hỗ trợ lưu ngoại tuyến nếu mất mạng).
    - 3. Hệ thống tự động thu bài khi hết giờ đếm ngược.
  - Checkbox xác nhận: `[v] Em đã đọc kỹ và cam kết tuân thủ nghiêm túc quy chế phòng thi`.
  - Cụm nút hành động: Nút `[ Quay lại ]` và nút lớn `[ BẮT ĐẦU LÀM BÀI ]` (Emerald, nổi bật).
- **Prompt Stitch:**
  > Exam lobby and integrity rules screen for "Mathrix". Centered container (max-w 800px) on dark slate canvas (#090D16). Breadcrumb navigation at top. Large exam title "Khảo sát Chuyên đề Giải tích & C++17", instructor name, and subject tag. 3 clean metric badges for Duration (90 phút), Questions (50 câu), Attempts (1 lần). Crucial warning card with amber border (#F59E0B) detailing anti-cheat rules: full-screen enforcement, auto-save mechanism, automatic submission. Mandatory checkbox "Em đã đọc kỹ và cam kết tuân thủ quy chế". Large primary CTA button "BẮT ĐẦU LÀM BÀI" with green glow accent.

---

### SC-04: Phòng thi - Không gian làm bài (`/s/attempts/:id`) - [ĐÃ CÓ]
- **Trạng thái:** Đã lưu trữ tại `design/screens/SC-04-assessment-workspace.html` & `.png`.
- **Thành phần:** Top bar, Countdown Pill 3 trạng thái, Focus Zone câu hỏi (Trắc nghiệm, Đúng/Sai 4 ý, Mã nguồn C++17 syntax highlighted), Bento Question Palette 50 ô bên phải.

---

### SC-04-VAR-OFFLINE: Phòng thi - Cảnh báo mất mạng & Outbox Offline
- **Bố cục:** Giống SC-04 nhưng kích hoạt banner khẩn cấp màu Amber/Red trên thanh Top Bar.
- **Thành phần:**
  - Alert Banner toàn chiều ngang ở đỉnh trang: Icon wifi-off, dòng cảnh báo nổi bật: `[MẤT KẾT NỐI MẠNG] - 2 câu trả lời đang được lưu tạm trên máy. TUYỆT ĐỐI KHÔNG TẢI LẠI TRANG. Hệ thống sẽ tự động đồng bộ ngay khi có mạng.`
  - Hộp Outbox trạng thái nhỏ ở góc dưới: Danh sách các câu đang chờ đồng bộ (`Câu 12: B [Pending]`, `Câu 13: Đ/S [Pending]`).
  - Nút thử kết nối lại thủ công: `[ Thử đồng bộ lại ngay ]`.
- **Prompt Stitch:**
  > Online exam workspace in network interruption (offline fallback) state for "Mathrix". Top alert banner in vibrant amber/red (#EF4444 / #F59E0B) warning: "MẤT KẾT NỐI MẠNG - 2 câu trả lời được lưu tạm trong Outbox. TUYỆT ĐỐI KHÔNG TẢI LẠI TRANG". Floating bottom-right offline sync status widget showing local outbox queue. Examination workspace with KaTeX math equation, timer still counting down locally, question palette showing offline-cached indicators. Industrial precision UI.

---

### SC-05: Nộp bài thành công (`/s/attempts/:id/done`)
- **Bố cục:** Minimal Confirmation Card (max-w 640px, căn giữa).
- **Thành phần:**
  - Icon thành công lớn: Checkmark hình tròn Emerald `#10B981` tinh tế.
  - Tiêu đề: "Nộp bài thi thành công!".
  - Hộp tóm tắt ca thi: Tên bài thi, Mã số bài làm `#ATT-2026-8941`, Thời gian nộp `09:28:15 05/11/2026`, Tổng số câu đã trả lời: `50/50 câu`.
  - Thông báo công bố điểm: "Đề thi này cho phép xem kết quả và lời giải ngay lập tức."
  - 2 nút điều hướng thoát hiểm:
    - Nút phụ: `[ Quay lại danh sách đề thi ]` (Về `/s/exams`).
    - Nút chính: `[ Xem kết quả & Lời giải chi tiết ]` (Chuyển sang `/s/attempts/:id/result`).
- **Prompt Stitch:**
  > Exam submission success confirmation screen for "Mathrix". Centered elegant card layout on dark canvas (#090D16). Glowing emerald checkmark icon in circular badge. Headline "Nộp bài thi thành công!". Submission summary card showing Exam title, Attempt ID #ATT-2026-8941, Submission timestamp, and Answered status (50/50). Dual navigation actions: secondary outline button "Quay lại danh sách đề thi" and primary solid emerald button "Xem kết quả & Lời giải chi tiết". Clean anti-AI slop layout.

---

### SC-06: Kết quả & Lời giải chi tiết (`/s/attempts/:id/result`)
- **Bố cục:** Review Container 1 cột (max-w 900px, căn giữa) + Header cố định.
- **Thành phần:**
  - Header: Logo Mathrix, Tên đề thi, Nút `[ Về danh sách đề thi ]`.
  - Bảng tổng kết điểm (Score Hero Card):
    - Điểm số to lớn font `Space Grotesk`: `9.20 / 10.0`.
    - Số câu đúng: `46/50`, Sai: `4`, Chưa làm: `0`. Thời gian làm bài: `74 phút 12 giây`.
  - Bộ lọc xem câu hỏi: `[ Tất cả (50) ]` - `[ Câu đúng (46) ]` - `[ Câu sai (4) ]`.
  - Danh sách Accordion lời giải từng câu:
    - Câu 1 (Đúng - Badge xanh): Đề bài Toán KaTeX + Lời giải chi tiết từng bước.
    - Câu 2 (Sai - Badge đỏ): Đáp án bạn chọn (B), Đáp án đúng (C) tô màu nổi bật, kèm khối code giải thích thuật toán C++17 có highlight cú pháp.
- **Prompt Stitch:**
  > Comprehensive exam results and solution breakdown screen for "Mathrix". Dark mode theme (#090D16). Top score card displaying overall score "9.20 / 10.0" in large Space Grotesk font, breakdown metrics (46 correct, 4 incorrect, duration 74m 12s). Filter tabs: All (50), Correct (46), Incorrect (4). Expandable solution cards with KaTeX mathematical formulas, clear indication of student's choice vs correct answer, and syntax-highlighted C++ code blocks explaining the algorithm. Clean, high-legibility typographic hierarchy.

---

### SC-07: Bảng điều khiển Quản trị (`/a`)
- **Bố cục:** Admin Sidebar Shell (Sidebar trái cố định 260px: Logo Mathrix, Menu Đề thi, Lớp học, Học sinh, Chấm thi, Cài đặt; Khu vực nội dung chính bên phải).
- **Thành phần:**
  - Top Bar: Tìm kiếm nhanh toàn hệ thống, Thông báo chuông, Profile Quản trị viên / Giáo viên "Thầy Trần Minh Đức".
  - Tiêu đề: "Tổng quan Quản trị".
  - Cụm 4 Metric Cards:
    - Tổng số học sinh: `342` (+12 tháng này).
    - Đề thi đang mở: `3` (Đang có 78 học sinh làm bài).
    - Ca thi đã hoàn thành: `1,280`.
    - Tỷ lệ hoàn thành đúng hạn: `98.4%`.
  - Bảng ca thi đang diễn ra (Live Monitoring Shortcut): Bảng hiển thị 3 phòng thi đang chạy, tiến độ làm bài, nút `[ Giám sát trực tiếp ]`.
  - Quick Actions: `[ + Soạn đề thi mới ]`, `[ + Nhập danh sách lớp CSV ]`.
- **Prompt Stitch:**
  > Admin and teacher overview dashboard for "Mathrix". Persistent left sidebar with Mathrix branding and navigation links (Dashboard, Đề thi, Lớp học, Học sinh, Chấm thi, Cài đặt). Top app bar with search and teacher profile "Thầy Trần Minh Đức". 4 key metric cards: Total Students (342), Active Exams (3 with live badge), Completed Submissions (1,280), On-time Completion Rate (98.4%). Live exam sessions table showing active rooms with progress bars and "Giám sát trực tiếp" quick buttons. Emerald accent #10B981, dark palette #090D16.

---

### SC-08: Quản lý Lớp học (`/a/classes`)
- **Bố cục:** Admin Sidebar Shell + Main Table View.
- **Thành phần:**
  - Header: Tiêu đề "Quản lý Lớp học", Thanh tìm kiếm lớp, Bộ lọc Khối (Khối 10 / Khối 11 / Khối 12), Nút `[ + Tạo lớp học mới ]`.
  - Bảng dữ liệu lớp học:
    - Cột: Mã lớp, Tên lớp, Khối, Sĩ số (ví dụ: `42 học sinh`), Giáo viên chủ nhiệm, Đề thi đã gán, Hành động (`[ Chi tiết & CSV ]`, `[ Sửa ]`, `[ Đổi mã ]`).
  - Phân trang dưới đáy bảng: `Trang 1 / 4` (Hiển thị 10 lớp / trang).
- **Prompt Stitch:**
  > Class management interface for "Mathrix" admin portal. Dark theme. Left navigation sidebar. Main area features page header "Quản lý Lớp học", search input, grade level dropdown filter, and primary button "+ Tạo lớp học mới". Data table with sharp 1px borders (#1E293B) listing classes (Mã lớp, Tên lớp, Khối, Sĩ số, Giáo viên phụ trách, Actions). Clean typography with tabular numbers, pagination bar at bottom.

---

### SC-09: Chi tiết Lớp học & Wizard nhập CSV 3 bước (`/a/classes/:id`)
- **Bố cục:** Admin Shell + Tabbed Container + Modal Wizard nhập CSV 3 bước đè trên nền mờ.
- **Thành phần:**
  - Chi tiết lớp: `Lớp 12 Tin Chuyên` (Sĩ số 35 học sinh).
  - Modal Wizard 3 bước:
    - Step 1: `Tải lên file CSV` (Khu vực kéo thả file `.csv`, link tải file mẫu `mau_danh_sach_mathrix.csv`).
    - Step 2: `Xem trước & Khớp cột` (Bảng 5 hàng đầu tiên, khớp cột Tên, Ngày sinh, Mã học sinh, Tên đăng nhập).
    - Step 3: `Xác nhận & Hoàn tất` (Thống kê: 35 dòng hợp lệ, 0 dòng lỗi, nút `[ Nhập 35 học sinh vào lớp ]`).
- **Prompt Stitch:**
  > Class details and 3-step CSV student import wizard modal for "Mathrix". Background displays class roster "Lớp 12 Tin Chuyên". Centered 3-step wizard modal on dark glass overlay: Step indicator (1. Tải lên -> 2. Khớp dữ liệu -> 3. Xác nhận). Drag-and-drop zone for CSV files with download template link. Preview table mapping columns (Mã HS, Họ và tên, Ngày sinh, Tên đăng nhập). Validation badge "35 dòng hợp lệ, 0 lỗi". Primary confirm CTA button in emerald #10B981.

---

### SC-10: Tra cứu & Danh sách Học sinh (`/a/students`)
- **Bố cục:** Admin Shell + Data Grid.
- **Thành phần:**
  - Bộ lọc nâng cao: Tìm kiếm theo họ tên/mã học sinh, Dropdown chọn Lớp, Trạng thái (Đang học / Đã khóa).
  - Bảng học sinh:
    - Cột: Avatar chữ cái, Mã HS (`HS-2026-012`), Họ và tên (`Lê Hoàng Nam`), Lớp (`12A1`), Điểm trung bình (`8.75`), Số bài thi đã làm (`14`), Trạng thái tài khoản (Badge xanh Đang hoạt động), Thao tác (`[ Đặt lại mật khẩu ]`, `[ Xem lịch sử thi ]`).
- **Prompt Stitch:**
  > Student directory and lookup table for "Mathrix" administrator portal. Dark UI (#090D16 canvas, #111726 surface). Filter bar with student name/code search, class filter, and account status toggle. Comprehensive data table displaying Avatar, Student ID, Full Name, Class, Average Score (with color-coded badge), Exams Completed, and Action buttons (Reset password, View exam history). Crisp 1px borders, Space Grotesk numerals.

---

### SC-11: Quản lý Đề thi (`/a/exams`)
- **Bố cục:** Admin Shell + Grid/Table switchable layout.
- **Thành phần:**
  - Header: "Quản lý Đề thi", Nút `[ + Tạo đề thi mới ]`, Nút `[ Nhập đề từ DOCX/LaTeX ]`.
  - 4 Tab trạng thái: `Tất cả (24)` - `Bản nháp (4)` - `Đã xuất bản (8)` - `Đang diễn ra (2)` - `Đã đóng (10)`.
  - Danh sách đề thi dạng thẻ Bento:
    - Tag môn: Toán / Tin.
    - Tiêu đề đề thi, Thời lượng, Số lượng câu, Lớp được gán (`12A1, 12A2`).
    - Nút thao tác nhanh: `[ Soạn câu hỏi ]`, `[ Xem trước ]`, `[ Giám sát ca thi ]`, `[ Thống kê phổ điểm ]`.
- **Prompt Stitch:**
  > Exam management dashboard for "Mathrix". Dark theme. Top bar with primary action "+ Tạo đề thi mới" and secondary "+ Nhập từ DOCX/LaTeX". Status tabs: Tất cả, Bản nháp, Đã xuất bản, Đang diễn ra (with glowing live dot), Đã đóng. Bento card list of exams showing Subject tag (Math/CS), title, duration, assigned classes, and contextual action buttons (Edit, Preview, Live Monitor, Analytics). High contrast emerald accents.

---

### SC-12: Soạn thảo Đề thi 5 dạng câu (`/a/exams/:id/edit`)
- **Bố cục:** Fullscreen Split Editor (Cột trái: Danh sách 50 câu hỏi; Cột giữa: Form soạn câu hỏi; Cột phải: Xem trước KaTeX / Code thời gian thực).
- **Thành phần:**
  - Header: Tên đề thi, Nút chuyển đổi 5 dạng câu hỏi:
    1. Trắc nghiệm 4 lựa chọn (A, B, C, D)
    2. Đúng / Sai 4 ý mệnh đề
    3. Điền số (Trả lời ngắn)
    4. Bài tập Lập trình C++ (Mã nguồn + Testcase)
    5. Tự luận nộp file ảnh / PDF
  - Thanh công cụ gõ công thức Toán học KaTeX (`\int`, `\frac`, `\sqrt`, `\lim`) và chèn code block C++.
  - Xem trước tức thì (Live Preview) câu hỏi giống hệt như màn hình thi của học sinh.
  - Nút `[ Lưu bản nháp ]` và `[ Xuất bản đề thi ]`.
- **Prompt Stitch:**
  > Fullscreen advanced exam authoring studio for "Mathrix" supporting 5 question types. 3-column split layout: Left question navigator (list of 50 questions), Center markdown & math formula editor with KaTeX toolbar (integrals, fractions, limits) and C++ code block insert, Right real-time live preview showing rendered question as seen by students. Dropdown to toggle question archetype (Multiple choice 4-options, True/False 4-statements, Numeric short-answer, C++ code execution, File upload essay). Emerald accent #10B981, dark slate palette.

---

### SC-13: Xem trước Đề thi (`/a/exams/:id/preview`)
- **Bố cục:** Assessment Workspace Simulated (Mô phỏng trải nghiệm thi của học sinh nhưng có Banner quản trị màu tím/cyan ở đỉnh).
- **Thành phần:**
  - Top Banner: `[ CHẾ ĐỘ XEM TRƯỚC DÀNH CHO GIÁO VIÊN - Không tính điểm ]`, Nút `[ Quay lại chỉnh sửa đề ]`.
  - Màn hình làm bài hoàn chỉnh với câu hỏi Toán KaTeX và Tin học C++, đồng hồ chạy thử nghiệm, palette câu hỏi 50 ô.
  - Cho phép giáo viên click chọn đáp án thử để kiểm tra tính logic và đáp án đúng.
- **Prompt Stitch:**
  > Exam preview simulator for "Mathrix" teachers. Top banner indicating "CHẾ ĐỘ XEM TRƯỚC DÀNH CHO GIÁO VIÊN - Không tính điểm" with "Quay lại chỉnh sửa" button. Complete assessment workspace identical to student interface (KaTeX math rendering, C++ code syntax highlighting, countdown timer simulator, and interactive 50-question bento palette). Dark mode #090D16.

---

### SC-14: Giám sát Trực tiếp phòng thi (`/a/exams/:id/monitor`)
- **Bố cục:** Realtime Bento Matrix (Giám sát ca thi thời gian thực).
- **Thành phần:**
  - Header: Tên đề thi "Khảo sát Chuyên đề Giải tích", Thời gian ca thi còn lại: `42:15`, Số thí sinh: `45/45 Đang thi`.
  - Bảng cảnh báo bất thường: Danh sách thí sinh có cảnh báo (ví dụ: `Trần Văn B: Rời tab 2 lần`, `Lê Thị C: Mất mạng 1 phút trước`).
  - Ma trận 45 ô thí sinh (Student Grid Cards):
    - Mỗi ô hiển thị: Tên học sinh, Tiến độ (`38/50 câu`), Chấm trạng thái (Xanh lá: Đang gõ làm bài; Vàng: Rời tab; Đỏ: Mất kết nối; Xám: Đã nộp bài).
  - Tác vụ khẩn cấp của giáo viên: Nút `[ + Cộng 5 phút bù giờ ]`, `[ Thu bài cả phòng ]`.
- **Prompt Stitch:**
  > Real-time live exam proctoring monitor for "Mathrix" teachers. Top status bar showing remaining exam time, live student count (45/45 active), and emergency teacher actions ("+ Cộng 5 phút bù giờ", "Thu bài cả lớp"). Central bento matrix of 45 student status cards: avatar, name, current question progress (e.g. 38/50), pulse status dot (green: active, amber: unfocused/tab switched, red: disconnected, gray: submitted). Dedicated alert panel listing recent integrity warnings. Dark industrial control center aesthetic.

---

### SC-15: Chấm bài Tự luận (`/a/exams/:id/grading`)
- **Bố cục:** Dual Pane Grading Workspace (Hai cột song song).
- **Thành phần:**
  - Cột trái (Bài nộp của thí sinh): Trình xem bài làm tự luận (Ảnh chụp bài làm Toán / file PDF / Mã nguồn C++ nộp kèm kết quả chạy testcase).
  - Cột phải (Bảng chấm điểm & Rubric):
    - Danh sách tiêu chí chấm điểm (Ý a: 1.0đ, Ý b: 1.5đ, Ý c: 1.5đ).
    - Ô nhập điểm nhanh (font `JetBrains Mono` lớn).
    - Hộp nhận xét của giáo viên.
    - Cụm nút: `[ Lưu & Chấm bài tiếp theo (Enter) ]`, `[ Bỏ qua ]`.
- **Prompt Stitch:**
  > Dual-pane exam grading workstation for "Mathrix" teachers. Left pane: student submission viewer displaying math handwritten scan/PDF and C++ source code with testcase pass/fail results. Right pane: grading rubric with individual criteria point inputs (font JetBrains Mono), total score tally, rich feedback comment box, and quick keyboard-driven navigation buttons ("Lưu & Chấm tiếp theo [Enter]"). Dark theme with clean borders.

---

### SC-16: Báo cáo Phổ điểm & Xuất CSV (`/a/exams/:id/results`)
- **Bố cục:** Analytics Dashboard.
- **Thành phần:**
  - Header: Tên đề thi, Lớp `12 Tin`, Nút `[ Xuất bảng điểm CSV ]`, Nút `[ In báo cáo PDF ]`.
  - 4 Thẻ chỉ số tổng kết: Điểm trung bình (`7.82`), Điểm cao nhất (`10.0`), Điểm thấp nhất (`4.2`), Độ lệch chuẩn (`1.15`).
  - Biểu đồ phổ điểm (Histogram): Cột điểm từ 0 đến 10 với dải màu Emerald.
  - Bảng phân tích câu hỏi khó nhất: Top 5 câu hỏi có tỷ lệ sai cao nhất (cần chữa bài trên lớp).
  - Bảng điểm danh sách học sinh: Họ tên, Điểm trắc nghiệm, Điểm tự luận, Tổng điểm, Xếp loại.
- **Prompt Stitch:**
  > Comprehensive exam analytics and score distribution dashboard for "Mathrix". Dark theme. Header with "Xuất bảng điểm CSV" and "In báo cáo PDF" buttons. Top summary statistics: Average Score (7.82), High Score (10.0), Low Score (4.2), Standard Deviation (1.15). Prominent score distribution histogram chart with emerald bars. Table analyzing most difficult questions (highest error rates) with KaTeX formulas. Full student grade ranking table with exportable columns.

---

### SC-17: Cài đặt Hệ thống Quản trị (`/a/settings`)
- **Bố cục:** Admin Form Layout (Tabs cài đặt: Chung / Lưu trữ & Dữ liệu / Bảo mật & Phân quyền).
- **Thành phần:**
  - Tab Chung: Tên trung tâm `Mathrix`, Múi giờ `GMT+7 (Hà Nội)`, Chế độ mặc định đề thi.
  - Tab Lưu trữ & Backup: Đường dẫn sao lưu dữ liệu, trạng thái kết nối MinIO / S3, nút `[ Sao lưu cơ sở dữ liệu ngay ]`.
  - Tab Bảo mật: Đổi mật khẩu tài khoản quản trị (Yêu cầu mật khẩu hiện tại, mật khẩu mới $\ge 12$ ký tự, không dùng mật khẩu mặc định), Cấu hình thời gian hết hạn phiên làm việc (Session Timeout: 120 phút).
  - Nút `[ Lưu thay đổi cấu hình ]`.
- **Prompt Stitch:**
  > Administrative settings and security preferences page for "Mathrix". Dark mode interface. Tab navigation: General Settings, Storage & Backups, Security & Access. Form controls for center branding ("Mathrix"), timezone (GMT+7), MinIO/S3 object storage connection status with "Sao lưu ngay" trigger button, administrator password change form with strength indicator, and session timeout slider. Primary green save button "Lưu thay đổi cấu hình".

---

## 4. CƠ CHẾ VÒNG LẶP SINH MÀN HÌNH & KIỂM THỬ TỰ ĐỘNG (`stitch-loop`)

Hệ thống quản lý tiến độ thực thi qua script điều phối `scripts/stitch_batch_runner.py`:
1. **Kiểm tra trạng thái (`TC-1.3-02`):** Duyệt qua bảng danh mục mục 2, nếu một màn hình đã có đủ cả hai file `.html` và `.png` trong `design/screens/`, script tự động bỏ qua, không sinh trùng lặp.
2. **Khả năng tạm dừng & khôi phục (`TC-1.3-03`):** Tiến trình ghi nhận checkpoint sau từng màn hình hoàn tất. Khi tiến trình bị dừng hoặc khởi động lại, script tiếp tục ngay tại màn hình chưa hoàn thành đầu tiên.
3. **Xử lý hạn mức & Ngoại lệ MCP (`TC-1.3-04`):** Nếu Stitch MCP trả về lỗi Quota Limit hoặc kết nối, script dừng an toàn, ghi nhận trạng thái `BLOCKED_QUOTA` và thông báo rõ ràng cho kỹ sư, không gây crash dữ liệu.
4. **Kiểm tra tính đồng nhất Design System (`TC-1.3-05`):** Mọi mã HTML sinh ra được kiểm tra tự động xem có sử dụng đúng bảng màu Emerald `#10B981`, nền `#090D16` / `#111726` và các font chữ quy định trong `DESIGN.md`.
