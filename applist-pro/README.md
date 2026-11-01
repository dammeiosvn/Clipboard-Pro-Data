# AppList Pro

© Sentechtipsvn · 1.1.0-beta.5

Native iOS quick launcher. The first screen is the app list, pinned apps first,
with **Manage** at the bottom. Tap an app to open it. Normal launches make no HTTP
request and write no file. Community-facing text uses the selected language.

## Nâng cấp từ beta4

Cài `AppList-Pro-1.1-beta5.shortcut` và chạy. Khi chưa có dữ liệu beta5, phím tắt
tự nhận danh sách và bộ ngôn ngữ beta4 trên cùng iCloud. Không cần nhập lại hoặc
tải lại ngôn ngữ nếu bộ lưu beta4 còn hợp lệ. Tệp beta4 được giữ nguyên.

Dữ liệu beta5 dùng tên tệp mới. Chỉnh sửa trên beta5 không cập nhật ngược danh sách
beta4. Nếu cả tệp chính và tệp trước của beta5 hỏng, phím tắt mở luồng phục hồi;
không tự quay về một danh sách beta4 cũ và làm người dùng tưởng đó là dữ liệu mới.

Cài mới hoàn toàn: chọn một trong 20 ngôn ngữ, sau đó chọn **Thêm ứng dụng**.
Tải ngôn ngữ và tìm ứng dụng cần mạng. Mở app dùng dữ liệu lưu sẵn khi các tệp
iCloud đã có trên máy. Huỷ hộp thoại sẽ kết thúc phiên.

## Màn hình và quản lý

Danh sách app nằm ngoài cùng. Menu Quản lý có sáu mục:

- Thêm ứng dụng
- Chỉnh sửa danh sách
- Sao lưu và khôi phục
- Ngôn ngữ
- Info
- Quay lại

Chọn một app trong **Chỉnh sửa danh sách** để đổi tên, ghim/bỏ ghim, đặt vị trí,
mở App Store hoặc xoá mục. Xoá mục không gỡ ứng dụng khỏi iPhone. Mở App Store
không tự cài ứng dụng. Không có bước kiểm tra mạng hoặc cập nhật trước khi mở app.

**Sắp xếp vị trí** nhận số từ 1 đến số app trong nhóm hiện tại. Nhóm ghim và nhóm
thường được xếp riêng; nhóm ghim luôn đứng trước. Thứ tự mới được lưu cho lần chạy
sau. App mới thêm vào cuối nhóm thường. Các mục cùng thứ hạng dùng tên để phân xử.
Các app chuyển từ beta4 ban đầu giữ cách xếp ghim trước, tên A–Z trong từng nhóm.

Ngôn ngữ hiện tại nằm đầu danh sách với dấu ✓. Chọn lại cùng ngôn ngữ đã có bộ lưu
không tải hoặc lưu thêm. Đổi ngôn ngữ quay về Quản lý; tải lại bộ ngôn ngữ quay về
Sao lưu và khôi phục. Tải lại riêng bộ giao diện không tạo mốc dữ liệu ứng dụng.

Info chứa phiên bản, giới thiệu và hướng dẫn dùng bằng ngôn ngữ đã chọn.

## Nhập JSON có xem trước

Vào **Quản lý → Sao lưu và khôi phục → Nhập từ tệp**. Nhận bản sao lưu beta5,
beta4 hoặc tệp gốc `AppList_Pro.json` dạng `{"Tên ứng dụng":"com.example.App"}`.
Tệp gốc trong Files không bị sửa hoặc xoá.

Màn hình xem trước hiển thị số mục hợp lệ, có thể thêm mới, đã có trong danh sách,
mục lỗi và tên xung đột khi gộp:

- **Gộp và giữ mục đã có**: đối chiếu bằng Bundle ID. Giữ nguyên tên, ghim, link
  và vị trí của app hiện có. Chỉ thêm app mới không gây trùng tên. Không có mục
  mới thì không ghi dữ liệu hoặc xoay mốc phục hồi.
- **Thay toàn bộ danh sách**: có bước xác nhận riêng, sau đó thay bằng các mục hợp
  lệ trong tệp. Các mục lỗi đã được đếm trong màn hình xem trước sẽ bị loại.
- **Quay lại**: giữ nguyên toàn bộ danh sách và các mốc lưu.

Hai tên trong cùng tệp gốc trỏ đến một Bundle ID được coi là xung đột: loại cả
nhóm tên đó và đếm rõ, thay vì tự chọn một tên. Hai Bundle ID có cùng tên trong
bản sao lưu cũng bị loại cùng nhau. Tệp toàn mục lỗi không được dùng để xoá sạch
danh sách. Tệp rỗng có thể thay danh sách bằng danh sách rỗng sau xác nhận rõ ràng.

Nhập thông thường giữ ngôn ngữ hiện tại. Phục hồi một mốc cũ phục hồi cả ngôn ngữ
của mốc đó. Khi chưa có cấu hình mà nhập bản sao lưu hiện đại, ngôn ngữ trong tệp
được dùng; không bắt buộc tải bộ giao diện để phục hồi danh sách.

## Các mốc phục hồi

Trong Sao lưu và khôi phục, **Các mốc phục hồi** hiển thị tối đa ba trạng thái cũ
được giữ tự động, kèm thời điểm và số app. Bản trước gần nhất được dùng bổ sung
nếu chưa có trong các mốc; các revision trùng không hiển thị lặp. Chọn mốc rồi
xác nhận để phục hồi. Mốc hỏng bị bỏ qua. Mốc từ beta4 hiển thị dấu phiên bản
`beta4` vì định dạng cũ không có thời điểm lưu.

Mốc tự động có thể bị thay thế theo các lần sửa sau. Muốn giữ một bản lâu dài,
dùng **Xuất bản sao lưu** và lưu tệp ở nơi bạn chọn.

Tệp ở `iCloud Drive/Shortcuts/AppListPro/`:

| Tệp | Nội dung |
| --- | --- |
| `apps.v5.json` | Danh sách và thứ tự hiện tại |
| `apps.pending.v5.json` | Bản tạm được đọc và đối chiếu trước khi thay tệp chính |
| `apps.previous.v5.json` | Trạng thái trước thay đổi gần nhất |
| `history.1.v5.json` đến `history.3.v5.json` | Ba mốc cũ, mới nhất trước |
| `labels.v5.json`, `labels.previous.v5.json` | Bộ giao diện hiện tại và bộ trước |

Dữ liệu riêng không tải lên GitHub. Ghi theo thứ tự bản tạm → mốc cũ/bản trước →
bản chính, có kiểm tra đọc lại. Lỗi lưu dừng phiên để giữ tệp chính hoặc bản trước.
Các mã `AP5 / tên tệp`, `AP5 history` giúp xác định bước thất bại. Lỗi quyền truy
cập/I/O hệ thống có thể xuất hiện trực tiếp từ tác vụ Files.

Kiểm tra revision trước ghi và ngay trước thay tệp chính, kể cả khi tệp ban đầu
chưa có, giúp tránh ghi đè thay đổi đã hiện trên máy. Đây không phải cơ sở dữ liệu
giao dịch; hai thiết bị còn chờ iCloud đồng bộ vẫn có thể xung đột. Nên chỉnh sửa
trên một thiết bị mỗi lúc.

## Implementation and validation

The beta4 native Dictionary → Save File protocol is retained. Schema 5 adds
`orderJSON` and `savedAt` to the eight existing fields. Five JSON map strings are
encoded by native Dictionary conversion, with explicit `{}` for empty maps.
The outer dictionary is saved directly. No Base64 state envelope or JSON-byte
checksum is used. Revision is an opaque concurrency token. Files are readable
JSON, not encrypted storage.

Readers accept schema4 and schema5. Required fields, scalar types, map counts,
matching ID sets and position syntax are checked. Imports additionally validate
each record, Bundle-ID hash and conflicting names. Potentially empty comparisons
use a shared nonempty prefix; both operands are materialized as Text. Native
array Contains and the obsolete file-picker flag remain excluded.

Within a session, the app label text and route map are reused until a save
invalidates them. A fresh list is built from cached text for each presentation,
avoiding appended controls leaking into later menus. First renders use a single
app loop plus native sorting and text operations.

Translations and Info are public under `releases/1.1.0-beta.5`. Existing beta1
release files are unchanged. `config/strings.json` holds the original labels;
`config/extensions.json` adds beta5 labels. Compact embedded extensions let a
beta4 language cache upgrade offline. **Reload** updates the compatible UI pack,
not the engine. New translation changes require a new release path.

```sh
python3 src/build.py
python3 tests/test_workflow.py
python3 src/audit.py
python3 src/sign.py
python3 src/audit.py --signed
python3 tests/measure_workload.py
```

Tests execute the emitted graph with simulated I/O and ICU regex. Cases include
migration in all 20 locales, app/empty-list reloads, merge/replace/cancel, alias
and name conflicts, ordering, history rotation, corrupt/I/O-failed saves, and
concurrent revisions. Lists of 10/50/100 apps are also edited and reopened.
`qa/menu-workload.json` counts interpreted actions; it is not iPhone timing.
The comparison baseline is used only when the signed beta4 file is locally
available. Signed-archive verification requires Python `lzfse`.

Signing uses Shortcuty's documented public API during the build. The installed
shortcut never contacts that service. The signed action graph must match the
inspected source. Only public generated source is signed; no personal list is
read or uploaded by the signing script.

Beta4 basic operation was confirmed by the owner on iPhone. Beta5 host tests do
not establish native device timing or complete iPhone acceptance. Opening an app
that is not installed remains a system error; edit or remove that entry. Real
app-icon rows are deferred to a separate experiment; the main launcher remains
native and contains no browser/Web View layer.
