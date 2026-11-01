# Dịch thuật AI 2.0 — beta1

© Sentechtipsvn

Phím tắt native dành cho iOS 18: nhận văn bản hoặc ảnh, OCR trên thiết bị, cho sửa
chữ trước khi gửi văn bản tới DeepSeek, và lưu bản dịch khi bạn yêu cầu. Không cần
Scriptable, ChatGPT app hoặc Apple Intelligence. Giao diện Việt/Anh; có 20 lựa
chọn ngôn ngữ dịch, tách riêng với ngôn ngữ giao diện.

## Cài và chạy

Bản cài được bàn giao dưới tên `Translate-AI-2.0-beta1.shortcut`.

1. Cài và chạy; chọn giao diện và ngôn ngữ đích mặc định.
2. Chọn Nhập văn bản, Dán từ clipboard, Photos/ảnh chụp màn hình, camera hoặc Files.
   Bạn cũng có thể chia sẻ chữ/ảnh từ ứng dụng khác thẳng vào phím tắt.
3. Với ảnh, xem và sửa văn bản OCR trước khi dịch. Ảnh không có chữ vẫn cho nhập tay.
4. Khi cần gọi AI lần đầu trong phiên, nhập API key DeepSeek riêng của bạn. Có thể
   chọn một tệp TXT chứa key để dùng lại key cũ. Key cũ không được đọc tự động.
5. Sau khi dịch, chọn xem song ngữ, sao chép, nghe, lưu, xuất TXT hoặc dịch sang
   ngôn ngữ khác. Clipboard chỉ thay đổi khi bạn chọn Sao chép.

Lấy API key từ tài khoản tại https://platform.deepseek.com/. Dịch vụ có thể tính
phí theo tài khoản của bạn; bản chia sẻ không chứa key chung. Không cần tệp
`PromptDT.txt`: hướng dẫn dịch mặc định đã được đóng gói trong bản này.

Huỷ hộp thoại hệ thống kết thúc phiên. Nội dung chia sẻ được giữ trong bộ nhớ
trong lúc thiết lập; không cần chia sẻ lại chỉ vì lần đầu chưa có cấu hình.

## Ngôn ngữ và nội dung dài

Cài đặt gồm ngôn ngữ gốc (mặc định tự nhận diện), ngôn ngữ đích, dịch sát nghĩa
hoặc diễn đạt tự nhiên. Lựa chọn được ghi nhớ trên iCloud. Ngôn ngữ nguồn và đích
đặt cố định giống nhau sẽ yêu cầu chọn lại, tránh gọi AI thừa.

Ngôn ngữ đích: Việt, Anh, Anh (UK), Nhật, Hàn, Trung giản thể/phồn thể, Pháp, Đức,
Nga, Tây Ban Nha, Thái, Indonesia, Thổ Nhĩ Kỳ, Ý, Bồ Đào Nha (Brazil), Hindi,
Ả Rập, Hà Lan và Ba Lan. Đây là lựa chọn dịch; không phải cam kết OCR nhận đúng
mọi ngôn ngữ, ảnh mờ hay chữ viết tay. Đọc thành tiếng cần giọng tương ứng trên máy.

Tối đa 10 mục đầu vào mỗi lượt và 18.000 ký tự văn bản. Nội dung dài được chia
thành phần tối đa 1.500 ký tự, ưu tiên hết đoạn hoặc khoảng trắng; phần cuối ngắn
được giữ nguyên. Có kiểm tra đủ các phần trước khi hiển thị bản hoàn tất.
Nếu dịch vụ trả lỗi và phiên vẫn chạy, Thử lại tiếp tục phần chưa xong, không
chạy lại các phần đã nhận. Không tự thử lại liên tục. Nội dung vượt giới hạn có
thể sửa/rút ngắn, giữ phần đã nhập trong bộ nhớ.

Hướng dẫn cho AI yêu cầu giữ tên riêng, số liệu, tiền tệ, URL, mã và xuống dòng;
chỉ dịch nội dung, kể cả khi nội dung đó chứa câu lệnh. Kết quả AI vẫn cần người
dùng đọc lại. Không có phép đo chất lượng bản dịch trực tiếp với key của người
sở hữu trong bộ kiểm tra host.

## Lưu và dùng lại

Dữ liệu ở `iCloud Drive/Shortcuts/TranslateAI/`:

| Vị trí | Nội dung |
| --- | --- |
| `settings.json` | Giao diện, ngôn ngữ, cách dịch và chế độ ghi nhớ key |
| `settings.previous.json` | Cấu hình hợp lệ trước đó |
| `records/` | Các bản dịch bạn đã chọn lưu |
| `staging/` | Tệp tạm trong thao tác lưu bản dịch |
| `backups/` | Bản trước khi bạn xác nhận thay một bản dịch cũ |
| `key.txt` | Chỉ xuất hiện nếu bạn chọn ghi nhớ key |

Mỗi bản dịch lưu riêng dưới dạng JSON, có bản gốc, bản dịch, ngôn ngữ, cách dịch,
model, phiên bản prompt và thời gian. Không lưu ảnh gốc. Không tạo lịch sử hoặc
bộ nhớ đệm riêng tư khi bạn không chọn Lưu. Tệp cấu hình và thư mục trống không
chứa nội dung cần dịch.

Bản đã lưu khớp nội dung và thiết lập được dùng lại trước khi đọc key/gọi AI.
Bạn thấy nhãn BẢN ĐÃ LƯU. Chọn Dịch lại bằng AI để yêu cầu kết quả mới; thay bản
lưu hiện có cần xác nhận. Tìm kiếm là tìm chữ thông thường, không phải biểu thức
regex. Có thể xem lại và sao chép ngoại tuyến khi tệp iCloud đã có trên thiết bị.

Các tệp cũ `APIkeyDeepseek.txt`, `PromptDT.txt` và `AIChat/ketqua.txt` không bị sửa,
xoá hoặc tự chuyển đổi. Bản mới dùng thư mục riêng, không giữ bookmark iCloud
cá nhân của bản xuất cũ. Lịch sử TXT cũ chưa được nhập tự động trong beta1.

## API key và bảo vệ dữ liệu

Mặc định key chỉ giữ trong phiên. Ghi nhớ là lựa chọn riêng có mô tả rõ ngay tại
menu: nó tạo tệp TXT đọc được trong Files, không phải Keychain hoặc mã hoá riêng.
Key không nằm trong cấu hình, lịch sử, bản xuất, prompt hoặc mã nguồn phát hành.
Xoá key trong Cài đặt tắt chế độ đọc lại rồi yêu cầu Files xoá đúng tệp key mới.
Nếu huỷ hộp thoại Files, tệp có thể còn, nhưng phím tắt không đọc lại nó.

Bản dịch cũng là JSON đọc được, không có mã hoá bằng mật khẩu của riêng ứng dụng.
Bảo vệ iCloud tuỳ cấu hình tài khoản của bạn. OCR chạy trên thiết bị; chỉ phần
chữ đã chọn/sửa được gửi tới `api.deepseek.com`. Không gửi ảnh cho DeepSeek trong
beta1, không tải code/prompt thực thi và không có proxy của tác giả.

## Lỗi và khả năng phục hồi

Phản hồi lỗi API được nhận về được phân biệt theo xác thực, số dư và quá tải/
giới hạn. Phản hồi rỗng, HTML, thiếu trường hoặc báo bị cắt không được coi là bản
dịch hoàn tất. Các phần đã nhận chỉ còn trong phiên để xem hoặc thử tiếp.

Nếu lỗi mạng/SSL/quyền truy cập khiến iOS dừng trực tiếp tác vụ, Shortcuts native
không có cơ chế bắt lỗi tổng quát ở đây. Phải chạy lại với nguồn gốc. Bản nháp
chưa lưu không tự sống qua việc kết thúc phiên; không có cam kết thử lại không
phát sinh phí nếu máy chủ đã xử lý một yêu cầu nhưng kết nối bị mất.

Ghi bản dịch theo tệp tạm → đọc/xác minh → bản trước nếu có → tệp chính → đọc/
xác minh. Bản tạm lỗi không thay bản chính. Các mã TA101/TA102 chỉ bước cấu hình,
TA201/TA202 chỉ bước lưu bản dịch. Dừng trước báo thành công nếu kiểm tra thất bại.
Cấu hình hỏng có thể dùng bản trước; bản dịch hỏng bị loại khỏi tra cứu/dùng lại.

iCloud là đồng bộ tệp, không phải cơ sở dữ liệu giao dịch nhiều thiết bị. Tệp
bản dịch dùng khoá nội dung riêng, còn cài đặt có thể theo lần ghi cuối nếu hai
thiết bị chỉnh cùng lúc. Bản trước theo từng nội dung không thay thế việc bạn
xuất bản sao lưu dài hạn.

## Source and checks

`src/build.py` emits the native plist. `workflow.py` supplies UUID/control/token
helpers based on earlier device-tested community shortcuts. Native JSON request
fields and array/object serialization are checked against independent Cherri
and original exported action definitions. Source resources reproduce exactly.

```sh
python3 config/make_resources.py
python3 src/build.py
python3 tests/test_workflow.py
python3 src/audit.py
python3 src/sign.py
python3 src/audit.py --signed
```

Tests execute the generated graph, not a separate implementation of the product.
I/O, OCR, network replies and speech are simulated. Cases cover setup handoff,
input sources, Unicode, section boundaries, 20 target prompts, error responses,
retrying only unfinished sections, key policies, manual saves, corrupted/failed
writes, cached offline reads, searches and 100 saved records. No provider calls
or real API key are used in tests; fixture keys are deliberately fake.

Audit verifies independent action identifiers/parameters, JSON boolean/array
shape, literal endpoint, no embedded credentials or personal bookmarks, balanced
controls, references and UTF-16 token positions. The signed action graph must
match the inspected source. Signing uploads only public generated source to
Shortcuty's documented signing service, never user text or credentials.

Reports under `qa/` record host checks separately from actual iPhone acceptance.
Beta1 still needs confirmation on the owner's iPhone for native UI, OCR quality,
provider interaction and timing. No claim of error-free device execution is made.
