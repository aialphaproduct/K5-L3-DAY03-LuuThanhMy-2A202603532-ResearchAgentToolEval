---
name: define
track: bonus
kind: live_api
provider: dictionaryapi.dev
requires_env: []
inputs: [word, lang]
outputs: [meanings, phonetic]
side_effect: false
requires_confirmation: false
---

# define

Tra nghĩa một từ (mặc định tiếng Anh) qua dictionaryapi.dev — không cần key.

**Khi nào dùng:** người dùng hỏi nghĩa/định nghĩa của một TỪ cụ thể
("define serendipity", "từ X nghĩa là gì").

**Khi nào KHÔNG dùng:** giới thiệu khái niệm dài/thực thể (dùng `wiki`), tin
tức (`lookup`), hay dịch cả câu. Trả về nghĩa theo từ loại; từ không tồn tại
(HTTP 404) hoặc lỗi mạng trả về dict lỗi, không raise.
