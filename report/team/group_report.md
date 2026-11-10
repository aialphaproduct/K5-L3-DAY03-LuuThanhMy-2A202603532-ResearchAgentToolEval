# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
>
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: Lưu Thanh Mỹ
- Members: Vũ Trí Dũng, Nguyễn Tuấn Quang, Khổng Tiến Dương, Phan Hải Đăng, Lưu Thanh Mỹ
- Provider và model đã đánh giá gồm OpenRouter với `openai/gpt-4o-mini`, Ollama với `functiongemma:270m` và `qwen3:0.6b`.

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent tìm thông tin từ web, X, Hacker News, Wikipedia, GitHub và arXiv, đọc nội dung từ URL và tổng hợp thành bản tin có link nguồn. Agent có thể tra chính sách mẫu của bài lab, lưu ghi chú cục bộ, hỏi lại khi thiếu dữ kiện và xin xác nhận trước khi gửi bản tin lên Telegram.

**Cấu hình demo** dùng prompt `v3` và model `openai/gpt-4o-mini` qua OpenRouter. Giao diện Streamlit hỗ trợ hội thoại nhiều lượt, hiển thị công cụ đã gọi và lưu transcript. Nhóm cũng chạy hai model qua Ollama, xem mục B7.

**Dùng thử trên máy** tại [giao diện Streamlit](http://localhost:8501) sau khi chạy `python -m streamlit run app.py` từ thư mục `starter_v0/`. Chưa có URL công khai được xác nhận.

**Kết quả base của v3 trước khi sửa G10** đạt **19/20 (95%)**, chấm đủ 20 case và không có lỗi provider. [Run kiểm chứng](../../starter_v0/runs/v3-rerun_B_base_openrouter_20261110T184840496642.json)

**Cấu hình demo sau khi sửa G10** đạt **10/10** trên bộ group. [Run group hiện tại](../../starter_v0/runs/v3-g10-fix_B_group_openrouter_20261110T232714907324.json)

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
| v0 | Baseline | Đo hành vi của cấu hình starter để xác định nhóm lỗi. | — → **70% (14/20)** | [Run v0](../../starter_v0/runs/v0_B_base_openrouter_20261110T094641803175.json) |
| v1 | `system_prompt.md` | Hướng dẫn rõ phạm vi nghiên cứu và khi nào hỏi lại để giảm gọi nhầm công cụ. | 70% → **85% (17/20)** | [Run v1](../../starter_v0/runs/v1_B_base_openrouter_20261110T103823244196.json) |
| v2 | `system_prompt.md` và `tools.yaml` | Làm rõ cách chọn công cụ và tham số để giảm lỗi chọn sai. Điểm chọn đúng tool tăng từ 95% lên 100%, trong khi điểm toàn case giữ ở 85%. Vòng này thay đổi hai file nên kết quả đo tác động chung. | 85% → **85% (17/20)** | [Run v2](../../starter_v0/runs/v2_B_base_openrouter_20261110T113325303962.json) |
| v3-rerun | Prompt và tools trước khi sửa G10 | Kiểm tra lại v3 trên cùng bộ base. | 85% ở v2 → **95% (19/20)** | [Run base v3 trước bản sửa](../../starter_v0/runs/v3-rerun_B_base_openrouter_20261110T184840496642.json) |
| v2-LTM | Mô tả tool và bộ tool | Viết rõ thời điểm dùng tool và quy ước tham số. Vòng này cũng thêm bốn tool, nên không thể tách tác động của từng thay đổi. | 85% → **95% (19/20)** | [Run v2-LTM](../../starter_v0/runs/v2_B_base_openrouter_20261110T111547574574.json) |
| v3-LTM | Prompt | Làm rõ routing, ví dụ handle và quy tắc xác nhận. R12 vẫn dùng sai kiểu xác nhận. | 95% → **95% (19/20)** | [Run v3-LTM](../../starter_v0/runs/v3_B_base_openrouter_20261110T111759856270.json) |
| v4-LTM | Prompt | Yêu cầu `clarify(response_type="yes_no")` trước khi gửi. R12 đạt nhưng M06 gọi thừa `social_search`. | 95% → **95% (19/20)** | [Run v4-LTM](../../starter_v0/runs/v4_B_base_openrouter_20261110T111941600954.json) |

Các dòng trên dùng log hợp lệ và có hash, giả thuyết, điểm trước/sau trong [nhật ký phiên bản](../../starter_v0/artifacts/version_log.csv). Run `v3-rerun` đo cấu hình v3 trước khi sửa G10. Run đã chấm đủ **20 case**, có **0 lỗi provider**, artifact `v3-rerun+p151ad41190b9+t8d9098dbc911`. Dòng `v3` lịch sử ghi 100% có hash khác và vẫn thiếu run đối chiếu. Run `v3-LTM` là kết quả riêng của nhánh LTM. Mỗi run phản ánh đúng bộ prompt và tool có hash ghi trong JSON.

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

Ở `v3-LTM`, lỗi còn lại là `R12_confirm_before_send`. Model chọn đúng `clarify` nhưng truyền `response_type="text"` thay vì `"yes_no"`. `v4-LTM` sửa được R12, song `M06_switch_tool` phát sinh lời gọi `social_search` thừa khi người dùng đã chuyển sang tìm tin trên web.

Run base trước khi sửa G10 trượt một case `M06_switch_tool`: sau khi người dùng chuyển từ X sang tin web, model gọi đúng `lookup` và gọi thêm `social_search`. Case xác nhận Telegram `R12_confirm_before_send` đạt. Lần chạy giữ Telegram ở trạng thái tắt và dùng tệp tạm cho ghi chú.

Sau khi sửa G10, [lần kiểm tra riêng M06](../../starter_v0/runs/v3-m06-check_B_base_openrouter_20261110T233946536828.json) vẫn FAIL vì gọi thừa `social_search`. Lần kiểm tra này chỉ chạy M06. Chưa có kết quả full base cho cấu hình sau bản sửa.

## B3. Eval nhóm

Bộ [eval nhóm](../../starter_v0/data/eval_group.json) gồm đúng **10 case**, chia thành **5 single turn** (`query`) và **5 multi turn** (`turns`). Tám tool nhóm tự thêm đều có case kiểm tra routing. Hai case còn lại kiểm tra hủy gửi và hỏi lại khi thiếu tài khoản.

[Run group trước bản sửa](../../starter_v0/runs/v3-rerun_B_group_openrouter_20261110T185813206017.json) đạt **9/10**. G10 gọi `timeline` với `screenname=""` sau khi người dùng chỉ bổ sung số lượng.

Prompt v3 bổ sung ví dụ nhiều lượt để hỏi lại khi đã biết số bài nhưng còn thiếu tài khoản. Khai báo `timeline.screenname` bỏ mặc định rỗng và đặt `minLength: 1`. [Run sau bản sửa](../../starter_v0/runs/v3-g10-fix_B_group_openrouter_20261110T232714907324.json) đạt **10/10 (100%)**, chấm đủ 10 case và có **0 lỗi provider**. G10 gọi đúng `clarify(response_type="text")` để hỏi tài khoản X. [Lần chạy lại cùng hai hash](../../starter_v0/runs/v3-check_B_group_openrouter_20261110T232849101679.json) cũng đạt **10/10**. Bảng dưới đây ghi kết quả sau bản sửa.

| Case | Kiểu | Hành vi kiểm tra | Tool và tham số kỳ vọng | Kết quả |
| --- | --- | --- | --- | --- |
| `LTM_G01_calc_routing` | Single turn | Phép tính số học rõ ràng → gọi calc, không phải lookup/web. | `calc` | PASS |
| `LTM_G02_wiki_concept_routing` | Single turn | Kiến thức bách khoa ổn định ('X là gì') → wiki, không phải lookup topic=news. | `wiki` | PASS |
| `LTM_G03_define_word_routing` | Single turn | Hỏi nghĩa một TỪ đơn → define với word đúng, không dùng wiki/lookup. | `define(word="serendipity")` | PASS |
| `LTM_G04_datetime_routing` | Single turn | Hỏi thời gian hiện tại → datetime, không phải lookup. | `datetime` | PASS |
| `G12_wikipedia_search_vi` | Single turn | Chọn wiki_search cho danh sách bài Wikipedia tiếng Việt thay vì wiki để lấy tóm tắt một trang. | `wiki_search(query="học tăng cường", language="vi", max_results=3)` | PASS |
| `G08_cancel_delivery` | Multi turn | Tôn trọng yêu cầu hủy ở lượt cuối, không gọi công cụ sau khi người dùng từ chối. | Không gọi tool | PASS |
| `LTM_G10_still_missing_handle_clarify` | Multi turn | 2 turns: đã có limit=5 nhưng VẪN thiếu handle → clarify xin tên tài khoản, không đoán bừa. | `clarify(response_type="text")` | PASS — hỏi tên tài khoản qua clarify |
| `G11_hn_refine_to_ask` | Multi turn | Giữ từ khóa và số lượng từ lượt trước, đổi bộ lọc sang Ask HN. | `hn_search(query="local LLM", tag="ask_hn", max_results=3)` | PASS |
| `G13_repo_sort_correction` | Multi turn | Giữ GitHub, từ khóa và số lượng từ lượt trước, đồng thời đổi cách sắp xếp sang updated. | `repo_search(query="agent evaluation", sort="updated", max_results=4)` | PASS |
| `G14_notes_list_limit` | Multi turn | Giữ ý định xem ghi chú ở lượt trước và gọi notes với thao tác list, giới hạn 2. | `notes(action="list", limit=2)` | PASS |

## B4. Bằng chứng chat trực tiếp

[Transcript CLI v3, 4 lượt](../../starter_v0/transcripts/v3_openrouter_20261110T104038722560.transcript.json) dùng OpenRouter / `openai/gpt-4o-mini`, artifact `v3+p691183f1c7d8+t6802d6a76102`. Đây là bằng chứng hội thoại trên cấu hình lưu trong transcript.

| Lượt | Yêu cầu | Công cụ thực tế | Kết quả |
| --- | --- | --- | --- |
| 1 | Tìm tin AI hôm nay và bài đăng thảo luận về AI. | `lookup`, `social_search` | Tra web trả dữ liệu. Tool tìm bài trên X báo thiếu `RAPIDAPI_KEY`. |
| 2 | Tóm tắt 5 bài đăng mới nhất nhưng chưa nêu tài khoản. | `social_search` | Model tiếp tục tìm theo chủ đề AI từ lượt trước. Nếu yêu cầu là lấy bài từ một tài khoản, agent cần hỏi lại. Tool cũng báo thiếu key. |
| 3 | Bổ sung tài khoản Sam Altman. | `timeline(screenname="sama", limit=5)` | Model giữ đúng số lượng và chọn đúng tài khoản. Tool báo thiếu key nên chưa lấy được bài đăng. |
| 4 | Đăng bản tin lên Telegram. | `clarify(response_type="yes_no")` | Agent hỏi xác nhận và dừng chờ người dùng. Transcript kết thúc ở bước này. |

[Transcript CLI v3 bổ sung](../../starter_v0/transcripts/v3_openrouter_20261110T172734871916.transcript.json) ghi ba lượt đều trả lời thành công trên OpenRouter / `openai/gpt-4o-mini`, artifact `v3+pcd962915f509+t8d9098dbc911`. Agent gọi lần lượt `lookup` để tìm tin AI, `wiki` để tóm tắt Transformer và `calc` để tính `125*48+90`. [Commit bổ sung transcript `d533ccf`](#b8-commit-đối-chiếu)

## B5. Bằng chứng tool, UI và phần thưởng

| Hạng mục | Bằng chứng | Kết quả và giới hạn |
| --- | --- | --- |
| Telegram | [Transcript CLI v3, lượt 4](../../starter_v0/transcripts/v3_openrouter_20261110T104038722560.transcript.json), [unit test](../../starter_v0/tests/test_tools_todo.py) | Chat thật đã hỏi xác nhận. Unit test dùng HTTP giả để kiểm tra gửi sau khi xác nhận. [Transcript bot Telegram mới](../../starter_v0/transcripts/v3_telegram_20261110T160752173575.transcript.json) ghi bot trả lời qua `wiki_search`. Chưa có transcript chứng minh đủ luồng xác nhận rồi gọi `send(confirmed=true)` với `status: sent`. |
| Chính sách nội bộ và arXiv | [Mã policy](../../starter_v0/tools/policy/tool.py), [mã papers](../../starter_v0/tools/papers/tool.py), [mã paper_text](../../starter_v0/tools/paper_text/tool.py) | Policy có unit test cho bộ lọc và cách tách nội dung giống chỉ dẫn. Các tool arXiv đã có mã triển khai. Chưa có log demo arXiv được xác nhận. |
| Streamlit | [Mã UI](../../starter_v0/app.py), [transcript UI](../../starter_v0/transcripts/ui_openrouter_20261110T105357382951.transcript.json) | UI đã ghi nhận một lượt tìm tin AI qua `lookup`. URL công khai chờ xác nhận. |
| Unit test | [test_tools_todo.py](../../starter_v0/tests/test_tools_todo.py), [test_new_tools.py](../../starter_v0/tests/test_new_tools.py) | **146 đạt, 0 lỗi, 0 bỏ qua**. Tám tool mới có **29 unit test**. Chưa có bằng chứng về bug starter đã sửa kèm regression test cho Challenge+. |

Ví dụ, eval kiểm tra model truyền `search_type="Top"` cho `social_search`. Unit test `test_social_search_passes_search_type` kiểm tra mã Python có đưa tham số đó vào yêu cầu HTTP. Nếu hàm bỏ quên bộ lọc khi gọi API, unit test bắt được lỗi ngay cả khi eval chấm PASS.

## B6. Nhận xét

- **Quy tắc trong system prompt.** Hỏi lại khi thiếu tài khoản hoặc URL, xử lý câu hỏi ngoài phạm vi, giữ thông tin qua các lượt, và xin xác nhận có/không trước khi gửi.
- **Khai báo trong tools.yaml.** Phân biệt `timeline` theo tài khoản và `social_search` theo chủ đề. Mô tả riêng các tham số như handle không có `@`, `topic="news"`, `timeframe` và `search_type`.
- **Việc cần đọc log thủ công.** Lời gọi `timeline(screenname="sama", limit=5)` ở lượt chat 3 có tham số phù hợp nhưng tool trả lỗi thiếu key. Cần xem cả kết quả thực thi mới đánh giá được agent có lấy được dữ liệu cho người dùng hay chưa.
- **Bước cải thiện tiếp theo.** Kiểm tra lại cách tách từ khóa khỏi bộ lọc tin tức, cách giữ yêu cầu chuyển nguồn ở lượt cuối, và yêu cầu hỏi lại khi thiếu tài khoản. Tách lỗi chọn tool khỏi lỗi cấu hình RapidAPI khi demo X.

## B7. Small Local Model Challenge

Hai model Ollama và hai vòng tối ưu đã chạy đủ **20 case base** trên mỗi run, với **0 lỗi provider**. Hai baseline local dùng cùng hash prompt và tools. Cả hai vòng tối ưu giữ nguyên hash tools của baseline local. Run cloud v3-LTM có cấu hình riêng, còn cặp v5-local và v5-cloud dùng đúng cùng hash prompt và tools để đối chiếu giữa hai model.

| Run | Model và provider | Cấu hình | Case accuracy | Chọn tool | Tham số | Nhiều lượt | Log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v3-LTM | `openai/gpt-4o-mini` (openrouter) | Cấu hình cloud nhánh LTM | 19/20 (95%) | 100% | 95% | 100% | [JSON](../../starter_v0/runs/v3_B_base_openrouter_20261110T111759856270.json) |
| v3 baseline local | `functiongemma:270m` (ollama) | Cấu hình local chung | 3/20 (15%) | 20% | 15% | 0% | [JSON](../../starter_v0/runs/v3-functiongemma270m_B_base_ollama_20261110T165021609724.json) |
| v3 baseline local | `qwen3:0.6b` (ollama) | Cấu hình local chung | 6/20 (30%) | 45% | 30% | 0% | [JSON](../../starter_v0/runs/v3-qwen3-0.6b_B_base_ollama_20261110T170632104625.json) |
| v4-local | `qwen3:0.6b` (ollama) | Routing theo thứ tự ưu tiên | 7/20 (35%) | 75% | 35% | 16,67% | [JSON](../../starter_v0/runs/v4-local-qwen3-0.6b_B_base_ollama_20261110T172125250313.json) |
| v5-local | `qwen3:0.6b` (ollama) | Thêm ví dụ và quy ước tham số | 3/20 (15%) | 15% | 15% | 0% | [JSON](../../starter_v0/runs/v5-local-qwen3-0.6b_B_base_ollama_20261110T173628840565.json) |
| v5-cloud | `openai/gpt-4o-mini` (openrouter) | Cùng prompt và tool với v5-local | 19/20 (95%) | 95% | 95% | 83,33% | [JSON](../../starter_v0/runs/v5-cloud_B_base_openrouter_20261110T174751090408.json) |

| Dạng lỗi | Bằng chứng từ run |
| --- | --- |
| Thiếu tool kỳ vọng | FunctionGemma có 16 case `missing_tool_call`. Qwen có 10 ở baseline, giảm xuống 5 ở v4 rồi tăng lên 17 ở v5. Nhãn này bao gồm cả trường hợp gọi nhầm tool. |
| Tên tool ngoài khai báo | FunctionGemma gọi `tweets_recent_latest_posts` ở R05 và `api_call_openai` ở M06. |
| Tham số sai | Qwen v4 có 8 case `wrong_arg_value`, tăng từ 4 ở baseline. Ở R11, model gọi được `clarify` nhưng vẫn sai tham số. |
| Bỏ qua xác nhận | Qwen baseline và v5 không gọi tool ở R12. Qwen v4 gọi `clarify` nhưng sai tham số. |
| Gọi lặp hoặc chọn nhầm nguồn | Qwen baseline gọi `social_search` hai lần ở R13. Qwen v5 gọi `hn_search` hai lần ở cùng case. |
| JSON tham số không hợp lệ | Không ghi nhận trường `_invalid_json_arguments` trong bốn run Ollama. |

[Prompt v4-local](../../starter_v0/artifacts/system_prompt_v4_local.md) ưu tiên các quy tắc routing và tăng điểm chọn tool của Qwen từ **45% lên 75%**, nhưng điểm toàn case chỉ tăng từ **30% lên 35%** do tham số vẫn sai. [Prompt v5-local](../../starter_v0/artifacts/system_prompt_v5_local.md) bổ sung ví dụ và kiểm tra tham số. Trên Qwen, điểm toàn case giảm xuống **15%**. Trên OpenRouter, cùng prompt và tools đó đạt **95%**. Trong các run đã đo, v4 cho Qwen kết quả tốt nhất. Cặp v5 cho thấy khác biệt về khả năng tuân thủ cùng cấu hình giữa hai model.

## B8. Commit đối chiếu

| Commit | Đóng góp có trong lịch sử repo |
| --- | --- |
| `3c79c77` | Thêm `hn_search`, `wiki_search`, `repo_search`, `notes`, UI và test. |
| `5ab3043` | Thêm `calc`, `datetime`, `wiki`, `define`, test và run nhánh LTM. |
| `8ae6362` | Thêm prompt v3. |
| `d533ccf` | Bổ sung transcript chat live và Telegram. |
| `f3bf5ee`, `b381d83` | Bổ sung log Ollama, prompt v4/v5 local và run kiểm tra trên cloud. |
| `d9ba82a` | Cập nhật báo cáo nhóm và bổ sung case cho bốn tool mới còn thiếu. |
