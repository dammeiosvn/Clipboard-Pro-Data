# Quick Call Image · ©️ Sentechtipsvn

Kho dữ liệu công khai cho Quick Call Image beta 7 trở đi. Không chứa ảnh, số
điện thoại được quét, nhật ký cuộc gọi hoặc cấu hình riêng của người dùng.

## Chỉ bảo trì một JSON nguồn

Sửa `quick-call-image/catalog.json` trên nhánh `main`.
GitHub Actions **Publish QuickCall data** kiểm tra nguồn rồi tự tạo chỉ mục và
các gói nhỏ. Phím tắt đã cài không cần thay khi thêm vùng hoặc ngôn ngữ tương
thích với schema `2`, engine `3`.

- `countries.<ISO>`: hồ sơ đánh số đầy đủ của một vùng; thêm ISO vào `countryOrder`.
- `languages.<BCP47>`: đủ các khoá của `languages.en`; thêm mã vào `languageOrder`.
- `icons`, `menus`, `behavior`, `digitMap`: giao diện và quy tắc chung.
- Quốc gia/vùng và ngôn ngữ là hai lựa chọn độc lập. US và CA cùng `+1` nhưng có hồ sơ riêng.

Không chỉnh tay `index.*` hoặc `packs/`. Sau khi commit nguồn, đợi workflow xanh.
Nguồn sai bị từ chối trước khi chỉ mục đang phát hành bị thay đổi. Giữ các thư mục
revision cũ để thiết bị đang thiết lập dở vẫn tải được đúng các phần của cùng một bản.

## Phím tắt tải gì?

Khi thiết lập, đổi vùng/ngôn ngữ hoặc bấm **Cập nhật dữ liệu**, phím tắt tải:

1. `index.txt`: tên/mã các lựa chọn và checksum; không có toàn bộ quy tắc hoặc bản dịch.
2. Gói quy tắc chung `core.txt`.
3. Đúng một gói `regions/<ISO>.txt`.
4. Đúng một gói `languages/<BCP47>.txt`.

Các gói nằm dưới `packs/<revision>/`. Bản `.txt` chứa nguyên JSON để iOS giữ
đúng văn bản khi kiểm tra SHA-256; bản `.json` tương ứng có cùng nội dung cho
người bảo trì đọc. Không có API, proxy, token GitHub hoặc ứng dụng phụ chạy trên iPhone.
Chỉ mục dùng URL nhánh ổn định; checksum gói được lấy từ chỉ mục hiện hành,
không ghim cứng một checksum catalog trong phím tắt.

Thiết bị chỉ lưu một hồ sơ vùng, một gói ngôn ngữ và quy tắc chung trong
`Shortcuts/QuickCall/active.json`. Quét ảnh/gọi không tải mạng hoặc ghi lại cache.
Cập nhật chỉ mục trên repo không tự đổi cấu hình thiết bị đang offline;
người dùng chọn **Cài đặt → Cập nhật dữ liệu** để nhận thay đổi.

Số quốc tế khác vùng đang chọn cần đổi vùng để xác minh. Không cất bộ quy tắc
của mọi vùng trên thiết bị, và không tự đoán số chưa xác minh để gọi.

## Chạy bộ xuất thủ công

```bash
python3 quick-call-image/export.py
```

Chỉ thêm dữ liệu cho các xử lý hiện có. Chức năng native mới hoặc phép biến đổi
khác mà engine chưa hiểu vẫn cần cập nhật phím tắt. Dữ liệu không phải cơ chế
thực thi mã từ xa hoặc bảo vệ chống sao chép.

## Nguồn quy tắc

Các mẫu di động/điện thoại bàn ban đầu được trích từ Google libphonenumber
9.0.42, commit `8593ab70fa4fadffc042b2714034f4c52bef7daf`.
Nguồn: https://github.com/google/libphonenumber/tree/8593ab70fa4fadffc042b2714034f4c52bef7daf

Giữ `meta.metadataSource`, thông tin phiên bản và `LICENSE.libphonenumber` khi
phân phối phần dữ liệu này. Quy tắc đánh số cần được kiểm chứng trước khi mở vùng mới.
