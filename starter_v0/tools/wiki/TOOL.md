---
name: wiki
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [title, sentences]
outputs: [summary, url]
side_effect: false
requires_confirmation: false
---

# wiki

Tóm tắt bách khoa từ Wikipedia (REST API công khai, không cần key).

**Khi nào dùng:** cần kiến thức nền ổn định về một khái niệm/thực thể —
"X là gì", "giới thiệu ngắn về Y". Tốt cho định nghĩa, bối cảnh lịch sử.

**Khi nào KHÔNG dùng:** tin tức mới/thời sự (dùng `lookup topic=news`), tìm
bài đăng mạng xã hội (dùng `social_search`), hay đọc một URL cụ thể (dùng
`fetch`).

`sentences` giới hạn số câu trả về (mặc định 3). Lỗi mạng / không tìm thấy
trang trả về dict lỗi, không raise.
