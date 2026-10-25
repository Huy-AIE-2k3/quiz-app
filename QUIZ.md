
# ĐẶC TẢ DỰ ÁN: HỆ THỐNG QUIZ NỘI BỘ MÔN TOÁN – TIN

> Phiên bản 1.0 · Ngày 21/10/2026 · Trạng thái: bản nháp để bắt tay triển khai
> Quy ước: **[MVP]** = làm ngay; **[V2]** = để sau; **[?]** = cần bạn xác nhận (xem mục 15).

---

## 0. Tóm tắt nhanh

**Là gì:** Web làm bài kiểm tra ngắn cho học sinh một lớp nội bộ. Học sinh chỉ *làm và nộp*; giáo viên mới thấy điểm/đáp án và quyết định có công bố cho học sinh hay không.

**Techstack đề xuất (đơn giản, miễn phí):**

| Lớp           | Công nghệ                                                                   |
| -------------- | ----------------------------------------------------------------------------- |
| Frontend       | React + Vite + TypeScript, Tailwind CSS, KaTeX (render LaTeX)                 |
| Backend        | Python 3.12 + FastAPI, SQLAlchemy 2.0, Alembic                                |
| Database       | PostgreSQL (Neon free)                                                        |
| Lưu file/ảnh | Object storage chuẩn S3 (Cloudflare R2, phương án phụ: Supabase Storage) |
| Hosting        | Frontend: Cloudflare Pages · Backend: Render (free web service)              |
| Tên miền     | `ten-ban-chon.pages.dev` (miễn phí), có thể gắn tên miền riêng sau  |

**5 nguyên tắc thiết kế cốt lõi** (mọi quyết định bên dưới xoay quanh chúng):

1. **Server là nguồn sự thật về thời gian.** Hạn nộp (`deadline_at`) do server tính và lưu; đồng hồ trên máy học sinh chỉ để hiển thị.
2. **Lưu từng câu trả lời ngay khi học sinh thao tác (autosave).** Mất điện/đóng tab thì mở lại làm tiếp đúng chỗ cũ.
3. **Học sinh không bao giờ nhận được đáp án đúng từ API.** Dữ liệu trả cho học sinh dùng schema riêng, không chứa khóa đáp án.
4. **Nộp bài và tự động nộp phải idempotent** (gọi nhiều lần vẫn chỉ nộp/chấm một lần).
5. **Giữ nhỏ gọn:** 1 service backend, 1 database, 1 bucket, 1 frontend tĩnh. Không Redis, không queue ngoài, không websocket ở bản MVP.

---

## 1. Mục tiêu & phạm vi

### 1.1 Bối cảnh & mục tiêu

- Dùng nội bộ cho lớp học Toán và Tin, kiểm tra ngắn (khoảng 10–45 phút).
- Giáo viên soạn đề nhanh bằng LaTeX, giao theo lớp, theo dõi trực tiếp, chấm tự động phần lớn, chấm tay phần còn lại, rồi chủ động công bố kết quả.
- Chạy ổn định trên hạ tầng miễn phí, chịu được sự cố phía học sinh (mất điện, rớt mạng, thoát web).

### 1.2 Trong phạm vi [MVP]

- Đăng nhập bằng tên đăng nhập + mật khẩu (không email, không OTP).
- Quản lý lớp, học sinh, ghi danh học sinh vào lớp.
- Tạo đề với 5 dạng câu hỏi: MCQ, TF, trả lời ngắn (chữ), trả lời ngắn (số), nộp file.
- Soạn nội dung bằng Markdown + LaTeX, đính kèm ảnh tải lên.
- Điểm riêng từng câu, thời gian làm bài, cửa sổ mở/đóng đề.
- Làm bài có đếm ngược, tự lưu, tiếp tục khi quay lại, tự nộp khi hết giờ.
- Chấm tự động + chấm tay; công bố kết quả có kiểm soát.
- Theo dõi học sinh đang làm; cộng thêm giờ; mở lại bài.
- Xuất kết quả CSV; xóa dữ liệu cũ (lưu ngắn hạn).

### 1.3 Ngoài phạm vi [V2]

- Đăng nhập Google/SSO, quên mật khẩu qua email.
- Giám sát camera/chống gian lận nâng cao (MVP chỉ ghi nhận số lần rời tab, không phạt).
- Nhập nguyên file đề `.tex` hoặc Word hàng loạt.
- Ngân hàng câu hỏi dùng lại nhiều đề, thống kê phân tích câu hỏi.
- Realtime bằng WebSocket, ứng dụng native, thông báo đẩy.

### 1.4 Quy mô & giả định

- Đồng thời tối đa **~6 người**; thiết kế chịu được **30–50** mà không cần đổi kiến trúc.
- 1 tài khoản giáo viên/admin (có thể thêm vài tài khoản giáo viên).
- Mỗi lớp ≤ 40 học sinh; mỗi đề ≤ 60 câu; mỗi học sinh làm 1 lần/đề (giáo viên có thể mở lại).
- Dữ liệu lưu **ngắn hạn** (mặc định 90 ngày, cấu hình được).

---

## 2. Vai trò & phân quyền

| Vai trò                | Mô tả                                                                                      |
| ----------------------- | -------------------------------------------------------------------------------------------- |
| `admin` (giáo viên) | Toàn quyền: lớp, học sinh, đề, chấm điểm, công bố kết quả, xuất/xóa dữ liệu |
| `student`             | Chỉ thấy đề của lớp mình được ghi danh, làm bài và nộp                         |

| Hành động                                       | Admin |            Student            |
| -------------------------------------------------- | :---: | :----------------------------: |
| Tạo/sửa/xóa lớp, học sinh, đề, câu hỏi    |  ✅  |               ❌               |
| Ghi danh học sinh vào lớp                       |  ✅  |               ❌               |
| Xem danh sách đề của lớp mình (đang mở)    |  ✅  |               ✅               |
| Làm bài, tự lưu, nộp bài (của chính mình) |  —  |               ✅               |
| Xem đáp án đúng / điểm                      |  ✅  | Chỉ khi giáo viên công bố |
| Chấm tay, sửa điểm, cộng giờ, mở lại bài  |  ✅  |               ❌               |
| Xuất CSV, xóa dữ liệu                          |  ✅  |               ❌               |

Phân quyền thực thi ở **backend** (dependency theo vai trò + kiểm tra quyền sở hữu attempt). Ẩn nút ở frontend chỉ là phần trải nghiệm.

---

## 3. Yêu cầu chức năng

### 3.1 Xác thực

- Đăng nhập: `POST /auth/login` với `username` + `password`. Đúng là vào, không xác thực email.
- Giáo viên tạo tài khoản học sinh; học sinh không tự đăng ký.
- Mật khẩu lưu dạng **hash (Argon2)**. Khi giáo viên tạo/reset mật khẩu, hệ thống hiển thị mật khẩu rõ **một lần** và cho tải danh sách (CSV) để phát cho học sinh.
- Phiên đăng nhập: token ngẫu nhiên (opaque), lưu **hash** trong bảng `sessions`, gửi qua header `Authorization: Bearer`. Hết hạn sau 12 giờ không hoạt động (cấu hình được). Giáo viên có thể thu hồi phiên của một học sinh.
- Chống dò mật khẩu: giới hạn 10 lần sai/phút theo IP + username (slowapi hoặc bộ đếm trong DB).
- Quy tắc username: chữ thường không dấu `[a-z0-9._-]`, 3–32 ký tự, duy nhất.
- Tài khoản admin đầu tiên tạo bằng lệnh CLI hoặc biến môi trường khi khởi chạy lần đầu.

### 3.2 Quản lý lớp & học sinh

- CRUD **lớp** (`tên`, `mã lớp`, `môn` Toán/Tin/cả hai, `năm học`).
- CRUD **học sinh** (`họ tên`, `username`, `mật khẩu`, trạng thái hoạt động).
- **Ghi danh** (enrollment): học sinh thuộc một hoặc nhiều lớp [?]. Học sinh chỉ thấy đề được giao cho lớp mình ghi danh.
- **Nhập hàng loạt bằng CSV**: cột `ho_ten, username, mat_khau (tùy chọn), ma_lop`. Thiếu mật khẩu thì tự sinh mật khẩu ngẫu nhiên dễ đọc (tránh ký tự dễ nhầm như `0/O`, `1/l`).
- Reset mật khẩu, khóa/mở tài khoản, chuyển lớp.

### 3.3 Tạo & quản lý đề

- Trạng thái đề: `draft` → `published` → `closed` (→ `archived`).
- Đề gắn vào **một hoặc nhiều lớp**.
- Thao tác: tạo, sửa, **nhân bản đề**, xem trước như học sinh, xuất bản, đóng, lưu trữ, xóa.
- Sau khi đã có học sinh bắt đầu làm: **khóa chỉnh sửa nội dung câu hỏi/đáp án/điểm** (để điểm số nhất quán). Muốn sửa thì nhân bản đề. Giáo viên vẫn được sửa điểm chấm tay.

### 3.4 Các dạng câu hỏi

| Dạng                  | Mã              | Học sinh thấy                                                              | Khóa đáp án (chỉ giáo viên)   | Cách chấm                                    |
| ---------------------- | ---------------- | ---------------------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------- |
| Trắc nghiệm          | `mcq`          | 2–8 lựa chọn (A, B, C…), chọn 1                                         | 1 lựa chọn đúng                  | Tự động, đúng được toàn điểm, sai 0 |
| Đúng/Sai             | `tf`           | Một ý dẫn + N mệnh đề (a, b, c, d…), mỗi mệnh đề chọn Đúng/Sai | Đáp án từng mệnh đề           | Tự động, theo chế độ chấm (xem dưới)  |
| Trả lời ngắn (chữ) | `short_text`   | 1 ô nhập chữ                                                              | Danh sách đáp án chấp nhận     | Tự động hoặc chấm tay                     |
| Trả lời ngắn (số)  | `short_number` | 1 ô nhập số                                                               | Giá trị đúng + sai số cho phép | Tự động                                     |
| Nộp file              | `file_upload`  | Nút tải file/ảnh lên (xem trước tên file)                             | Không có                           | Chấm tay                                      |

**Chấm câu `tf`** (chọn một chế độ khi tạo câu, mặc định `thpt`) [?]:

- `thpt`: theo tỉ lệ đúng 1/2/3/4 mệnh đề = 10% / 25% / 50% / 100% điểm câu (áp dụng khi có đúng 4 mệnh đề; số mệnh đề khác thì tự chuyển sang `proportional`).
- `proportional`: điểm = (số mệnh đề đúng / tổng) × điểm câu.
- `all_or_nothing`: chỉ đúng hết mới có điểm.

**Chấm câu `short_number`:**

- Chuẩn hóa đầu vào: bỏ khoảng trắng, đổi dấu phẩy thập phân thành dấu chấm (`1,5` → `1.5`), hỗ trợ phân số đơn giản `a/b`.
- So sánh bằng `Decimal`: đúng nếu `|x − đáp án| ≤ sai số`. Sai số mặc định 0 (chính xác); chọn được sai số tuyệt đối hoặc tương đối.
- Cho phép khai báo nhiều giá trị đúng (ví dụ cả `0.5` và `1/2` đều tự quy về số).

**Chấm câu `short_text`:**

- Chuẩn hóa: Unicode NFC, trim, gộp khoảng trắng, không phân biệt hoa/thường (bật được phân biệt), tùy chọn bỏ dấu tiếng Việt.
- Đúng nếu khớp một trong các đáp án chấp nhận.
- Chế độ `manual`: không tự chấm, chuyển giáo viên chấm. Chế độ `auto`: khi sai vẫn đánh dấu `cần xem lại` nếu giáo viên bật tùy chọn này.

**Câu `file_upload`:**

- Cấu hình: số file tối đa (mặc định 3), dung lượng mỗi file tối đa (mặc định 10 MB), đuôi cho phép (mặc định `jpg, jpeg, png, pdf`).
- File tải lên là **lưu ngay** (tương đương autosave). Học sinh được xóa/thay file cho tới khi nộp.
- Giáo viên xem/tải file qua đường dẫn ký có hạn (signed URL), không công khai.

### 3.5 Soạn đề bằng LaTeX và ảnh

- Nội dung câu hỏi, lựa chọn, mệnh đề, lời giải: **Markdown + LaTeX**.
  - Công thức nội dòng: `$x^2 + y^2 = r^2$`; công thức dòng riêng: `$$\int_0^1 x\,dx$$`.
  - Hỗ trợ in đậm, danh sách, bảng, **khối code** (hữu ích cho môn Tin).
- Trình soạn có **xem trước trực tiếp** (render KaTeX) bên cạnh khung nhập.
- **Ảnh:** giáo viên tải ảnh lên (jpg/png/webp ≤ 5 MB, tự nén phía client nếu lớn), hệ thống trả về đường dẫn và chèn `![mô tả](url)` vào nội dung. Ảnh dùng được trong câu hỏi, lựa chọn, lời giải.
- **An toàn:** không cho phép HTML thô trong nội dung (dùng `rehype-sanitize`); KaTeX chạy ở chế độ không tin tưởng (`trust: false`).
- Công thức sai cú pháp: hiện báo lỗi tại chỗ thay vì làm hỏng cả trang.

### 3.6 Thiết lập đề

| Thiết lập                                | Mô tả                                                                                   | Mặc định       |
| ------------------------------------------ | ----------------------------------------------------------------------------------------- | ----------------- |
| `title`, `subject`, `description`    | Tên đề, môn, hướng dẫn hiển thị trước khi bắt đầu                           | —                |
| `duration_minutes`                       | Thời gian làm bài tính từ lúc học sinh bấm “Bắt đầu”                         | 30                |
| `open_at`, `close_at`                  | Cửa sổ cho phép bắt đầu; hết `close_at` thì ai chưa nộp bị tự nộp [?]      | Không giới hạn |
| Điểm từng câu                          | Điểm riêng mỗi câu (số thập phân, ví dụ 0.25)                                   | 1                 |
| Thang điểm                               | Tổng điểm tối đa tự cộng; tùy chọn quy về thang 10                              | Cộng thẳng      |
| `shuffle_questions`, `shuffle_options` | Xáo thứ tự câu/lựa chọn (cố định theo từng học sinh, ổn định khi tải lại) | Tắt              |
| `result_visibility`                      | `hidden` / `score_only` / `full` (điểm + đáp án + lời giải)                  | `hidden`        |
| `grace_seconds`                          | Độ trễ mạng cho phép sau hạn khi nhận bài                                         | 10                |

Xáo trộn dùng **seed lưu theo attempt** để học sinh tải lại trang vẫn thấy đúng thứ tự cũ.

### 3.7 Luồng làm bài của học sinh

```
Đăng nhập → Danh sách đề của lớp → Trang giới thiệu đề (thời lượng, số câu, lưu ý)
   → [Bắt đầu] → Làm bài (đếm ngược, tự lưu) → [Nộp bài] (hỏi xác nhận)
   → Màn hình “Đã nộp bài lúc hh:mm” (KHÔNG hiển thị điểm/đáp án)
```

Trạng thái attempt: `in_progress` → `submitted` (lý do: `manual` | `timeout` | `teacher_closed` | `teacher_forced`).

- Bấm **Bắt đầu** tạo attempt (idempotent: bấm hai lần hoặc mở hai tab chỉ tạo một attempt).
- Thanh điều hướng câu hỏi, đánh dấu “câu đã làm / chưa làm / cần xem lại”.
- Học sinh **không** xem được điểm hay đáp án sau khi nộp, trừ khi giáo viên công bố (mục 3.10).
- Học sinh đã nộp không thể vào làm lại trừ khi giáo viên mở lại.

### 3.8 Chống gián đoạn (yêu cầu trọng tâm)

**Mục tiêu:** mất điện, hết pin, rớt mạng, đóng trình duyệt, tắt máy đều không làm mất bài; đồng hồ vẫn chạy; hết giờ tự nộp.

**a) Đồng hồ do server quyết định**

- Khi bắt đầu: `started_at = now()`, `deadline_at = min(started_at + duration + extra_seconds, exam.close_at)`.
- Mọi phản hồi của API làm bài kèm `server_now`, `deadline_at`, `status`.
- Client tính độ lệch `offset = server_now − Date.now()` và đếm ngược theo `deadline_at − (Date.now() + offset)`. Đồng bộ lại mỗi lần autosave và mỗi 30 giây. Học sinh chỉnh đồng hồ máy không ảnh hưởng.

**b) Tự lưu**

- Mỗi thay đổi đáp án: debounce 800 ms rồi `PUT /student/attempts/{id}/answers/{question_id}`. Dữ liệu là **từng câu một**, nên không có xung đột giữa các câu.
- Mỗi lần ghi kèm `client_seq` (số thứ tự tăng dần trên client, theo từng câu). Server chỉ nhận nếu `client_seq` lớn hơn giá trị đang lưu → chống ghi đè bằng dữ liệu cũ khi gói tin đến sai thứ tự hoặc mở hai tab.
- **Offline:** client giữ hàng đợi các thay đổi chưa gửi trong `localStorage`; hiện banner “Mất kết nối – đang lưu tạm trên máy”; tự gửi lại khi có mạng; thử lại với backoff.
- Chỉ báo trạng thái lưu: “Đã lưu” / “Đang lưu…” / “Chưa gửi được”.
- Cảnh báo khi `beforeunload` nếu còn thay đổi chưa gửi.

**c) Tiếp tục bài**

- Mở lại đề đang `in_progress` → `GET /student/attempts/{id}` trả toàn bộ câu hỏi (không có khóa đáp án), đáp án đã lưu, thời gian còn lại. Nếu còn bản nháp trong `localStorage` mới hơn (`client_seq` lớn hơn) thì gửi bù.

**d) Tự động nộp khi hết giờ** — dùng nhiều lớp bảo đảm, cùng gọi **một hàm** `finalize_attempt(attempt_id, reason)` idempotent:

1. Client: đếm ngược về 0 thì gọi `submit`.
2. **Lazy:** bất kỳ request nào chạm vào attempt đã quá `deadline_at + grace` → server finalize ngay rồi trả `status = submitted`.
3. **Sweeper:** job nền (APScheduler) mỗi 30 giây quét attempt quá hạn.
4. **Khi giáo viên mở trang theo dõi/kết quả:** gọi `finalize_expired(exam_id)` trước khi tính, nên kể cả server từng “ngủ” (free tier) thì số liệu vẫn đúng.
5. Giáo viên đóng đề: finalize toàn bộ attempt đang làm (`teacher_closed`).

Khi finalize do hết giờ: `submitted_at = deadline_at` (không phải lúc server quét), các đáp án đã lưu đến thời điểm đó được chấm bình thường. Sau `deadline_at + grace_seconds`, ghi đáp án bị từ chối (`409 attempt_closed`).

**e) Can thiệp của giáo viên**

- **Cộng thêm thời gian** cho một học sinh (do sự cố) → tăng `extra_seconds`, `deadline_at` cập nhật.
- **Mở lại bài đã nộp** (attempt về `in_progress`, giữ nguyên đáp án, cấp thêm thời gian).
- **Nộp hộ / buộc nộp**.

### 3.9 Chấm điểm

- Khi `finalize`: tự chấm `mcq`, `tf`, `short_number`, và `short_text` ở chế độ tự động. Câu cần chấm tay đánh dấu `pending_manual`.
- Attempt có `grading_status`: `auto_done` | `needs_manual` | `complete`.
- Màn hình chấm tay: xem bài từng học sinh (hoặc theo từng câu cho cả lớp), nhập điểm 0…điểm câu, ghi nhận xét, xem file đã nộp.
- Giáo viên có thể **ghi đè điểm** của bất kỳ câu nào (ghi lại ai sửa, khi nào).
- `total_score = Σ điểm các câu`. Có thể **chấm lại tự động** toàn đề sau khi sửa khóa đáp án (chỉ khi giáo viên chủ động bấm).

### 3.10 Công bố kết quả

- Mặc định `hidden`: học sinh chỉ thấy “Đã nộp bài”.
- Giáo viên bấm **Công bố** cho cả lớp hoặc từng học sinh, chọn mức: `score_only` hoặc `full`.
- Có thể **thu hồi công bố**.
- API phía học sinh kiểm tra cờ công bố ở **backend**; nếu chưa công bố thì trả 403/rỗng, không chỉ ẩn ở giao diện.

### 3.11 Theo dõi trực tiếp (trang giám sát)

- Bảng theo lớp/đề: **Chưa vào / Đang làm / Đã nộp**, thời gian còn lại, số câu đã trả lời, lần lưu cuối, số lần rời tab (nếu có).
- Cập nhật bằng **polling 10 giây** (đủ dùng cho ≤ 40 học sinh).
- Hành động nhanh: cộng giờ, nộp hộ, mở lại, thu hồi phiên đăng nhập.

### 3.12 Xuất & dọn dữ liệu (lưu ngắn hạn)

- Xuất **CSV** (điểm tổng, điểm từng câu) cho mỗi đề.
- Nút **Xóa dữ liệu của đề** (xóa attempts, answers, file đã nộp). Nên xuất CSV trước.
- Job dọn dẹp hằng ngày: xóa attempt/file của đề đã `archived` hoặc quá `DATA_RETENTION_DAYS` (mặc định 90 ngày).
- Phù hợp giới hạn dung lượng DB miễn phí (xem mục 6).

---

## 4. Yêu cầu phi chức năng

| Hạng mục     | Yêu cầu                                                                                                                   |
| -------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Hiệu năng    | Thao tác autosave < 500 ms ở điều kiện bình thường; tải trang làm bài < 3 giây                                  |
| Độ tin cậy  | Không mất đáp án đã được báo “Đã lưu”; finalize idempotent                                                  |
| Khả dụng     | Chấp nhận cold start của gói free, nhưng không được làm sai thời gian hay mất bài (mục 6.3)                   |
| Tương thích | Chạy tốt trên điện thoại (học sinh có thể dùng điện thoại) và trình duyệt phổ biến; giao diện responsive |
| Ngôn ngữ     | Giao diện tiếng Việt                                                                                                     |
| Múi giờ      | Lưu UTC (`timestamptz`), hiển thị `Asia/Ho_Chi_Minh`                                                                 |
| Bảo mật      | Mục 10                                                                                                                     |
| Bảo trì      | Có migration (Alembic), test cho phần chấm điểm và thời gian, log có cấu trúc                                     |
| Dung lượng   | DB ≤ 0.5 GB (giới hạn gói free); file nằm ngoài DB                                                                    |

---

## 5. Kiến trúc & Techstack

### 5.1 Sơ đồ

```mermaid
flowchart LR
  S[Học sinh / Giáo viên<br/>trình duyệt] -->|HTTPS| FE[Frontend React SPA<br/>Cloudflare Pages]
  FE -->|REST JSON + Bearer| BE[Backend FastAPI<br/>Render free web service]
  BE --> DB[(PostgreSQL<br/>Neon free)]
  BE --> OBJ[(Object storage S3<br/>Cloudflare R2)]
  PING[Cron ping /healthz<br/>cron-job.org / UptimeRobot] -.giữ server thức.-> BE
```

Một **backend duy nhất** (monolith). Job nền chạy trong cùng tiến trình bằng APScheduler, **chạy 1 worker** để job không bị chạy trùng.

### 5.2 Bảng techstack và lý do

| Thành phần       | Lựa chọn                                                                            | Lý do                                                                           |
| ------------------ | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Ngôn ngữ backend | Python 3.12                                                                           | Theo yêu cầu dùng Python                                                      |
| Framework backend  | **FastAPI** + Uvicorn                                                           | Nhẹ, tự sinh tài liệu API (`/docs`), validate bằng Pydantic, dễ học     |
| ORM / migration    | SQLAlchemy 2.0 + Alembic                                                              | Chuẩn, hỗ trợ khóa dòng (`FOR UPDATE`), migration rõ ràng               |
| Validate/Config    | Pydantic v2, pydantic-settings                                                        | Schema riêng cho student/admin để không lộ đáp án                        |
| Hash mật khẩu    | `argon2-cffi`                                                                       | An toàn, thư viện nhỏ                                                        |
| Driver Postgres    | `psycopg` 3 (binary)                                                                | Ổn định, tương thích Neon                                                  |
| Job nền           | APScheduler (trong tiến trình)                                                      | Đủ cho quét hết giờ + dọn dẹp; không cần Celery/Redis                   |
| Rate limit         | `slowapi`                                                                           | Chống dò mật khẩu                                                            |
| Upload/Storage     | `boto3` (S3 API) + `python-multipart`                                             | Dùng được cho R2/Supabase/MinIO                                              |
| Test               | `pytest` + `httpx`                                                                | Test API và logic chấm/thời gian                                              |
| Quản lý gói     | `uv` (hoặc `pip` + `requirements.txt`)                                         | Nhanh, đơn giản                                                               |
| Framework frontend | **React + Vite + TypeScript**                                                   | Theo yêu cầu dùng JS; SPA tĩnh deploy miễn phí dễ dàng                   |
| Routing/dữ liệu  | React Router, TanStack Query                                                          | Quản lý cache, retry, trạng thái tải                                        |
| UI                 | Tailwind CSS (+ shadcn/ui nếu muốn)                                                 | Dựng nhanh, responsive                                                          |
| Form               | react-hook-form + zod                                                                 | Form soạn đề phức tạp                                                       |
| LaTeX/Markdown     | `react-markdown`, `remark-math`, `rehype-katex`, `rehype-sanitize`, `katex` | Render công thức, an toàn                                                     |
| Database           | **PostgreSQL**                                                                  | Cần giao dịch, ràng buộc unique, khóa dòng, JSONB cho cấu hình câu hỏi |

### 5.3 Vì sao chọn như vậy (các phương án đã loại)

- **Vì sao không SQLite:** các dịch vụ free thường có ổ đĩa tạm (mất khi redeploy/ngủ). Mất DB giữa kỳ thi là không chấp nhận được. SQLite chỉ hợp khi tự thuê VM có ổ đĩa bền.
- **Vì sao không Next.js:** backend đã là Python, Next.js thêm một server nữa và khó deploy miễn phí hơn. SPA React + Vite là đủ.
- **Vì sao không WebSocket/Redis:** polling 10 giây và lưu DB là đủ cho ≤ 50 người; ít thành phần = ít lỗi.
- **Vì sao dùng token trong header thay vì cookie:** frontend và backend khác domain; cookie chéo domain hay bị trình duyệt chặn. Token opaque lưu hash trong DB vẫn thu hồi được.
- **Nếu muốn một deploy duy nhất:** có thể để FastAPI phục vụ luôn thư mục build của React (cùng origin, bỏ CORS), đổi lại trang đầu cũng chịu cold start.

### 5.4 Cấu trúc thư mục (monorepo)

```
quiz-app/
├── backend/
│   ├── app/
│   │   ├── main.py              # tạo app, middleware, CORS, đăng ký router
│   │   ├── core/                # config, security (hash, token), time, errors
│   │   ├── db/                  # session, base
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic: admin_*.py và student_*.py TÁCH RIÊNG
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── admin_classes.py / admin_students.py / admin_exams.py
│   │   │   ├── admin_grading.py / admin_monitor.py
│   │   │   └── student.py
│   │   ├── services/
│   │   │   ├── grading.py       # chấm từng dạng câu (hàm thuần, dễ test)
│   │   │   ├── attempts.py      # start, save_answer, finalize_attempt
│   │   │   ├── storage.py       # giao diện lưu file (S3)
│   │   │   └── retention.py     # dọn dữ liệu
│   │   └── jobs.py              # APScheduler: sweeper, retention
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/student/ ...   # Login, ExamList, ExamIntro, TakeExam, Submitted, Result
│   │   ├── pages/admin/ ...     # Classes, Students, ExamEditor, Monitor, Grading, Results
│   │   ├── components/          # MathText, QuestionRenderer, Timer, SaveIndicator
│   │   ├── lib/                 # api.ts, auth.ts, timer.ts, offlineQueue.ts
│   │   └── main.tsx
│   └── vite.config.ts
├── .env.example
└── README.md
```

---

## 6. Hosting & tên miền (miễn phí)

> Điều kiện của các gói miễn phí thay đổi thường xuyên. Kiểm tra lại trên trang chính thức trước khi triển khai (dữ liệu dưới đây rà soát tháng 10/2026).

### 6.1 Phương án khuyến nghị (A)

| Thành phần      | Dịch vụ                            | Ghi chú                                                                                                                                           |
| ----------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Frontend          | **Cloudflare Pages**           | Miễn phí, có HTTPS, mỗi dự án có domain `*.pages.dev`, gắn được tên miền riêng                                                     |
| Backend           | **Render** – free web service | Ngủ sau ~15 phút không có truy cập; đánh thức mất khoảng 1 phút; có giới hạn giờ chạy/tháng                                       |
| Database          | **Neon** – free Postgres      | Free: 0.5 GB/dự án, 100 CU-giờ/tháng, compute tự tắt sau 5 phút rảnh và bật lại trong vài trăm ms khi có truy vấn; không cần thẻ |
| File/ảnh         | **Cloudflare R2** (S3 API)     | Dung lượng bền, không mất khi redeploy. Kiểm tra yêu cầu đăng ký (có thể cần phương thức thanh toán)                             |
| Giữ server thức | cron-job.org / UptimeRobot           | Ping `GET /healthz` mỗi 10 phút (xem 6.3)                                                                                                      |

**Lưu ý quan trọng:**

- **Không dùng Postgres miễn phí của Render** cho dự án này: nó hết hạn sau 30 ngày kể từ lúc tạo. Dùng Neon.
- Ổ đĩa của free web service Render **không bền** (mất khi redeploy/ngủ): không ghi file hay SQLite vào đĩa; mọi thứ bền phải nằm ở Neon và R2.
- Fly.io không còn gói miễn phí cho tài khoản mới.

### 6.2 Phương án dự phòng

- **(B) Oracle Cloud Always Free (VM luôn bật):** chạy Docker Compose (FastAPI + Postgres + Caddy) trên một VM. Ưu: luôn bật, không cold start. Nhược: cần xác minh thẻ, tự quản trị server, và Oracle có thể thu hồi VM Always Free nếu CPU/mạng/bộ nhớ ở mức rất thấp kéo dài, mà một app quiz thì rất rảnh.
- **(C) Trả phí nhẹ cho backend** (gói Render trả phí): bỏ hẳn hiện tượng ngủ. Cân nhắc nếu cold start gây phiền.
- **(D) Supabase** (Postgres + Storage trong một): tiện, nhưng dự án free có thể bị tạm dừng khi lâu không hoạt động; cần kiểm tra điều kiện hiện hành.

### 6.3 Xử lý “server ngủ” khi đang thi

- Backend free sẽ ngủ nếu không ai truy cập. Cách giảm thiểu:
  1. Cron ping `GET /healthz` mỗi 10 phút (có thể giới hạn khung giờ có bài thi). Một web service chạy liên tục khoảng 720 giờ/tháng, trong hạn mức giờ chạy miễn phí của Render [kiểm tra lại].
  2. Nút **“Làm nóng hệ thống”** trong giao diện giáo viên: gọi healthz + một truy vấn DB; nên bấm 5–10 phút trước giờ thi.
  3. Frontend hiển thị “Đang đánh thức máy chủ…” và tự thử lại thay vì báo lỗi.
- **Thời gian vẫn đúng** vì `deadline_at` nằm trong DB, không phụ thuộc server có thức hay không. Nếu server ngủ lúc hết giờ, bài vẫn được finalize ngay khi server hoặc giáo viên chạm vào (cơ chế lazy, mục 3.8).
- Kết nối DB: dùng chuỗi kết nối **pooled** của Neon, bật `pool_pre_ping=True` và `pool_recycle` để không dùng kết nối đã bị đóng khi compute ngủ.

### 6.4 Tên miền dễ nhớ

- **Miễn phí:** đặt tên dự án Cloudflare Pages ngắn gọn, ví dụ `quiz-toantin.pages.dev`. Học sinh chỉ cần nhớ địa chỉ này; backend (`*.onrender.com`) học sinh không thấy.
- **Tùy chọn có phí nhẹ:** mua tên miền riêng, gắn vào Cloudflare Pages (cần trỏ DNS/nameserver theo hướng dẫn của Cloudflare), có HTTPS tự động.
- Có thể tạo **mã QR** hoặc link rút gọn dán lên lớp học.

---

## 7. Thiết kế dữ liệu

### 7.1 Sơ đồ quan hệ

```mermaid
erDiagram
  users ||--o{ class_members : "ghi danh"
  classes ||--o{ class_members : "có"
  classes ||--o{ exam_classes : "được giao"
  exams ||--o{ exam_classes : "giao cho"
  exams ||--o{ questions : "gồm"
  exams ||--o{ attempts : "có bài làm"
  users ||--o{ attempts : "làm"
  attempts ||--o{ answers : "gồm"
  questions ||--o{ answers : "trả lời"
  users ||--o{ sessions : "đăng nhập"
  attempts ||--o{ files : "file nộp"
  exams ||--o{ files : "ảnh đề"
```

### 7.2 Bảng chính

**users**: `id`, `username` (unique), `password_hash`, `full_name`, `role` (`admin`|`student`), `is_active`, `created_at`.

**sessions**: `id`, `user_id`, `token_hash` (unique), `created_at`, `last_seen_at`, `expires_at`.

**classes**: `id`, `name`, `code` (unique), `subject`, `school_year`, `created_at`.

**class_members**: `class_id`, `user_id`, **PK (class_id, user_id)**.

**exams**: `id`, `title`, `subject`, `description_md`, `duration_minutes`, `open_at`, `close_at`, `status` (`draft|published|closed|archived`), `shuffle_questions`, `shuffle_options`, `result_visibility`, `grace_seconds`, `created_by`, `created_at`, `locked_at` (có khi đã có người bắt đầu làm).

**exam_classes**: `exam_id`, `class_id`, **PK (exam_id, class_id)**.

**questions**: `id`, `exam_id`, `position`, `type`, `content_md`, `points` (numeric), `config` (JSONB, phần học sinh được thấy), `answer_key` (JSONB, **chỉ giáo viên**), `explanation_md`.

Ví dụ `config` / `answer_key` theo dạng câu:

```json
// mcq
{ "config": { "options": [ {"id":"A","text_md":"$2$"}, {"id":"B","text_md":"$3$"} ] },
  "answer_key": { "correct": "B" } }

// tf (4 mệnh đề)
{ "config": { "statements": [ {"id":"a","text_md":"..."}, {"id":"b","text_md":"..."} ],
              "scoring": "thpt" },
  "answer_key": { "a": true, "b": false } }

// short_text
{ "config": { "grading": "auto" },
  "answer_key": { "accepted": ["đa thức","da thuc"], "case_sensitive": false, "strip_accents": true } }

// short_number
{ "config": {},
  "answer_key": { "values": ["0.5"], "tolerance": "0", "tolerance_type": "abs" } }

// file_upload
{ "config": { "max_files": 3, "max_mb": 10, "allowed_ext": ["jpg","jpeg","png","pdf"] },
  "answer_key": {} }
```

**attempts**: `id`, `exam_id`, `student_id`, `status`, `started_at`, `deadline_at`, `extra_seconds`, `submitted_at`, `submit_reason`, `shuffle_seed`, `score_auto`, `score_manual`, `total_score`, `grading_status`, `released` (bool), `released_visibility`, `blur_count`, `version`. **UNIQUE (exam_id, student_id)**. Index `(status, deadline_at)` để sweeper quét nhanh.

**answers**: `id`, `attempt_id`, `question_id`, `value` (JSONB), `client_seq`, `updated_at`, `score`, `is_correct`, `needs_review`, `teacher_comment`, `graded_by`, `graded_at`. **UNIQUE (attempt_id, question_id)**.

Giá trị `value`: `mcq` → `{"choice":"B"}`; `tf` → `{"a":true,"b":false}`; `short_text` / `short_number` → `{"text":"1,5"}` (giữ chuỗi thô, chuẩn hóa khi chấm); `file_upload` → `{"file_ids":["..."]}`.

**files**: `id`, `kind` (`question_image`|`submission`), `owner_id`, `exam_id`, `attempt_id` (null nếu ảnh đề), `question_id`, `storage_key` (tên ngẫu nhiên), `original_name`, `mime`, `size_bytes`, `created_at`.

**audit_log** (tùy chọn, nhẹ): `id`, `user_id`, `event` (`login`, `start`, `submit`, `blur`, `grade_override`, `extend`, `reopen`…), `meta` JSONB, `created_at`.

---

## 8. Thiết kế API (REST, tiền tố `/api/v1`)

Tách router theo vai trò: `/admin/*` yêu cầu `role=admin`; `/student/*` yêu cầu `role=student` và kiểm tra quyền sở hữu.

### 8.1 Chung

| Method | Đường dẫn    | Mô tả                               |
| ------ | ---------------- | ------------------------------------- |
| POST   | `/auth/login`  | Đăng nhập, trả token              |
| POST   | `/auth/logout` | Hủy phiên                           |
| GET    | `/auth/me`     | Thông tin người dùng hiện tại   |
| GET    | `/healthz`     | Kiểm tra sống (dùng cho cron ping) |
| GET    | `/time`        | Giờ server (UTC)                     |

### 8.2 Học sinh

| Method | Đường dẫn                                            | Mô tả                                                                                                      |
| ------ | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| GET    | `/student/exams`                                       | Đề đang mở của lớp mình + trạng thái từng đề                                                     |
| POST   | `/student/exams/{id}/start`                            | Bắt đầu/tiếp tục (idempotent), trả attempt                                                             |
| GET    | `/student/attempts/{id}`                               | Nạp lại bài: câu hỏi (không có khóa đáp án), đáp án đã lưu, `deadline_at`, `server_now` |
| PUT    | `/student/attempts/{id}/answers/{question_id}`         | Lưu một câu `{value, client_seq}`                                                                       |
| POST   | `/student/attempts/{id}/questions/{question_id}/files` | Tải file nộp (multipart)                                                                                   |
| DELETE | `/student/attempts/{id}/files/{file_id}`               | Xóa file đã tải                                                                                          |
| POST   | `/student/attempts/{id}/submit`                        | Nộp bài (idempotent)                                                                                       |
| POST   | `/student/attempts/{id}/events`                        | Ghi sự kiện nhẹ (rời tab)                                                                                |
| GET    | `/student/attempts/{id}/result`                        | Chỉ trả dữ liệu khi giáo viên đã công bố                                                           |

### 8.3 Giáo viên

| Nhóm      | Đường dẫn chính                                                                                                                              |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Lớp       | `GET/POST /admin/classes`, `PATCH/DELETE /admin/classes/{id}`                                                                                 |
| Học sinh  | `GET/POST /admin/students`, `PATCH /admin/students/{id}`, `POST /admin/students/import` (CSV), `POST /admin/students/{id}/reset-password` |
| Ghi danh   | `PUT /admin/classes/{id}/members`                                                                                                               |
| Đề       | `GET/POST /admin/exams`, `GET/PATCH/DELETE /admin/exams/{id}`, `POST /admin/exams/{id}/duplicate`, `/publish`, `/close`, `/archive`   |
| Câu hỏi  | `POST /admin/exams/{id}/questions`, `PATCH/DELETE /admin/questions/{id}`, `POST /admin/exams/{id}/questions/reorder`                        |
| Ảnh đề  | `POST /admin/assets` (multipart), trả URL                                                                                                      |
| Theo dõi  | `GET /admin/exams/{id}/attempts` (kèm finalize hết hạn)                                                                                      |
| Can thiệp | `POST /admin/attempts/{id}/extend`, `/reopen`, `/force-submit`                                                                              |
| Chấm      | `GET /admin/attempts/{id}`, `PUT /admin/answers/{id}/grade`, `POST /admin/exams/{id}/regrade`                                               |
| Công bố  | `POST /admin/exams/{id}/release` (`scope`, `visibility`), `/unrelease`                                                                    |
| Xuất/xóa | `GET /admin/exams/{id}/export.csv`, `DELETE /admin/exams/{id}/data`                                                                           |

### 8.4 Quy ước lỗi

JSON thống nhất: `{ "error": { "code": "attempt_closed", "message": "…" } }`. Mã thường dùng: `unauthorized`, `forbidden`, `not_found`, `attempt_closed`, `exam_not_open`, `validation_error`, `rate_limited`.

---

## 9. Xử lý đồng thời & toàn vẹn dữ liệu

| Tình huống                                             | Cách xử lý                                                                                                                                                     |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Bấm “Bắt đầu” hai lần / mở hai tab               | `UNIQUE(exam_id, student_id)` + `INSERT … ON CONFLICT DO NOTHING` rồi đọc lại attempt → luôn một attempt                                              |
| Nộp bài và job quét hết giờ chạy cùng lúc       | `finalize_attempt` dùng cập nhật có điều kiện, chỉ một bên thắng (xem mã bên dưới); bên còn lại thấy `status` đã `submitted` và dừng |
| Hai tab cùng ghi một câu / gói tin tới sai thứ tự | `client_seq`: chỉ nhận khi lớn hơn giá trị hiện có; mỗi câu một dòng nên không xung đột giữa các câu                                         |
| Ghi đáp án khi đã hết hạn                         | Kiểm tra `now() ≤ deadline_at + grace` trong cùng giao dịch; nếu không → `409 attempt_closed`                                                          |
| Giáo viên sửa điểm cùng lúc với tự chấm        | Tự chấm chỉ ghi điểm khi `finalize`; giáo viên sửa sau đó dùng `version` (optimistic lock) để tránh đè nhau                                   |
| Sửa đề khi có người đang làm                     | Khóa chỉnh sửa khi `locked_at` đã có; sửa phải qua “Nhân bản đề”                                                                                  |
| Hai giáo viên cùng sửa một đề                     | Cột `version` trên đề/câu hỏi; lưu với `version` cũ bị từ chối                                                                                    |
| Kết nối DB bị đóng (Neon ngủ)                      | `pool_pre_ping`, thử lại 1 lần ở tầng session                                                                                                              |

Mức cô lập mặc định `READ COMMITTED` của Postgres là đủ nhờ các ràng buộc `UNIQUE` và cập nhật có điều kiện.

**Mẫu finalize idempotent (SQL):**

```sql
UPDATE attempts
   SET status = 'submitted',
       submitted_at = LEAST(now(), deadline_at),   -- hết giờ thì lấy đúng deadline
       submit_reason = :reason
 WHERE id = :id AND status = 'in_progress'
RETURNING *;
-- Có dòng trả về  → bạn là "người thắng": chấm điểm trong cùng giao dịch
-- Không có dòng   → đã được nộp trước đó: bỏ qua, không chấm lại
```

**Mẫu chuẩn hóa số (Python):**

```python
from decimal import Decimal, InvalidOperation

def parse_number(raw: str) -> Decimal | None:
    s = raw.strip().replace(" ", "").replace(",", ".")
    try:
        if "/" in s:
            a, b = s.split("/", 1)
            return Decimal(a) / Decimal(b)
        return Decimal(s)
    except (InvalidOperation, ZeroDivisionError, ValueError):
        return None
```

---

## 10. Bảo mật

- **Không lộ đáp án:** schema Pydantic cho học sinh (`StudentQuestionOut`) không có `answer_key` và `explanation_md`. Có test tự động kiểm tra không rò rỉ khóa trong bất kỳ phản hồi nào của `/student/*`.
- **Kết quả ẩn ở backend:** `/student/attempts/{id}/result` kiểm tra `released`.
- **Phân quyền theo đối tượng:** học sinh chỉ truy cập attempt có `student_id` là mình; chỉ thấy đề thuộc lớp mình.
- **Mật khẩu:** Argon2; không ghi log mật khẩu; mật khẩu sinh ngẫu nhiên chỉ hiện một lần.
- **Token:** ngẫu nhiên đủ dài, lưu hash, có hạn; thu hồi được.
- **Giới hạn tốc độ:** đăng nhập, upload.
- **CORS:** chỉ cho phép đúng origin của frontend; bắt buộc HTTPS.
- **Upload:** kiểm tra đuôi + MIME thật (đọc đầu file), giới hạn dung lượng, tên lưu ngẫu nhiên, bucket riêng tư, tải xuống bằng signed URL có hạn ngắn; không render file học sinh nộp như HTML.
- **Nội dung đề:** Markdown được sanitize, không cho phép script/HTML thô; KaTeX `trust: false`.
- **Header bảo mật:** CSP cho frontend (nguồn script chỉ từ chính site), `X-Content-Type-Options`, `Referrer-Policy`.
- **Bí mật:** nằm trong biến môi trường, không commit lên Git.
- **Ghi vết nhẹ:** đăng nhập, bắt đầu, nộp, sửa điểm, cộng giờ, mở lại.
- **Chống gian lận [MVP nhẹ]:** chỉ ghi số lần rời tab để giáo viên tham khảo; không tự động phạt.

---

## 11. Danh sách màn hình (dùng làm đầu vào thiết kế UI)

**Chung:** Đăng nhập; trang lỗi / mất kết nối.

**Học sinh**

1. Danh sách đề của tôi (trạng thái: chưa làm / đang làm / đã nộp / có kết quả)
2. Giới thiệu đề (tên, thời lượng, số câu, lưu ý) + nút Bắt đầu
3. **Làm bài**: thanh đồng hồ đếm ngược cố định, chỉ báo lưu, lưới điều hướng câu, vùng câu hỏi theo dạng (MCQ, TF, trả lời ngắn chữ, số, nộp file), nút Nộp bài
4. Hộp thoại xác nhận nộp (nêu số câu chưa làm)
5. Đã nộp bài (không hiển thị điểm)
6. Xem kết quả (chỉ khi được công bố; mức `score_only` hoặc `full`)

**Giáo viên**

1. Bảng điều khiển (đề sắp/đang diễn ra, việc cần chấm)
2. Danh sách lớp + chi tiết lớp (học sinh, ghi danh, nhập CSV)
3. Danh sách/Chi tiết học sinh (reset mật khẩu, khóa)
4. Danh sách đề
5. **Soạn đề**: thông tin chung, danh sách câu (kéo thả sắp xếp), trình soạn câu hỏi có preview LaTeX + tải ảnh, cấu hình điểm/đáp án theo từng dạng, thiết lập đề (thời gian, cửa sổ, xáo trộn, hiển thị kết quả)
6. Xem trước như học sinh
7. **Giám sát trực tiếp** (trạng thái từng học sinh, còn bao lâu, cộng giờ/nộp hộ/mở lại, nút Làm nóng hệ thống)
8. **Chấm bài** (theo học sinh hoặc theo câu; xem file nộp; nhập điểm + nhận xét)
9. Kết quả đề (bảng điểm, lọc, công bố/thu hồi, xuất CSV, xóa dữ liệu)
10. Cài đặt (thời gian lưu dữ liệu, đổi mật khẩu admin)

---

## 12. Kiểm thử & nghiệm thu

### 12.1 Kiểm thử tự động (pytest)

- Hàm chấm từng dạng: MCQ, TF (3 chế độ), số (dấu phẩy, phân số, sai số), chữ (hoa/thường, dấu).
- `finalize_attempt` idempotent: gọi song song nhiều lần chỉ chấm một lần.
- Quy tắc thời gian: tính `deadline_at`, grace, `submitted_at = deadline_at` khi hết giờ.
- `client_seq`: gói cũ không ghi đè gói mới.
- Rò rỉ đáp án: quét mọi phản hồi `/student/*`.
- Phân quyền: học sinh A không đọc được attempt của học sinh B; học sinh không gọi được `/admin/*`.

### 12.2 Kịch bản nghiệm thu (thủ công)

| #  | Kịch bản                                                   | Kết quả mong đợi                                                                 |
| -- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| 1  | Làm 5 câu, đóng tab, mở lại sau 2 phút                | Đáp án còn nguyên, đồng hồ đã giảm tương ứng                           |
| 2  | Ngắt mạng khi đang làm, trả lời tiếp, bật lại mạng | Banner mất kết nối, sau đó tự đồng bộ, hiện “Đã lưu”                  |
| 3  | Đóng máy hẳn, không mở lại tới khi quá giờ         | Bài tự nộp với các đáp án đã lưu; giáo viên thấy `timeout`           |
| 4  | Chỉnh đồng hồ máy học sinh sớm/trễ                   | Thời gian còn lại vẫn đúng theo server                                         |
| 5  | Mở hai tab cùng một bài                                  | Không tạo hai attempt; đáp án mới nhất được giữ                           |
| 6  | Server đang ngủ khi học sinh vào                         | Hiện “đang đánh thức máy chủ”, vào được sau khi thức, bài không mất |
| 7  | Học sinh nộp bài rồi xem thử đường dẫn kết quả    | Không có điểm/đáp án tới khi giáo viên công bố                           |
| 8  | Giáo viên cộng 5 phút cho một học sinh                 | Chỉ học sinh đó có thêm giờ                                                   |
| 9  | 6–10 học sinh cùng làm và nộp                          | Không lỗi, không mất đáp án                                                   |
| 10 | Tải file 15 MB / file `.exe`                              | Bị từ chối kèm thông báo rõ                                                   |

---

## 13. Lộ trình triển khai (ước tính 3–4 tuần làm bán thời gian)

| Giai đoạn                           | Nội dung                                                                                                   | Kết quả                                                       |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **P0. Khởi tạo**              | Repo, FastAPI + Vite chạy cục bộ, Postgres (Docker hoặc Neon), Alembic, CI cơ bản                     | Hello-world nối FE–BE–DB                                     |
| **P1. Tài khoản & lớp**      | Đăng nhập, phiên, lớp, học sinh, ghi danh, nhập CSV                                                  | Giáo viên quản lý được lớp                              |
| **P2. Soạn đề**              | CRUD đề/câu hỏi 5 dạng, preview LaTeX, upload ảnh, thiết lập đề                                   | Tạo được một đề hoàn chỉnh                             |
| **P3. Làm bài**               | Start, autosave, offline queue, đếm ngược, resume, submit, finalize (lazy + sweeper)                    | Học sinh làm trọn vẹn một bài, chịu được gián đoạn |
| **P4. Chấm & kết quả**       | Tự chấm, chấm tay, công bố, giám sát, cộng giờ/mở lại, xuất CSV                                 | Vòng đời đề khép kín                                     |
| **P5. Triển khai & rà soát** | Deploy Cloudflare Pages + Render + Neon + R2, cron ping, tên miền, kiểm thử nghiệm thu, dọn dữ liệu | Chạy thử với lớp thật                                      |

Gợi ý: làm **P3 sớm và test kỹ**, đây là phần rủi ro cao nhất.

---

## 14. Rủi ro & giảm thiểu

| Rủi ro                                            | Mức        | Giảm thiểu                                                                                            |
| -------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------- |
| Server free ngủ đúng giờ thi                   | Cao         | Cron ping, nút làm nóng, deadline lưu trong DB, cơ chế lazy finalize; phương án trả phí nhẹ |
| Gói miễn phí đổi điều kiện                 | Trung bình | Lớp `StorageBackend` trừu tượng, dùng Postgres/S3 chuẩn để dễ chuyển nhà cung cấp         |
| DB 0.5 GB đầy                                    | Thấp–TB   | Ảnh/file ở R2; dọn dữ liệu cũ; xuất CSV trước khi xóa                                         |
| Học sinh dùng chung tài khoản                  | TB          | Giáo viên thu hồi phiên; ghi vết đăng nhập; mỗi học sinh một mật khẩu riêng               |
| Công thức LaTeX sai làm hỏng đề              | TB          | Preview trực tiếp, báo lỗi tại chỗ, xem trước như học sinh trước khi xuất bản             |
| Mạng yếu của học sinh                          | TB          | Hàng đợi offline, retry, chỉ báo lưu, độ trễ `grace_seconds`                                 |
| Mất dữ liệu do thao tác nhầm của giáo viên | TB          | Xác nhận trước khi xóa, khuyến nghị xuất CSV, “lưu trữ” trước khi “xóa”                |

---

## 15. Giả định & câu hỏi cần bạn xác nhận [?]

1. **Câu Đúng/Sai** có theo kiểu 4 mệnh đề a, b, c, d với điểm từng phần 10%/25%/50%/100% không, hay chỉ cần chấm tất-cả-hoặc-không? (Đang giả định hỗ trợ cả ba, mặc định `thpt`.)
2. **MCQ** chọn 1 đáp án đúng, hay cần cả dạng nhiều đáp án đúng? (Đang giả định chọn 1.)
3. **Một học sinh thuộc nhiều lớp** được không? (Đang giả định được.)
4. **Hết `close_at` mà học sinh còn đang làm** thì tự nộp luôn hay vẫn cho đủ thời lượng? (Đang giả định `deadline = min(start + thời lượng, close_at)`.)
5. **“Nhập đề bằng LaTeX”** nghĩa là gõ công thức LaTeX trong nội dung câu hỏi (đang giả định), hay cần nhập **nguyên file `.tex`** để hệ thống tách thành câu? (Phương án sau để [V2].)
6. **File học sinh nộp** nên cho phép loại nào và tối đa bao nhiêu MB? (Đang giả định ảnh/PDF ≤ 10 MB, ≤ 3 file/câu.)
7. **Thời gian lưu dữ liệu** mong muốn bao lâu? (Đang giả định 90 ngày.)
8. Có cần **nhiều giáo viên** với quyền riêng (mỗi người chỉ thấy lớp của mình) không? (MVP giả định một admin chung.)
9. Chấp nhận **cold start** (~1 phút lần đầu) hay muốn trả phí nhẹ để server luôn bật?

---

## Phụ lục A. Biến môi trường (`.env.example`)

```
# Backend
DATABASE_URL=postgresql+psycopg://USER:PASS@HOST/DB?sslmode=require
SECRET_KEY=doi-thanh-chuoi-ngau-nhien-dai
CORS_ORIGINS=https://quiz-toantin.pages.dev
ADMIN_USERNAME=admin
ADMIN_PASSWORD=doi-mat-khau-manh
TIMEZONE=Asia/Ho_Chi_Minh
ATTEMPT_GRACE_SECONDS=10
SESSION_TTL_HOURS=12
DATA_RETENTION_DAYS=90
MAX_UPLOAD_MB=10

# Object storage (S3-compatible)
S3_ENDPOINT=https://<account>.r2.cloudflarestorage.com
S3_BUCKET=quiz-files
S3_ACCESS_KEY=...
S3_SECRET_KEY=...

# Frontend (Vite)
VITE_API_BASE_URL=https://ten-backend.onrender.com/api/v1
```

## Phụ lục B. Thuật toán đồng hồ phía client (rút gọn)

```ts
// Khi nhận bất kỳ phản hồi nào có server_now:
offset = Date.parse(server_now) - Date.now();

// Mỗi 250 ms:
remainingMs = Date.parse(deadline_at) - (Date.now() + offset);
if (remainingMs <= 0) submitOnce();   // server vẫn là bên quyết định cuối cùng

// Mỗi 30 s và sau mỗi lần autosave: cập nhật lại offset + deadline_at từ phản hồi.
```

## Phụ lục C. Checklist trước ngày thi

- [ ] Xuất bản đề, xem thử bằng tài khoản học sinh thật.
- [ ] Mọi học sinh đã được ghi danh đúng lớp; mật khẩu đã phát.
- [ ] Cron ping đang chạy; bấm “Làm nóng hệ thống” trước giờ thi 10 phút.
- [ ] `result_visibility` đang là `hidden`.
- [ ] Đã thử một bài làm đầy đủ (gồm đóng tab, tắt mạng) trên điện thoại và máy tính.
- [ ] Đã xuất CSV của đợt thi trước và dọn dữ liệu cũ.
