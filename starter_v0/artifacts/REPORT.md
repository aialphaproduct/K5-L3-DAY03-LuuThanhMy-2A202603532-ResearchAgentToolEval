# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
>
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: Lưu Thanh Mỹ
- Members: Vũ Trí Dũng, Nguyễn Tuấn Quang, Khổng Tiến Dương, Phan Hải Đăng, Lưu Thanh Mỹ
- Provider/model dùng trong các run trích dẫn: OpenRouter / `openai/gpt-4o-mini`.

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent tìm thông tin từ web, X, Hacker News, Wikipedia, GitHub và arXiv, đọc nội dung từ URL và tổng hợp thành bản tin có link nguồn. Agent có thể tra chính sách mẫu của bài lab, lưu ghi chú cục bộ, hỏi lại khi thiếu dữ kiện và xin xác nhận trước khi gửi bản tin lên Telegram.

**Cấu hình demo** dùng prompt `v3` và model `openai/gpt-4o-mini` qua OpenRouter. Giao diện Streamlit hỗ trợ hội thoại nhiều lượt, hiển thị công cụ đã gọi và lưu transcript.

**Dùng thử trên máy** tại [giao diện Streamlit](http://localhost:8501) sau khi chạy `python -m streamlit run app.py` từ thư mục `starter_v0/`. Chưa có URL công khai được xác nhận.

## A2. Tool agent có

| Công cụ | Làm được gì | Nhóm tự thêm? |
| --- | --- | --- |
| `clarify` | Hỏi thông tin còn thiếu hoặc xin xác nhận, sau đó chờ lượt trả lời. | Không |
| `timeline` | Lấy bài đăng gần đây của một tài khoản X đã xác định. | Không |
| `social_search` | Tìm bài đăng trên X theo từ khóa, ưu tiên bài mới nhất hoặc nổi bật. | Không |
| `lookup` | Tìm thông tin hoặc tin tức trên web theo khoảng thời gian qua Tavily. | Không |
| `fetch` | Trích nội dung của một URL cụ thể qua Firecrawl để đọc hoặc tóm tắt. | Không |
| `format` | Trình bày kết quả đã thu thập thành bản tin Markdown có link nguồn. | Không |
| `send` | Gửi văn bản đến kênh Telegram đã cấu hình khi lời gọi có `confirmed=true`. | Không |
| `policy` | Tra các mục trong bộ chính sách nội bộ mẫu, kèm nguồn và ngày hiệu lực nếu có. | Không |
| `papers` | Tìm bài nghiên cứu trên arXiv theo từ khóa, kèm tóm tắt và link bài. | Không |
| `paper_text` | Tải PDF từ ID hoặc URL arXiv và trích văn bản từ số trang đã chọn. | Không |
| `hn_search` | Tìm bài viết và thảo luận trên Hacker News theo chủ đề. | **Có** |
| `wiki_search` | Tra bài và đoạn giới thiệu trên Wikipedia tiếng Việt hoặc tiếng Anh. | **Có** |
| `repo_search` | Tìm kho mã nguồn công khai trên GitHub, sắp theo sao, lượt fork hoặc lần cập nhật. | **Có** |
| `notes` | Lưu và xem lại ghi chú trong tệp `notes/notes.json` trên máy chạy agent. | **Có** |
| `calc` | Tính biểu thức số học từ các số cụ thể. | **Có** |
| `datetime` | Lấy ngày giờ hiện tại theo múi giờ IANA. | **Có** |
| `wiki` | Lấy tóm tắt một trang Wikipedia theo tên chủ đề. | **Có** |
| `define` | Tra nghĩa một từ, mặc định dùng tiếng Anh. | **Có** |

Hai công cụ X cần cấu hình RapidAPI. Tính năng gửi cần cấu hình bot và kênh Telegram.

## A3. Câu hỏi mẫu để thử

1. Tìm 3 tin về AI agent trên web trong 24 giờ qua và tóm tắt thành bản tin ngắn có link nguồn.
2. Tìm 3 bài thảo luận trên Hacker News về model AI chạy trên máy cá nhân.
3. Tra Wikipedia tiếng Việt để giải thích học tăng cường là gì và dẫn link bài viết.
4. Tìm 3 repository GitHub về đánh giá AI agent, ưu tiên kho có nhiều sao.
5. Lưu ghi chú “Demo Day 03 cần một bản tin có nguồn”. Ở lượt sau, hỏi “Cho tôi xem các ghi chú đã lưu”.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Kết quả theo phiên bản

Các run base đã đối chiếu đều dùng OpenRouter với `openai/gpt-4o-mini`. Điểm chính là `case_accuracy` trên bộ base 20 case.

| Phiên bản | Thay đổi | Giả thuyết | Điểm trước → sau | Run JSON |
| --- | --- | --- | --- | --- |
| v0 | Baseline | Đo hành vi của cấu hình starter để xác định nhóm lỗi. | — → **70% (14/20)** | [Run v0](../runs/v0_B_base_openrouter_20261110T094641803175.json) |
| v1 | `system_prompt.md` | Hướng dẫn rõ phạm vi nghiên cứu và khi nào hỏi lại để giảm gọi nhầm công cụ. | 70% → **85% (17/20)** | [Run v1](../runs/v1_B_base_openrouter_20261110T103823244196.json) |
| v2 | `system_prompt.md` và `tools.yaml` | Làm rõ cách chọn công cụ và tham số để giảm lỗi chọn sai. Điểm chọn đúng tool tăng từ 95% lên 100%, trong khi điểm toàn case giữ ở 85%. Vòng này thay đổi hai file nên kết quả đo tác động chung. | 85% → **85% (17/20)** | [Run v2](../runs/v2_B_base_openrouter_20261110T113325303962.json) |
| v3 | `system_prompt.md` | Làm rõ cách tách từ khóa khỏi bộ lọc tin tức và kiểu xác nhận khi đăng. | 85% → **100% theo nhật ký, chờ đối chiếu** | `runs/v3_B_base_openrouter_20261110T122716662718.json` chưa có trong thư mục hiện tại. |
| v3-rerun | `system_prompt_v3.md` và `tools.yaml` hiện tại | Đo lại cấu hình v3 mà UI đang dùng. Hash khác dòng v3 lịch sử. | **85% (17/20)** | [Run base hiện tại](../runs/v3-rerun_B_base_openrouter_20261110T173844109126.json) |

Hai run hiện tại dùng artifact `v3-rerun+p151ad41190b9+t8d9098dbc911`. Eval chấm lời gọi và tham số. Khi chạy, Telegram được tắt và ghi chú dùng tệp tạm để tách khỏi dữ liệu của nhóm.

## B2. Phân tích lỗi

Sáu lỗi dưới đây lấy từ đúng run `v0` trong B1. Cột cuối mô tả thay đổi hoặc kết quả đã quan sát được ở `v1` và `v2`.

| Case | Phân loại | Lời gọi thực tế ở v0 | Sai ở đâu | Thay đổi và kết quả |
| --- | --- | --- | --- | --- |
| `R08_out_of_scope` | `out_of_scope` | `send(text=…)` | Gọi công cụ gửi cho câu hỏi tích phân. | Quy tắc ngoài phạm vi yêu cầu trả lời mà không gọi công cụ. PASS ở v1 và v2. |
| `R10_missing_handle` | `missing_info` | `timeline(screenname="sama")` | Đoán tài khoản thay vì hỏi. | v1 đã gọi `clarify` nhưng thiếu `response_type`. v2 PASS. |
| `R11_missing_url` | `missing_info` | `fetch(url="https://example.com/article")` | Tự điền URL khi chưa có link. | v1 đã hỏi link nhưng thiếu `response_type="text"`. v2 PASS. |
| `R12_confirm_before_send` | `wrong_boundary` | `send(text=…)` | Gọi tool gửi khi chưa xin xác nhận. | v2 chuyển sang `clarify` nhưng dùng `text` thay cho `yes_no`. Prompt hiện tại yêu cầu hỏi xác nhận dạng có/không trước. |
| `R13_parallel_web_and_tweets` | `wrong_arg_value` quan sát được | `lookup(query="AI news", timeframe="day")` và `social_search(query="AI")` | Chọn đủ hai tool nhưng `lookup` thiếu `topic="news"` và thêm chữ `news` vào từ khóa. | v2 đã truyền đúng topic, vẫn gộp “tin” và “hôm nay” vào query. Prompt hiện tại yêu cầu tách chủ đề khỏi bộ lọc. |
| `R14_out_of_scope_coding` | `out_of_scope` | `send(text=…)` | Gọi công cụ gửi để trả lời bài lập trình. | Quy tắc ngoài phạm vi yêu cầu tránh gọi tool. PASS ở v1 và v2. |

Ở v2, `R03_web_news_routing` cũng trượt vì `query="tin tức AI hôm nay"` thay cho `"AI"`. Cùng với R13, lỗi này giải thích vì sao chọn đúng tool 100% vẫn chỉ đạt 85% toàn case.

Ở lần chạy lại v3, R12 đã PASS. Base còn ba lỗi:

- `R03_web_news_routing` và `R13_parallel_web_and_tweets` gọi đúng công cụ nhưng truyền “tin tức AI” hoặc “tin AI hôm nay” thay cho từ khóa “AI”.
- `M06_switch_tool` gọi thêm `social_search` dù người dùng đã chuyển từ X sang tìm tin trên web.

## B3. Eval nhóm

Bộ [eval nhóm hiện tại](../data/eval_group.json) có **24 case**, gồm **12 một lượt và 12 nhiều lượt**. Cả tám tool nhóm bổ sung đều có ít nhất một case kỳ vọng model gọi đúng tool.

[Run group v3 hiện tại](../runs/v3-rerun_B_group_openrouter_20261110T173844839336.json) đạt **22/24 (91,67%)**, không có lỗi provider. Cả bốn case G11–G14 đều PASS. [Run group v4 của nhánh LTM](../runs/v4_B_group_openrouter_20261110T112154431374.json) đạt **9/10** trên bộ 10 case lịch sử.

| Case | Kiểu | Hành vi kiểm tra | Tool và tham số kỳ vọng | Kết quả v3 hiện tại |
| --- | --- | --- | --- | --- |
| `G01_missing_article_link` | Một lượt | Hỏi xin URL khi chưa có link để đọc bài cụ thể. | PASS |
| `G02_news_filters` | Một lượt | Tách từ khóa khỏi loại tìm kiếm, khoảng thời gian và số lượng kết quả. | PASS |
| `G03_handle_normalization` | Một lượt | Truy xuất bài từ một tài khoản, bỏ ký tự @ và giữ giới hạn 2. | PASS |
| `G04_search_latest_posts` | Một lượt | Tìm theo từ khóa trên X và sắp xếp theo bài mới nhất. | PASS |
| `G05_confirm_delivery` | Một lượt | Yêu cầu xác nhận trước khi đăng dù nội dung đã đầy đủ. | PASS |
| `G06_replace_article_url` | Nhiều lượt | Dùng URL thay thế ở lượt cuối và chỉ gọi fetch một lần. | PASS |
| `G07_change_news_timeframe` | Nhiều lượt | Cập nhật thời gian và giữ từ khóa, loại tin tức, số lượng từ lượt trước. | PASS |
| `G08_cancel_delivery` | Nhiều lượt | Tôn trọng yêu cầu hủy ở lượt cuối, không gọi công cụ sau khi người dùng từ chối. | PASS |
| `G09_switch_to_account` | Nhiều lượt | Chuyển từ tìm theo từ khóa sang lấy bài từ tài khoản được chỉ định. | PASS |
| `G10_missing_comparison_url` | Nhiều lượt | Hỏi xin URL còn thiếu và chờ đủ dữ liệu theo yêu cầu trước khi gọi fetch. | PASS |
| `LTM_G01_calc_routing` | Một lượt | Phép tính số học rõ ràng → gọi calc, không phải lookup/web. | PASS |
| `LTM_G02_wiki_concept_routing` | Một lượt | Kiến thức bách khoa ổn định ('X là gì') → wiki, không phải lookup topic=news. | PASS |
| `LTM_G03_define_word_routing` | Một lượt | Hỏi nghĩa một TỪ đơn → define với word đúng, không dùng wiki/lookup. | PASS |
| `LTM_G04_datetime_routing` | Một lượt | Hỏi thời gian hiện tại → datetime, không phải lookup. | PASS |
| `LTM_G05_algebra_out_of_scope` | Một lượt | Đại số ký hiệu (giải phương trình chữ) KHÔNG phải số học → KHÔNG được lạm dụng calc, phải từ chối/định hướng. | FAIL — gọi calc để giải phương trình có biến. |
| `LTM_G06_calc_multiturn_fill` | Nhiều lượt | 3 turns: gom số từ lượt trước, lượt cuối yêu cầu cộng → calc (không hỏi lại nữa vì đã đủ số). | PASS |
| `LTM_G07_wiki_multiturn_correction` | Nhiều lượt | 3 turns: sửa chủ đề RAG→LoRA, lượt cuối vẫn là 'X là gì' → wiki về LoRA. | PASS |
| `LTM_G08_summarize_not_send_boundary` | Nhiều lượt | 2 turns: người dùng rút lại yêu cầu gửi → chỉ lookup tin, KHÔNG gọi send/clarify-để-gửi. | PASS |
| `LTM_G09_lookup_carryover_timeframe` | Nhiều lượt | 2 turns: carry timeframe=week + topic=news từ lượt 1, thu hẹp query=Bitcoin ở lượt 2. | PASS |
| `LTM_G10_still_missing_handle_clarify` | Nhiều lượt | 2 turns: đã có limit=5 nhưng VẪN thiếu handle → clarify xin tên tài khoản, không đoán bừa. | FAIL — gọi timeline với handle rỗng. |
| `G11_hn_ask_posts` | Một lượt | Chọn công cụ Hacker News và truyền đúng từ khóa, loại bài Ask HN và số lượng. | PASS |
| `G12_wikipedia_search_vi` | Một lượt | Chọn wiki_search cho danh sách bài Wikipedia tiếng Việt thay vì wiki để lấy tóm tắt một trang. | PASS |
| `G13_repo_sort_correction` | Nhiều lượt | Giữ GitHub, từ khóa và số lượng từ lượt trước, đồng thời đổi cách sắp xếp sang updated. | PASS |
| `G14_notes_list_limit` | Nhiều lượt | Giữ ý định xem ghi chú ở lượt trước và gọi notes với thao tác list, giới hạn 2. | PASS |

## B4. Bằng chứng chat trực tiếp

[Transcript CLI v3, 4 lượt](../transcripts/v3_openrouter_20261110T104038722560.transcript.json) dùng OpenRouter / `openai/gpt-4o-mini`, artifact `v3+p691183f1c7d8+t6802d6a76102`. Đây là bằng chứng hội thoại trên cấu hình lưu trong transcript.

| Lượt | Yêu cầu | Công cụ thực tế | Kết quả |
| --- | --- | --- | --- |
| 1 | Tìm tin AI hôm nay và bài đăng thảo luận về AI. | `lookup`, `social_search` | Tra web trả dữ liệu. Tool tìm bài trên X báo thiếu `RAPIDAPI_KEY`. |
| 2 | Tóm tắt 5 bài đăng mới nhất nhưng chưa nêu tài khoản. | `social_search` | Model tiếp tục tìm theo chủ đề AI từ lượt trước. Nếu yêu cầu là lấy bài từ một tài khoản, agent cần hỏi lại. Tool cũng báo thiếu key. |
| 3 | Bổ sung tài khoản Sam Altman. | `timeline(screenname="sama", limit=5)` | Model giữ đúng số lượng và chọn đúng tài khoản. Tool báo thiếu key nên chưa lấy được bài đăng. |
| 4 | Đăng bản tin lên Telegram. | `clarify(response_type="yes_no")` | Agent hỏi xác nhận và dừng chờ người dùng. Transcript kết thúc ở bước này. |

## B5. Bằng chứng tool, UI và phần thưởng

| Hạng mục | Bằng chứng | Kết quả và giới hạn |
| --- | --- | --- |
| Telegram | [Transcript CLI v3, lượt 4](../transcripts/v3_openrouter_20261110T104038722560.transcript.json), [unit test](../tests/test_tools_todo.py) | Chat thật đã hỏi xác nhận. Unit test dùng HTTP giả để kiểm tra gửi sau khi xác nhận. Chưa có bằng chứng gửi thành công trong transcript trên. |
| Chính sách nội bộ và arXiv | [Mã policy](../tools/policy/tool.py), [mã papers](../tools/papers/tool.py), [mã paper_text](../tools/paper_text/tool.py) | Policy có unit test cho bộ lọc và cách tách nội dung giống chỉ dẫn. Các tool arXiv đã có mã triển khai. Chưa có log demo arXiv được xác nhận. |
| Streamlit | [Mã UI](../app.py), [transcript UI](../transcripts/ui_openrouter_20261110T105357382951.transcript.json) | UI đã ghi nhận một lượt tìm tin AI qua `lookup`. URL công khai chờ xác nhận. |
| Unit test | [test_tools_todo.py](../tests/test_tools_todo.py), [test_new_tools.py](../tests/test_new_tools.py) | **146 đạt, 0 lỗi, 0 bỏ qua**. Tám tool mới có **29 unit test**. Chưa có bằng chứng về bug starter đã sửa kèm regression test cho Challenge+. |

Ví dụ, eval kiểm tra model truyền `search_type="Top"` cho `social_search`. Unit test `test_social_search_passes_search_type` kiểm tra mã Python có đưa tham số đó vào yêu cầu HTTP. Nếu hàm bỏ quên bộ lọc khi gọi API, unit test bắt được lỗi ngay cả khi eval chấm PASS.

## B6. Nhận xét

- **Quy tắc trong system prompt.** Hỏi lại khi thiếu tài khoản hoặc URL, xử lý câu hỏi ngoài phạm vi, giữ thông tin qua các lượt, và xin xác nhận có/không trước khi gửi.
- **Khai báo trong tools.yaml.** Phân biệt `timeline` theo tài khoản và `social_search` theo chủ đề. Mô tả riêng các tham số như handle không có `@`, `topic="news"`, `timeframe` và `search_type`.
- **Việc cần đọc log thủ công.** Lời gọi `timeline(screenname="sama", limit=5)` ở lượt chat 3 có tham số phù hợp nhưng tool trả lỗi thiếu key. Cần xem cả kết quả thực thi mới đánh giá được agent có lấy được dữ liệu cho người dùng hay chưa.
- **Bước cải thiện tiếp theo.** Kiểm tra lại cách tách từ khóa khỏi bộ lọc tin tức, cách giữ yêu cầu chuyển nguồn ở lượt cuối, và yêu cầu hỏi lại khi thiếu tài khoản. Tách lỗi chọn tool khỏi lỗi cấu hình RapidAPI khi demo X.

## B7. Small Local Model Challenge

Chưa có run Ollama được xác nhận để điền bảng so sánh cloud và local.

---

