---
always_on: true
description: "Quy tắc phân nhánh Git và chính sách đẩy code sang nhánh main"
---

# Quy Tắc Phân Nhánh Git & Đẩy Code (Git Workflow Policy)

> **CHỈ THỊ CỐ ĐỊNH CỦA NGƯỜI DÙNG (BẮT BUỘC TUÂN THỦ 100%):**

1. **Trong quá trình phát triển (từng task/từng tính năng):**
   - **CHỈ commit và push vào nhánh `dev`** (`git push origin dev`).
   - **TUYỆT ĐỐI KHÔNG** chạm, không merge và không push vào nhánh `main` khi đang làm task lẻ.

2. **Điều kiện để đẩy code sang nhánh `main`:**
   - Chỉ thực hiện vào **cuối ngày làm việc**.
   - Phải đáp ứng đầy đủ 2 điều kiện:
     1. Đã hoàn thành toàn bộ khối lượng công việc dự kiến của ngày hôm đó.
     2. Đã chạy kiểm thử tự động đầy đủ (100% Backend Pytest, 100% Frontend Vitest, Linting không lỗi).
   - Được sự xác nhận của người dùng tại thời điểm tổng kết ngày làm việc.

