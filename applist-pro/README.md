# AppList Pro

© Sentechtipsvn · 1.1.0-beta.4

A native iOS quick launcher. Apps appear on the first screen, pinned apps first,
with **Manage** at the bottom. Opening an app does not require a management menu.
Normal launches make no HTTP request and write no file.

Bản cài đã ký được bàn giao dưới tên `AppList-Pro-1.1-beta4.shortcut`.

## Cài và dùng

1. Cài tệp beta4; có thể kiểm tra **1.1.0-beta.4** trong Info để phân biệt với
   các bản trước. Chạy và chọn ngôn ngữ. Lần thiết lập đầu cần mạng.
2. Chọn **Thêm ứng dụng → Tìm theo tên**, tìm và chọn ứng dụng đã cài. Có thể thêm
   bằng liên kết App Store hoặc chia sẻ liên kết App Store vào phím tắt.
3. Chạy lại phím tắt và chạm ứng dụng ngay trên màn hình đầu để mở.

Trong **Quản lý** có thêm, đổi tên, ghim/bỏ ghim, xoá mục, mở trang App Store,
ngôn ngữ, sao lưu/khôi phục và **Info**. Info chứa phiên bản, giới thiệu tính năng
và hướng dẫn sử dụng bằng ngôn ngữ đã chọn. Xoá mục không gỡ ứng dụng khỏi iPhone.
Tìm trên App Store không tự cài ứng dụng. Huỷ hộp thoại sẽ kết thúc phiên.

## Nhập danh sách gốc

Sau khi chọn ngôn ngữ, vào **Quản lý → Sao lưu và khôi phục → Nhập từ tệp**.
Chọn `iCloud Drive/AppList Pro/AppList_Pro.json` rồi xác nhận. Tệp gốc có dạng
`{"Tên ứng dụng":"com.example.App"}`. Tệp gốc không bị sửa hay xoá; một bản được
lưu trong thư mục dữ liệu trước khi chuyển đổi.

Nhập là thay toàn bộ danh sách. Danh sách hiện tại được sao lưu trước khi thay.
Tệp có hai tên dùng cùng Bundle ID, tên không hợp lệ hoặc Bundle ID không hợp lệ
bị từ chối cả lần nhập, tránh bỏ mất mục âm thầm.

Beta4 nhận JSON gốc và bản sao lưu xuất bởi beta4. Các tệp nội bộ/bản sao lưu dạng
mã hoá của beta1–3 không phải định dạng nhập của beta4. Chúng được giữ nguyên;
để chuyển danh sách trên máy trong video, chọn tệp `AppList_Pro.json` gốc.
Không cần xoá thư mục iCloud hoặc sửa thủ công phím tắt.

## Thay đổi sau video beta3

Video xác nhận trình chọn Files và bước xác nhận nhập đã chạy, nhưng cả nhập JSON
lẫn thiết lập mới đều dừng ở **AP201**, trước khi ghi tệp. Video không cho biết
chính xác nhánh con nào trong bộ tự kiểm tra thất bại.

Beta4 thay lớp lưu này bằng **Dictionary → Save File** gốc của Shortcuts, theo
cách bản xuất ban đầu dùng. Bộ ghi không tự ghép toàn bộ JSON, không mã hoá
Base64 và không xác minh dựa trên thứ tự/khoảng trắng của JSON. Hai vế của mọi
so sánh động được tạo thành Text trước khi dùng trong If. So sánh giá trị có thể
rỗng, như URL của mục nhập cũ, thêm cùng một tiền tố không rỗng vào cả hai vế.

Dữ liệu ứng dụng và bộ ngôn ngữ được tách riêng. Bộ ngôn ngữ hỏng hoặc không khớp
không chặn mở ứng dụng: dùng bộ lưu trước nếu khớp, sau đó dùng tiếng Anh có sẵn.
Có thể tải lại bộ ngôn ngữ trong Sao lưu và khôi phục khi có mạng.

Các lỗi native trước đó vẫn được chặn: không dùng điều kiện Array Contains bị
thiếu tham số, không dùng kiểm tra tồn tại để suy ra chuỗi có ký tự, không dùng
cờ mở picker cũ hoặc mã tác vụ `detect.urls` không tồn tại.

## Dữ liệu và phục hồi

Tệp ở `iCloud Drive/Shortcuts/AppListPro/`:

| Tệp | Nội dung |
| --- | --- |
| `apps.v4.json` | Danh sách đang dùng |
| `apps.previous.v4.json` | Trạng thái trước lần thay đổi gần nhất |
| `apps.pending.v4.json` | Bản ghi tạm được đọc và kiểm tra trước khi thay tệp chính |
| `labels.v4.json` | Bộ ngôn ngữ đã chọn |
| `labels.previous.v4.json` | Bộ ngôn ngữ trước đó |

Beta4 dùng tên tệp mới; không ghi đè tệp beta1–3. Dữ liệu riêng không được tải lên
GitHub. Muốn giữ một mốc lâu dài, dùng **Xuất bản sao lưu**. Ghim, đổi tên, nhập,
xoá mục hoặc đổi ngôn ngữ đều tính là một lần thay đổi. **Khôi phục lần lưu trước**
cần xác nhận và phục hồi toàn bộ trạng thái trước đó.

Ghi dữ liệu theo thứ tự bản tạm → bản trước → bản chính. Bản tạm và bản chính
được đọc lại, đối chiếu từng giá trị với dữ liệu trong phiên. Tệp chính hỏng sẽ
được thay bằng bản trước trong bộ nhớ nếu bản đó còn hợp lệ; phím tắt thông báo
phục hồi. Nếu cả hai hỏng, có lựa chọn nhập, thiết lập mới hoặc huỷ.

Thông báo `AP4 / apps.pending.v4.json`, `AP4 / apps.previous.v4.json` hoặc
`AP4 / apps.v4.json` cho biết tệp không qua kiểm tra sau ghi. `AP410` và `AP411`
lần lượt chỉ lỗi kiểm tra bản tạm và bản chính của bộ ngôn ngữ. Lỗi quyền truy
cập hoặc I/O của hệ thống có thể hiển thị trực tiếp từ tác vụ Files.

Danh sách dùng được ngoại tuyến khi tệp iCloud đã có trên máy. Tìm ứng dụng,
tra liên kết và tải ngôn ngữ cần mạng. Kiểm tra revision trước ghi và ngay trước
thay tệp chính giúp phát hiện thay đổi đã hiện trên máy; không bảo đảm giao dịch
đồng thời giữa các thiết bị còn chờ iCloud đồng bộ. Nên sửa trên một máy mỗi lúc.

## Source and public data

Public source, translations and Info text live in this repository. The twenty
locale choices and existing readable language JSON files are retained. Only the
selected `.json` file is fetched during setup/change/reload, then cached locally.
Language content stays under the unchanged `releases/1.1.0-beta.1` path. Updating
that content requires a new data release; **Reload** does not update the engine.

State schema 4 is a native flat dictionary with eight string fields: `product`,
`schema`, `language`, `revision`, `namesJSON`, `bundlesJSON`, `storesJSON`, `pinsJSON`.
The four map values are serialized by native Dictionary-to-Text conversion,
using an explicit `{}` for empty maps; the outer Dictionary is saved directly.
JSON grammar, allowed/required keys and matching map counts are checked on read.
Imports additionally validate every record, Bundle-ID hash and unique name.
The revision is an opaque concurrency token, not a JSON integrity checksum.
App IDs use SHA-256 of the Bundle ID, avoiding dotted dictionary-key ambiguity.
The files are readable JSON, not encrypted storage.

```sh
python3 src/build.py
python3 tests/test_workflow.py
python3 src/audit.py
python3 src/sign.py
python3 src/audit.py --signed
```

Tests execute the emitted native action graph with simulated I/O and ICU regex.
They cover separate setup/add/import/relaunch sessions, JSON reformatting, empty
maps/URLs, save corruption, I/O failures, revision changes, recovery and UI-cache
failure. Audit checks action identifiers against independent references, text
comparison operands, control groups, output references and UTF-16 token ranges.
The signed action graph must equal the inspected source. Signing uses Shortcuty's
public documented API at build time; the installed shortcut never calls it.

This is an iOS 18 beta. Host-side checks do not establish actual iPhone execution,
menu rendering or timing. Native open-app errors, such as an app not installed,
remain system errors; install, edit or remove the relevant entry. Current check
results and device-verification status are recorded under `qa/`.
