# Quick Translation — 1.0 beta1

© Sentechtipsvn

Dịch văn bản bằng tác vụ Apple có sẵn trong Phím tắt, có OCR trên thiết bị,
sửa chữ trước khi dịch và Xem nhanh cho nội dung dài. Dành cho iOS 18 trở lên;
không cần API key, Apple Intelligence hoặc ứng dụng tự động hoá bên thứ ba.

## Hai phím tắt và cách cài

1. Thêm **Quick-Translation.shortcut** trước, giữ tên **Quick-Translation**.
2. Chạy phím chính khi có mạng để tải danh mục và chọn một gói giao diện Việt/Anh,
   sau đó chọn ngôn ngữ đích. Cấu hình được ghi nhớ trên iCloud.
3. Thêm **Quick-Translation-Screen.shortcut** nếu muốn chụp màn hình nhanh.
4. Gán **Quick-Translation-Screen** trong Cài đặt → Trợ năng → Cảm ứng → Chạm vào
   mặt sau (hai/ba lần), hoặc gán vào thao tác/menu AssistiveTouch.
5. Đứng ở màn hình cần dịch rồi kích hoạt: chụp trước → chuyển ảnh vào phím chính
   → OCR → sửa chữ → Dịch Apple → Xem nhanh.

Phím chính chạy độc lập cho chữ, ảnh và tệp. Phím phụ chỉ có bốn tác vụ, cần cài
phím chính. Nếu đổi tên phím chính, chọn lại nó trong tác vụ Chạy phím tắt của
phím phụ. Không tự đoán phương thức khởi chạy từ một đầu vào trống.

Không tự lưu screenshot vào Photos. Thiết lập lần đầu giữ nội dung chia sẻ hoặc
ảnh đã chụp trong phiên, không buộc chụp/chia sẻ lại sau khi chọn ngôn ngữ.
Màn hình bảo vệ hoặc giới hạn của iOS có thể chặn chụp/cho ảnh trống; cần mở khoá
máy và cấp quyền cho thao tác được dùng.

## Nhận nội dung

Menu chính: Dán từ clipboard, Nhập văn bản, Ảnh/ảnh chụp màn hình, Chụp ảnh,
Chọn tệp, Bản dịch đã lưu, Cài đặt, Info và hướng dẫn. Chia sẻ chữ, ảnh hoặc tệp
vào phím chính để đi thẳng tới xử lý đầu vào. Không tự đọc clipboard lúc mở.

Ảnh được OCR và luôn có bước sửa trước khi dịch. OCR trống vẫn cho nhập tay.
Văn bản trên 6.000 ký tự được xem đầy đủ bằng Xem nhanh và có thể sửa từng phần;
khi sửa, các phần còn lại giữ nguyên, không thêm dấu phân cách vào bản gốc.

| Loại nội dung | Xử lý |
| --- | --- |
| Chữ, TXT | Đọc chữ trực tiếp, chuẩn hoá BOM và xuống dòng |
| Ảnh, screenshot, camera | OCR trên thiết bị rồi kiểm tra/sửa |
| PDF có chữ | Trích chữ từng trang được chọn |
| PDF scan | Tạo ảnh từng trang rồi OCR |
| PDF trộn | Tự đọc chữ hoặc OCR theo từng trang, ghép theo thứ tự tài liệu |
| MD, CSV, JSON, LOG, INI, YAML, XML, HTML, RTF | Cho chọn trích chữ, tạo TXT trong phiên và sửa trước khi dịch |
| Word/Pages, ZIP, video, tệp khác | Hướng dẫn xuất TXT/PDF từ ứng dụng gốc |

Chuyển TXT là trích được chữ rồi tạo bản văn bản mới, không chỉ đổi tên tệp nhị
phân. Tệp nguồn được giữ nguyên. TXT lỗi mã hoá hoặc có ký tự NUL được báo để
xuất lại UTF-8. Kiểm tra nội dung sau khi trích xuất; không có bộ chuyển mọi
định dạng thành văn bản.

Giới hạn sản phẩm trong beta1: tối đa 10 mục đầu vào/10 ảnh, 25 MB mỗi tệp,
10 trang PDF và 24.000 ký tự nguồn mỗi lượt. PDF trên 200 trang cần tách nhỏ.
Không âm thầm dịch riêng phần đầu của một nội dung vượt giới hạn.

PDF có lựa chọn tự đọc chữ hoặc ép OCR tất cả trang được chọn. Nếu trang chỉ có
tiêu đề dạng chữ còn phần chính là ảnh, chọn ép OCR. Trang không nhận được chữ
được báo để bổ sung. Chọn một số trang không có nghĩa kết quả là bản dịch của
cả tài liệu. Thứ tự cột, bảng, chú thích và chữ viết tay cần người dùng kiểm tra.

## Dịch và xem kết quả

Nguồn mặc định tự nhận diện, có nguồn cố định trong Cài đặt. Nguồn chưa rõ sẽ
cho chọn cho lượt hiện tại; có thể chấp nhận tiếp tục tự nhận diện. Menu kết quả
cũng có Chọn lại ngôn ngữ gốc và luôn dùng lại bản gốc. Chọn nguồn cho một lượt
không tự thay mặc định Tự nhận diện của các lượt sau.

Nội dung chỉ gồm số/ký hiệu được giữ nguyên, không gọi nhận diện/dịch. Cùng ngôn
ngữ hoặc hai biến thể tiếng Anh cũng giữ nguyên để tránh cặp không được hỗ trợ.
Nhãn kết quả khi đó là BẢN GỐC. Không coi tên riêng/mã được giữ nguyên là lỗi.

Dịch theo phần tối đa 1.200 cụm ký tự Unicode, ưu tiên đoạn hoặc khoảng trắng.
Regex dùng cụm grapheme để tránh tách emoji ghép và dấu kết hợp. Các phần được
xử lý tuần tự. Phần rỗng không được coi là hoàn tất; thử tiếp chỉ chạy phần chưa
xong. Không có prompt AI để ép giữ định dạng, vì bộ dịch là tác vụ Apple native.
Bản gốc luôn được giữ trong phiên để đối chiếu.

Bản dịch, bản gốc, song ngữ và hướng dẫn dùng **Xem nhanh** với tệp TXT UTF-8.
**Hiển thị kết quả** chỉ dùng cho các xác nhận ngắn. Menu sau xem cho phép sao
chép, đọc, lưu, đổi nguồn/đích, dịch mới, xuất TXT/PDF hoặc mở bảng Chia sẻ.
Đổi đích không dịch vòng qua bản dịch cũ. Bản PDF xuất là văn bản đơn giản,
không tái tạo dàn trang của PDF nguồn.

Apple Translate cần khả năng ngôn ngữ của iOS/thiết bị. OCR và giọng đọc có phạm
vi riêng. Ngoại tuyến cần tải cả nguồn và đích trong Dịch/cài đặt Dịch của Apple;
kiểm tra riêng tác vụ phím tắt bằng chế độ máy bay. Bản build trên host không
thực hiện được phép kiểm tra ngoại tuyến hoặc chất lượng dịch trên iPhone.

## Lưu và tái sử dụng

Dữ liệu nằm tại `iCloud Drive/Shortcuts/QuickTranslation/`:

| Đường dẫn | Nội dung |
| --- | --- |
| `settings.json`, `settings.previous.json` | Ngôn ngữ giao diện, nguồn/đích và phiên bản ghi cấu hình |
| `catalog.json`, `catalog.previous.json` | Danh mục đã tải và bản dự phòng |
| `ui.<locale>.json`, `ui.<locale>.previous.json` | Chỉ những giao diện đã chọn tải |
| `*.pending.json` | Tệp kiểm tra trong lúc lưu cấu hình/tài nguyên |
| `records/<id>.json` | Chỉ các bản dịch người dùng đã chọn Lưu |
| `staging/`, `backups/` | Tệp kiểm tra/bản trước khi thay kết quả đã lưu |

Không ghi nội dung dịch hoặc ảnh ngầm để điều hướng. Bản gốc/bản dịch chỉ ghi
khi chọn Lưu hoặc xuất. JSON đọc được, chưa có mật khẩu/mã hoá riêng. Tệp cũ trong
`Sentechtipsvn`, dữ liệu Translate AI và các dự án khác được giữ nguyên.

Khoá bản dịch dựa trên hash nội dung, nguồn, đích và phiên bản bộ xử lý Apple.
Khớp bản đã lưu sẽ dùng lại trước khi nhận diện/gọi dịch. Nội dung bản gốc/bản
dịch và danh tính bản lưu được kiểm tra hash. Thay bản lưu cần xác nhận; bản
trước được giữ. Không có lịch sử của mỗi lần chạy nếu chưa chọn Lưu.

iCloud là đồng bộ tệp, không phải giao dịch cơ sở dữ liệu nhiều thiết bị. Hãy chờ
đồng bộ nếu tệp chưa có trên máy. Cấu hình có thể theo lần ghi cuối nếu hai thiết
bị chỉnh đồng thời. Không xoá thư mục dữ liệu để cập nhật phím tắt.

## Ngôn ngữ và cập nhật từ repo

`resources/v1/catalog.json` là danh mục dữ liệu; `resources/v1/ui/<locale>.json`
là các gói giao diện. Tác vụ chỉ GET các đường dẫn cố định này, không gửi bản
gốc/bản dịch lên GitHub. Không tải hoặc thực thi code từ xa.

Chạy thường dùng cache. Cài đặt → Cập nhật gói ngôn ngữ mới kiểm tra repo. Chọn
một giao diện chưa có chỉ tải gói đã chọn. Danh mục có thể mở rộng giao diện và
lựa chọn ngôn ngữ mà không sửa menu/bộ kiểm tra whitelist trong native graph,
miễn đúng schema v1. Tuy nhiên Apple phải thực sự hỗ trợ ngôn ngữ đó.

Danh mục hiện có 21 lựa chọn và ngưỡng phiên bản iOS: 20 mục trên iOS 18, Hindi
được đặt từ iOS 27 theo mô tả App Store Apple hiện tại. Đây là cấu hình dữ liệu
có thể sửa sau khi xác nhận tác vụ trên thiết bị, không phải tự dò khả năng dịch
của hệ điều hành. Mã Nhật/Việt dùng `ja_JP`/`vi_VN` từ bản xuất của người dùng;
không dùng các giá trị sai `jp_JP`/`vn_VN` trong enum Cherri tham khảo.

Schema v1: catalog là object chuỗi phẳng với metadata, các map JSON chuỗi cho
locales, revisions, names, apple, speech, minIOS và aliases. Kiểm tra cú pháp
trước khi giải mã, số trường, key trùng, tập ID đồng nhất và ít nhất một ngôn
ngữ phù hợp iOS. Gói UI có tập nhãn cố định và locale/revision khớp catalog.
Nhãn lựa chọn trong mỗi danh mục cần phân biệt được với nhau.

Để cập nhật: thêm dữ liệu phù hợp trong `config/make_resources.py`, tăng revision
catalog; khi đổi chữ của một locale thì tăng revision của đúng pack đó trong
catalog và metadata pack. Tạo lại tài nguyên bằng generator, chạy kiểm tra rồi
đưa các file JSON lên repo. Thêm UI mới cần đủ bộ nhãn. Đổi schema hoặc thêm
chức năng/tác vụ vẫn cần bản phím tắt mới.

Ghi UI mới đã kiểm tra trước rồi catalog, với tệp pending/đọc lại và bản trước.
Cập nhật hỏng có thể dùng catalog/UI dự phòng; chưa ghi thành công không báo
đã cập nhật. Mã QT101/QT102 cho cài đặt, QT201/QT202 cho bản dịch,
QT301/QT302 cho tài nguyên. Tệp nguồn không bị xoá để phục hồi lỗi.

## Kiểm tra và giới hạn xác minh

```sh
python3 config/make_resources.py
python3 src/build.py
python3 tests/test_workflow.py
python3 src/audit.py
python3 src/sign.py
python3 src/audit.py --signed
```

Tests chạy trực tiếp graph đã sinh với I/O/OCR/PDF/ảnh màn hình/dịch Apple mô
phỏng, không phải một bản triển khai thứ hai của luồng sản phẩm. Audit độc lập
kiểm tra các action ID và tham số dựa trên bản xuất gốc và định nghĩa Cherri,
tham chiếu, nhóm điều kiện/lặp, span UTF-16, endpoint GET và dữ liệu cá nhân.
Graph sau ký phải khớp graph đã kiểm tra. Ký qua API công khai của Shortcuty chỉ
nhận workflow công khai đã sinh, không có ảnh/tệp/nội dung riêng của người dùng.

Chưa chạy bản beta1 mới trên iPhone. Cần xác nhận quyền iOS, screenshot trước UI,
nhận diện/dịch native, PDF native thực tế, giọng đọc và ngoại tuyến trên máy.
Lỗi mạng/quyền, tệp PDF hỏng/có mật khẩu hoặc dịch vụ Apple có thể khiến iOS dừng
thẳng tác vụ; Shortcuts không có catch tổng quát trong bản này. Nội dung chưa lưu
không tự phục hồi sau khi kết thúc phiên. Không có cam kết không lỗi mọi thiết bị.

Nguồn tham khảo:

- https://support.apple.com/en-ca/106430
- https://support.apple.com/guide/iphone/iphddb6e7264/ios
- https://apps.apple.com/us/app/translate/id1514844618
- https://support.apple.com/guide/iphone/iphaa57e7885/ios
- https://support.apple.com/guide/iphone/iph96b21954/ios
- https://github.com/electrikmilk/cherri/tree/main/actions
- https://github.com/Shortcuty/Signing-Server-API-Documentation
