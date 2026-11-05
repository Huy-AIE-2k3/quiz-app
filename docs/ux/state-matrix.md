# MA TRẬN TRẠNG THÁI GIAO DIỆN & ÁNH XẠ MÃ LỖI API (STATE MATRIX & ERROR MAPPING)

> **Tài liệu tham chiếu:** `ke-hoach-trien-khai-quiz.md` (Bước 1.1) & `docs/ui_ux_rules.md`  
> **Mục tiêu:** Định nghĩa hành vi trực quan của từng màn hình qua 6 trạng thái chuẩn và ánh xạ 100% mã lỗi backend sang thông điệp tiếng Việt thân thiện.

---

## 1. MA TRẬN 6 TRẠNG THÁI CHO TỪNG ROUTE

| Route | Đang tải (Loading) | Rỗng (Empty) | Lỗi (Error) | Mất mạng (Offline) | Không đủ quyền (Forbidden) | Hết hạn / Đã nộp (Expired/Submitted) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`/login`** | Nút bấm hiện spinner nhỏ `16px` + chữ "Đang xác thực..." | N/A (Form nhập liệu) | Viền đỏ quanh ô input + text báo sai tài khoản/mật khẩu | Toast: "Không thể kết nối máy chủ để đăng nhập" | Toast: "Tài khoản của bạn đã bị tạm khóa" | N/A |
| **`/s/exams`** | 3 Skeleton cards giả lập khung đề thi | Card minh họa: "Hiện chưa có bài kiểm tra nào được giao cho lớp của bạn" | Banner lỗi kèm nút "Thử tải lại" | Đọc từ bộ nhớ đệm `localStorage` (nếu có) + banner offline | Tự động chuyển hướng về `/login` | Hiện badge "Đã hoàn thành" hoặc "Đã đóng" trên thẻ đề |
| **`/s/exams/:id`** | Skeleton phần nội dung quy chế | "Đề thi không tồn tại hoặc đã bị xóa" | Thẻ thông báo lỗi + nút "Quay lại danh sách đề" | Banner: "Cần có kết nối Internet để bắt đầu bài thi mới" | "Bạn không thuộc danh sách lớp được giao bài thi này" | Nút "Bắt đầu" chuyển thành "Đã nộp bài" hoặc "Đã hết hạn làm bài" |
| **`/s/attempts/:id`** | Skeleton câu hỏi + skeleton bảng Bento | "Đề thi chưa có câu hỏi nào" | Toast lỗi + giữ nguyên câu trả lời trong Outbox | **Offline Banner màu Amber**: Cho phép làm bài tiếp, lưu vào Outbox | Bị chặn, chuyển về `/s/exams` | **Khóa bàn phím/chuột**, tự động chuyển sang trang `/done` |
| **`/s/attempts/:id/done`** | Spinner trung tâm | N/A | Thông báo lỗi xác nhận nộp + nút "Kiểm tra lại trạng thái" | Đọc trạng thái xác nhận từ cache gần nhất | Bị từ chối truy cập | Màn hình hiển thị thời gian nộp bài thành công |
| **`/s/attempts/:id/result`**| Skeleton chi tiết từng câu hỏi | "Chưa có dữ liệu bài làm" | Thông báo lỗi không tải được kết quả | Đọc kết quả đã lưu trong cache (nếu đã từng xem) | Thông báo: "Giáo viên chưa công bố kết quả cho bài thi này" | Xem chi tiết điểm, đáp án đúng và lời giải $\LaTeX$ |
| **`/a` (Dashboard)** | Skeleton các thẻ chỉ số thống kê | "Chưa có hoạt động nào trong tuần này" | Card báo lỗi tải dữ liệu thống kê | Báo không có mạng | Chuyển hướng về `/login` | N/A |
| **`/a/classes`** | Skeleton bảng lớp học | "Chưa có lớp học nào. Hãy bấm 'Tạo lớp mới'" | Thông báo lỗi tải danh sách lớp | Báo mất mạng | Bị chặn nếu tài khoản không phải Admin/Giáo viên | N/A |
| **`/a/classes/:id`** | Skeleton bảng học sinh | "Lớp học chưa có học sinh nào. Bấm 'Nhập từ CSV'" | Báo lỗi tải danh sách lớp | Không cho phép chỉnh sửa khi offline | Chặn xem lớp của giáo viên khác (nếu phân quyền) | N/A |
| **`/a/students`** | Skeleton bảng danh sách | "Không tìm thấy học sinh nào phù hợp với bộ lọc" | Báo lỗi tìm kiếm | Báo mất kết nối mạng | Bị chặn | N/A |
| **`/a/exams`** | Skeleton danh sách đề | "Chưa có đề thi nào. Bấm 'Soạn đề mới'" | Báo lỗi tải danh sách đề | Báo mất kết nối mạng | Bị chặn | Hiển thị bộ lọc đề: Bản nháp / Đang mở / Đã đóng |
| **`/a/exams/:id/edit`** | Skeleton bộ soạn thảo | "Đề thi chưa có câu hỏi. Bấm 'Thêm câu hỏi mới'" | Toast cảnh báo lỗi khi lưu câu hỏi | Chặn lưu lên máy chủ, lưu tạm vào `localStorage` | Bị chặn | Đề thi đã có học sinh làm thì bị khóa cấu trúc câu hỏi |
| **`/a/exams/:id/preview`**| Skeleton mô phỏng phòng thi | "Đề thi chưa có câu hỏi để xem trước" | Báo lỗi dựng câu hỏi | Chạy mô phỏng cục bộ bình thường | Bị chặn | N/A |
| **`/a/exams/:id/monitor`**| Lưới Skeleton Bento 40 ô | "Chưa có học sinh nào vào phòng thi" | Cảnh báo mất kết nối luồng realtime | **Banner Đỏ**: "Mất kết nối giám sát thời gian thực!" | Bị chặn | Đề thi đã kết thúc $\to$ nút chuyển sang trang Kết quả |
| **`/a/exams/:id/grading`**| Skeleton bài nộp tự luận | "Không có câu hỏi tự luận nào cần chấm tay" | Báo lỗi lưu điểm chấm | Không cho phép chấm khi mất mạng | Bị chặn | Đã hoàn thành chấm toàn bộ bài thi |
| **`/a/exams/:id/results`**| Skeleton biểu đồ phổ điểm | "Chưa có học sinh nào nộp bài để thống kê" | Báo lỗi tính toán kết quả | Cho phép xem cache thống kê cũ | Bị chặn | Bảng điểm hoàn chỉnh kèm nút bấm "Công bố kết quả cho học sinh" |
| **`/a/settings`** | Skeleton form cài đặt | N/A | Toast lỗi lưu cấu hình | Báo mất kết nối | Chỉ cho phép Admin cấp cao | N/A |

---

## 2. BẢNG ÁNH XẠ TOÀN BỘ MÃ LỖI API SANG GIAO DIỆN TIẾNG VIỆT (TC-1.1-02)

| Mã lỗi API (`error_code`) | HTTP Status | Thông điệp Tiếng Việt hiển thị cho người dùng | Kiểu giao diện (UI Pattern) | Hành động xử lý đề xuất (Call to Action) |
| :--- | :---: | :--- | :--- | :--- |
| `unauthenticated` | 401 | Phiên đăng nhập đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại. | Modal Chặn / Toast Đỏ | Nút `[ Đăng nhập lại ]` $\to$ Chuyển về `/login` |
| `forbidden` | 403 | Bạn không có quyền truy cập vào tài nguyên hoặc trang này. | Error Card toàn trang | Nút `[ Quay về trang chủ ]` |
| `account_disabled` | 403 | Tài khoản của bạn đã bị khóa. Vui lòng liên hệ giáo viên quản nhiệm. | Alert Banner Đỏ | Nút `[ Đăng xuất ]` |
| `not_found` | 404 | Không tìm thấy dữ liệu yêu cầu (Đề thi, lớp học hoặc bài làm không tồn tại). | Empty State / 404 View | Nút `[ Quay lại ]` |
| `exam_not_open` | 409 | Bài thi chưa đến giờ bắt đầu. Vui lòng quay lại vào đúng thời gian quy định. | Warning Banner Vàng Amber | Đồng hồ đếm ngược tới giờ mở đề + Nút `[ Tải lại ]` |
| `exam_closed` | 409 | Đã quá hạn thời gian nộp bài của kỳ thi này. Hệ thống không tiếp nhận thêm bài làm. | Status Badge Đỏ | Nút `[ Quay về danh sách đề thi ]` |
| `attempt_closed` | 409 | Bài thi của bạn đã được nộp hoặc đã hết hạn làm bài. | Info Modal Xanh / Xám | Nút `[ Xem trang xác nhận nộp bài ]` $\to$ `/done` |
| `attempt_already_started` | 409 | Bạn đã có một lượt làm bài đang diễn ra cho đề thi này. | Info Dialog | Nút `[ Tiếp tục làm bài đang dở ]` |
| `result_not_released` | 403 | Điểm số và lời giải chi tiết của bài thi này chưa được giáo viên công bố. | Empty State Chờ đợi | Thông báo: *"Kết quả sẽ xuất hiện tại đây khi giáo viên công bố."* |
| `rate_limited` | 429 | Thao tác quá nhanh hoặc quá nhiều lần liên tiếp. Vui lòng đợi trong giây lát. | Toast Cảnh báo | Bộ đếm ngược thời gian chờ (`Retry-After: Xs`) |
| `payload_too_large` | 413 | Dung lượng tệp tải lên vượt quá giới hạn cho phép (Tối đa 10 MB). | Field Error dưới ô Upload | Nút `[ Chọn tệp khác nhỏ hơn ]` |
| `unsupported_media_type` | 415 | Định dạng tệp không được hỗ trợ. Chỉ chấp nhận ảnh PNG, JPG hoặc PDF. | Field Error | Hiển thị danh sách định dạng được hỗ trợ |
| `validation_error` | 422 | Dữ liệu nhập vào chưa đúng định dạng hoặc thiếu thông tin bắt buộc. | Inline Form Error | Đánh dấu đỏ các trường bị lỗi kèm hướng dẫn cụ thể |
| `server_error` | 500 | Máy chủ gặp sự cố xử lý nội bộ. Bài làm cục bộ của bạn vẫn an toàn. | Toast Đỏ góc dưới | Nút `[ Thử lại sau ít phút ]` |
| `db_unavailable` | 503 | Dịch vụ cơ sở dữ liệu tạm thời gián đoạn. Đang tự động kết nối lại... | Sticky Banner Cam trên đỉnh | Tự động thử lại mỗi 3 giây (Backoff) |

