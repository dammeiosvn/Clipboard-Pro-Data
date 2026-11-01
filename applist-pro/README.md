# AppList Pro

© Sentechtipsvn · 1.1.0-beta.3

A native iOS quick launcher. The first screen is the user's app list: tap an
app to open it. Pinned apps appear first. Management and Info are secondary.
The normal launch path reads local data, makes no HTTP request and writes no file.

## Dành cho người dùng

1. Cài tệp AppList-Pro-1.1-beta3.shortcut và chạy trong ứng dụng Phím tắt.
2. Chọn ngôn ngữ. Lần đầu cần mạng để tải đúng một bộ ngôn ngữ từ repo này.
3. Chọn **Thêm ứng dụng → Tìm theo tên**, tìm và chọn ứng dụng đã cài trên iPhone.
   Hoặc dán liên kết App Store; cũng có thể chia sẻ liên kết từ App Store vào phím tắt.
4. Những lần sau, chạy phím tắt rồi chạm tên ứng dụng ngay trên màn hình đầu.
   Không cần vào menu quản lý để mở ứng dụng.

Menu chính hiển thị các ứng dụng, mục có ⭐ được ghim lên trước, sau cùng là
**⚙️ Quản lý**. Trong Quản lý có thêm, sửa/ghim, xoá mục, tìm trên App Store,
ngôn ngữ, sao lưu/khôi phục và **ℹ️ Info**. Info chứa giới thiệu tính năng và
hướng dẫn sử dụng bằng ngôn ngữ đã chọn.

Xoá một mục chỉ xoá khỏi danh sách này, không gỡ ứng dụng khỏi iPhone.
Tìm trên App Store chỉ mở trang ứng dụng để bạn tự tải. Phím tắt không xác nhận
được mọi ứng dụng đã cài và không chặn được mọi lỗi của tác vụ Mở ứng dụng.
Nếu app không mở, kiểm tra ứng dụng đã cài rồi chạy lại phím tắt; bạn vẫn có
thể sửa hoặc xoá mục trong Quản lý.

## Sửa lỗi của beta2

Video beta2 trên iPhone xác nhận trình chọn Files đã mở được, nhưng cả thêm
ứng dụng và nhập danh sách dừng ở tác vụ **Nếu Keys chứa** bị thiếu tham số
trong giao diện native. Beta3 bỏ toàn bộ điều kiện Contains trên mảng ở phần
kiểm tra ID. Các khoá ID được kết hợp thành văn bản có dấu phân cách rõ ràng,
sau đó đối chiếu nguyên dòng bằng regex và điều kiện số lượng kết quả > 0.

Tác vụ lấy URL được sửa từ mã không tồn tại `detect.urls` sang `detect.link`.
Mọi mã tác vụ trong bản tạo ra được đối chiếu với các bản tham chiếu độc lập
ở `config/native-actions.json`; kiểm tra cấu trúc cũng chặn hai mẫu điều kiện
đã gây lỗi trên thiết bị.

Bộ đọc trạng thái nhận tám thuộc tính ở mọi thứ tự, vẫn kiểm tra kiểu và tên
thuộc tính, đồng thời chặn thuộc tính trùng hoặc thiếu. Khi danh sách rỗng,
phần ghi dữ liệu tạo đối tượng JSON `{}` rõ ràng. Dữ liệu mới được chạy qua
chính bộ đọc trước khi ghi và đọc lại sau khi ghi. Nếu bước tự kiểm tra không
qua, thông báo có mã AP201 (trước ghi) hoặc AP205 (sau ghi) để xác định bước.

Các phép thử bổ sung thực hiện thiết lập, thêm hoặc nhập, kết thúc phiên rồi
chạy lại mở ứng dụng. Có kiểm tra thay đổi thứ tự thuộc tính và tình huống ép
kiểu từ điển rỗng thành không có văn bản. Hai tình huống sau là kiểm tra độ
bền; chưa có tệp active.json của người dùng để kết luận đó là nguyên nhân
chính xác của màn hình phục hồi lặp lại trong video. Chúng không thay cho
việc xác nhận bản beta3 trên iPhone.

## Sửa lỗi trước đó của beta1

Beta2 sửa hai lỗi đã thấy trong video trên iPhone: thiết lập mới báo nhầm
“Danh sách đã thay đổi ở một phiên khác”, và nút Nhập từ tệp không mở trình
chọn tệp. Kiểm tra chuỗi rỗng nay dùng số ký tự hoặc định dạng mã kiểm tra;
nhập tệp dùng tác vụ Select File riêng của iOS hiện hành.

Nếu bản cũ đã lỗi, cài beta3 rồi chạy. Khi hiện màn hình phục hồi, chọn
**New list / Danh sách mới** để thiết lập, hoặc **Import from file** để chọn
JSON cũ/bản sao lưu. Không cần xoá thư mục dữ liệu. Nhập JSON cũ từ màn hình
phục hồi sẽ giữ tệp đã chọn trong lúc bạn chọn ngôn ngữ, rồi quay lại xác nhận
nhập. Huỷ trước khi xác nhận không lưu danh sách trống đè lên tệp cũ.

## Chuyển danh sách cũ

Sau thiết lập ngôn ngữ, mở **Quản lý → Sao lưu và khôi phục → Nhập từ tệp**,
chọn `iCloud Drive/AppList Pro/AppList_Pro.json` của bản cũ. Xác nhận thay danh
sách. Phím tắt chuyển tên và Bundle ID sang định dạng mới, giữ một bản tệp cũ
trong thư mục riêng và không sửa hoặc xoá tệp gốc.

Nhập tệp là thay toàn bộ danh sách, không phải ghép hai danh sách. Danh sách
hiện tại được sao lưu trước khi thay. Nếu tệp cũ chứa nhiều tên cho cùng một
Bundle ID hoặc tên không hợp lệ, bản beta từ chối cả lần nhập để tránh tự ý
làm mất mục. Giữ tệp gốc và kiểm tra các mục trùng trước khi nhập lại.

## Sao lưu, khôi phục và ngoại tuyến

Dữ liệu cá nhân nằm ở `iCloud Drive/Shortcuts/AppListPro/active.json`.
`active.previous.json` giữ trạng thái trước thay đổi gần nhất; các thao tác
ghim, đổi tên, đổi ngôn ngữ hoặc nhập dữ liệu đều tính là thay đổi. Muốn giữ
một bản lâu dài, dùng **Xuất bản sao lưu** và lưu tệp ở nơi bạn chọn.

**Khôi phục lần lưu trước** phục hồi toàn bộ trạng thái trước đó và cần xác
nhận. **Nhập từ tệp** nhận bản sao lưu mới hoặc JSON bản cũ. Khi tệp chính bị
hỏng và bản trước còn hợp lệ, phím tắt dùng bản trước và báo cho bạn. Nếu cả
hai không hợp lệ, có lựa chọn nhập bản sao lưu, tạo danh sách mới hoặc huỷ.
Không có thao tác xoá thư mục dữ liệu hàng loạt.

Khi tệp iCloud đã có trên máy, mở danh sách dùng dữ liệu lưu sẵn và không
kiểm tra mạng mỗi lượt. Tải ngôn ngữ, tải lại bộ ngôn ngữ và tìm ứng dụng cần
mạng. Mạng lỗi giữa lúc tải không thay thế tệp đang dùng. iCloud có thể đồng
bộ chậm; nên hoàn tất chỉnh sửa trên một máy trước khi chỉnh sửa trên máy khác.
Huỷ hộp thoại sẽ kết thúc phiên; mục Quay lại dùng để điều hướng trong phiên.

## Public data and source

This repository contains interface translations, Info text and reviewed build
source only. No personal app list is uploaded here. Twenty locale choices are
retained from the original workflow, including the two English variants.

- Edit `config/strings.json`; it is the translation source of truth.
- `src/catalog.py` exports a separate public package for each locale.
- `src/build.py` emits the native workflow. Static values are grouped in its
  first Dictionary; navigation, validation and saving stay in runtime order.
- `src/audit.py` checks control groups, output references and UTF-16 token ranges.
- `tests/test_workflow.py` executes the generated graph using simulated iOS I/O
  and ICU regular expressions. It includes destructive-change and recovery cases.
- `src/sign.py` signs public generated source through Shortcuty's documented API.
  Signing is a build step; the installed shortcut never contacts that service.

```sh
python3 src/build.py
python3 tests/test_workflow.py
python3 src/audit.py
python3 src/sign.py
python3 src/audit.py --signed
```

The host-side tests require the system ICU library. The optional signed-file
audit additionally uses Python `lzfse`. Signing requires network access.

## Data format and technical limits

Each language package is pinned by its payload SHA-256 in the generated
workflow. **Reload language pack** reloads the compatible package for this
version; it does not silently replace the shortcut engine. Release paths are
immutable. Publish a new release and rebuild to change the pinned content.
The beta3 engine deliberately reuses the unchanged beta1 interface packages.

The active state is one JSON envelope containing a stable Base64 payload and
its checksum. Only that scalar payload is hashed, so iOS may reformat the outer
JSON without invalidating the file. Base64 is encoding, not encryption. The
stored list remains readable to anyone with access to the user's iCloud files.

The payload contains names, original Bundle IDs, App Store links and pin flags.
Records use a SHA-256 key derived from the Bundle ID, avoiding dotted-key
ambiguity and accidental collisions between display names. Names are preserved
in full; subtitles after colons and dashes are not removed.

Saving stages and verifies new data, preserves the old verified state, and
verifies the final write. A local revision check prevents overwriting a newer
revision already visible to this session. This is not a transactional database
or a guarantee against simultaneous writes still awaiting iCloud sync.

The menu loop is bounded to 60 navigation passes, with explicit exit after
opening an app. It does not recursively run the whole shortcut. More actions
than the original are needed for management and recovery; action count alone
is not a performance measurement. Timing and native rendering require device
testing, particularly on large lists.

This is a beta targeting the user's iOS 18 workflow. Automated graph and signing
checks are recorded under `qa`; they do not assert actual iPhone execution or
native-speaker review of every translation. The signed action graph must match
the inspected generated source before distribution.
