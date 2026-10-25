
# KẾ HOẠCH TRIỂN KHAI: HỆ THỐNG QUIZ NỘI BỘ MÔN TOÁN – TIN

> Căn cứ: `QUIZ.md` v1.0 (21/10/2026) · Kế hoạch v1.0 · Bắt đầu dự kiến: 22/10/2026 · Thời lượng: ~4–5 tuần bán thời gian (≈ 15–20 giờ/tuần)
> Mỗi bước nhỏ gồm 4 phần: **Yêu cầu cần đạt → Cách thức triển khai → Test case (≥ 7) → Tiêu chí hoàn thành (DoD)**.
> Quy ước test: `T<bước>.<số>`; loại: **[U]** unit, **[I]** integration/API, **[E]** end-to-end, **[M]** thủ công, **[S]** bảo mật, **[P]** hiệu năng.

---

## PHẦN A. TỔNG QUAN QUẢN TRỊ DỰ ÁN

### A.1 Cấu trúc phân rã công việc (WBS) và lịch

| Giai đoạn | Nội dung                                      | Tuần       | Cột mốc (Milestone)                                 |
| ----------- | ---------------------------------------------- | ----------- | ----------------------------------------------------- |
| P0          | Thiết kế UI/UX với AI & Stitch              | 1           | M0: Giao diện trực quan trên Stitch được duyệt |
| P1          | Khởi tạo hạ tầng & khung dự án           | 1           | M1: FE–BE–DB nối thông, CI xanh                   |
| P2          | Tài khoản, lớp, học sinh                   | 2           | M2: Giáo viên quản lý được lớp                |
| P3          | Soạn đề (LaTeX, ảnh, 5 dạng câu)         | 2–3        | M3: Tạo được 1 đề hoàn chỉnh                  |
| P4          | Làm bài, autosave, chống gián đoạn       | 3           | M4: Học sinh làm trọn bài, chịu gián đoạn     |
| P5          | Chấm điểm, giám sát, công bố, xuất CSV | 4           | M5: Vòng đời đề khép kín                       |
| P6          | Kiểm thử chất lượng, bảo mật, tải      | 4–5        | M6: 10 kịch bản nghiệm thu đạt                   |
| P7          | Triển khai hosting, pilot, go-live            | 5           | M7: Chạy thử với lớp thật                        |
| P8          | Vận hành & đóng dự án                    | sau go-live | M8: Bàn giao + tài liệu                            |

**Đường găng (critical path):** P1 → P2.1 (auth) → P3.1 (model đề) → P4 (làm bài) → P5.1–5.2 (chấm) → P6 → P7. P0 chạy song song với P1 (không chặn). P4 là phần rủi ro cao nhất: làm sớm, test kỹ, không dồn cuối.

### A.2 Vai trò (dự án cá nhân/nhóm nhỏ)

| Vai trò                    | Trách nhiệm                                              | Ghi chú                                  |
| --------------------------- | ---------------------------------------------------------- | ----------------------------------------- |
| Product owner (giáo viên) | Duyệt prototype, trả lời mục 15 của spec, nghiệm thu | Bạn                                      |
| Dev full-stack              | Code BE + FE                                               | Bạn / thêm 1 người                    |
| QA                          | Viết test, chạy nghiệm thu                              | Có thể kiêm; nhờ 2–3 học sinh pilot |

### A.3 Quyết định cần chốt TRƯỚC khi code (đóng mục 15 spec)

| # | Câu hỏi                              | Mặc định đề xuất                              | Hạn chốt |
| - | -------------------------------------- | --------------------------------------------------- | ---------- |
| 1 | Chấm Đúng/Sai                       | Hỗ trợ cả 3 chế độ, mặc định `thpt`      | Cuối P0   |
| 2 | MCQ nhiều đáp án đúng            | Chỉ chọn 1 (MVP)                                  | Cuối P0   |
| 3 | Học sinh nhiều lớp                  | Cho phép                                           | Cuối P0   |
| 4 | Hết `close_at`                      | `deadline = min(start+duration, close_at)`        | Cuối P0   |
| 5 | Nhập `.tex` nguyên file            | Để V2                                             | Cuối P0   |
| 8 | Nhiều giáo viên phân quyền riêng | MVP 1 admin chung                                   | Cuối P0   |
| 9 | Cold start                             | Chấp nhận + cron ping; đánh giá lại sau pilot | Trước P7 |

### A.4 Quy trình làm việc & chất lượng

- **Git:** nhánh `main` (luôn deploy được), `feat/<tên>`; commit theo Conventional Commits; PR nhỏ (<400 dòng) có checklist.
- **CI (GitHub Actions):** backend `ruff` + `mypy` + `pytest` (Postgres service container); frontend `eslint` + `tsc --noEmit` + `vitest` + build. PR không xanh không merge.
- **Definition of Done chung:** code review xong; test mới đạt; không giảm coverage; cập nhật tài liệu API (`/docs`); migration có `downgrade`; không có secret trong repo.
- **Quản lý thay đổi:** thay đổi phạm vi ghi vào `CHANGELOG.md`, mọi tính năng V2 không chen vào MVP trừ khi đánh đổi bằng tính năng khác.

### A.5 Sổ rủi ro vận hành dự án

| Rủi ro                            | Xác suất | Tác động | Giảm thiểu                                                      | Chủ sở hữu |
| ---------------------------------- | ---------- | ----------- | ----------------------------------------------------------------- | ------------- |
| Server free ngủ đúng giờ thi   | Cao        | Cao         | Cron ping, nút làm nóng, lazy finalize, phương án trả phí | Dev           |
| Quá tải phạm vi (feature creep) | Cao        | TB          | Khóa MVP/V2, review hằng tuần                                  | PO            |
| Lỗi thời gian/múi giờ          | TB         | Cao         | Lưu UTC, test freeze-time, dùng giờ server                     | Dev           |
| Rò rỉ đáp án                  | Thấp      | Rất cao    | Schema tách, test quét tự động                               | Dev           |
| Gói free đổi điều kiện       | TB         | TB          | Abstraction Storage, Postgres/S3 chuẩn                           | Dev           |
| Công thức LaTeX sai hàng loạt  | TB         | TB          | Preview, báo lỗi tại chỗ, xem trước như học sinh          | Dev           |

---

# PHẦN B. KẾ HOẠCH CHI TIẾT THEO GIAI ĐOẠN

---

## P0. THIẾT KẾ UI/UX VỚI AI & STITCH (Tuần 1)

> **Nguyên tắc thực hiện P0:** Hoàn toàn dùng AI (Impeccable) và Stitch MCP để thiết kế và sinh giao diện trực quan; **tuyệt đối không lập tài liệu kỹ thuật** (SRS, tài liệu phân tích luồng phức tạp). Trước khi tạo giao diện, AI sẽ hỏi trực tiếp người dùng về giao diện tham khảo và các yêu cầu customize đặc thù.

### Bước 0.1 – Khảo sát giao diện tham khảo & thu thập yêu cầu customize từ người dùng

**Yêu cầu cần đạt**

- Thu thập đầy đủ thông tin/ảnh/đường dẫn giao diện tham khảo (reference UI) mà người dùng yêu thích (ví dụ: phong cách thi trắc nghiệm hiện đại, tối giản, gamified, hoặc học đường chuẩn mực).
- Xác định toàn bộ yêu cầu đặc thù muốn customize: màu sắc chủ đạo, phong cách typography, bố cục hiển thị trên Mobile (1 câu/màn hình vs cuộn dọc), vị trí cố định của đồng hồ & chỉ báo lưu, trải nghiệm thanh điều hướng câu hỏi, cách hiển thị công thức LaTeX / khối code môn Tin.
- Thống nhất các quyết định UX cốt lõi (A.3) trực tiếp với người dùng qua trao đổi tương tác ngắn gọn; không tạo file spec hay tài liệu kỹ thuật dài dòng.

**Cách thức triển khai**

1. Trợ lý AI đặt câu hỏi trực tiếp cho người dùng qua chat/modal để lấy ý kiến về:
   - Các web/app làm bài kiểm tra hoặc sản phẩm số có phong cách giao diện người dùng đánh giá cao (ảnh chụp màn hình, đường dẫn tham khảo, hoặc trường phái thiết kế mong muốn).
   - Tone màu nhận diện thương hiệu (xanh học đường, tím công nghệ, dark/light mode hoặc bảng màu tùy chỉnh).
   - Các điểm nhấn tương tác đặc thù (font chữ Toán - Tin, dạng thẻ bài thi, hiển thị đếm ngược nguy cấp, hiệu ứng nộp bài).
2. Lắng nghe và tổng hợp nhanh thành bộ chỉ dẫn phong cách (Style Guidance & Customization Brief) dạng gạch đầu dòng súc tích, phục vụ trực tiếp cho việc viết prompt sinh giao diện trên Stitch.
3. Chốt nhanh các câu hỏi nghiệp vụ trong A.3 với giáo viên (chế độ chấm TF, MCQ 1 đáp án, kết thúc giờ thi). Không tạo file spec hoặc tài liệu kỹ thuật dài dòng.

**Test case (kiểm tra yêu cầu & định hướng)**

| ID     | Loại | Kịch bản                                                                          | Kết quả mong đợi                                                                                  |
| ------ | ----- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| T0.1.1 | [M]   | Trao đổi về giao diện tham khảo                                                | Người dùng cung cấp hoặc đồng thuận với phong cách thiết kế tham khảo được đề xuất |
| T0.1.2 | [M]   | Thu thập yêu cầu customize về màu sắc & font chữ                             | Xác định rõ bảng màu chính, màu trạng thái (lưu/nguy cấp) và kiểu font chữ Toán - Tin |
| T0.1.3 | [M]   | Thu thập yêu cầu customize về bố cục màn hình làm bài trên điện thoại | Chốt phương án hiển thị (1 câu/màn hình, thanh điều hướng đáy hoặc ngăn kéo drawer) |
| T0.1.4 | [M]   | Thu thập yêu cầu customize về trải nghiệm soạn đề của giáo viên         | Xác định rõ cách bố trí 2 cột / 3 cột soạn thảo LaTeX và vị trí xem trước trực tiếp |
| T0.1.5 | [M]   | Rà soát nhánh bất thường (mất mạng, hết giờ, server ngủ)                 | Người dùng thống nhất vị trí và nội dung hiển thị của banner trấn an                     |
| T0.1.6 | [M]   | Kiểm tra tiêu chí "không tài liệu kỹ thuật dài dòng"                      | Không tạo file spec/SRS cồng kềnh; brief nằm gọn trong bộ prompt sinh giao diện               |
| T0.1.7 | [M]   | Chốt các quyết định A.3 mục 15 spec                                           | 100% câu hỏi cốt lõi được người dùng xác nhận trực tiếp                                 |

**DoD:** Người dùng xác nhận hài lòng với định hướng giao diện tham khảo và danh sách các yêu cầu customize; sẵn sàng tạo dự án trên Stitch.

---

### Bước 0.2 – Khởi tạo dự án Stitch & sinh Design System bằng AI (Impeccable + Stitch)

**Yêu cầu cần đạt**

- Tạo thành công dự án mới trên nền tảng Stitch thông qua MCP tool (`create_project`).
- Thiết lập hệ thống Design System chuẩn mực (màu sắc, typography, component style) dựa trên các yêu cầu customize đã chốt ở Bước 0.1 và các nguyên tắc thiết kế của `impeccable`.
- Sẵn sàng `designSystemId` để tái sử dụng xuyên suốt cho toàn bộ các màn hình, đảm bảo tính đồng bộ thị giác tuyệt đối giữa màn hình Học sinh và Giáo viên.

**Cách thức triển khai**

1. Kích hoạt bộ công cụ `impeccable` để chuẩn hóa các thông số: thang màu (primary, danger, warning, neutral), kiểu chữ tiếng Việt và công thức Toán KaTeX, tỷ lệ khoảng cách (spacing), bán kính bo góc (border radius).
2. Gọi công cụ Stitch MCP `create_project` để tạo dự án mới (ví dụ: `Quiz Toan Tin`).
3. Khởi tạo Design System trên Stitch (tự động thông qua màn hình đầu tiên hoặc gọi `create_design_system_from_design_md`), gắn liền với các đặc thù của môn Toán – Tin.
4. Kiểm tra mã định danh `designSystemId` được cấp từ Stitch để chuẩn bị áp dụng cho các bước sinh màn hình tiếp theo.

**Test case (kiểm tra Design System trên Stitch)**

| ID     | Loại | Kịch bản                                                             | Kết quả mong đợi                                                                               |
| ------ | ----- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| T0.2.1 | [M]   | Gọi lệnh tạo project trên Stitch                                   | Dự án được tạo thành công, trả về `projectId` hợp lệ                                 |
| T0.2.2 | [M]   | Kiểm tra tính nhất quán của bảng màu trên Stitch               | Màu sắc hiển thị đúng tone đã customize (primary, alert, success, warning)                 |
| T0.2.3 | [M]   | Kiểm tra typography cho tiếng Việt và công thức Toán            | Font chữ hiển thị rõ ràng, không lỗi dấu tiếng Việt, bố cục công thức hài hòa      |
| T0.2.4 | [M]   | Kiểm tra độ tương phản màu sắc (WCAG AA)                       | Tương phản chữ trên nền đạt chuẩn ≥ 4.5:1, các nút bấm nổi bật dễ nhận biết      |
| T0.2.5 | [M]   | Kiểm tra các thành phần cốt lõi (Buttons, Badges, Inputs, Cards) | Các component có style thống nhất về bo góc, viền và đổ bóng                            |
| T0.2.6 | [M]   | Tái sử dụng `designSystemId` cho project                          | API Stitch nhận diện đúng Design System và áp dụng xuyên suốt                             |
| T0.2.7 | [M]   | Kiểm tra tính sẵn sàng cho cả 2 môi trường Mobile và Desktop  | Các biến thể kích thước chữ và khoảng cách thích ứng tốt trên cả 2 loại màn hình |

**DoD:** Dự án và Design System trên Stitch được khởi tạo hoàn tất; người dùng xem trước và duyệt phong cách tổng quan.

---

### Bước 0.3 – Sinh giao diện trực quan phía HỌC SINH trên Stitch (AI Screen Generation & Variants)

**Yêu cầu cần đạt**

- Tạo trực quan toàn bộ 6 màn hình phía học sinh trên Stitch (`deviceType: MOBILE` và `DESKTOP`), tái sử dụng Design System của dự án:
  1. Đăng nhập (gọn nhẹ, chỉ username + password)
  2. Danh sách đề thi của lớp (kèm các trạng thái: Chưa làm, Đang làm, Đã nộp, Đã công bố kết quả)
  3. Giới thiệu đề thi (thời lượng, số câu, quy định, nút Bắt đầu)
  4. Màn hình Làm bài thi trọng tâm (thanh Timer đếm ngược cố định, chỉ báo SaveIndicator 3 trạng thái, lưới điều hướng câu hỏi, 5 dạng câu hỏi: MCQ, TF, chữ, số, file upload)
  5. Hộp thoại xác nhận nộp bài (thống kê câu chưa làm, câu đánh dấu xem lại)
  6. Màn hình Đã nộp bài (thông báo an tâm, không hé lộ điểm/đáp án) & Màn hình Kết quả (khi giáo viên công bố)
- Thiết kế trực quan các trạng thái đặc biệt: Banner mất kết nối mạng, Banner "Đang đánh thức máy chủ", Thông báo hết giờ tự nộp.
- Tạo các biến thể layout (`generate_variants`) trên Stitch cho màn hình làm bài để người dùng chọn trải nghiệm tốt nhất trên điện thoại.

**Cách thức triển khai**

1. Soạn prompt chi tiết cho từng màn hình học sinh dựa trên đặc tả `QUIZ.md` và yêu cầu customize đã chốt ở Bước 0.1.
2. Gọi `generate_screen_from_text` trên Stitch MCP với `projectId` và `designSystemId` đã tạo.
3. Với màn hình trọng tâm "Làm bài thi trên điện thoại", gọi `generate_variants` để tạo 2–3 phương án bố cục khác nhau (vị trí timer, thanh chuyển câu, dạng bảng Đúng/Sai).
4. Gửi link xem trực quan màn hình và ảnh mockup cho người dùng đánh giá.
5. Tiếp thu phản hồi và gọi `edit_screens` trên Stitch để tinh chỉnh theo ý người dùng nếu cần.

**Test case (kiểm tra giao diện Học sinh trên Stitch)**

| ID     | Loại | Kịch bản                                                           | Kết quả mong đợi                                                                                           |
| ------ | ----- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| T0.3.1 | [M]   | Xem trực quan màn hình Đăng nhập trên điện thoại 360 px    | Giao diện tối giản, tập trung vào ô nhập username/password, bàn phím không che form                  |
| T0.3.2 | [M]   | Xem màn hình Danh sách đề thi                                   | Thể hiện rõ các tag trạng thái (chưa làm, đã nộp, điểm số nếu được mở), nút bấm rõ ràng |
| T0.3.3 | [M]   | Xem màn hình Giới thiệu đề thi                                 | Bố cục thông tin rõ ràng: thời gian, số lượng câu, lưu ý chống gian lận, nút Bắt đầu to      |
| T0.3.4 | [M]   | Xem màn hình Làm bài thi (Mobile & Desktop)                      | Timer và SaveIndicator luôn nổi bật ở đỉnh; các dạng câu MCQ, TF, số, chữ hiển thị sắc nét     |
| T0.3.5 | [M]   | Kiểm tra biến thể lưới điều hướng câu hỏi                 | Có ít nhất 2 biến thể bố cục (dạng thanh trượt ngang vs dạng modal/drawer) để chọn               |
| T0.3.6 | [M]   | Xem banner cảnh báo mất mạng & đang đánh thức máy chủ      | Banner xuất hiện vị trí trang trọng, không che lấp nội dung câu hỏi hoặc nút trả lời             |
| T0.3.7 | [M]   | Xem màn hình Đã nộp bài                                        | Tuyệt đối không để lộ điểm số/đáp án; câu từ mang tính trấn an học sinh                      |
| T0.3.8 | [M]   | Xem màn hình Kết quả thi (chế độ `score_only` và `full`) | Hiển thị điểm rõ ràng; ở chế độ full có lời giải LaTeX chi tiết từng câu                       |

**DoD:** Toàn bộ luồng màn hình học sinh trên Stitch được người dùng duyệt trực quan và chốt biến thể ưng ý.

---

### Bước 0.4 – Sinh giao diện trực quan phía GIÁO VIÊN trên Stitch & duyệt Prototype (M0)

**Yêu cầu cần đạt**

- Tạo trực quan toàn bộ các màn hình chính phía giáo viên trên Stitch (`deviceType: DESKTOP`):
  1. Bảng điều khiển (Dashboard tổng quan: đề sắp thi, bài cần chấm tay, thống kê nhanh)
  2. Quản lý lớp & học sinh (danh sách lớp, danh sách học sinh, modal nhập CSV, reset mật khẩu)
  3. Trình soạn thảo đề thi Toán - Tin (bố cục đa cột: danh sách câu hỏi kéo thả, khung soạn thảo Markdown/LaTeX có nút chèn ảnh, khung xem trước KaTeX trực tiếp, cấu hình điểm và đáp án)
  4. Màn hình Giám sát thi trực tiếp (bảng học sinh đang làm bài, đếm ngược thời gian, cảnh báo học sinh sắp hết giờ, nút cộng giờ/mở lại/nộp hộ, nút "Làm nóng hệ thống")
  5. Màn hình Chấm bài (chấm tay tự luận, xem ảnh/file bài làm đính kèm, nhập nhận xét)
  6. Màn hình Bảng điểm & Xuất dữ liệu (lọc kết quả, công bố điểm, nút xuất CSV, xóa dữ liệu)
- Tinh chỉnh giao diện dựa trên góp ý của người dùng thông qua Stitch AI.
- Đạt cột mốc **M0: Toàn bộ Prototype giao diện hệ thống được giáo viên duyệt** trước khi bắt tay viết code.

**Cách thức triển khai**

1. Soạn prompt chuyên sâu cho giao diện quản trị giáo viên với phong cách trang nhã, hiện đại, tối ưu cho năng suất thao tác.
2. Gọi `generate_screen_from_text` trên Stitch MCP để lần lượt sinh các màn hình quản trị của giáo viên.
3. Tạo biến thể cho màn hình "Soạn đề thi" (thử nghiệm bố cục 2 cột vs 3 cột) để giáo viên lựa chọn trải nghiệm soạn công thức LaTeX thuận tiện nhất.
4. Trình chiếu toàn bộ danh mục màn hình (Học sinh + Giáo viên) đã tạo trên Stitch cho người dùng đánh giá tổng thể luồng tương tác.
5. Thực hiện các chỉnh sửa nhanh cuối cùng trên Stitch nếu có yêu cầu.

**Test case (kiểm tra giao diện Giáo viên & nghiệm thu M0)**

| ID     | Loại | Kịch bản                                                         | Kết quả mong đợi                                                                                        |
| ------ | ----- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| T0.4.1 | [M]   | Xem Dashboard giáo viên trên Desktop (1366×768 và 1920×1080) | Bố cục thoáng, hiển thị ngay việc cần làm và các đề thi đang mở                               |
| T0.4.2 | [M]   | Xem màn hình Soạn đề thi Toán - Tin                          | Khu vực nhập LaTeX và khung KaTeX preview cạnh nhau; nút upload ảnh bố trí thuận tiện             |
| T0.4.3 | [M]   | Xem cấu hình 5 dạng câu hỏi trong trình soạn đề           | Form cấu hình đáp án và thang điểm cho từng dạng câu (MCQ, TF, số, chữ, file) trực quan       |
| T0.4.4 | [M]   | Xem màn hình Giám sát trực tiếp phòng thi                   | Đọc được tình trạng của 40 học sinh trong 5 giây; các nút hành động khẩn cấp dễ thao tác |
| T0.4.5 | [M]   | Xem màn hình Chấm bài và duyệt file nộp                     | Vùng hiển thị file ảnh/PDF bài làm rộng rãi, ô nhập điểm và nhận xét thuận tay              |
| T0.4.6 | [M]   | Xem màn hình Kết quả & modal Công bố điểm                  | Phân biệt rõ ràng giữa 2 chế độ công bố (`score_only` vs `full`); nút xuất CSV nổi bật    |
| T0.4.7 | [M]   | Thao tác duyệt toàn bộ luồng từ Giáo viên đến Học sinh  | Đảm bảo tính liền mạch, nhất quán về Design System giữa tất cả các màn hình                  |
| T0.4.8 | [M]   | Rà soát nghiệm thu Milestone M0                                 | Người dùng hài lòng và chính thức phê duyệt toàn bộ thiết kế giao diện trên Stitch          |

**DoD:** M0 – Giáo viên chính thức phê duyệt toàn bộ prototype giao diện trên Stitch; sẵn sàng chuyển giao sang P1 (Khởi tạo hạ tầng & Code).

---

## P1. KHỞI TẠO HẠ TẦNG & KHUNG DỰ ÁN (Tuần 1, song song P0)

### Bước 1.1 – Repo, công cụ, CI, môi trường cục bộ

**Yêu cầu cần đạt**

- Monorepo đúng cấu trúc mục 5.4; một lệnh khởi động toàn bộ môi trường dev.
- CI chạy tự động test + lint cho cả BE và FE.
- Không secret trong Git; có `.env.example`.

**Cách thức triển khai**

1. `git init`, thêm `.gitignore` (Python, Node, `.env`), `.editorconfig`, `README.md`.
2. **Backend:** `uv init`, thêm `fastapi uvicorn[standard] sqlalchemy alembic psycopg[binary] pydantic-settings argon2-cffi slowapi apscheduler boto3 python-multipart`; dev: `pytest pytest-asyncio httpx ruff mypy freezegun`. Dùng **SQLAlchemy sync** (đủ nhanh cho ≤ 50 người, ít lỗi hơn async); cấu hình Uvicorn **1 worker**.
3. **Frontend:** `npm create vite@latest -- --template react-ts`, thêm `tailwindcss react-router-dom @tanstack/react-query react-hook-form zod react-markdown remark-math rehype-katex rehype-sanitize katex`; dev: `vitest @testing-library/react msw eslint prettier`.
4. `docker-compose.yml` chỉ cho Postgres 16 cục bộ (+ tùy chọn MinIO làm S3 giả).
5. `Makefile`/`justfile`: `make dev` (db + be + fe), `make test`, `make lint`, `make migrate`.
6. **GitHub Actions:** job `backend` (service postgres, `uv sync`, `ruff`, `mypy`, `pytest`), job `frontend` (`npm ci`, `eslint`, `tsc`, `vitest`, `build`). Cache dependency.
7. Bật **branch protection** trên `main`; thêm `pre-commit` (ruff, prettier, phát hiện secret `gitleaks`).

**Test case**

| ID     | Loại | Kịch bản                                                      | Kết quả mong đợi                                                   |
| ------ | ----- | --------------------------------------------------------------- | ---------------------------------------------------------------------- |
| T1.1.1 | [M]   | Máy mới: clone → `cp .env.example .env` → `make dev`    | Chạy được trong ≤ 15 phút theo README                            |
| T1.1.2 | [I]   | Mở PR có lỗi lint cố ý                                     | CI đỏ, không cho merge                                              |
| T1.1.3 | [I]   | Mở PR có test fail cố ý                                     | CI đỏ                                                                |
| T1.1.4 | [S]   | Commit thử file chứa chuỗi giống khóa AWS                  | `gitleaks` chặn ở pre-commit/CI                                    |
| T1.1.5 | [I]   | Chạy CI trên `main` sạch                                   | Xanh, thời gian < 5 phút nhờ cache                                  |
| T1.1.6 | [M]   | `.env` thiếu biến bắt buộc                                | Backend dừng khởi động với thông báo nêu rõ tên biến thiếu |
| T1.1.7 | [M]   | Xóa `node_modules`/`.venv`, cài lại từ lock file        | Phiên bản đúng như lock, build giống nhau                        |
| T1.1.8 | [M]   | `make test` trên máy khác hệ điều hành (Win/Linux/Mac) | Chạy được, hoặc README ghi rõ cách chạy qua Docker             |

**DoD:** CI xanh; README có hướng dẫn chạy từ đầu.

---

### Bước 1.2 – Khung Backend: cấu hình, lỗi thống nhất, log, thời gian

**Yêu cầu cần đạt**

- Cấu hình qua `pydantic-settings`, kiểm tra ngay khi khởi động.
- Mọi lỗi trả về JSON `{ "error": { "code", "message" } }` (mục 8.4).
- Log có cấu trúc (JSON), có `request_id`.
- Một nguồn thời gian duy nhất (`core/time.py`) để test được.

**Cách thức triển khai**

1. `core/config.py`: lớp `Settings` (DATABASE_URL, SECRET_KEY, CORS_ORIGINS, SESSION_TTL_HOURS, ATTEMPT_GRACE_SECONDS, DATA_RETENTION_DAYS, MAX_UPLOAD_MB, S3_*…) với `lru_cache`.
2. `core/errors.py`: lớp `AppError(code, message, status)` + các lớp con (`Unauthorized`, `Forbidden`, `NotFound`, `AttemptClosed`, `ExamNotOpen`, `ValidationFailed`, `RateLimited`). Đăng ký `exception_handler` cho `AppError`, `RequestValidationError` (chuyển thành `validation_error` kèm danh sách trường), và `Exception` chung (500, không lộ stack trace).
3. `core/time.py`: `def utcnow() -> datetime` (aware, UTC) là **hàm duy nhất** được gọi `now`; test dùng `freezegun` hoặc ghi đè dependency. **Cấm** `datetime.now()` rải rác (thêm rule ruff `DTZ`).
4. Middleware: gắn `X-Request-ID` (UUID), log `method path status duration_ms user_id`. Không log body/mật khẩu.
5. `GET /healthz` (không chạm DB, trả nhanh), `GET /readyz` (chạm DB `SELECT 1`), `GET /time` (giờ UTC ISO).
6. CORS: chỉ `CORS_ORIGINS`; bật `allow_headers=["Authorization","Content-Type"]`.
7. Tiền tố `/api/v1`; tài liệu `/docs` tắt ở production hoặc chỉ bật qua biến môi trường.

**Test case**

| ID     | Loại | Kịch bản                                             | Kết quả mong đợi                                                      |
| ------ | ----- | ------------------------------------------------------ | ------------------------------------------------------------------------- |
| T1.2.1 | [I]   | `GET /healthz`                                       | 200 trong < 50 ms, không truy vấn DB                                    |
| T1.2.2 | [I]   | `GET /readyz` khi DB tắt                            | 503 + `error.code = "db_unavailable"`                                   |
| T1.2.3 | [I]   | Gọi endpoint ném `AppError("attempt_closed", 409)` | JSON đúng chuẩn, status 409                                            |
| T1.2.4 | [I]   | Gửi body sai kiểu                                    | 422 → `validation_error` kèm trường lỗi, tiếng Việt thân thiện |
| T1.2.5 | [I]   | Endpoint ném `ZeroDivisionError`                    | 500 `internal_error`, không lộ stack trace; log có stack             |
| T1.2.6 | [I]   | Request từ origin lạ                                 | Không có header CORS cho phép                                          |
| T1.2.7 | [U]   | `utcnow()` dưới `freeze_time`                    | Trả đúng thời điểm đóng băng, có tzinfo UTC                     |
| T1.2.8 | [I]   | Mỗi response                                          | Có `X-Request-ID`; log cùng ID                                        |
| T1.2.9 | [U]   | Thiếu `SECRET_KEY`                                  | `Settings()` raise lỗi rõ ràng                                       |

**DoD:** coverage lõi ≥ 90%; không còn lệnh `datetime.now()` ngoài `core/time.py`.

---

### Bước 1.3 – Cơ sở dữ liệu: model, migration, chỉ mục, dữ liệu mẫu

**Yêu cầu cần đạt**

- Đủ bảng mục 7.2, đúng ràng buộc `UNIQUE`, khóa ngoại, kiểu `timestamptz`.
- Migration Alembic chạy lên/xuống sạch.
- Kết nối bền trước Neon ngủ.

**Cách thức triển khai**

1. Mapped class SQLAlchemy 2.0 (`Mapped[...]`, `mapped_column`), PK `UUID` (v4) cho `attempts/answers/files`, `BigInt/serial` cho bảng nhỏ nếu muốn gọn; thống nhất dùng UUID để tránh lộ thứ tự.
2. **Ràng buộc quan trọng:** `UNIQUE(exam_id, student_id)` trên `attempts`; `UNIQUE(attempt_id, question_id)` trên `answers`; `UNIQUE(token_hash)`; `CHECK (status IN (...))`; `CHECK (points >= 0)`; `ON DELETE CASCADE` cho `answers`→`attempts`, `questions`→`exams` (nhưng **không cascade** `users`→`attempts`).
3. **Chỉ mục:** `attempts(status, deadline_at)` (sweeper), `attempts(exam_id)`, `answers(attempt_id)`, `class_members(user_id)`, `sessions(user_id)`.
4. Engine: `pool_pre_ping=True`, `pool_recycle=300`, `pool_size=5`, `max_overflow=5` (khớp giới hạn Neon), chuỗi kết nối **pooled**.
5. `JSONB` cho `config/answer_key/value`; Pydantic validate cấu trúc JSON theo `type` ở tầng service (DB không kiểm schema).
6. Alembic: `alembic revision --autogenerate`, **luôn đọc lại** file sinh ra; kiểm `upgrade head` và `downgrade base` trong CI.
7. `scripts/seed_dev.py`: 1 admin, 2 lớp, 20 học sinh, 1 đề mẫu đủ 5 dạng câu.
8. Kiểu tiền tệ điểm: `Numeric(6,2)`; trong Python dùng `Decimal`.

**Test case**

| ID     | Loại | Kịch bản                                               | Kết quả mong đợi                                   |
| ------ | ----- | -------------------------------------------------------- | ------------------------------------------------------ |
| T1.3.1 | [I]   | `upgrade head` rồi `downgrade base` trên DB trống | Không lỗi, DB trở về rỗng                         |
| T1.3.2 | [I]   | Chèn 2 attempt cùng (exam, student)                    | Vi phạm UNIQUE                                        |
| T1.3.3 | [I]   | Chèn 2 answer cùng (attempt, question)                 | Vi phạm UNIQUE                                        |
| T1.3.4 | [I]   | Xóa exam có câu hỏi                                  | Câu hỏi bị xóa theo (cascade)                      |
| T1.3.5 | [I]   | Xóa user đã có attempt                               | Bị chặn (RESTRICT)                                   |
| T1.3.6 | [I]   | `EXPLAIN` truy vấn sweeper với 10.000 attempt        | Dùng index `(status, deadline_at)`                  |
| T1.3.7 | [I]   | Đóng kết nối DB giữa chừng rồi gọi API           | `pool_pre_ping` kết nối lại, request thành công |
| T1.3.8 | [U]   | Lưu `datetime` naive                                  | Bị từ chối/chuyển đúng, DB luôn nhận UTC aware |
| T1.3.9 | [I]   | Chạy `seed_dev.py` hai lần                           | Idempotent, không nhân đôi dữ liệu               |

**DoD:** `alembic check` sạch (model khớp migration); seed chạy được.

---

### Bước 1.4 – Khung Frontend: router, API client, trạng thái, bảo vệ route

**Yêu cầu cần đạt**

- Routing theo vai trò; không vào nhầm trang.
- API client thống nhất: gắn token, bắt lỗi chuẩn, xử lý 401, retry hợp lý.
- Hiển thị "đang đánh thức máy chủ" khi backend ngủ.

**Cách thức triển khai**

1. `lib/api.ts`: bọc `fetch`; gắn `Authorization: Bearer`; parse `{error:{code,message}}` thành `ApiError`; **timeout 15 s** với `AbortController`.
2. **Chống cold start:** nếu request đầu bị timeout/5xx/network error → hiển thị banner "Đang đánh thức máy chủ…", thử lại theo **exponential backoff** (2 s, 4 s, 8 s, 16 s, tối đa 5 lần, thêm jitter) trước khi báo lỗi. Chỉ retry tự động với phương thức **idempotent** (GET, PUT autosave, POST start/submit — vì đều idempotent theo thiết kế).
3. 401 → xóa token, chuyển `/login?next=<đường dẫn hiện tại>`.
4. Token lưu `localStorage` (khóa `quiz_token`); chấp nhận rủi ro XSS vì đã sanitize Markdown + CSP; thay thế bằng `sessionStorage` nếu muốn an toàn hơn (đổi lại phải đăng nhập lại khi đóng tab — **không** nên cho trang làm bài, vì mất điện là tình huống cốt lõi).
5. TanStack Query: `staleTime` ngắn cho dữ liệu làm bài (`0`), dài hơn cho danh sách lớp; `retry` tắt ở mutation không idempotent.
6. `RequireRole` (HOC/route loader): đọc `GET /auth/me`, điều hướng theo `role`.
7. Error Boundary toàn cục + trang lỗi "Có sự cố, bài của bạn vẫn an toàn nếu đã hiện 'Đã lưu'".
8. Cấu hình CSP (meta/`_headers` Cloudflare Pages) từ đầu để phát hiện sớm lỗi script inline.

**Test case**

| ID     | Loại | Kịch bản                                           | Kết quả mong đợi                                                   |
| ------ | ----- | ---------------------------------------------------- | ---------------------------------------------------------------------- |
| T1.4.1 | [U]   | `api.get` nhận `{error:{code:"forbidden"}}` 403 | Ném `ApiError` có `code`, `status`                             |
| T1.4.2 | [U]   | Nhận 401 ở route bảo vệ                          | Xóa token, chuyển `/login?next=…`                                 |
| T1.4.3 | [U]   | Mô phỏng timeout 3 lần rồi thành công (msw)    | Banner hiện, retry theo backoff, cuối cùng thành công, banner ẩn |
| T1.4.4 | [U]   | Timeout 5 lần liên tiếp                           | Hiện lỗi mất kết nối với nút "Thử lại", không lặp vô hạn  |
| T1.4.5 | [U]   | Học sinh truy cập `/admin/classes`               | Chuyển về trang học sinh/403                                        |
| T1.4.6 | [U]   | Chưa đăng nhập vào `/student/exams`           | Chuyển `/login`                                                     |
| T1.4.7 | [U]   | Component con ném lỗi render                       | Error Boundary hiển thị trang lỗi thân thiện, không trắng trang |
| T1.4.8 | [U]   | POST không idempotent (tạo lớp) bị timeout       | **Không** tự retry (tránh tạo trùng)                        |
| T1.4.9 | [M]   | Build production, mở trang với CSP bật            | Không lỗi CSP trên console                                          |

**DoD:** M1 – FE gọi được `/healthz`, `/auth/me`; hiển thị banner khi giả lập server chậm.

---

## P2. TÀI KHOẢN, LỚP, HỌC SINH (Tuần 2)

### Bước 2.1 – Xác thực & phiên (backend)

**Yêu cầu cần đạt**

- `POST /auth/login|logout`, `GET /auth/me`.
- Mật khẩu Argon2; token opaque lưu hash; hết hạn sau 12 giờ không hoạt động; thu hồi được.
- Chống dò mật khẩu: ≤ 10 lần sai/phút theo IP + username.

**Cách thức triển khai**

1. `core/security.py`: `hash_password` / `verify_password` (argon2-cffi `PasswordHasher`, kèm `check_needs_rehash`); `new_token()` = `secrets.token_urlsafe(32)`; `hash_token(t)` = `hmac_sha256(SECRET_KEY, t)` (lưu hex).
2. Đăng nhập:
   - Chuẩn hóa `username.strip().lower()`.
   - **Chống dò user (timing/enumeration):** nếu không tìm thấy user, vẫn gọi `verify_password` với hash giả để thời gian tương đương; luôn trả cùng thông báo `"Sai tên đăng nhập hoặc mật khẩu"`.
   - User `is_active=false` → trả cùng thông báo chung (hoặc `account_disabled` nếu muốn minh bạch với học sinh; chốt khi duyệt UX).
   - Thành công: tạo `sessions(token_hash, expires_at = now + TTL)`, trả `{token, user}`.
3. Dependency `get_current_user`: lấy Bearer → hash → tìm session chưa hết hạn → **trượt** `last_seen_at`/`expires_at` (chỉ cập nhật nếu cách lần trước > 60 s để giảm ghi DB).
4. `require_role("admin")` / `require_role("student")` là dependency riêng.
5. Rate limit: `slowapi` key = `ip + ":" + username`; 10 lần/phút, 429 `rate_limited` kèm `Retry-After`. (Nếu chạy 1 worker, bộ nhớ trong là đủ; nhiều worker thì dùng bộ đếm DB.)
6. Logout: xóa session hiện tại. Admin: `DELETE /admin/students/{id}/sessions` thu hồi hết phiên.
7. Ghi `audit_log` cho `login` (thành công/thất bại, IP).
8. Dọn session hết hạn trong job retention.

**Test case**

| ID      | Loại | Kịch bản                                                      | Kết quả mong đợi                                                                   |
| ------- | ----- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| T2.1.1  | [I]   | Đăng nhập đúng                                             | 200, có token, DB chỉ lưu **hash** token                                      |
| T2.1.2  | [I]   | Sai mật khẩu / sai username                                   | Cùng thông báo và status 401; thời gian phản hồi xấp xỉ nhau                  |
| T2.1.3  | [I]   | 11 lần sai trong 1 phút                                       | Lần 11 trả 429 `rate_limited`; sau 1 phút thử lại được                       |
| T2.1.4  | [I]   | Dùng token sau khi đã logout                                 | 401                                                                                    |
| T2.1.5  | [I]   | Token hết hạn (freeze time +13h không hoạt động)          | 401                                                                                    |
| T2.1.6  | [I]   | Dùng liên tục (mỗi 5 phút trong 14h)                       | Phiên được gia hạn trượt, vẫn hợp lệ                                         |
| T2.1.7  | [I]   | Tài khoản bị khóa đang có phiên                          | Mọi request tiếp theo 401/403; phiên bị vô hiệu                                  |
| T2.1.8  | [S]   | Học sinh gọi `/admin/*`                                     | 403 `forbidden`                                                                      |
| T2.1.9  | [S]   | Username có chữ hoa/khoảng trắng đầu cuối (`" HS01 "`) | Chuẩn hóa, đăng nhập được như `hs01`                                        |
| T2.1.10 | [S]   | Header `Authorization` sai định dạng / token ngẫu nhiên  | 401, không 500                                                                        |
| T2.1.11 | [I]   | Admin thu hồi phiên học sinh đang làm bài                 | Request kế tiếp của học sinh 401; đăng nhập lại **vào đúng bài cũ** |

**DoD:** không có đường truy cập nào bỏ qua `get_current_user`; test phân quyền đạt.

---

### Bước 2.2 – Khởi tạo admin đầu tiên (CLI) & quản lý mật khẩu

**Yêu cầu cần đạt**

- Tạo admin lần đầu bằng CLI hoặc biến môi trường, an toàn, idempotent.
- Sinh mật khẩu ngẫu nhiên dễ đọc, tránh ký tự dễ nhầm.

**Cách thức triển khai**

1. `python -m app.cli create-admin --username admin` (đọc mật khẩu bằng `getpass`, hoặc từ `ADMIN_PASSWORD` nếu chạy tự động); nếu admin đã tồn tại → không ghi đè, báo rõ.
2. Khi khởi động, nếu có `ADMIN_USERNAME/ADMIN_PASSWORD` và **chưa có admin nào** → tạo; sau đó khuyến nghị xóa biến `ADMIN_PASSWORD` khỏi môi trường.
3. `generate_password(length=8)`: bảng chữ `abcdefghjkmnpqrstuvwxyz23456789` (bỏ `0 o 1 l i`), dùng `secrets.choice`; đảm bảo có cả chữ và số.
4. Đổi mật khẩu admin: `POST /auth/change-password` (yêu cầu mật khẩu cũ, tối thiểu 8 ký tự), thu hồi các phiên khác.
5. Kiểm tra độ mạnh tối thiểu cho admin (≥ 10 ký tự); học sinh ≥ 6 ký tự (tự sinh 8).

**Test case**

| ID     | Loại | Kịch bản                                                                        | Kết quả mong đợi                                                    |
| ------ | ----- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| T2.2.1 | [I]   | Chạy `create-admin` khi chưa có admin                                        | Tạo được, đăng nhập thành công                                 |
| T2.2.2 | [I]   | Chạy lần 2                                                                      | Không tạo trùng, không đổi mật khẩu, thông báo rõ            |
| T2.2.3 | [U]   | `generate_password` 10.000 lần                                                 | Không chứa ký tự cấm; luôn có cả chữ và số; độ dài đúng |
| T2.2.4 | [U]   | Kiểm tra tính ngẫu nhiên (không trùng lặp bất thường trong 10.000 mẫu) | Tỉ lệ trùng thấp theo xác suất                                    |
| T2.2.5 | [I]   | Khởi động có `ADMIN_*` khi đã có admin                                   | Bỏ qua, không lỗi                                                    |
| T2.2.6 | [I]   | Đổi mật khẩu với mật khẩu cũ sai                                          | 400/401, không đổi                                                   |
| T2.2.7 | [I]   | Đổi mật khẩu thành công                                                     | Phiên khác bị thu hồi, phiên hiện tại giữ                       |
| T2.2.8 | [S]   | Mật khẩu admin quá ngắn (< 10)                                                | Từ chối với `validation_error`                                     |

**DoD:** hướng dẫn tạo admin ghi trong README.

---

### Bước 2.3 – Quản lý lớp, học sinh, ghi danh, nhập CSV (backend)

**Yêu cầu cần đạt**

- CRUD lớp, học sinh; ghi danh nhiều–nhiều; nhập CSV hàng loạt; reset mật khẩu; khóa/mở; chuyển lớp.
- Hiển thị mật khẩu rõ **một lần** và cho tải CSV danh sách tài khoản.

**Cách thức triển khai**

1. Validator `username`: regex `^[a-z0-9._-]{3,32}$`, unique (kiểm trong DB, bắt `IntegrityError` → `409 username_taken`).
2. Ghi danh: `PUT /admin/classes/{id}/members` nhận `{user_ids: [...]}` → **đồng bộ tập hợp** (thêm mới/xóa thiếu) trong **một giao dịch** bằng `INSERT … ON CONFLICT DO NOTHING` và `DELETE … WHERE user_id NOT IN`.
3. **Nhập CSV (`POST /admin/students/import`):**
   - Nhận file ≤ 1 MB; đọc UTF-8 (có/không BOM) bằng `csv.DictReader`; kiểm tra tiêu đề `ho_ten, username, mat_khau, ma_lop`.
   - Pha 1 **validate toàn bộ dòng, chưa ghi**: trả danh sách lỗi theo số dòng (thiếu họ tên, username sai quy tắc, trùng username trong file, `ma_lop` không tồn tại, trùng với user đã có).
   - Chế độ `dry_run=true` cho xem trước; `dry_run=false` ghi trong **một giao dịch** (tất cả hoặc không gì cả).
   - Thiếu mật khẩu → tự sinh; trả về bảng `username, mat_khau` **chỉ trong response này** (không lưu bản rõ).
4. Reset mật khẩu: sinh mới, hash, thu hồi phiên, trả mật khẩu rõ một lần.
5. Khóa tài khoản: `is_active=false` + xóa session.
6. Xóa học sinh: nếu đã có attempt → chỉ cho **khóa/lưu trữ**, không xóa cứng (bảo toàn dữ liệu điểm); xóa lớp có học sinh → yêu cầu xác nhận, chỉ xóa liên kết `class_members`.
7. Phân trang + tìm kiếm tên/username (`ILIKE`, index trigram nếu cần > 1.000 bản ghi).

**Test case**

| ID      | Loại | Kịch bản                                                   | Kết quả mong đợi                                                                    |
| ------- | ----- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| T2.3.1  | [I]   | Tạo học sinh username hợp lệ                             | 201, mật khẩu rõ chỉ có trong response, DB chỉ có hash                           |
| T2.3.2  | [I]   | Username `HS 01!` hoặc 2 ký tự hoặc 33 ký tự         | 422 kèm lý do                                                                         |
| T2.3.3  | [I]   | Username trùng                                              | 409 `username_taken`                                                                  |
| T2.3.4  | [I]   | CSV hợp lệ 30 dòng, không cột mật khẩu                | Tạo đủ 30, mỗi người một mật khẩu ngẫu nhiên khác nhau                      |
| T2.3.5  | [I]   | CSV có 1 dòng lỗi giữa file (`ma_lop` sai)             | Không tạo ai (all-or-nothing); báo đúng số dòng                                  |
| T2.3.6  | [I]   | CSV trùng username ngay trong file                          | Báo cả hai dòng trùng                                                               |
| T2.3.7  | [I]   | CSV có BOM, dấu phẩy trong tên (có ngoặc kép), CRLF   | Đọc đúng                                                                            |
| T2.3.8  | [I]   | CSV rỗng/ sai tiêu đề/ 5 MB                              | Từ chối với thông báo rõ                                                          |
| T2.3.9  | [I]   | Ghi danh đồng thời hai request cùng thêm một học sinh | Không lỗi, chỉ một bản ghi `class_members`                                       |
| T2.3.10 | [I]   | Học sinh thuộc 2 lớp, đề giao lớp A                    | Học sinh thấy đề (qua lớp A)                                                       |
| T2.3.11 | [I]   | Xóa học sinh đã có attempt                              | Bị chặn; gợi ý khóa tài khoản                                                    |
| T2.3.12 | [I]   | Reset mật khẩu học sinh đang làm bài                   | Phiên cũ bị thu hồi; đăng nhập lại bằng mật khẩu mới, vào lại đúng bài |
| T2.3.13 | [I]   | Tìm kiếm `"nguyen"` khi tên có dấu `"Nguyễn"`      | Tìm được (bỏ dấu khi tìm kiếm — dùng cột `search_name` đã bỏ dấu)      |

**DoD:** M2 backend; tài liệu định dạng CSV mẫu nằm trong `docs/csv-mau.csv`.

---

### Bước 2.4 – Frontend: đăng nhập & quản lý lớp/học sinh

**Yêu cầu cần đạt**

- Màn đăng nhập, danh sách/chi tiết lớp, danh sách học sinh, nhập CSV có xem trước lỗi, hộp thoại hiện mật khẩu một lần + tải CSV.

**Cách thức triển khai**

1. `LoginPage`: react-hook-form + zod; hiển thị lỗi chung; sau thành công chuyển theo `role` hoặc `next`.
2. `AuthProvider`: nạp `/auth/me` khi khởi động; lưu `user`; hàm `logout`.
3. Trang **Lớp:** bảng + modal tạo/sửa; chi tiết lớp có danh sách học sinh, chọn nhiều để ghi danh (multi-select có tìm kiếm).
4. Trang **Học sinh:** bảng phân trang, cờ trạng thái, menu (reset mật khẩu, khóa/mở, thu hồi phiên).
5. **Nhập CSV:** chọn file → gọi `dry_run` → bảng lỗi theo dòng (tô đỏ) → nếu sạch nút "Nhập" bật. Sau khi nhập, hiện modal **"Mật khẩu chỉ hiện một lần"** với nút Tải CSV (tạo `Blob` phía client; xóa dữ liệu khỏi state khi đóng).
6. Dùng `useMutation` + `invalidateQueries` để làm tươi danh sách; nút bị vô hiệu khi đang gửi (chống bấm đúp).

**Test case**

| ID     | Loại | Kịch bản                                           | Kết quả mong đợi                                                                |
| ------ | ----- | ---------------------------------------------------- | ----------------------------------------------------------------------------------- |
| T2.4.1 | [E]   | Đăng nhập admin rồi tạo lớp, thêm 3 học sinh | Hiển thị đúng; F5 vẫn còn đăng nhập                                        |
| T2.4.2 | [E]   | Đăng nhập sai                                     | Thông báo chung; ô mật khẩu được xóa                                       |
| T2.4.3 | [E]   | Bấm "Tạo lớp" hai lần liên tiếp                | Chỉ tạo một lớp (nút khóa khi đang gửi)                                     |
| T2.4.4 | [E]   | Nhập CSV có lỗi                                   | Hiện bảng lỗi đúng dòng; nút Nhập bị khóa                                 |
| T2.4.5 | [E]   | Nhập CSV hợp lệ                                   | Modal mật khẩu hiện; tải được CSV; đóng modal rồi không xem lại được |
| T2.4.6 | [E]   | Học sinh đăng nhập                               | Chuyển thẳng trang học sinh, không thấy menu admin                             |
| T2.4.7 | [E]   | Token hết hạn khi đang ở trang admin             | Chuyển `/login?next=…`, sau đăng nhập quay lại trang cũ                    |
| T2.4.8 | [E]   | Danh sách 200 học sinh                             | Phân trang/ảo hóa mượt, tìm kiếm có debounce 300 ms                         |
| T2.4.9 | [M]   | Giao diện trên điện thoại                       | Dùng được (card)                                                                |

**DoD:** M2 – giáo viên thực hiện được trọn "tạo lớp → nhập học sinh → phát mật khẩu".

---

## P3. SOẠN ĐỀ (Tuần 2–3)

### Bước 3.1 – Model & API đề thi, câu hỏi (5 dạng), khóa chỉnh sửa, phiên bản

**Yêu cầu cần đạt**

- CRUD đề/câu hỏi theo mục 8.3; validate `config`/`answer_key` theo từng dạng; sắp xếp lại thứ tự; nhân bản đề.
- Khóa chỉnh sửa khi đã có người bắt đầu làm (`locked_at`); khóa lạc quan bằng `version`.
- Trạng thái đề chuyển hợp lệ: `draft → published → closed → archived`.

**Cách thức triển khai**

1. **Pydantic discriminated union** theo `type` cho `config` và `answer_key` (ví dụ `McqConfig/McqKey`, `TfConfig/TfKey`, `ShortTextKey`, `ShortNumberKey`, `FileConfig`). Quy tắc nghiệp vụ trong validator:
   - MCQ: 2–8 lựa chọn, id duy nhất (`A..H`), `correct` ∈ ids.
   - TF: 1–8 mệnh đề, `answer_key` có đủ khóa cho từng mệnh đề (kiểu bool); `scoring=thpt` chỉ hợp lệ với đúng 4 mệnh đề, nếu khác → tự hạ thành `proportional` và báo cảnh báo.
   - Số: `values` là chuỗi số hợp lệ qua `parse_number`, `tolerance ≥ 0`.
   - Chữ: `accepted` không rỗng khi `auto`.
   - File: `max_files` 1–10, `max_mb` 1–20 (≤ `MAX_UPLOAD_MB`), `allowed_ext` thuộc danh sách trắng.
   - `points ≥ 0`, tối đa 2 chữ số thập phân.
2. **Máy trạng thái đề:** bảng chuyển hợp lệ trong `services/exams.py`; `publish` yêu cầu: có ≥ 1 câu, mọi câu hợp lệ, ≥ 1 lớp được giao, tổng điểm > 0, `open_at < close_at` nếu có cả hai.
3. **Khóa chỉnh sửa:** khi `start` attempt đầu tiên → set `exams.locked_at = now()` (cùng giao dịch). API sửa câu/điểm/đáp án kiểm `locked_at IS NULL`, nếu không → `409 exam_locked` kèm gợi ý "Nhân bản đề".
4. **Khóa lạc quan:** `PATCH` kèm `version`; `UPDATE … WHERE id=:id AND version=:v` (`rowcount=0` → `409 version_conflict`).
5. **Thứ tự câu:** `POST /questions/reorder {ordered_ids}` cập nhật `position` trong 1 giao dịch (kiểm tra danh sách khớp hoàn toàn tập câu hiện có).
6. **Nhân bản:** sao chép exam + questions (đặt `status=draft`, `locked_at=null`, tiêu đề thêm "(bản sao)"); **không** sao chép attempts; ảnh dùng chung `storage_key` (đếm tham chiếu khi dọn dẹp).
7. Xóa đề: chỉ khi `draft` hoặc chưa có attempt; còn lại → `archive`.

**Test case**

| ID      | Loại | Kịch bản                                                                                    | Kết quả mong đợi                                                         |
| ------- | ----- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| T3.1.1  | [U]   | MCQ có 1 lựa chọn / 9 lựa chọn / `correct` không tồn tại                            | `validation_error` cho từng trường hợp                                 |
| T3.1.2  | [U]   | TF 4 mệnh đề `thpt` / 3 mệnh đề `thpt`                                              | 4: chấp nhận; 3: tự chuyển `proportional` + cảnh báo                 |
| T3.1.3  | [U]   | Số: đáp án `"1,5"`, `"1/2"`, `"abc"`, `""`                                        | Hợp lệ, hợp lệ, từ chối, từ chối                                     |
| T3.1.4  | [U]   | File: `allowed_ext` chứa `exe`/`html`/`svg`                                          | Từ chối (danh sách trắng)                                                |
| T3.1.5  | [I]   | Xuất bản đề không có câu / không giao lớp / tổng điểm 0 / `open_at ≥ close_at` | Mỗi trường hợp 422 với lý do riêng                                    |
| T3.1.6  | [I]   | Sửa đề sau khi có học sinh bắt đầu                                                    | 409 `exam_locked` kèm gợi ý nhân bản                                  |
| T3.1.7  | [I]   | Hai giáo viên sửa cùng đề với `version` cũ                                          | Người sau nhận 409 `version_conflict`                                   |
| T3.1.8  | [I]   | Reorder thiếu/thừa id                                                                       | 422, thứ tự không thay đổi                                              |
| T3.1.9  | [I]   | Nhân bản đề 20 câu có ảnh                                                              | Đề mới ở `draft`, 20 câu, ảnh hiển thị được, không có attempt |
| T3.1.10 | [I]   | Chuyển trạng thái bất hợp lệ (`closed → published`, `archived → draft`)           | 409 `invalid_transition`                                                   |
| T3.1.11 | [I]   | Xóa đề đã có attempt                                                                    | Bị chặn; gợi ý lưu trữ                                                 |
| T3.1.12 | [I]   | Giao đề cho lớp không tồn tại                                                           | 404/422                                                                      |
| T3.1.13 | [S]   | Học sinh gọi `GET /admin/exams/{id}`                                                      | 403                                                                          |

**DoD:** bộ test validator cho 5 dạng câu đạt 100% nhánh.

---

### Bước 3.2 – Hiển thị Markdown + LaTeX an toàn (`MathText`)

**Yêu cầu cần đạt**

- Render Markdown (đậm, danh sách, bảng, khối code) + LaTeX nội dòng `$…$` và dòng riêng `$$…$$`.
- Không cho HTML thô/script; KaTeX `trust:false`; công thức lỗi chỉ báo lỗi tại chỗ.
- Dùng được cho: nội dung câu, lựa chọn, mệnh đề, lời giải, mô tả đề.

**Cách thức triển khai**

1. Pipeline: `react-markdown` + `remark-gfm` (bảng) + `remark-math` + `rehype-katex` (`{ trust:false, strict:'ignore', throwOnError:false, errorColor:'#c00', output:'htmlAndMathml' }`) + `rehype-sanitize` với schema mở rộng chỉ cho thẻ/thuộc tính KaTeX cần thiết (`span.className`, `math`, …). **Thứ tự bắt buộc:** sanitize *trước* khi chèn nội dung KaTeX hoặc dùng schema cho phép riêng lớp KaTeX.
2. Ảnh: chỉ cho `src` thuộc domain ảnh của hệ thống (R2/proxy) hoặc đường dẫn tương đối; chặn `javascript:`, `data:` (trừ khi muốn cho `data:image/png` nhỏ), thêm `loading="lazy"`, `max-width:100%`.
3. Link: bắt buộc `rel="noopener noreferrer" target="_blank"` hoặc vô hiệu hóa hoàn toàn trong đề thi (khuyến nghị: vô hiệu để học sinh không rời trang).
4. **Hiệu năng:** `React.memo` theo nội dung; lazy-load `katex.css` và font; với 60 câu, chỉ render câu đang xem (mobile) hoặc dùng `IntersectionObserver` để render khi cuộn tới.
5. Công thức lỗi: `throwOnError:false` hiển thị chuỗi đỏ; ngoài ra preview của giáo viên thêm bộ **linter**: phát hiện `$` không khớp (đếm dấu `$` không thoát), `{` `}` mất cân bằng, hiển thị cảnh báo trước khi xuất bản.
6. Escape: ký tự `\$` hiển thị dấu đô la; hỗ trợ `\(...\)`/`\[...\]` bằng tiền xử lý chuyển sang `$`/`$$` (tùy chọn).
7. Khối code (môn Tin): highlight nhẹ (`rehype-highlight` hoặc `shiki` lazy), font mono, cuộn ngang.

**Test case**

| ID      | Loại | Kịch bản                                                         | Kết quả mong đợi                                                                 |
| ------- | ----- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| T3.2.1  | [U]   | `Tính $x^2+y^2=r^2$`                                            | Render công thức nội dòng                                                        |
| T3.2.2  | [U]   | `$$\int_0^1 x\,dx$$`                                             | Render dạng khối, canh giữa                                                       |
| T3.2.3  | [S]   | `<script>alert(1)</script>` và `<img src=x onerror=alert(1)>` | Không chạy; bị loại bỏ hoặc hiện dạng chữ                                   |
| T3.2.4  | [S]   | `[click](javascript:alert(1))`                                   | Link bị vô hiệu                                                                   |
| T3.2.5  | [S]   | `$\href{javascript:alert(1)}{x}$` (KaTeX trust)                  | Không tạo link độc (trust:false)                                                 |
| T3.2.6  | [U]   | Công thức sai `$\frac{1}{$`                                    | Hiện lỗi đỏ tại chỗ, phần còn lại trang vẫn bình thường                 |
| T3.2.7  | [U]   | Bảng Markdown 3×3, danh sách lồng, khối code Python           | Render đúng                                                                        |
| T3.2.8  | [U]   | `Giá 5\$ và $x$`                                               | `5$` hiển thị chữ, `x` là công thức                                        |
| T3.2.9  | [P]   | Render 60 câu mỗi câu 3 công thức                             | Cuộn mượt, thời gian render ban đầu < 1 giây trên máy trung bình           |
| T3.2.10 | [U]   | Ảnh `![](https://evil.com/x.png)`                               | Bị chặn (ngoài danh sách domain cho phép)                                       |
| T3.2.11 | [U]   | Nội dung rất dài (50 KB)                                        | Không treo giao diện; có giới hạn độ dài ở backend (≤ 20.000 ký tự/câu) |

**DoD:** có bộ snapshot test các mẫu LaTeX thường gặp lớp 6–12 (phân số, căn, tích phân, ma trận, hệ phương trình `cases`, vector).

---

### Bước 3.3 – Tải ảnh & dịch vụ lưu trữ (S3/R2)

**Yêu cầu cần đạt**

- Giáo viên tải ảnh jpg/png/webp ≤ 5 MB (tự nén ở client nếu lớn); lưu bền ở bucket riêng tư.
- Học sinh nộp file (≤ 10 MB, jpg/png/pdf) lưu bền; giáo viên xem qua signed URL có hạn.
- Có lớp trừu tượng `StorageBackend` để đổi nhà cung cấp.

**Cách thức triển khai**

1. Interface: `put(key, fileobj, content_type)`, `get_signed_url(key, expires=300)`, `delete(key)`, `exists(key)`. Cài `S3Storage` (boto3), `LocalStorage` (dev/test), có thể `MinIO` qua `S3_ENDPOINT`.
2. **Đường tải lên (thiết kế an toàn):**
   - Giới hạn kích thước ở tầng ASGI: đọc `Content-Length`, và **đọc theo khối** (stream) dừng khi vượt giới hạn.
   - Kiểm tra **magic bytes** (đầu file) bằng thư viện `filetype`/`puremagic`: JPEG `FFD8FF`, PNG `89504E47`, PDF `%PDF-`, WebP `RIFF....WEBP`; so với đuôi/MIME khai báo; không khớp → `415`.
   - Tên lưu: `uuid4().hex + đuôi chuẩn hóa`; đường dẫn `exams/{exam_id}/q/{uuid}` hoặc `attempts/{attempt_id}/{uuid}`.
   - Ảnh đề: xử lý lại bằng Pillow (loại bỏ EXIF/GPS, giới hạn kích thước tối đa 2000 px) trước khi lưu.
   - Ghi bảng `files` **sau khi** upload thành công; nếu ghi DB lỗi → xóa object (bù trừ).
3. **Phân phát ảnh đề:** ảnh nằm trong bucket riêng tư, nhưng học sinh phải xem được trong lúc thi → endpoint `GET /files/{id}` kiểm tra quyền (học sinh chỉ xem ảnh của đề thuộc attempt của mình; giáo viên xem tất cả) rồi **redirect 302** tới signed URL (hạn 10 phút) hoặc proxy stream. Tạo `Cache-Control: private, max-age=300`.
4. Client nén ảnh bằng `canvas` hoặc `browser-image-compression` (giới hạn 1600 px, chất lượng 0.8) trước khi gửi.
5. Giới hạn: số file/câu, tổng dung lượng/attempt (ví dụ ≤ 50 MB), rate limit upload (20/phút/user).
6. Dọn mồ côi: job tuần quét `files` không còn tham chiếu (ảnh đề không còn xuất hiện trong nội dung nào) hoặc thuộc attempt đã xóa.

**Test case**

| ID      | Loại | Kịch bản                                                  | Kết quả mong đợi                            |
| ------- | ----- | ----------------------------------------------------------- | ----------------------------------------------- |
| T3.3.1  | [I]   | Tải ảnh PNG 2 MB                                          | 201, trả URL, hiển thị được trong preview |
| T3.3.2  | [S]   | Tải file `.exe` đổi tên thành `.png`               | 415 (magic bytes không khớp)                  |
| T3.3.3  | [I]   | Tải ảnh 6 MB (giáo viên) / file 15 MB (học sinh)       | 413 `file_too_large` với thông báo rõ     |
| T3.3.4  | [S]   | Tải SVG/HTML                                               | Bị từ chối (không thuộc danh sách trắng) |
| T3.3.5  | [S]   | Học sinh A truy cập `/files/{id}` của bài học sinh B | 403                                             |
| T3.3.6  | [S]   | Truy cập signed URL sau khi hết hạn                      | Bị từ chối bởi S3                           |
| T3.3.7  | [I]   | Ghi DB lỗi sau khi upload (giả lập)                      | Object được xóa, không còn file mồ côi  |
| T3.3.8  | [I]   | Ảnh có GPS EXIF                                           | File lưu không còn EXIF                      |
| T3.3.9  | [I]   | Hai request tải cùng lúc cùng tên gốc                 | Hai `storage_key` khác nhau, không ghi đè |
| T3.3.10 | [I]   | Đổi `S3Storage` ↔ `LocalStorage`                     | Cùng bộ test pass (hợp đồng interface)     |
| T3.3.11 | [P]   | Ảnh 5 MB tải qua mạng yếu (throttle 3G)                 | Có tiến trình; không timeout dưới 60 s    |

**DoD:** bộ test hợp đồng `StorageBackend` chạy cho cả hai cài đặt.

---

### Bước 3.4 – Giao diện soạn đề (Exam Editor)

**Yêu cầu cần đạt**

- Soạn đủ 5 dạng câu; preview trực tiếp; kéo thả sắp xếp; chèn ảnh; cấu hình điểm/thiết lập đề.
- Tự lưu bản nháp phía giáo viên, không mất khi lỡ đóng tab.

**Cách thức triển khai**

1. **Trạng thái form:** `react-hook-form` + `zod` (schema FE khớp BE); `useFieldArray` cho lựa chọn/mệnh đề/đáp án chấp nhận.
2. **Lưu tự động bản nháp:** debounce 1.5 s → `PATCH` câu đang sửa (kèm `version`); nếu 409 → hộp thoại "Đề đã thay đổi ở nơi khác" (Tải lại / Giữ bản của tôi). Lưu `localStorage` phòng mất mạng.
3. **Trình soạn:** `<textarea>` có thanh công cụ (đậm, công thức `$…$`, khối `$$…$$`, bảng, code, ảnh); chọn `CodeMirror 6` nếu cần số dòng/gợi ý (nhẹ hơn Monaco). Preview dùng `MathText` với debounce 200 ms.
4. **Kéo thả:** `@dnd-kit/sortable`; sau khi thả gọi `reorder` (lạc quan: cập nhật UI ngay, rollback nếu API lỗi).
5. **Dán ảnh:** bắt sự kiện `paste` có `clipboardData.files` → nén → upload → chèn Markdown tại vị trí con trỏ; hiển thị placeholder `![đang tải…]()` rồi thay bằng URL thật.
6. **Biên tập theo dạng:** component riêng `McqEditor`, `TfEditor`, `ShortTextEditor`, `ShortNumberEditor`, `FileEditor`; dùng chung `QuestionShell` (nội dung, điểm, lời giải).
7. **Kiểm tra trước xuất bản:** `PublishChecklist` hiển thị mọi vấn đề (câu thiếu đáp án, công thức lỗi, điểm = 0) có liên kết nhảy tới câu.
8. Khi đề `locked`: giao diện chuyển chế độ chỉ đọc + nút "Nhân bản để sửa".
9. Tính tổng điểm hiển thị trực tiếp; tùy chọn "Chia đều điểm" (chia và **làm tròn hợp lý**, phần dư vào câu cuối để tổng chẵn).

**Test case**

| ID      | Loại | Kịch bản                                             | Kết quả mong đợi                                             |
| ------- | ----- | ------------------------------------------------------ | ---------------------------------------------------------------- |
| T3.4.1  | [E]   | Tạo đề đủ 5 dạng câu, lưu, tải lại trang     | Mọi dữ liệu nguyên vẹn                                      |
| T3.4.2  | [E]   | Gõ công thức, preview cập nhật                    | Cập nhật ≤ 300 ms, không giật                               |
| T3.4.3  | [E]   | Dán ảnh bằng Ctrl+V                                 | Ảnh được tải, chèn đúng vị trí con trỏ                |
| T3.4.4  | [E]   | Kéo thả câu 5 lên vị trí 1 rồi tải lại        | Thứ tự được giữ                                            |
| T3.4.5  | [E]   | Kéo thả khi API reorder lỗi                         | UI hoàn tác, hiển thị toast lỗi                             |
| T3.4.6  | [E]   | Mở cùng đề ở hai tab, sửa ở cả hai             | Tab sau nhận hộp thoại xung đột                             |
| T3.4.7  | [E]   | Ngắt mạng khi đang soạn                            | Nháp giữ trong `localStorage`; khi có mạng đồng bộ lại |
| T3.4.8  | [E]   | Đề đã khóa (có người làm)                     | Chỉ đọc; nút nhân bản hoạt động                         |
| T3.4.9  | [E]   | Chia đều 100 điểm cho 7 câu                       | Tổng đúng bằng 100 (có điều chỉnh làm tròn)            |
| T3.4.10 | [E]   | Xuất bản với công thức lỗi/câu thiếu đáp án | Checklist chặn, chỉ rõ từng câu                             |
| T3.4.11 | [E]   | Đề 60 câu                                           | Soạn/cuộn mượt; danh sách câu không lag                   |

**DoD:** giáo viên dựng thử 1 đề thật 20 câu trong ≤ 30 phút.

---

### Bước 3.5 – Xem trước như học sinh, xuất bản, đóng, lưu trữ

**Yêu cầu cần đạt**

- Giáo viên xem trước đúng giao diện học sinh (không tạo attempt thật, không khóa đề).
- Xuất bản/đóng/lưu trữ có kiểm tra điều kiện và hậu quả rõ ràng.

**Cách thức triển khai**

1. **Preview:** `GET /admin/exams/{id}/preview` trả dữ liệu qua **schema học sinh** (không đáp án) để kiểm tra đúng cái học sinh sẽ thấy; FE dùng cùng component làm bài ở chế độ `previewMode` (không gọi autosave/finalize, đồng hồ giả).
2. **Đóng đề:** `POST /close` → trong một giao dịch: `status=closed`, rồi `finalize_attempt(reason='teacher_closed')` cho mọi attempt `in_progress` (gọi hàm ở bước 4.3; nếu chưa có thì stub, nối sau).
3. **Lưu trữ:** chỉ đề `closed`; ẩn khỏi danh sách mặc định; đưa vào hàng chờ dọn dữ liệu.
4. **Cửa sổ mở/đóng:** học sinh thấy đề khi `status=published AND (open_at IS NULL OR open_at ≤ now) AND (close_at IS NULL OR close_at > now)`; hiển thị đề sắp mở dưới dạng "Mở lúc …" (không cho bắt đầu).
5. Hộp thoại xác nhận nêu rõ hậu quả: "Đóng đề sẽ tự nộp bài của N học sinh đang làm".
6. Hiển thị thời gian theo `Asia/Ho_Chi_Minh` bằng `Intl.DateTimeFormat`; input datetime chuyển về UTC trước khi gửi.

**Test case**

| ID     | Loại | Kịch bản                                                   | Kết quả mong đợi                                                       |
| ------ | ----- | ------------------------------------------------------------ | -------------------------------------------------------------------------- |
| T3.5.1 | [E]   | Preview đề có đáp án                                   | Giao diện như học sinh; mạng trình duyệt không chứa `answer_key` |
| T3.5.2 | [I]   | Preview rồi kiểm tra DB                                    | Không có attempt, `locked_at` vẫn null                                |
| T3.5.3 | [I]   | Học sinh xem danh sách khi đề `open_at` ở tương lai | Hiển thị "Mở lúc …", `POST /start` trả `exam_not_open`           |
| T3.5.4 | [I]   | Học sinh bấm bắt đầu sau `close_at`                   | 409 `exam_not_open`                                                      |
| T3.5.5 | [I]   | Đóng đề khi 3 học sinh đang làm                       | Cả 3 chuyển `submitted` lý do `teacher_closed`                      |
| T3.5.6 | [I]   | Lưu trữ đề đang `published`                           | Bị từ chối (phải đóng trước)                                       |
| T3.5.7 | [U]   | Chuyển `2026-10-25 08:00 (GMT+7)` ↔ UTC                  | Lưu `01:00Z`, hiển thị lại đúng 08:00                              |
| T3.5.8 | [I]   | Đề giao cho lớp A, học sinh lớp B                       | Không thấy, `POST /start` trả 403/404                                 |
| T3.5.9 | [E]   | Đề `draft`                                               | Học sinh không thấy trong danh sách                                    |

**DoD:** M3 – tạo, xuất bản được một đề hoàn chỉnh và xem trước đúng.

---

## P4. LÀM BÀI & CHỐNG GIÁN ĐOẠN (Tuần 3) — ƯU TIÊN CAO NHẤT

### Bước 4.1 – Schema học sinh (không lộ đáp án) & bắt đầu bài (idempotent)

**Yêu cầu cần đạt**

- Học sinh không nhận được `answer_key`, `explanation_md` trong **bất kỳ** phản hồi nào.
- `POST /student/exams/{id}/start` idempotent: nhiều lần/nhiều tab vẫn một attempt.
- Xáo câu/lựa chọn ổn định theo `shuffle_seed`.

**Cách thức triển khai**

1. **Tách schema:** `schemas/student_*.py` định nghĩa `StudentQuestionOut` chỉ gồm `id, position, type, content_md, points, config_public`. Hàm `to_public_config(question)` **loại** mọi khóa nhạy cảm theo dạng câu (ví dụ TF chỉ giữ `statements[].{id,text_md}`; MCQ chỉ giữ `options`; chỉ giữ `scoring`/`max_files`/… không bao giờ chứa đáp án). Dùng `model_config = ConfigDict(extra="forbid")` cho schema ra để lỗi sớm.
2. **Start:**

   ```sql
   INSERT INTO attempts (id, exam_id, student_id, status, started_at, deadline_at, shuffle_seed, ...)
   VALUES (...)
   ON CONFLICT (exam_id, student_id) DO NOTHING;
   -- sau đó SELECT lại attempt (luôn trả bản đã có)
   ```

   Trong cùng giao dịch: kiểm tra học sinh thuộc lớp được giao, đề đang mở (giờ **server**), tính `deadline_at = LEAST(started_at + duration, close_at)`; đặt `exams.locked_at` nếu null (`UPDATE … WHERE locked_at IS NULL`).
3. Nếu attempt đã `submitted` → trả `status=submitted` (không tạo mới, không cho làm lại).
4. **Xáo trộn:** `rng = random.Random(f"{shuffle_seed}:{question_id}")`; hoán vị lựa chọn bằng `rng.shuffle`; thứ tự câu dùng `Random(seed)`. Hàm thuần, không dùng `random` toàn cục. Khi chấm, chấm theo **id lựa chọn**, không theo vị trí → xáo không ảnh hưởng điểm.
5. `GET /student/attempts/{id}`: kiểm `attempt.student_id == current_user.id` (nếu sai trả **404**, không phải 403, để không lộ sự tồn tại), gọi lazy-finalize nếu quá hạn (bước 4.3), trả câu hỏi (đã xáo), đáp án đã lưu, `deadline_at`, `server_now`, `status`.
6. Test tự động quét rò rỉ: hàm `assert_no_leak(json)` duyệt đệ quy tìm các khóa cấm (`answer_key`, `explanation_md`, `correct`, `accepted`, `values`, `tolerance`) và chạy trên mọi response `/student/*` trong test.

**Test case**

| ID      | Loại | Kịch bản                                                      | Kết quả mong đợi                                        |
| ------- | ----- | --------------------------------------------------------------- | ----------------------------------------------------------- |
| T4.1.1  | [S]   | `GET /student/attempts/{id}` đề đủ 5 dạng                | Không chứa khóa cấm nào (quét đệ quy)               |
| T4.1.2  | [S]   | Cố tình thêm field `answer_key` vào model ra              | Test/`extra="forbid"` báo lỗi                           |
| T4.1.3  | [I]   | `POST start` hai lần liên tiếp                             | Cùng một `attempt_id`, `started_at` không đổi      |
| T4.1.4  | [I]   | 20 request `start` song song (cùng học sinh)                | Đúng 1 dòng attempt, tất cả trả cùng id              |
| T4.1.5  | [I]   | `start` khi đề `closed`/chưa mở/không thuộc lớp      | `exam_not_open`/403 phù hợp, không tạo attempt        |
| T4.1.6  | [I]   | `start` khi đã `submitted`                                | Trả `status=submitted`, không tạo mới                 |
| T4.1.7  | [U]   | Cùng `shuffle_seed` gọi 100 lần                            | Thứ tự giống nhau; seed khác → thứ tự khác          |
| T4.1.8  | [U]   | Chấm bài đã xáo lựa chọn                                 | Điểm giống hệt bài không xáo                         |
| T4.1.9  | [S]   | Học sinh B đọc attempt của học sinh A                      | 404                                                         |
| T4.1.10 | [I]   | `deadline_at` khi `close_at` sớm hơn `start + duration` | Bằng `close_at`                                          |
| T4.1.11 | [I]   | Bắt đầu lần đầu                                           | `exams.locked_at` được set; sửa đề sau đó bị 409 |

**DoD:** test rò rỉ chạy trong CI và là điều kiện chặn merge.

---

### Bước 4.2 – Tự lưu đáp án từng câu (autosave) với `client_seq`

**Yêu cầu cần đạt**

- `PUT /student/attempts/{id}/answers/{question_id}` lưu từng câu; gói cũ không đè gói mới; từ chối khi hết hạn + grace.
- Phản hồi < 500 ms, kèm `server_now`, `deadline_at`, `status`.

**Cách thức triển khai**

1. **Upsert có điều kiện** trong một câu SQL (nguyên tử, không cần khóa dòng riêng):

   ```sql
   INSERT INTO answers (id, attempt_id, question_id, value, client_seq, updated_at)
   VALUES (:id, :attempt_id, :qid, :value, :seq, now())
   ON CONFLICT (attempt_id, question_id)
   DO UPDATE SET value = EXCLUDED.value, client_seq = EXCLUDED.client_seq, updated_at = now()
   WHERE answers.client_seq < EXCLUDED.client_seq
   RETURNING client_seq;
   ```

   Không có dòng trả về = gói cũ bị bỏ qua → trả `200 {accepted:false, current_seq}` (không phải lỗi, để client dừng retry).
2. **Kiểm tra thời gian cùng giao dịch:** `SELECT status, deadline_at FROM attempts WHERE id=:id AND student_id=:uid` (đọc 1 lần); nếu `status != 'in_progress'` hoặc `utcnow() > deadline_at + grace` → nếu quá hạn mà chưa finalize thì finalize (lazy), rồi trả `409 attempt_closed`. Trong grace (mặc định 10 giây) vẫn nhận để bù trễ mạng.
3. **Validate giá trị theo dạng câu** (schema `AnswerIn`): MCQ `choice` ∈ option ids; TF khóa ⊂ mệnh đề, kiểu bool (cho phép thiếu = chưa trả lời); chữ ≤ 500 ký tự; số ≤ 64 ký tự; file: `file_ids` thuộc về attempt này. Lưu **chuỗi thô** của số/chữ (chuẩn hóa chỉ khi chấm).
4. `question_id` phải thuộc `exam_id` của attempt (chống ghi chéo đề).
5. Tối ưu: không cập nhật `attempts` mỗi lần lưu (tránh khóa dòng nóng); `last_saved_at` có thể lấy `MAX(answers.updated_at)` khi giám sát. Chỉ trả JSON nhỏ (`{accepted, server_now, deadline_at, status}`).
6. Giới hạn kích thước body (≤ 8 KB) và rate limit mềm (≤ 20 request/giây/attempt) để chống lặp lỗi vòng.

**Test case**

| ID      | Loại | Kịch bản                                            | Kết quả mong đợi                                                       |
| ------- | ----- | ----------------------------------------------------- | -------------------------------------------------------------------------- |
| T4.2.1  | [I]   | Lưu câu 1 với seq=1                                | `accepted:true`, DB lưu đúng giá trị                                |
| T4.2.2  | [I]   | Gửi seq=3 rồi seq=2 (đến sai thứ tự)            | Giữ giá trị của seq=3; gói seq=2 `accepted:false`                   |
| T4.2.3  | [I]   | Gửi cùng seq hai lần                               | Idempotent, không lỗi                                                    |
| T4.2.4  | [I]   | 50 request song song cùng câu với seq tăng dần   | Kết quả cuối = seq lớn nhất, không deadlock                          |
| T4.2.5  | [I]   | Lưu sau `deadline_at + grace`                      | 409 `attempt_closed`; bài được finalize; đáp án không thay đổi |
| T4.2.6  | [I]   | Lưu trong grace (deadline + 5 s)                     | Chấp nhận                                                                |
| T4.2.7  | [I]   | Lưu vào attempt đã `submitted`                  | 409 `attempt_closed`                                                     |
| T4.2.8  | [S]   | `question_id` của đề khác                       | 404/422                                                                    |
| T4.2.9  | [S]   | MCQ `choice="Z"` / TF khóa lạ / số 1.000 ký tự | 422                                                                        |
| T4.2.10 | [S]   | Học sinh B ghi vào attempt học sinh A              | 404                                                                        |
| T4.2.11 | [I]   | Xóa đáp án (gửi `value=null`, seq mới)        | Đáp án trở về "chưa làm"                                            |
| T4.2.12 | [P]   | 40 học sinh × 1 lưu/2 giây trong 5 phút          | p95 < 500 ms, 0 lỗi 5xx                                                   |

**DoD:** pháp lý dữ liệu: không còn trường hợp "báo Đã lưu" mà DB không có (xác minh ở E2E 4.4).

---

### Bước 4.3 – `finalize_attempt` idempotent, lazy, sweeper, đóng đề

**Yêu cầu cần đạt**

- Một hàm duy nhất `finalize_attempt(attempt_id, reason)` an toàn khi gọi song song/nhiều lần.
- `submitted_at = deadline_at` khi hết giờ; hết giờ vẫn được chấm các đáp án đã lưu.
- Năm lớp bảo đảm (client, lazy, sweeper, giáo viên mở trang, đóng đề) cùng dùng hàm này.

**Cách thức triển khai**

1. **Thuật toán** (trong một giao dịch):

   ```python
   def finalize_attempt(db, attempt_id, reason):
       row = db.execute(text("""
           UPDATE attempts SET status='submitted',
                  submitted_at = LEAST(:now, deadline_at),
                  submit_reason = :reason
           WHERE id=:id AND status='in_progress'
           RETURNING id, exam_id""")).first()
       if row is None:          # đã có người thắng: bỏ qua, không chấm lại
           return get_attempt(db, attempt_id)
       grade_attempt(db, attempt_id)   # tự chấm, ghi score/ grading_status
       return get_attempt(db, attempt_id)
   ```

   `submitted_at = LEAST(now, deadline_at)`: nếu nộp **trước** hạn dùng `now`; nếu hết giờ dùng đúng `deadline_at`. Chỉ người "thắng" UPDATE mới gọi `grade_attempt`. Chấm trong **cùng giao dịch** để không có trạng thái `submitted` mà chưa có điểm (nếu chấm lỗi → rollback toàn bộ, attempt giữ `in_progress`, sweeper thử lại lần sau; ghi log lỗi).
2. **Lazy:** helper `ensure_fresh(attempt)` được gọi ở mọi endpoint chạm attempt: nếu `in_progress AND now > deadline_at + grace` → `finalize_attempt(reason='timeout')`.
3. **Sweeper (APScheduler):** mỗi 30 giây:

   ```sql
   SELECT id FROM attempts
   WHERE status='in_progress' AND deadline_at + (grace || ' seconds')::interval < now()
   ORDER BY deadline_at LIMIT 100 FOR UPDATE SKIP LOCKED;
   ```

   Mỗi id gọi `finalize_attempt`. `coalesce=True`, `max_instances=1`, `misfire_grace_time=60`. Chạy **1 worker** Uvicorn để không trùng; nếu chạy trùng cũng an toàn nhờ idempotent + `SKIP LOCKED`.
4. **Giáo viên mở giám sát/kết quả:** `finalize_expired(exam_id)` trước khi tính số liệu (đảm bảo đúng kể cả server từng ngủ).
5. **Đóng đề:** `finalize_all(exam_id, reason='teacher_closed')` — với `submitted_at = now()` (không phải deadline, vì bị buộc dừng).
6. **Nộp thủ công:** `POST /submit` gọi `finalize_attempt(reason='manual')`; luôn trả `200` với trạng thái hiện tại (idempotent, kể cả đã nộp).
7. Phục hồi sau khi server ngủ/khởi động lại: sự kiện `startup` chạy ngay một vòng sweeper.
8. Ghi `audit_log` cho mỗi finalize (lý do, thời điểm).

**Test case**

| ID      | Loại | Kịch bản                                                                    | Kết quả mong đợi                                                                       |
| ------- | ----- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| T4.3.1  | [I]   | Nộp thủ công khi còn thời gian                                           | `submitted`, `submit_reason=manual`, `submitted_at≈now`, đã chấm                 |
| T4.3.2  | [I]   | Gọi `submit` 10 lần song song                                             | Chấm đúng 1 lần (điểm không nhân đôi), cả 10 trả 200                           |
| T4.3.3  | [I]   | Sweeper và `submit` chạy cùng lúc                                       | Chỉ một bên thắng; trạng thái nhất quán; không lỗi                               |
| T4.3.4  | [I]   | Hết giờ, không ai chạm (freeze time +1 giờ) rồi chạy sweeper           | `timeout`, `submitted_at == deadline_at`, chấm theo đáp án đã lưu               |
| T4.3.5  | [I]   | Hết giờ; học sinh mở lại bài sau đó                                   | Lazy finalize; thấy trạng thái đã nộp                                                |
| T4.3.6  | [I]   | Server "ngủ" 2 giờ (không chạy sweeper); giáo viên mở trang giám sát | `finalize_expired` chuyển các bài quá hạn sang `submitted` trước khi hiển thị |
| T4.3.7  | [I]   | Giáo viên đóng đề với 5 học sinh đang làm                           | 5 bài `teacher_closed`, đã chấm                                                      |
| T4.3.8  | [I]   | Chấm lỗi (giả lập exception trong `grade_attempt`)                      | Giao dịch rollback; attempt vẫn `in_progress`; sweeper thử lại và log lỗi          |
| T4.3.9  | [I]   | 500 attempt quá hạn cùng lúc                                              | Sweeper xử lý theo lô 100, đủ trong < 1 phút, không giữ khóa lâu                 |
| T4.3.10 | [I]   | Hai tiến trình sweeper chạy trùng                                         | `SKIP LOCKED` → không xử lý trùng, không lỗi                                      |
| T4.3.11 | [U]   | `LEAST(now, deadline)`: nộp sớm 5 phút / nộp trễ                       | `now` / `deadline` tương ứng                                                        |
| T4.3.12 | [I]   | Khởi động lại server khi có bài quá hạn                               | Vòng sweeper khởi động finalize ngay                                                   |

**DoD:** bộ test đồng thời chạy 50 lần liên tiếp không flaky; đây là điều kiện để qua M4.

---

### Bước 4.4 – Client: đồng hồ theo server, hàng đợi offline, chỉ báo lưu

**Yêu cầu cần đạt**

- Đếm ngược theo `deadline_at` của server, không bị ảnh hưởng chỉnh giờ máy.
- Mất mạng/đóng tab/tắt máy không mất đáp án đã trả lời; tự đồng bộ khi có mạng.
- Chỉ báo "Đã lưu / Đang lưu… / Chưa gửi được" luôn đúng sự thật.

**Cách thức triển khai**

1. **`lib/timer.ts`:** `syncClock(server_now, deadline_at)` tính `offset = Date.parse(server_now) − Date.now()` (cải tiến: trừ nửa RTT đo được, và **giữ mẫu có RTT nhỏ nhất**); `remainingMs = deadline − (Date.now() + offset)`. Dùng `setInterval 250 ms` nhưng tính lại từ đồng hồ (không đếm tích lũy) để không trôi khi tab nền bị throttle; lắng nghe `visibilitychange` để đồng bộ lại ngay khi quay lại tab. Khi `remaining ≤ 0` gọi `submitOnce()` (cờ chống gọi lặp); server vẫn quyết định cuối.
2. **`lib/offlineQueue.ts`:** cấu trúc `Map<questionId, {value, seq}>` lưu `localStorage` khóa `quiz:{attemptId}:pending`. Mỗi thay đổi: `seq = ++counter[questionId]` (đếm lưu cùng `localStorage`, **khởi tạo từ `max(seq server, seq local)`** khi nạp lại), ghi vào hàng đợi **đồng bộ ngay** (trước debounce), rồi debounce 800 ms gửi `PUT`.
3. **Bộ gửi (sender):** mỗi câu có tối đa 1 request đang bay; nếu có thay đổi mới trong lúc đang gửi → đánh dấu dirty và gửi lại sau khi xong (gộp, luôn gửi giá trị mới nhất). Thành công (`accepted` true/false đều là xong) → xóa khỏi hàng đợi **nếu seq trong hàng đợi ≤ seq đã được ghi nhận**. Lỗi mạng/5xx → giữ, retry theo backoff (1, 2, 4, 8, tối đa 30 s) + sự kiện `online` kích hoạt gửi ngay. `409 attempt_closed` → dừng gửi, chuyển màn "Đã nộp".
4. **Chỉ báo lưu:** `đang lưu` khi còn request bay hoặc debounce chờ; `chưa gửi được` khi có mục trong hàng đợi bị lỗi > 5 giây (kèm banner "Mất kết nối – đang lưu tạm trên máy"); `đã lưu` chỉ khi hàng đợi rỗng **và** request cuối được server xác nhận.
5. **`beforeunload`:** nếu hàng đợi khác rỗng → hiển thị cảnh báo của trình duyệt; đồng thời dùng `navigator.sendBeacon`/`fetch keepalive` thử gửi lần cuối (body ≤ 64 KB, nhớ gắn token trong body/header bằng `fetch keepalive`).
6. **Resume:** khi nạp lại, so sánh hàng đợi cục bộ với đáp án server; mục nào `seq` cục bộ lớn hơn → gửi bù trước khi cho phép thao tác (hoặc song song nhưng hiển thị "đang đồng bộ").
7. **Lỗi lưu `localStorage`** (đầy/chế độ riêng tư): bắt `try/catch`, rơi về hàng đợi trong bộ nhớ + cảnh báo mềm.
8. **Xung đột nhiều tab:** dùng `BroadcastChannel('quiz-'+attemptId)` để các tab dùng chung bộ đếm `seq` và cảnh báo "Bài đang mở ở tab khác"; phía server đã an toàn nhờ `client_seq`.

**Test case**

| ID      | Loại | Kịch bản                                            | Kết quả mong đợi                                                                 |
| ------- | ----- | ----------------------------------------------------- | ------------------------------------------------------------------------------------ |
| T4.4.1  | [U]   | Đổi `Date.now` lệch +10 phút so với server     | `remainingMs` vẫn đúng theo server (sai số < 1 s)                              |
| T4.4.2  | [U]   | Tab nền 5 phút (giả lập throttle) rồi quay lại  | Đồng hồ nhảy đúng, không trôi                                                |
| T4.4.3  | [U]   | Đồng hồ về 0                                      | `submitOnce` gọi đúng 1 lần dù timer chạy tiếp                              |
| T4.4.4  | [U]   | Gõ nhanh 20 ký tự vào ô chữ                     | Chỉ ~1 request sau debounce; giá trị cuối đúng                                 |
| T4.4.5  | [E]   | Ngắt mạng, trả lời 5 câu, bật mạng             | Banner mất kết nối → tự đồng bộ → "Đã lưu"; DB có đủ 5 câu           |
| T4.4.6  | [E]   | Ngắt mạng, **đóng tab**, mở lại có mạng | Đáp án cục bộ được gửi bù; không mất                                     |
| T4.4.7  | [E]   | Server trả 503 trong 20 giây rồi phục hồi        | Retry backoff, không mất, chỉ báo đúng trạng thái                            |
| T4.4.8  | [U]   | Gói 1 (seq=1) đang bay, đã có thay đổi seq=2   | Gửi seq=2 sau; server giữ seq=2                                                    |
| T4.4.9  | [E]   | Hai tab cùng bài, sửa cùng câu                   | Giữ giá trị mới nhất; tab kia nhận cảnh báo                                  |
| T4.4.10 | [U]   | `localStorage` ném lỗi `QuotaExceeded`          | Rơi về bộ nhớ, hiện cảnh báo, không crash                                    |
| T4.4.11 | [E]   | Server trả `409 attempt_closed` khi đang gửi     | Dừng gửi; chuyển màn "Đã nộp"                                                 |
| T4.4.12 | [E]   | Đóng tab khi còn thay đổi chưa gửi             | Có cảnh báo `beforeunload`; sau đó mở lại vẫn còn bản nháp              |
| T4.4.13 | [E]   | Học sinh gõ → tắt nguồn ngay (≤ 800 ms sau gõ) | Giá trị đã nằm trong `localStorage` (ghi đồng bộ) nên khôi phục được |

**DoD:** các kịch bản nghiệm thu #1–#5 trong mục 12.2 spec đạt trên Chrome Android + Safari iOS + Chrome desktop.

---

### Bước 4.5 – Giao diện làm bài đầy đủ (5 dạng câu, điều hướng, nộp bài, tải file)

**Yêu cầu cần đạt**

- Hoàn thiện luồng: Danh sách đề → Giới thiệu → Bắt đầu → Làm bài → Xác nhận nộp → Đã nộp → (Kết quả).
- Điều hướng câu, đánh dấu "cần xem lại", tải file có tiến trình.

**Cách thức triển khai**

1. **State làm bài:** `useAttemptStore` (Zustand nhẹ hoặc `useReducer` + context): `answers`, `flags`, `currentIndex`, `saveState`, `clock`. Câu trả lời cập nhật **lạc quan** ngay trên UI rồi đẩy vào hàng đợi (bước 4.4).
2. **Component theo dạng:** `McqQuestion` (radio, `aria-checked`), `TfQuestion` (mỗi mệnh đề 2 nút toggle, cho phép bỏ chọn), `ShortTextQuestion`, `ShortNumberQuestion` (`inputMode="decimal"`, chấp nhận `,` `.` `/` `-`; **không** tự đổi giá trị người nhập), `FileQuestion`.
3. **`FileQuestion`:** chọn nhiều file → kiểm tra phía client (đuôi/dung lượng/số lượng) → nén ảnh → upload từng file tuần tự với tiến trình; sau khi server trả `file_id` → cập nhật `answers[q].file_ids` và đi qua autosave; hỗ trợ xóa/thay; hiển thị tên file + dung lượng; thất bại → nút thử lại từng file.
4. **`QuestionNav`:** lưới số câu; màu theo trạng thái (đã làm/chưa/cần xem lại/hiện tại) kèm biểu tượng; click nhảy câu; nút Nộp bài ở cuối lưới.
5. **Hộp thoại nộp:** tính số câu chưa trả lời, số câu đánh dấu; trong lúc `saveState != saved` → hiển thị "Đang đồng bộ…" và **chờ hàng đợi rỗng** (tối đa 10 giây) rồi mới gọi `submit` (tránh nộp khi còn đáp án chưa gửi); nếu hết giờ thì nộp ngay không chờ.
6. **Sau khi nộp:** xóa `localStorage` của attempt, chuyển `Submitted` (không lưu đáp án đúng); chặn nút Back quay lại bài (`replace`).
7. **Hết giờ:** hiển thị đếm ngược 3 giây "Hết giờ — đang nộp bài" → `submit`; nếu mạng lỗi, hiển thị trạng thái và vẫn dựa vào server finalize.
8. **Chống thao tác vô ý:** vô hiệu hóa chuột phải/copy chỉ ở mức nhẹ (không đảm bảo chống gian lận; ghi `blur_count`).

**Test case**

| ID      | Loại | Kịch bản                                            | Kết quả mong đợi                                                                                                       |
| ------- | ----- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| T4.5.1  | [E]   | Làm đủ 5 dạng câu rồi nộp                      | Màn "Đã nộp"; DB có đủ đáp án; điểm tự động đúng                                                          |
| T4.5.2  | [E]   | Nhập số `1,5` và `3/4`                         | Giá trị thô được lưu nguyên; chấm đúng ở bước chấm                                                          |
| T4.5.3  | [E]   | Bấm Nộp khi còn đáp án chưa gửi (mạng chậm) | Chờ đồng bộ rồi mới nộp; không mất câu cuối                                                                     |
| T4.5.4  | [E]   | Bấm Nộp hai lần nhanh                              | Chỉ một lần nộp; không báo lỗi                                                                                      |
| T4.5.5  | [E]   | Hết giờ khi đang gõ dở                           | Tự nộp, giá trị đã gõ đến thời điểm hết giờ (đã đẩy vào hàng đợi) được ghi nhận nếu trong grace |
| T4.5.6  | [E]   | Tải 3 ảnh hợp lệ + thêm ảnh thứ 4              | 3 ảnh thành công; ảnh thứ 4 bị từ chối với thông báo                                                            |
| T4.5.7  | [E]   | Tải file 15 MB / `.exe`                            | Từ chối rõ ràng (client + server)                                                                                      |
| T4.5.8  | [E]   | Tải ảnh rồi mất mạng giữa chừng                | Báo lỗi theo file, nút "Thử lại", các câu khác không ảnh hưởng                                                 |
| T4.5.9  | [E]   | Sau khi nộp bấm nút Back của trình duyệt        | Không quay lại trang làm bài; ở màn Đã nộp                                                                        |
| T4.5.10 | [M]   | Đề 60 câu trên điện thoại                      | Điều hướng/cuộn mượt; đồng hồ không bị che                                                                     |
| T4.5.11 | [E]   | TF: bỏ chọn một mệnh đề đã chọn              | Trở về "chưa làm", được lưu                                                                                        |
| T4.5.12 | [E]   | Đánh dấu "cần xem lại" rồi tải lại trang      | Cờ được giữ (lưu trong `localStorage` hoặc kèm answer)                                                           |

**DoD:** M4 – 3 học sinh thật làm trọn một bài trên điện thoại, không lỗi.

---

### Bước 4.6 – Tiếp tục bài, nhiều tab, ghi nhận rời tab (events)

**Yêu cầu cần đạt**

- Mở lại đề đang làm → vào đúng chỗ, đáp án và thời gian còn lại chính xác.
- `POST /events` ghi số lần rời tab, nhẹ, không làm phiền học sinh.

**Cách thức triển khai**

1. `ExamIntro` kiểm tra `GET /student/exams` trả trạng thái từng đề (`not_started/in_progress/submitted/released`); nút hiển thị "Tiếp tục làm bài" nếu `in_progress`.
2. Nạp bài: gọi `GET attempt` (đã lazy-finalize) → nếu `submitted` chuyển màn Đã nộp.
3. Ghi `blur`: sự kiện `visibilitychange`/`window blur` → hàng đợi nhẹ, gộp theo 5 giây, gửi `POST /events {type:'blur', at}`; server tăng `attempts.blur_count` bằng `UPDATE … SET blur_count = blur_count + 1` (nguyên tử). Rate limit 30 sự kiện/phút/attempt.
4. Ghi `audit_log` cho `start`, `submit`; **không** phạt, chỉ hiển thị cho giáo viên.
5. Xử lý phiên hết hạn khi làm bài: hiển thị modal "Đăng nhập lại để tiếp tục" giữ nguyên trạng thái cục bộ (không điều hướng đi), sau đăng nhập tiếp tục gửi hàng đợi.

**Test case**

| ID     | Loại | Kịch bản                                          | Kết quả mong đợi                                                              |
| ------ | ----- | --------------------------------------------------- | --------------------------------------------------------------------------------- |
| T4.6.1 | [E]   | Làm 5 câu, đóng tab, mở lại sau 2 phút       | Đáp án còn; đồng hồ giảm đúng 2 phút                                   |
| T4.6.2 | [E]   | Mở bài trên máy khác (điện thoại → laptop) | Cùng attempt, đáp án mới nhất, cùng đồng hồ                             |
| T4.6.3 | [E]   | Chuyển tab 3 lần                                  | `blur_count = 3`; giáo viên thấy; học sinh không bị phạt                 |
| T4.6.4 | [I]   | 100 sự kiện blur trong 1 phút                    | Rate limit; không làm nghẽn server; `blur_count` tăng hợp lý              |
| T4.6.5 | [E]   | Phiên hết hạn giữa bài                         | Modal đăng nhập lại; không mất bản nháp; tiếp tục gửi sau đăng nhập |
| T4.6.6 | [E]   | Mở lại đề đã `submitted`                    | Màn Đã nộp                                                                    |
| T4.6.7 | [E]   | Mở lại đề sau khi quá hạn                     | Lazy finalize; Đã nộp (`timeout`)                                            |
| T4.6.8 | [I]   | `events` vào attempt đã nộp                   | Bỏ qua êm (200, không lỗi)                                                    |

**DoD:** chạy trọn các kịch bản nghiệm thu #1–#6 (mục 12.2 spec).

---

## P5. CHẤM ĐIỂM, GIÁM SÁT, CÔNG BỐ, XUẤT DỮ LIỆU (Tuần 4)

### Bước 5.1 – Thư viện chấm điểm thuần (pure functions)

**Yêu cầu cần đạt**

- Hàm chấm từng dạng đúng đặc tả mục 3.4: MCQ, TF (3 chế độ), số, chữ.
- Không phụ thuộc DB; dễ test; không lỗi làm tròn.

**Cách thức triển khai**

1. `services/grading.py` — hàm thuần `grade_question(question, answer_value) -> GradeResult(score: Decimal, is_correct: bool|None, needs_manual: bool, needs_review: bool)`.
2. **MCQ:** `score = points if value.choice == key.correct else 0`; không trả lời → 0.
3. **TF:** đếm số mệnh đề đúng `k` trên `n`. `thpt` (n=4): bảng `{0:0, 1:0.10, 2:0.25, 3:0.50, 4:1.0}` × điểm; `proportional`: `points * k / n`; `all_or_nothing`: `points if k==n else 0`. Mệnh đề **không trả lời tính là sai**. Dùng `Decimal` và `quantize(Decimal('0.01'), ROUND_HALF_UP)` ở bước **cuối** (không làm tròn trung gian).
4. **Số:** `normalize_number(raw)` = `parse_number` (mục 9 spec) + xử lý: bỏ khoảng trắng, `,`→`.`, chặn dạng nguy hiểm (`1e999999`, chuỗi quá dài, mẫu số 0), hỗ trợ dấu âm và phân số `a/b` đơn giản; so sánh `abs(x - v) <= tol` (tuyệt đối) hoặc `abs(x - v) <= tol * abs(v)` (tương đối, với `v=0` dùng tuyệt đối); nhiều giá trị đúng → đúng nếu khớp bất kỳ.
5. **Chữ:** `normalize_text`: NFC → `strip` → gộp khoảng trắng (`re.sub(r"\s+"," ",s)`) → `casefold` (nếu không phân biệt hoa/thường) → tùy chọn bỏ dấu (`unicodedata.normalize('NFD')`, loại ký tự `Mn`, đổi `đ→d`). So khớp chính xác với tập đáp án đã chuẩn hóa. Chế độ `manual` → `needs_manual=True`; `auto` + `flag_wrong_for_review` → sai thì `needs_review=True`.
6. **File:** luôn `needs_manual=True`, `score=None` (chưa chấm).
7. Mọi hàm bắt dữ liệu rác (`value` sai kiểu) → coi như chưa trả lời, **không ném lỗi** (một đáp án hỏng không được làm hỏng cả bài).

**Test case**

| ID      | Loại | Kịch bản                                                                                | Kết quả mong đợi                                   |
| ------- | ----- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| T5.1.1  | [U]   | MCQ đúng / sai / bỏ trống                                                             | `points` / 0 / 0                                     |
| T5.1.2  | [U]   | TF `thpt` 4 mệnh đề, đúng 0/1/2/3/4                                                | 0% / 10% / 25% / 50% / 100%                            |
| T5.1.3  | [U]   | TF `proportional` 3 mệnh đề đúng 2                                                 | 2/3 điểm, làm tròn HALF_UP 2 chữ số              |
| T5.1.4  | [U]   | TF `all_or_nothing` thiếu 1 mệnh đề                                                 | 0 điểm                                               |
| T5.1.5  | [U]   | TF có mệnh đề bỏ trống                                                              | Tính là sai                                          |
| T5.1.6  | [U]   | Số: đáp án `0.5`; nhập `0,5` / `1/2` / `0.50` / `.5`                       | Đúng cả 4                                           |
| T5.1.7  | [U]   | Số có sai số tuyệt đối 0.01: nhập `3.141` với đáp án `3.14`                | Đúng; nhập `3.2` → sai                           |
| T5.1.8  | [U]   | Số sai số tương đối 1%, đáp án 0                                                 | Dùng so sánh tuyệt đối, không chia 0             |
| T5.1.9  | [U]   | Số: `abc`, `1/0`, `1e999999`, chuỗi 5.000 ký tự                                 | Sai, không ném ngoại lệ, không treo               |
| T5.1.10 | [U]   | Chữ: `"  Đa   Thức "` vs đáp án `"đa thức"` (không phân biệt hoa/thường) | Đúng                                                 |
| T5.1.11 | [U]   | Chữ `strip_accents`: `"da thuc"` vs `"đa thức"`                                  | Đúng; khi tắt `strip_accents` → sai              |
| T5.1.12 | [U]   | Chữ NFD vs NFC cùng chữ `ế`                                                         | Đúng (đã chuẩn hóa NFC)                          |
| T5.1.13 | [U]   | Chữ `manual` / file_upload                                                             | `needs_manual=True`, chưa có điểm                |
| T5.1.14 | [U]   | `value` sai kiểu (`{"choice": 5}`, `None`, chuỗi)                                 | 0 điểm, không ném lỗi                             |
| T5.1.15 | [U]   | Tổng điểm 10 câu 0.25/câu                                                            | Chính xác 2.50, không sai số float (dùng Decimal) |

**DoD:** coverage nhánh 100% cho `grading.py`.

---

### Bước 5.2 – Chấm tự động khi finalize, chấm tay, ghi đè điểm, chấm lại

**Yêu cầu cần đạt**

- `grade_attempt` chấm đủ câu, lưu từng `answers.score`, `attempts.score_auto`, `grading_status`.
- Chấm tay: nhập điểm 0…điểm câu + nhận xét; ghi đè điểm có ghi vết; chấm lại tự động khi giáo viên chủ động.

**Cách thức triển khai**

1. `grade_attempt(db, attempt_id)`: tải toàn bộ `questions` của đề + `answers` của attempt (2 truy vấn); với mỗi câu tạo/ cập nhật bản ghi `answers` (kể cả chưa trả lời → score 0 để đủ dòng); gọi `grade_question`; cộng `score_auto`; `grading_status = needs_manual` nếu còn câu `pending_manual`, ngược lại `auto_done`; `total_score = score_auto + score_manual`.
2. **Chấm tay:** `PUT /admin/answers/{id}/grade {score, comment, version}`; validate `0 ≤ score ≤ question.points`; ghi `graded_by`, `graded_at`; cập nhật lại `score_manual`/`total_score` bằng **tính lại từ SUM** trong cùng giao dịch (tránh lệch do cộng dồn); khi không còn câu pending → `grading_status = complete`.
3. **Optimistic lock:** `attempts.version` tăng mỗi lần chấm; PUT kèm `version` cũ → `409 version_conflict`.
4. **Ghi đè điểm câu tự động:** cho phép, nhưng đánh dấu `overridden=true` (thêm cột) để lần chấm lại tự động **không** ghi đè bản ghi đã chỉnh tay (trừ khi chọn "chấm lại cả câu đã sửa tay"); ghi `audit_log(grade_override, trước/sau)`.
5. **Chấm lại:** `POST /admin/exams/{id}/regrade` chạy nền theo lô trong một request ngắn (≤ 40 bài, đủ nhanh), cho phép `dry_run` để xem thay đổi điểm trước khi áp dụng (bảng "học sinh, điểm cũ → điểm mới").
6. Chấm theo **câu** cho cả lớp: `GET /admin/exams/{id}/questions/{qid}/answers` (phân trang), tiện chấm câu nộp file.

**Test case**

| ID      | Loại | Kịch bản                                            | Kết quả mong đợi                                                           |
| ------- | ----- | ----------------------------------------------------- | ------------------------------------------------------------------------------ |
| T5.2.1  | [I]   | Finalize bài đủ câu tự động                    | Mọi câu có `score`; `total_score` = tổng; `grading_status=auto_done` |
| T5.2.2  | [I]   | Đề có câu file                                    | `grading_status=needs_manual`; câu file `score=None`                      |
| T5.2.3  | [I]   | Học sinh bỏ trống một câu                        | Vẫn có dòng `answers`, score 0                                            |
| T5.2.4  | [I]   | Chấm tay 0 / điểm tối đa / vượt tối đa / âm | 0 và max hợp lệ; vượt/âm → 422                                          |
| T5.2.5  | [I]   | Chấm hết câu tay còn lại                         | `grading_status=complete`, `total_score` đúng                            |
| T5.2.6  | [I]   | Hai giáo viên chấm cùng một bài (version cũ)   | Người sau nhận 409                                                          |
| T5.2.7  | [I]   | Sửa đáp án đúng rồi `regrade dry_run`        | Hiện đúng chênh lệch; DB chưa đổi                                      |
| T5.2.8  | [I]   | `regrade` áp dụng                                 | Chỉ chấm lại câu tự động, **giữ** điểm đã sửa tay           |
| T5.2.9  | [I]   | Ghi đè điểm câu tự động                       | `audit_log` có người sửa, trước/sau; điểm tổng cập nhật           |
| T5.2.10 | [I]   | `total_score` sau nhiều lần sửa                  | Luôn bằng `SUM(answers.score)` (không lệch)                              |
| T5.2.11 | [I]   | Chấm lại bài khi đề đã đóng/lưu trữ        | Cho phép chấm tay; chấm lại tự động cần xác nhận                     |
| T5.2.12 | [S]   | Học sinh gọi API chấm                              | 403                                                                            |

**DoD:** M5 phần chấm: mọi dạng câu chấm đúng với bộ dữ liệu mẫu giáo viên cung cấp.

---

### Bước 5.3 – Giám sát trực tiếp & can thiệp (cộng giờ, mở lại, nộp hộ)

**Yêu cầu cần đạt**

- Bảng theo dõi Chưa vào / Đang làm / Đã nộp, thời gian còn lại, số câu đã trả lời, lần lưu cuối, số lần rời tab; polling 10 giây.
- Cộng giờ cho từng học sinh; mở lại bài; nộp hộ; thu hồi phiên — đều idempotent và có ghi vết.

**Cách thức triển khai**

1. **`GET /admin/exams/{id}/attempts`:** (1) `finalize_expired(exam_id)`; (2) **một truy vấn** gộp: `students` (join `class_members` ∩ `exam_classes`) LEFT JOIN `attempts` và `answers` aggregate (`COUNT(*) FILTER (WHERE value IS NOT NULL)`, `MAX(updated_at)`) để tránh N+1; trả `server_now`.
2. FE dùng `refetchInterval: 10_000` + `refetchIntervalInBackground: false`; tính "còn lại" ở client bằng `deadline_at` + `offset`, chỉ làm mới dữ liệu mỗi 10 giây (giảm tải).
3. **Cộng giờ:** `POST /admin/attempts/{id}/extend {seconds}` → `UPDATE attempts SET extra_seconds = extra_seconds + :s, deadline_at = LEAST(deadline_at + :s * interval '1 second', COALESCE(exam.close_at + …, deadline_at + …)) WHERE id=:id AND status='in_progress'`. Giới hạn 1–3600 giây/lần; ghi `audit_log`. (Quy tắc: giáo viên cộng giờ **có thể vượt** `close_at` — chốt khi duyệt; mặc định cho phép và ghi vết.)
4. **Mở lại:** chỉ khi `submitted`: `UPDATE … SET status='in_progress', deadline_at = now() + :seconds, submitted_at=NULL, submit_reason=NULL, extra_seconds = extra_seconds + :seconds`; **giữ** đáp án; xóa điểm tự động cũ (sẽ chấm lại khi finalize) nhưng **giữ điểm chấm tay** của câu file; ghi `audit_log`. Yêu cầu nhập số phút cấp thêm (mặc định 10).
5. **Nộp hộ:** `finalize_attempt(reason='teacher_forced')` (idempotent).
6. **Thu hồi phiên:** xóa `sessions` của học sinh; học sinh đăng nhập lại và tiếp tục (đáp án nguyên vẹn).
7. Học sinh đang làm nhận thời gian mới ở lần autosave kế tiếp (phản hồi chứa `deadline_at` mới) → đồng hồ cập nhật ngay.

**Test case**

| ID      | Loại | Kịch bản                                                   | Kết quả mong đợi                                                   |
| ------- | ----- | ------------------------------------------------------------ | ---------------------------------------------------------------------- |
| T5.3.1  | [I]   | Lớp 30 học sinh: 10 chưa vào, 15 đang làm, 5 đã nộp | Bảng đếm đúng, không N+1 (≤ 5 truy vấn)                        |
| T5.3.2  | [I]   | Mở giám sát khi 3 bài đã quá hạn nhưng chưa quét  | Được finalize trước khi hiển thị                                |
| T5.3.3  | [I]   | Cộng 5 phút cho học sinh A                                | Chỉ A đổi `deadline_at` (+300 s), B không đổi                  |
| T5.3.4  | [E]   | Học sinh A đang làm bài, giáo viên cộng giờ          | Đồng hồ của A cập nhật sau lần autosave kế tiếp (≤ ~1 s)     |
| T5.3.5  | [I]   | Cộng giờ cho bài đã `submitted`                       | 409 (dùng "mở lại")                                                 |
| T5.3.6  | [I]   | Mở lại bài đã nộp, cấp 10 phút                       | `in_progress`, đáp án giữ nguyên, `deadline = now + 10 phút` |
| T5.3.7  | [I]   | Mở lại bài rồi hết giờ lần nữa                       | Finalize lại, chấm lại đúng, không nhân đôi điểm            |
| T5.3.8  | [I]   | Nộp hộ 2 lần liên tiếp                                  | Lần 2 idempotent                                                      |
| T5.3.9  | [I]   | Thu hồi phiên học sinh đang làm                         | 401 ở request sau; đăng nhập lại tiếp tục đúng bài           |
| T5.3.10 | [S]   | `seconds` âm / 0 / 100000                                 | 422                                                                    |
| T5.3.11 | [I]   | Mỗi can thiệp                                              | Có dòng `audit_log` (ai, khi nào, giá trị)                      |
| T5.3.12 | [P]   | 40 học sinh, polling 10 giây trong 10 phút                | p95 < 800 ms, tải DB ổn định                                       |

**DoD:** kịch bản nghiệm thu #8 đạt.

---

### Bước 5.4 – Công bố kết quả & màn hình kết quả học sinh

**Yêu cầu cần đạt**

- Mặc định `hidden`; công bố cho cả lớp hoặc từng học sinh, mức `score_only` | `full`; thu hồi được.
- Backend kiểm cờ công bố, không chỉ ẩn ở UI.

**Cách thức triển khai**

1. `POST /admin/exams/{id}/release {scope: "all" | {attempt_ids}, visibility}`: cập nhật `attempts.released=true`, `released_visibility`; chỉ áp dụng cho attempt `submitted` **và** `grading_status != needs_manual` (nếu còn chấm tay → cảnh báo, cho phép ép `force=true`).
2. `POST /unrelease`: đặt lại `released=false`.
3. `GET /student/attempts/{id}/result`:
   - Không `released` → `403 result_not_released` (không dữ liệu).
   - `score_only` → `{total_score, max_score}` (+ thang 10 nếu bật).
   - `full` → thêm từng câu: đáp án học sinh, đáp án đúng, điểm câu, lời giải, nhận xét. Dùng schema **`StudentResultOut`** riêng, dựng theo `released_visibility`.
4. `/student/exams` hiển thị "Có kết quả" chỉ khi `released`.
5. Thu hồi → mọi lần gọi tiếp theo trả 403 ngay (không cache; `Cache-Control: no-store`).
6. Ảnh trong lời giải: đi qua `/files/{id}` có kiểm tra quyền theo `released`.

**Test case**

| ID      | Loại | Kịch bản                                          | Kết quả mong đợi                                                                        |
| ------- | ----- | --------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| T5.4.1  | [S]   | Học sinh gọi `/result` khi chưa công bố      | 403, không có điểm/đáp án trong body                                                 |
| T5.4.2  | [I]   | Công bố `score_only`                            | Chỉ có điểm tổng, không có đáp án đúng/lời giải (quét rò rỉ)               |
| T5.4.3  | [I]   | Công bố `full`                                  | Có đáp án, lời giải, điểm từng câu                                                |
| T5.4.4  | [I]   | Công bố cho 1 học sinh                           | Chỉ học sinh đó xem được; người khác 403                                          |
| T5.4.5  | [I]   | Công bố khi còn bài `needs_manual`            | Cảnh báo; không công bố bài chưa chấm trừ khi `force`                            |
| T5.4.6  | [I]   | Thu hồi công bố rồi học sinh F5                | 403 ngay                                                                                    |
| T5.4.7  | [S]   | Học sinh A xem `/result` của B (đã công bố) | 404                                                                                         |
| T5.4.8  | [E]   | UI học sinh sau công bố                          | Xuất hiện nút "Xem kết quả"; hiển thị đúng mức                                    |
| T5.4.9  | [S]   | Ảnh trong lời giải khi chưa công bố           | 403                                                                                         |
| T5.4.10 | [I]   | Học sinh bị mở lại bài sau khi đã công bố  | Kết quả bị ẩn lại (released=false) hoặc cảnh báo cho giáo viên (chốt khi duyệt) |

**DoD:** kịch bản nghiệm thu #7 đạt.

---

### Bước 5.5 – Xuất CSV, dọn dữ liệu, lưu trữ ngắn hạn

**Yêu cầu cần đạt**

- Xuất CSV điểm tổng + từng câu; Excel mở không lỗi chữ Việt.
- Xóa dữ liệu theo đề; job dọn hằng ngày theo `DATA_RETENTION_DAYS`.

**Cách thức triển khai**

1. **CSV:** `StreamingResponse` ghi theo hàng (generator); mã hóa **UTF-8 có BOM** (`\ufeff`) để Excel hiểu dấu; dấu phân cách `,`; escape bằng `csv.writer`; chống **CSV injection**: ô bắt đầu bằng `= + - @` thì thêm `'` đầu (áp dụng cho họ tên/đáp án học sinh).
2. Cột: `ho_ten, username, lop, trang_thai, bat_dau, nop_luc, ly_do_nop, tong_diem, thang_10, câu_1…câu_n`; thời gian định dạng `Asia/Ho_Chi_Minh`.
3. **Xóa dữ liệu đề:** `DELETE /admin/exams/{id}/data` yêu cầu `confirm_title`; xóa `answers`, `attempts`, `files` (DB) **và** object trong R2 theo lô (tối đa 1.000/lần `delete_objects`); chạy trong giao dịch cho DB, xóa object **sau khi commit**; lỗi xóa object → ghi `files_orphan` để job dọn lại.
4. **Job retention (APScheduler, 03:00 hằng ngày):** tìm đề `archived` hoặc `closed` quá `DATA_RETENTION_DAYS` → xóa dữ liệu như trên; xóa `sessions` hết hạn; xóa `audit_log` > 180 ngày. Mỗi lần chạy giới hạn thời gian/khối lượng để không treo; log kết quả.
5. Nhắc giáo viên **xuất CSV trước** (modal xóa hiển thị nút xuất).

**Test case**

| ID      | Loại | Kịch bản                                               | Kết quả mong đợi                                    |
| ------- | ----- | -------------------------------------------------------- | ------------------------------------------------------- |
| T5.5.1  | [I]   | Xuất CSV đề 30 học sinh × 20 câu                   | Đủ 30 dòng; điểm khớp bảng điểm                |
| T5.5.2  | [M]   | Mở CSV bằng Excel                                      | Hiển thị đúng tiếng Việt có dấu                 |
| T5.5.3  | [S]   | Họ tên `=HYPERLINK("http://evil")`                   | Ô được vô hiệu hóa công thức (tiền tố `'`) |
| T5.5.4  | [I]   | Học sinh chưa vào/chưa nộp                          | Có dòng, trạng thái đúng, điểm trống           |
| T5.5.5  | [I]   | Tên có dấu phẩy/ngoặc kép/xuống dòng             | Escape đúng; cột không lệch                        |
| T5.5.6  | [I]   | Xóa dữ liệu đề nhưng gõ sai tiêu đề xác nhận | 422; không xóa                                        |
| T5.5.7  | [I]   | Xóa dữ liệu đề có 100 file nộp                    | DB sạch; object bị xóa khỏi R2                      |
| T5.5.8  | [I]   | Xóa object R2 lỗi giữa chừng                         | DB đã xóa; file mồ côi được job dọn lại sau   |
| T5.5.9  | [I]   | Job retention với đề 91 ngày tuổi (freeze time)     | Bị dọn; đề 89 ngày **không** bị dọn       |
| T5.5.10 | [I]   | Xuất CSV đề 5.000 dòng                               | Streaming, bộ nhớ ổn định, < 10 s                  |

**DoD:** M5 hoàn tất khi giáo viên chạy trọn vòng đời một đề (tạo → thi → chấm → công bố → xuất → xóa).

---

### Bước 5.6 – Giao diện giáo viên: giám sát, chấm bài, kết quả, bảng điều khiển

**Yêu cầu cần đạt**

- Hoàn thiện màn hình giáo viên 1, 7, 8, 9, 10 (mục 11) theo prototype P0.

**Cách thức triển khai**

1. **Bảng điều khiển:** truy vấn tổng hợp: đề sắp/đang diễn ra, số bài cần chấm, đề quá hạn chưa công bố.
2. **Giám sát:** bảng ảo hóa nếu > 100 hàng; badge trạng thái; menu hành động có xác nhận; nút **"Làm nóng hệ thống"** gọi `/readyz` + một truy vấn nhẹ; hiển thị thời gian server và độ trễ.
3. **Chấm bài:** layout hai khung (danh sách bài | chi tiết); `Prefetch` bài kế tiếp; phím tắt; ô điểm có kiểm tra theo điểm tối đa; hiển thị file nộp (ảnh phóng to bằng lightbox, PDF mở tab mới qua signed URL).
4. **Kết quả:** bảng điểm có sắp xếp/lọc/thống kê (trung bình, cao nhất, thấp nhất, phân bố điểm — biểu đồ cột đơn giản); công bố/thu hồi; xuất CSV; xóa dữ liệu.
5. **Cài đặt:** đổi mật khẩu, `DATA_RETENTION_DAYS` (lưu trong bảng `settings`).
6. Mọi mutation hiển thị toast; lỗi 409 hiện hộp thoại giải thích.

**Test case**

| ID     | Loại | Kịch bản                                               | Kết quả mong đợi                                  |
| ------ | ----- | -------------------------------------------------------- | ----------------------------------------------------- |
| T5.6.1 | [E]   | Giám sát trong khi 5 học sinh đang làm (mô phỏng) | Số liệu cập nhật sau ≤ 10 giây                  |
| T5.6.2 | [E]   | Bấm "Làm nóng hệ thống"                             | Hiển thị thành công + thời gian phản hồi       |
| T5.6.3 | [E]   | Chấm 10 bài liên tiếp bằng phím tắt               | Không mất điểm đã nhập; chuyển bài mượt    |
| T5.6.4 | [E]   | Nhập điểm vượt điểm tối đa                      | Báo lỗi tại ô, không gửi                        |
| T5.6.5 | [E]   | Xem file nộp (ảnh/PDF)                                 | Mở được; link hết hạn sau ~5 phút              |
| T5.6.6 | [E]   | Công bố rồi thu hồi                                  | Trạng thái đúng ở cả giáo viên và học sinh  |
| T5.6.7 | [E]   | Xuất CSV rồi xóa dữ liệu                            | Hộp thoại nhắc xuất; xóa xong danh sách trống  |
| T5.6.8 | [E]   | Xung đột chấm điểm (409)                            | Hộp thoại "Bài vừa được cập nhật", tải lại |
| T5.6.9 | [M]   | Giám sát trên điện thoại                           | Dạng card đầy đủ chức năng chính              |

**DoD:** giáo viên chạy trọn quy trình giám sát và chấm trên dữ liệu mô phỏng.

---

## P6. KIỂM THỬ CHẤT LƯỢNG, BẢO MẬT, TẢI (Tuần 4–5)

### Bước 6.1 – Rà soát & kiểm thử bảo mật

**Yêu cầu cần đạt**

- Mọi mục bảo mật ở mục 10 spec có test chứng minh.
- Không có lỗ hổng nghiêm trọng (OWASP Top 10 liên quan).

**Cách thức triển khai**

1. **Ma trận phân quyền tự động:** duyệt toàn bộ route từ `app.routes`; với mỗi route gọi bằng (ẩn danh, học sinh, admin) và kiểm tra mã trả về khớp bảng kỳ vọng; test **thất bại nếu thêm route mới chưa khai báo quyền**.
2. **Quét rò rỉ:** gọi toàn bộ endpoint `/student/*` trên bộ dữ liệu đủ 5 dạng, gồm trước/sau nộp, trước/sau công bố; chạy `assert_no_leak`.
3. **IDOR:** thử dùng id của học sinh khác trên mọi endpoint có `{id}`.
4. **Injection:** SQLAlchemy tham số hóa (cấm nối chuỗi SQL — rule `bandit`/grep CI); thử `' OR 1=1 --` ở username, tìm kiếm.
5. **XSS:** đưa payload vào tên học sinh, nội dung đề, tên file, nhận xét; kiểm tra render ở mọi màn hình.
6. **Header & cấu hình:** CSP, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, HSTS (do nền tảng), `Permissions-Policy`; CORS chặt; tắt `/docs` ở production.
7. **Phụ thuộc:** `pip-audit`, `npm audit` trong CI; `gitleaks`.
8. **Brute-force/Rate limit:** đăng nhập, upload, events.
9. Rà soát log: không chứa mật khẩu/token.

**Test case**

| ID      | Loại | Kịch bản                                               | Kết quả mong đợi                                                  |
| ------- | ----- | -------------------------------------------------------- | --------------------------------------------------------------------- |
| T6.1.1  | [S]   | Ma trận quyền (ẩn danh/HS/admin × mọi route)        | 100% khớp kỳ vọng; route mới thiếu khai báo → test đỏ        |
| T6.1.2  | [S]   | Quét rò rỉ toàn bộ `/student/*`                   | Không có khóa cấm ở mọi trạng thái                            |
| T6.1.3  | [S]   | IDOR: id attempt/file/answer của người khác          | 404/403, không dữ liệu                                             |
| T6.1.4  | [S]   | SQL injection ở login/tìm kiếm/CSV                    | Không ảnh hưởng; dữ liệu giữ nguyên                           |
| T6.1.5  | [S]   | XSS lưu trữ trong tên/đề/nhận xét/tên file       | Không thực thi script ở mọi trang                                 |
| T6.1.6  | [S]   | Kiểm tra header bảo mật production                    | Đủ header; `/docs` tắt                                           |
| T6.1.7  | [S]   | `pip-audit`/`npm audit`                              | Không lỗ hổng mức cao chưa xử lý                               |
| T6.1.8  | [S]   | Brute-force đăng nhập 100 lần/phút                  | Bị rate limit; log cảnh báo                                        |
| T6.1.9  | [S]   | Grep log cho `password`, `Bearer`, token             | Không xuất hiện                                                    |
| T6.1.10 | [S]   | Dùng token đã thu hồi / token của người bị khóa | 401                                                                   |
| T6.1.11 | [S]   | Gửi request thao tác (PUT answer) với `Origin` lạ  | Không được CORS cho phép đọc phản hồi; token vẫn bắt buộc |

**DoD:** báo cáo bảo mật `docs/security-review.md`, không còn lỗi mức cao/nghiêm trọng.

---

### Bước 6.2 – Kiểm thử đồng thời & tải

**Yêu cầu cần đạt**

- Chịu 50 học sinh làm bài đồng thời (gấp ~8 lần thiết kế 6 người) với p95 autosave < 500 ms, không mất đáp án.
- Chịu "thundering herd": 40 học sinh bấm Bắt đầu cùng lúc; 40 bài cùng hết giờ.

**Cách thức triển khai**

1. Công cụ: **k6** hoặc **Locust**; kịch bản mô phỏng học sinh: login → list → start → 30 lần `PUT answer` (cách nhau 2–5 giây ngẫu nhiên) → submit.
2. Môi trường: staging giống production (Render free + Neon free) — **không** đo trên laptop cục bộ.
3. Thu thập: p50/p95/p99, tỉ lệ lỗi, thời gian truy vấn chậm (`pg_stat_statements` nếu có), số kết nối DB.
4. **Tối ưu theo dữ liệu đo:** thêm index thiếu; gộp truy vấn; giảm kích thước payload `GET attempt` (gzip — bật `GZipMiddleware` cho phản hồi > 1 KB); đảm bảo kết nối không vượt giới hạn pool Neon.
5. Kiểm tra **đồng thời nghiệp vụ:** script gọi song song `start`, `submit`, `finalize`, `PUT answers` nhiều lần và kiểm tra bất biến: mỗi (exam, student) một attempt; mỗi attempt chấm một lần; `total_score = Σ`.
6. Kiểm tra bộ nhớ Render free (512 MB): theo dõi RSS khi 50 người dùng.

**Test case**

| ID     | Loại | Kịch bản                                            | Kết quả mong đợi                                                                     |
| ------ | ----- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| T6.2.1 | [P]   | 50 VU làm bài 20 phút                              | p95 `PUT answer` < 500 ms; lỗi 5xx < 0.1%                                             |
| T6.2.2 | [P]   | 40 học sinh `start` cùng giây                    | Mỗi người đúng 1 attempt; không deadlock                                           |
| T6.2.3 | [P]   | 40 bài hết giờ cùng lúc; sweeper chạy           | Tất cả finalize < 60 s, chấm đúng một lần                                         |
| T6.2.4 | [P]   | 50 học sinh upload ảnh 3 MB đồng thời            | Không timeout; bộ nhớ không vượt 400 MB                                            |
| T6.2.5 | [P]   | Giáo viên mở giám sát 40 HS khi 50 VU đang lưu | Phản hồi < 1 s                                                                         |
| T6.2.6 | [I]   | Kiểm tra bất biến sau test tải                    | 0 vi phạm (attempt trùng, điểm sai, mất đáp án đã xác nhận)                  |
| T6.2.7 | [P]   | Soak test 60 phút tải 10 VU                         | Không rò rỉ bộ nhớ/kết nối                                                        |
| T6.2.8 | [P]   | Cold start sau 20 phút ngủ                          | Request đầu thành công sau ≤ ~60 s nhờ backoff phía client; không mất dữ liệu |
| T6.2.9 | [P]   | Neon compute ngủ rồi gọi                           | Kết nối lại < 2 s nhờ `pool_pre_ping`                                              |

**DoD:** báo cáo `docs/load-test.md` kèm số liệu và quyết định (đủ dùng / nâng cấp gói).

---

### Bước 6.3 – Kiểm thử End-to-End & nghiệm thu theo 10 kịch bản

**Yêu cầu cần đạt**

- Tự động hóa tối đa các kịch bản mục 12.2 spec bằng Playwright; phần còn lại làm thủ công có biên bản.
- Chạy trên: Chrome desktop, Chrome Android, Safari iOS (thủ công).

**Cách thức triển khai**

1. Playwright với `browserContext.setOffline(true/false)`, `page.clock` (điều khiển thời gian trình duyệt), `route` (giả lập 503/chậm), nhiều context (nhiều học sinh).
2. Dữ liệu: fixture API tạo lớp/đề/học sinh bằng script trước mỗi test; dọn sau test.
3. Kịch bản nghiệm thu:

| #  | Kịch bản (mục 12.2)                        | Cách tự động hóa                                                      |
| -- | --------------------------------------------- | -------------------------------------------------------------------------- |
| 1  | Làm 5 câu, đóng tab, mở lại sau 2 phút | `page.close()` + trang mới cùng storage state; `clock.fastForward`   |
| 2  | Ngắt mạng, trả lời tiếp, bật mạng      | `context.setOffline`                                                     |
| 3  | Tắt máy không mở lại đến quá hạn     | Không mở lại; chạy sweeper (gọi endpoint nội bộ test) rồi kiểm DB |
| 4  | Chỉnh đồng hồ máy sớm/trễ              | `page.clock.install({time})` lệch; đối chiếu đồng hồ hiển thị   |
| 5  | Hai tab cùng bài                            | Hai `page` cùng context                                                 |
| 6  | Server ngủ khi vào                          | `route` trả 503/timeout 3 lần đầu                                    |
| 7  | Nộp rồi xem đường dẫn kết quả         | Gọi trực tiếp URL/API result                                            |
| 8  | Cộng 5 phút cho 1 học sinh                 | 2 context HS + 1 context admin                                             |
| 9  | 6–10 học sinh cùng làm và nộp           | Nhiều context song song (hoặc k6)                                        |
| 10 | Tải file 15 MB / `.exe`                    | `setInputFiles`                                                          |

4. CI chạy Playwright trên PR vào `main` (bộ rút gọn) và trước mỗi release (bộ đầy đủ).
5. Biên bản nghiệm thu thủ công trên thiết bị thật: ghi thiết bị, trình duyệt, kết quả, ảnh chụp.

**Test case (cấp hệ thống, bổ sung ngoài 10 kịch bản)**

| ID         | Loại | Kịch bản                                                                                                | Kết quả mong đợi                                       |
| ---------- | ----- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| T6.3.1–10 | [E]   | 10 kịch bản mục 12.2                                                                                   | Đạt đúng "kết quả mong đợi" của spec              |
| T6.3.11    | [E]   | Vòng đời đầy đủ: tạo lớp → tạo đề → 3 HS thi → chấm tay → công bố → xuất CSV → xóa | Không lỗi, số liệu nhất quán                         |
| T6.3.12    | [E]   | Học sinh làm bài đúng lúc giáo viên đóng đề                                                   | Bài được nộp `teacher_closed`; HS thấy thông báo |
| T6.3.13    | [E]   | Đề có `close_at` sớm hơn `start + duration`                                                      | Đồng hồ đếm đến `close_at`                        |
| T6.3.14    | [E]   | Giáo viên mở lại bài của HS đã nộp                                                               | HS vào lại, đáp án giữ nguyên, có thêm giờ       |
| T6.3.15    | [M]   | Safari iOS: bàn phím, `inputmode`, `beforeunload`, `localStorage` (chế độ riêng tư)          | Hoạt động; nếu hạn chế có cảnh báo thân thiện   |
| T6.3.16    | [M]   | Chrome Android khi chuyển ứng dụng/khóa màn hình 3 phút                                            | Đồng hồ đúng khi quay lại; không mất đáp án     |

**DoD:** M6 – 100% kịch bản nghiệm thu đạt; không còn lỗi mức nghiêm trọng/cao.

---

## P7. TRIỂN KHAI HOSTING (Tuần 5)

> Trước khi triển khai: kiểm tra lại điều kiện gói miễn phí hiện hành trên trang chính thức của từng dịch vụ (spec đã lưu ý các điều kiện thay đổi thường xuyên).

### Bước 7.1 – Dịch vụ dữ liệu: Neon (Postgres) & Cloudflare R2 (lưu file)

**Yêu cầu cần đạt**

- Có DB Postgres bền + bucket riêng tư; chuỗi kết nối pooled; khóa truy cập tối thiểu quyền.

**Cách thức triển khai**

1. **Neon:** tạo project (vùng gần Việt Nam nhất, ví dụ Singapore); lấy 2 chuỗi: **pooled** (dùng cho app) và **direct** (dùng cho Alembic migration). `sslmode=require`.
2. Chạy migration từ máy cá nhân hoặc CI với chuỗi direct: `alembic upgrade head`; tạo admin bằng CLI.
3. **R2:** tạo bucket `quiz-files` **riêng tư**; tạo API token chỉ có quyền `Object Read & Write` trên đúng bucket; lấy `S3_ENDPOINT`, `ACCESS_KEY`, `SECRET_KEY`. Cấu hình CORS bucket **không cần** vì truy cập qua backend/signed URL (nếu FE tải thẳng lên signed URL, thêm CORS cho origin FE).
4. **Lifecycle rule:** (tùy chọn) tự xóa object cũ > `DATA_RETENTION_DAYS + 30`.
5. Chỉ lưu bí mật trong **trình quản lý biến môi trường** của dịch vụ, không trong repo.
6. Sao lưu: bật Point-in-time/branch của Neon theo gói; hàng tuần chạy `pg_dump` (GitHub Actions định kỳ) lưu artifact mã hóa hoặc R2 riêng (giữ 4 bản).
7. Ghi lại thông tin tài khoản/khôi phục ở nơi an toàn.

**Test case**

| ID     | Loại | Kịch bản                                                           | Kết quả mong đợi                 |
| ------ | ----- | -------------------------------------------------------------------- | ------------------------------------ |
| T7.1.1 | [M]   | `alembic upgrade head` lên Neon                                   | Thành công; bảng đủ             |
| T7.1.2 | [I]   | App (cục bộ) nối Neon pooled, chạy bộ test tích hợp rút gọn | Pass                                 |
| T7.1.3 | [I]   | Upload/đọc/xóa object trên R2 bằng `S3Storage`                | Pass                                 |
| T7.1.4 | [S]   | Truy cập trực tiếp URL object không ký                          | Bị từ chối (403)                  |
| T7.1.5 | [S]   | Token R2 dùng thử với bucket khác                                | Bị từ chối                        |
| T7.1.6 | [I]   | Để Neon rảnh 6 phút rồi truy vấn                               | Thành công (compute tự bật lại) |
| T7.1.7 | [M]   | Khôi phục thử: `pg_dump` → DB tạm → kiểm dữ liệu          | Khôi phục đúng                   |
| T7.1.8 | [S]   | Quét repo/CI log tìm secret                                        | Không có                           |

**DoD:** DB + bucket sẵn sàng; có quy trình sao lưu/khôi phục đã thử.

---

### Bước 7.2 – Triển khai Backend lên Render

**Yêu cầu cần đạt**

- Backend chạy ổn định bằng Docker, 1 worker, tự triển khai khi push `main` (sau CI xanh).
- Biến môi trường đúng; healthcheck hoạt động; log xem được.

**Cách thức triển khai**

1. **Dockerfile** (đa tầng): `python:3.12-slim`, cài bằng `uv`, người dùng không phải root, `CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","$PORT","--workers","1","--proxy-headers","--forwarded-allow-ips","*"]`.
2. Render: Web Service (Docker) → kết nối repo, thư mục gốc `backend/`, **Health Check Path** `/healthz`, tắt Auto-Deploy trước CI (hoặc dùng "Deploy hook" gọi từ GitHub Actions sau khi test xanh).
3. Biến môi trường: toàn bộ Phụ lục A (DATABASE_URL pooled, SECRET_KEY ngẫu nhiên ≥ 32 byte, CORS_ORIGINS đúng domain FE, S3_*, `ENV=production`, tắt `/docs`).
4. **Migration:** không chạy trong tiến trình app; chạy bước `alembic upgrade head` bằng chuỗi direct trước khi deploy (tay hoặc job CI); tuân quy tắc **migration tương thích ngược** (thêm cột nullable trước, xóa sau một bản phát hành).
5. Tắt khả năng nhiều worker/instance (APScheduler 1 tiến trình); ghi chú trong README.
6. Giám sát: log Render, cảnh báo UptimeRobot (email) khi `/healthz` lỗi.
7. Quy trình **rollback:** giữ bản deploy trước; Render cho "Rollback" ở tab Deploys; migration phá hủy phải có kế hoạch riêng.

**Test case**

| ID     | Loại | Kịch bản                                          | Kết quả mong đợi                                             |
| ------ | ----- | --------------------------------------------------- | ---------------------------------------------------------------- |
| T7.2.1 | [M]   | `GET https://<backend>/healthz`                   | 200                                                              |
| T7.2.2 | [M]   | `GET /readyz`                                     | 200 khi DB sẵn sàng                                            |
| T7.2.3 | [M]   | Đăng nhập admin bằng Postman/curl               | Thành công; token hợp lệ                                     |
| T7.2.4 | [S]   | `GET /docs` ở production                         | 404/tắt                                                         |
| T7.2.5 | [M]   | Sweeper chạy: tạo bài quá hạn → đợi ≤ 60 s | Bài được finalize                                            |
| T7.2.6 | [M]   | Redeploy trong khi có bài đang làm              | Không mất đáp án đã "Đã lưu"; client retry khôi phục |
| T7.2.7 | [M]   | Rollback về bản trước                           | Chạy bình thường                                             |
| T7.2.8 | [S]   | `curl -I` kiểm tra HTTPS, header bảo mật, CORS | Đúng cấu hình                                                |
| T7.2.9 | [M]   | Ngắt `DATABASE_URL` sai cố ý trên bản thử   | `/readyz` 503, app không crash vòng lặp                     |

**DoD:** CI → deploy backend tự động; có tài liệu `docs/deploy.md`.

---

### Bước 7.3 – Triển khai Frontend lên Cloudflare Pages

**Yêu cầu cần đạt**

- SPA tĩnh được phục vụ qua HTTPS; route con (React Router) hoạt động khi F5; CSP/header đúng.

**Cách thức triển khai**

1. Pages → kết nối repo; **Build command:** `npm ci && npm run build`; **Output:** `frontend/dist`; Root: `frontend`; biến `VITE_API_BASE_URL` trỏ backend (`https://…/api/v1`).
2. **SPA fallback:** file `public/_redirects`: `/* /index.html 200`.
3. **Header bảo mật:** `public/_headers`:

   ```
   /*
     Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://<r2-hoặc-backend>; connect-src 'self' https://<backend>; font-src 'self'; frame-ancestors 'none'
     X-Content-Type-Options: nosniff
     Referrer-Policy: same-origin
     Permissions-Policy: camera=(), microphone=(), geolocation=()
   ```

   (Điều chỉnh khi cần cho KaTeX font/inline style.)
4. **Cache:** tệp băm tên (`/assets/*`) `immutable, max-age=31536000`; `index.html` `no-cache`.
5. Preview deployment cho mỗi PR (Pages tự có) — dùng để kiểm thử trước khi merge; nhớ thêm origin preview vào `CORS_ORIGINS` **chỉ cho môi trường staging**.
6. Tên dự án ngắn gọn dễ nhớ: `quiz-toantin.pages.dev`; tạo mã QR cho lớp học.
7. **Giữ phiên bản tương thích:** FE gửi header `X-Client-Version`; backend có thể trả `426` nếu quá cũ (tuỳ chọn) để tránh học sinh dùng bản FE cũ lúc đang thi sau khi phát hành.

**Test case**

| ID     | Loại | Kịch bản                                          | Kết quả mong đợi                                                                           |
| ------ | ----- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| T7.3.1 | [M]   | Mở `https://quiz-toantin.pages.dev`              | Trang đăng nhập hiển thị, HTTPS hợp lệ                                                  |
| T7.3.2 | [M]   | F5 ở `/student/exams`, `/admin/exams/123`      | Không 404, vào đúng trang                                                                  |
| T7.3.3 | [S]   | Console trình duyệt                               | Không lỗi CSP/CORS/mixed-content                                                             |
| T7.3.4 | [S]   | Kiểm tra header qua `curl -I`                    | Đủ CSP, nosniff, referrer                                                                    |
| T7.3.5 | [M]   | Lighthouse trên điện thoại (mạng 4G giả lập) | Performance ≥ 80, tải ban đầu ≤ 3 s                                                       |
| T7.3.6 | [M]   | Kích thước bundle trang làm bài                | ≤ ~300 KB gzip (lazy-load KaTeX/editor admin)                                                 |
| T7.3.7 | [M]   | Phát hành bản mới khi học sinh đang làm bài | Học sinh không bị gián đoạn (dùng bản cũ cho đến khi tải lại); API tương thích |
| T7.3.8 | [M]   | Quét mã QR bằng điện thoại                    | Mở đúng trang                                                                               |

**DoD:** FE production nối đúng BE, đăng nhập và làm bài thử được.

---

### Bước 7.4 – Giữ server thức, tên miền, cảnh báo & vận hành

**Yêu cầu cần đạt**

- Giảm tối đa cold start trong giờ thi; có nút làm nóng; có cảnh báo khi hệ thống lỗi.
- (Tuỳ chọn) tên miền riêng có HTTPS.

**Cách thức triển khai**

1. **Cron ping:** cron-job.org hoặc UptimeRobot gọi `GET /healthz` mỗi **10 phút** (có thể giới hạn khung giờ có thi); kiểm tra tổng giờ chạy/tháng nằm trong hạn mức Render (≈ 720 giờ nếu chạy 24/7 — kiểm tra lại hạn mức hiện hành).
2. **Làm nóng trước giờ thi:** lịch nhắc 10 phút trước; nút trong giao diện giáo viên (bước 5.6).
3. **Tên miền riêng (tùy chọn):** mua domain, thêm vào Pages (Custom domain), cập nhật `CORS_ORIGINS`; kiểm tra chứng chỉ HTTPS tự động.
4. **Cảnh báo:** UptimeRobot gửi email/Telegram khi `/healthz` hoặc trang FE lỗi > 2 lần liên tiếp.
5. **Nhật ký sự cố & runbook** `docs/runbook.md`: server không phản hồi → làm gì; DB đầy → xuất CSV + dọn; học sinh quên mật khẩu → reset; bài bị mất → kiểm tra `answers`/`localStorage` cục bộ; hết giờ sai → kiểm tra `deadline_at`.
6. **Theo dõi dung lượng DB** (lệnh `SELECT pg_database_size(...)`), cảnh báo khi > 70% (350 MB).
7. **Kế hoạch dự phòng khi gói free thất bại** (mục 6.2 spec): chuyển Render trả phí / Oracle VM; ghi các bước chuyển (đổi `DATABASE_URL`, `S3_*`).

**Test case**

| ID     | Loại | Kịch bản                                                       | Kết quả mong đợi                                                     |
| ------ | ----- | ---------------------------------------------------------------- | ------------------------------------------------------------------------ |
| T7.4.1 | [M]   | Để hệ thống 30 phút có cron ping rồi gọi API             | Phản hồi < 1 s (không cold start)                                     |
| T7.4.2 | [M]   | Tắt cron 20 phút, mở trang                                    | FE hiện "Đang đánh thức máy chủ…" rồi vào được ≤ ~60–90 s |
| T7.4.3 | [M]   | Giáo viên bấm "Làm nóng" 10 phút trước giờ              | Server sẵn sàng, DB ấm                                                |
| T7.4.4 | [M]   | Giả lập sập backend                                           | Cảnh báo email/Telegram trong ≤ 10 phút                              |
| T7.4.5 | [M]   | Domain riêng                                                    | HTTPS hợp lệ; đăng nhập hoạt động (CORS đúng)                  |
| T7.4.6 | [M]   | Diễn tập runbook "reset mật khẩu 1 học sinh trong giờ thi" | Thực hiện ≤ 2 phút                                                   |
| T7.4.7 | [M]   | Kiểm tra dung lượng DB sau dữ liệu thử                     | Báo cáo đúng; cảnh báo ngưỡng 70% hoạt động                   |

**DoD:** runbook hoàn chỉnh; cron ping & cảnh báo đang chạy.

---

### Bước 7.5 – Chạy thử (Pilot), nghiệm thu cuối, Go-live & rollback

**Yêu cầu cần đạt**

- Chạy thử với một nhóm học sinh thật (5–10 em) với đề ngắn; không mất bài; phản hồi được thu thập.
- Hoàn thành Phụ lục C (checklist trước ngày thi) và quyết định Go/No-Go.

**Cách thức triển khai**

1. **Chuẩn bị pilot:** 1 lớp thử, 1 đề 10 phút (đủ 5 dạng câu), mật khẩu đã phát, thông báo hướng dẫn (1 trang ảnh: địa chỉ, cách đăng nhập, "đừng hoảng khi mất mạng").
2. **Trong pilot:** giáo viên mở giám sát; ghi lại: lỗi gặp, thời gian phản hồi, thắc mắc của học sinh; chủ động cho một vài học sinh **ngắt mạng/đóng tab** (có kịch bản).
3. **Sau pilot:** họp 30 phút, phân loại lỗi (Chặn / Cao / Thấp); sửa Chặn+Cao; chạy lại các test liên quan; cập nhật runbook.
4. **Tiêu chí Go/No-Go:** (a) 0 lỗi mất dữ liệu; (b) 0 lỗi rò rỉ đáp án; (c) 10 kịch bản nghiệm thu đạt; (d) p95 autosave < 500 ms khi pilot; (e) giáo viên tự vận hành được không cần dev; (f) sao lưu/khôi phục đã thử.
5. **Go-live:** thông báo cho học sinh trước 1–2 ngày; ngày thi: làm nóng 10 phút trước, dev trực (kênh liên lạc mở), có phương án **thi giấy dự phòng** nếu hệ thống sự cố nặng.
6. **Rollback kế hoạch:** nếu lỗi nghiêm trọng khi đang thi → (1) giáo viên cộng giờ cho học sinh bị ảnh hưởng; (2) nếu cần, đóng đề, xuất CSV; (3) khôi phục bản deploy trước; (4) ghi nhận sự cố.
7. **Đóng sprint:** tag phát hành `v1.0.0`, cập nhật `CHANGELOG.md`.

**Test case**

| ID     | Loại | Kịch bản                                                                | Kết quả mong đợi                                                       |
| ------ | ----- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| T7.5.1 | [M]   | Pilot 8 học sinh làm bài thật                                         | 100% bài được ghi nhận, điểm tự động khớp tính tay mẫu 3 bài |
| T7.5.2 | [M]   | 2 học sinh cố ý ngắt mạng 1 phút khi làm                           | Bài đồng bộ lại; không mất đáp án                                |
| T7.5.3 | [M]   | 1 học sinh đóng tab, mở lại                                          | Tiếp tục đúng chỗ, đồng hồ đúng                                  |
| T7.5.4 | [M]   | 1 học sinh bỏ dở đến hết giờ                                       | Tự nộp `timeout` với đáp án đã lưu                              |
| T7.5.5 | [M]   | Giáo viên chấm tay câu file + công bố `score_only`                | Học sinh thấy điểm, không thấy đáp án                             |
| T7.5.6 | [M]   | Học sinh thử truy cập trái phép (đổi id trên URL)                 | Bị chặn                                                                  |
| T7.5.7 | [M]   | Diễn tập rollback (deploy bản lỗi cố ý → rollback)                 | Khôi phục ≤ 10 phút, dữ liệu nguyên vẹn                            |
| T7.5.8 | [M]   | Hoàn thành checklist Phụ lục C                                        | 100% mục đánh dấu                                                      |
| T7.5.9 | [M]   | Khảo sát học sinh (3 câu: dễ dùng? lỗi? giao diện điện thoại?) | ≥ 80% hài lòng; ghi nhận vấn đề                                     |

**DoD:** M7 – Quyết định Go; tag `v1.0.0`.

---

## P8. VẬN HÀNH & ĐÓNG DỰ ÁN

### Bước 8.1 – Bàn giao, đào tạo, theo dõi sau triển khai

**Yêu cầu cần đạt**

- Giáo viên tự vận hành; tài liệu đầy đủ; kế hoạch bảo trì và V2.

**Cách thức triển khai**

1. **Tài liệu:** `docs/user-guide-gv.md` (có ảnh chụp: tạo lớp, soạn đề, giám sát, chấm, công bố), `docs/user-guide-hs.md` (1 trang), `docs/runbook.md`, `docs/deploy.md`, `docs/architecture.md`, mục lục API (`/docs` bản xuất PDF).
2. **Đào tạo:** buổi 45 phút cho giáo viên (thực hành tạo đề từ đề giấy thật + diễn tập sự cố).
3. **Theo dõi 2 tuần đầu:** xem log lỗi hằng ngày, đo dung lượng DB, đo thời gian phản hồi, ghi nhận yêu cầu cải tiến vào backlog.
4. **Bảo trì định kỳ:** hằng tuần cập nhật phụ thuộc bảo mật; hằng tháng rà soát gói miễn phí, sao lưu, kiểm tra khôi phục.
5. **Backlog V2** (xếp theo giá trị/công sức): nhập `.tex`/Word hàng loạt, ngân hàng câu hỏi, thống kê phân tích câu hỏi, đăng nhập SSO, phân quyền nhiều giáo viên, WebSocket giám sát, chống gian lận nâng cao.
6. **Retrospective** 1 giờ: điều gì tốt/chưa tốt, số liệu (thời gian ước tính so với thực tế, số lỗi), cập nhật mẫu kế hoạch.

**Test case**

| ID     | Loại | Kịch bản                                                                                 | Kết quả mong đợi                                   |
| ------ | ----- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------ |
| T8.1.1 | [M]   | Giáo viên tự dựng đề mới chỉ bằng tài liệu hướng dẫn                         | Hoàn thành không cần hỗ trợ                      |
| T8.1.2 | [M]   | Giáo viên tự xử lý sự cố mẫu theo runbook (quên mật khẩu, cộng giờ, mở lại) | Làm đúng ≤ 5 phút mỗi việc                      |
| T8.1.3 | [M]   | Người ngoài dự án đọc `deploy.md` và dựng lại môi trường staging            | Thành công ≤ 2 giờ                                 |
| T8.1.4 | [M]   | Rà soát dung lượng DB/R2 sau 2 tuần                                                   | Dưới ngưỡng cảnh báo; job dọn dẹp chạy đúng |
| T8.1.5 | [M]   | Kiểm tra khôi phục từ sao lưu tuần                                                   | Thành công                                           |
| T8.1.6 | [M]   | Rà soát backlog V2 với PO                                                               | Có thứ tự ưu tiên và ước lượng               |
| T8.1.7 | [M]   | Kiểm tra cập nhật phụ thuộc (audit)                                                   | Không lỗ hổng mức cao tồn đọng                  |

**DoD:** M8 – bàn giao ký nhận; dự án chuyển sang bảo trì.

---

# PHẦN C. PHỤ LỤC

## C.1 Ma trận truy vết yêu cầu → bước → test

| Yêu cầu spec                               | Bước thực hiện | Test chính                         |
| -------------------------------------------- | ------------------ | ----------------------------------- |
| Nguyên tắc 1: server là nguồn thời gian | 4.1, 4.2, 4.3, 4.4 | T4.1.10, T4.2.5, T4.3.4, T4.4.1     |
| Nguyên tắc 2: autosave                     | 4.2, 4.4           | T4.2.2, T4.4.5, T4.4.6              |
| Nguyên tắc 3: không lộ đáp án         | 4.1, 5.4, 6.1      | T4.1.1, T5.4.1–2, T6.1.2           |
| Nguyên tắc 4: idempotent submit/finalize   | 4.3, 4.5           | T4.3.2, T4.3.3, T4.5.4              |
| Nguyên tắc 5: giữ nhỏ gọn               | 1.1, 7.2           | Kiến trúc 1 service/1 DB/1 bucket |
| 5 dạng câu hỏi                            | 3.1, 4.5, 5.1      | T3.1.1–4, T5.1.x                   |
| LaTeX + ảnh                                 | 3.2, 3.3, 3.4      | T3.2.x, T3.3.x                      |
| Chống gián đoạn                          | 4.2–4.6           | Kịch bản 1–6 (T6.3)              |
| Chấm tay & công bố                        | 5.2, 5.4, 5.6      | T5.2.x, T5.4.x                      |
| Giám sát/cộng giờ/mở lại               | 5.3, 5.6           | T5.3.x                              |
| Xuất CSV/dọn dữ liệu                     | 5.5                | T5.5.x                              |
| Bảo mật                                    | 2.1, 3.3, 6.1      | T6.1.x                              |
| Hosting miễn phí & cold start              | 7.1–7.4           | T7.2.x, T7.4.x                      |

## C.2 Danh sách bất biến dữ liệu (kiểm sau mỗi test tải/E2E)

1. Mỗi `(exam_id, student_id)` có tối đa một `attempt`.
2. Mỗi `attempt` ở trạng thái `submitted` có `submitted_at ≤ deadline_at` (trừ khi bị `teacher_closed`/`teacher_forced`).
3. `total_score = Σ answers.score` cho mọi attempt `submitted`.
4. Không `answers` nào có `updated_at > deadline_at + grace_seconds` của attempt (ngoại trừ trường hợp giáo viên cộng giờ/mở lại — khi đó dùng deadline mới).
5. Không tồn tại attempt `in_progress` có `deadline_at + grace` đã qua quá 2 phút (sweeper hoạt động).
6. Mọi `files.storage_key` tham chiếu đều tồn tại trong bucket (và ngược lại sau job dọn).
7. Không phản hồi `/student/*` nào chứa khóa cấm.

## C.3 Quy ước đặt tên & thực hành mã nguồn (tóm tắt)

- Python: `snake_case`, type hints bắt buộc, `ruff` + `mypy --strict` trên `services/` và `core/`; hàm nghiệp vụ lõi là **hàm thuần** hoặc nhận `db` rõ ràng (dễ test).
- TypeScript: `strict: true`; không `any`; zod schema tách khỏi component; không logic nghiệp vụ trong JSX.
- Lỗi: chỉ ném `AppError` từ service; router không bắt chung chung; FE chỉ hiển thị thông báo từ `error.code` qua bảng dịch.
- Thời gian: **luôn UTC ở backend**; chuyển múi giờ chỉ ở lớp hiển thị.
- Transaction: mỗi request một session; `commit` ở tầng router/service điều phối; không `commit` rải rác.
- Migration: mỗi PR đổi model phải kèm migration và test `alembic check`.

## C.4 Ước lượng nỗ lực (người-giờ, tham khảo)

| Giai đoạn         | Giờ ước tính           | Hệ số dự phòng                                                      |
| ------------------- | -------------------------- | ----------------------------------------------------------------------- |
| P0 UI/UX            | 20–28                     | +20%                                                                    |
| P1 Khởi tạo       | 10–14                     | +15%                                                                    |
| P2 Tài khoản/lớp | 18–24                     | +20%                                                                    |
| P3 Soạn đề       | 32–44                     | +25%                                                                    |
| P4 Làm bài        | 36–48                     | +30% (rủi ro cao)                                                      |
| P5 Chấm/giám sát | 30–40                     | +20%                                                                    |
| P6 Chất lượng    | 20–28                     | +20%                                                                    |
| P7 Hosting/pilot    | 16–24                     | +25%                                                                    |
| P8 Bàn giao        | 8–12                      | +10%                                                                    |
| **Tổng**     | **≈ 190–262 giờ** | → 4–5 tuần ở 40–60 giờ/tuần, hoặc 10–13 tuần ở 20 giờ/tuần |

> Lưu ý: nếu làm một mình ở 15–20 giờ/tuần, lịch thực tế sẽ kéo dài; ưu tiên cắt phạm vi bằng cách giữ P4–P5 nguyên vẹn và trì hoãn các phần "đẹp" (biểu đồ thống kê, kéo thả nâng cao, preview CodeMirror) sang V2.

## C.5 Checklist trước ngày thi (nối với Phụ lục C của spec)

- [ ] Đề đã xuất bản; đã **xem trước như học sinh** và làm thử bằng tài khoản học sinh thật.
- [ ] Học sinh đã ghi danh đúng lớp; mật khẩu đã phát; một học sinh đã đăng nhập thử.
- [ ] `result_visibility = hidden`.
- [ ] Cron ping chạy; bấm **Làm nóng hệ thống** 10 phút trước giờ thi.
- [ ] Đã thử đóng tab + tắt mạng trên điện thoại và máy tính.
- [ ] Đã xuất CSV đợt trước và dọn dữ liệu cũ; DB < 70%.
- [ ] Dev/giáo viên trực kênh liên lạc; có phương án thi giấy dự phòng.
- [ ] Biết cách: cộng giờ, mở lại, nộp hộ, reset mật khẩu (runbook).
