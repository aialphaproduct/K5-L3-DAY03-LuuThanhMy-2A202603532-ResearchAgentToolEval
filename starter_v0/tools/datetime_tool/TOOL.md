---
name: datetime
track: bonus
kind: local_formatter
provider: none
requires_env: []
inputs: [timezone, fmt]
outputs: [datetime, date, time, weekday]
side_effect: false
requires_confirmation: false
---

# datetime

Lấy ngày giờ hiện tại theo múi giờ IANA. Cục bộ, không gọi mạng.

**Khi nào dùng:** người dùng hỏi "bây giờ là mấy giờ", "hôm nay ngày bao nhiêu",
"thứ mấy", hoặc cần mốc thời gian hiện tại cho một bản tin/đầu mục.

**Khi nào KHÔNG dùng:** hỏi về một sự kiện trong quá khứ/tương lai, hay tin tức
theo ngày (dùng `lookup` với `timeframe`). Không phải nơi tra lịch sử.

`timezone` mặc định `UTC`; truyền tên IANA như `Asia/Ho_Chi_Minh`. Múi giờ
không hợp lệ trả về dict lỗi, không raise.
