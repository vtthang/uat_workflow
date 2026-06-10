# Quy Tắc Viết Test Case UAT

Áp dụng khi sinh KBKT UAT từ spec. Mục tiêu: test case phải mô tả chính xác hành vi **quan sát được trên UI**, đủ để automation script biết cần assert gì.

---

## RULE 1 — Kết quả sau redirect phải mô tả trạng thái trên màn hình đích

Khi hệ thống điều hướng sau một action (submit, lưu...), kết quả mong muốn phải mô tả **liên tục**:
1. Hệ thống điều hướng về màn hình nào
2. Trên màn hình đó hiển thị/trạng thái gì

**❌ Sai:**
```
- Tin tức có trạng thái: "Chờ duyệt"
- Hệ thống chuyển người dùng về màn hình Danh sách tin tức
```

**✅ Đúng:**
```
- Hệ thống chuyển người dùng về màn hình Danh sách tin tức
- Tại màn hình Danh sách tin tức: bản ghi tin tức vừa tạo hiển thị với trạng thái "Chờ duyệt"
```

---

## RULE 2 — Phân biệt rõ loại thông báo: inline message / toast / dialog

Mỗi loại có cơ chế trigger và vị trí khác nhau. Phải ghi rõ loại:

| Loại | Khi nào xảy ra | Vị trí hiển thị |
|---|---|---|
| **inline message** | Outfocus khỏi field | Bên dưới trường nhập liệu |
| **toast message** | Sau action (chọn ngày không hợp lệ, upload lỗi...) | Góc màn hình |
| **dialog** | Submit form khi có lỗi bắt buộc | Popup trung tâm màn hình |

**❌ Sai:**
```
4.1. Hệ thống hiển thị thông báo lỗi: "Vui lòng nhập tiêu đề bài viết"
```

**✅ Đúng (outfocus):**
```
2.1. Bên dưới trường Tiêu đề hiển thị inline message: "Vui lòng nhập tiêu đề bài viết"
```

**✅ Đúng (submit):**
```
4.1. Hệ thống hiển thị dialog thông báo lỗi: "Vui lòng nhập tiêu đề bài viết"
- Người dùng vẫn ở lại màn hình "Thêm mới tin tức", không điều hướng
```

---

## RULE 3 — Khi lỗi xảy ra, phải xác nhận màn hình hiện tại không thay đổi

Khi hệ thống block action do lỗi validation, assert thêm:
> "Người dùng vẫn ở lại màn hình [tên màn hình], không điều hướng"

Lý do: automation cần verify page không bị redirect nhầm.

---

## RULE 4 — Kết quả mong muốn phải mô tả giá trị cụ thể hiển thị trên UI

Không dùng mô tả trừu tượng như "giá trị được lưu" hay "dữ liệu đúng".

**❌ Sai:**
```
3.1. Giá trị được lưu vào trường, không hiển thị thông báo lỗi
```

**✅ Đúng:**
```
3.1. Trường "Đặt lịch đăng bài" hiển thị giá trị "25/12/2026 10:00:00", không hiển thị thông báo lỗi
```

---

## RULE 5 — Không mô tả cơ chế nội bộ (DB, server, API)

Test case là black-box — chỉ mô tả những gì **người dùng quan sát được trên UI**.

**❌ Sai:**
```
3.1. Hệ thống truy vấn DB kiểm tra slug, không hiển thị thông báo lỗi
```

**✅ Đúng:**
```
3.1. Trường Slug hiển thị giá trị "chuyen-doi-so-moi-2025", không xuất hiện inline message lỗi bên dưới trường
```

---

## RULE 6 — Mỗi bước phải là action của người dùng, không phải "quan sát"

Bước mô tả hành động. Kết quả quan sát thuộc về **Kết quả mong muốn**.

**❌ Sai (bước là quan sát):**
```
3. Quan sát trường Slug
```

**✅ Đúng:**
```
3. Click ra ngoài trường Tiêu đề (outfocus)

Kết quả mong muốn:
3.1. Trường Slug được tự động điền theo cấu trúc ...
```

**Ngoại lệ chấp nhận được:** Bước check trạng thái UI (disable/enable) có thể dùng "Thử click vào..." để tạo ra một action kiểm tra.

---

## RULE 7 — Bước outfocus phải tường minh trước khi verify inline message / trạng thái field

Khi cần verify kết quả sau khi rời khỏi field, phải có bước "Click ra ngoài (outfocus)" tường minh — automation cần biết trigger là gì.

**❌ Sai:**
```
3. Chọn thời gian 25/12/2026 10:30:00

3.1. Hệ thống hiển thị thông báo: "..."
```

**✅ Đúng:**
```
3. Chọn thời gian 25/12/2026 10:30:00
4. Click ra ngoài trường (outfocus)

4.1. Bên dưới trường hiển thị inline message: "..."
```

---

## RULE 8 — Pipeline: Sinh file testcase ngay, không hỏi confirm

**Rule:** Trong pipeline `/full-pipeline` và `/gen-uat` (khi user đã xác nhận bắt đầu), **sinh file `.md` ngay sau khi phân tích spec xong**, KHÔNG list TC rồi hỏi "có sinh không?".

**Lý do:** User muốn zero-intervention. Việc confirm từng bước làm chậm pipeline và phá vỡ luồng tự động.

**Áp dụng:**
- `/full-pipeline` — luôn sinh file ngay, không confirm bất kỳ bước nào
- `/gen-uat` — có thể list TC để user review (bước này là confirm duy nhất cho user), nhưng sau khi user oke → sinh file ngay không hỏi thêm

**Chỉ dừng khi bị block hoàn toàn:** không đọc được file spec, không connect được app, spec quá mơ hồ không thể suy ra TC.

---

## RULE 8 — API Response phải được phản ánh trên UI

Test case phải mô tả kết quả ứng với **từng trường hợp API trả về**, không chỉ happy path.

**Với mọi action gọi API (tạo mới, sửa, xóa, tìm kiếm...):**

| API trả về | Kết quả mong muốn phải ghi |
|---|---|
| 200/201 thành công | Toast thành công / navigate / trạng thái thay đổi cụ thể |
| 400 validation lỗi | Hiển thị đúng error message mà server trả về |
| 401/403 | Thông báo không có quyền / redirect login |
| 500 | Toast lỗi hệ thống |

**❌ Sai (chỉ mô tả happy path):**
```
3.1. Hệ thống lưu thành công và hiển thị thông báo "Tạo thành công"
```

**✅ Đúng (mô tả đủ cả error case):**
```
3.1. [Khi API trả về 201]: Hệ thống hiển thị toast "Tạo thành công", chuyển về màn hình danh sách
3.2. [Khi API trả về 400]: Hệ thống hiển thị inline message lỗi tương ứng bên dưới trường lỗi
3.3. Không có API call trùng lặp (form chỉ submit 1 lần)
```

**Mọi unhappy path của action submit/save phải có assertion: "Người dùng vẫn ở lại màn hình [X]"**

---

## RULE 9 — Màn hình danh sách phải có TC Pagination

Khi TLGP mô tả màn hình có phân trang (pagination controls), **bắt buộc** thêm đủ 8 TC dưới đây. Không skip dù không có yêu cầu rõ ràng.

### Bảng TC Pagination bắt buộc

| TC | Tên | Loại |
|---|---|---|
| TC-Px | Hiển thị phân trang khi đủ dữ liệu | Happy Path |
| TC-Px+1 | Chuyển sang trang tiếp theo | Happy Path |
| TC-Px+2 | Chuyển về trang trước đó | Happy Path |
| TC-Px+3 | Chuyển đến trang bất kỳ (nhập số trang / click số) | Happy Path |
| TC-Px+4 | Chuyển về trang đầu tiên | Happy Path |
| TC-Px+5 | Chuyển đến trang cuối cùng | Happy Path |
| TC-Px+6 | Trang cuối — nút Next bị vô hiệu; Trang đầu — nút Prev bị vô hiệu | Alternative Path |
| TC-Px+7 | Không đủ dữ liệu — không phân trang | Unhappy Path |
| TC-Px+8 | Đổi số item hiển thị/trang qua dropdown | Alternative Path (chỉ khi UI có dropdown) |

---

### Chi tiết từng TC

**TC-Px: Hiển thị phân trang khi đủ dữ liệu**
```
Precondition: CSDL có > [page_size] bản ghi (VD: > 10)
Các bước:
1. Truy cập màn hình danh sách

Kết quả mong muốn:
1.1. Danh sách hiển thị đúng [page_size] item (VD: 10 item)
1.2. Khu vực phân trang hiển thị: tổng số bản ghi, trang hiện tại (1), tổng số trang
1.3. Nút "Trang trước" / "First" bị vô hiệu hóa (đang ở trang 1)
1.4. Nút "Trang tiếp" / "Last" ở trạng thái hoạt động
```

**TC-Px+1: Chuyển sang trang tiếp theo**
```
Precondition: Đang ở trang 1, có ít nhất trang 2
Các bước:
1. Click nút "Trang tiếp" (›)

Kết quả mong muốn:
1.1. Danh sách cập nhật hiển thị bản ghi của trang 2
1.2. Indicator trang hiện tại cập nhật thành 2
1.3. Nút "Trang trước" chuyển sang trạng thái hoạt động
1.4. Chỉ 1 API GET được gọi (không duplicate)
```

**TC-Px+2: Chuyển về trang trước đó**
```
Precondition: Đang ở trang 2 trở lên
Các bước:
1. Click nút "Trang trước" (‹)

Kết quả mong muốn:
1.1. Danh sách cập nhật hiển thị bản ghi của trang trước (trang N-1)
1.2. Indicator trang hiện tại giảm 1
1.3. Chỉ 1 API GET được gọi
```

**TC-Px+3: Chuyển đến trang bất kỳ**
```
Precondition: Có ít nhất 3 trang
Dữ liệu mẫu: Nhập trang [3] (hoặc click số trang 3)
Các bước:
1. Nhập số trang vào ô input / click số trang 3 trong thanh phân trang
2. Nhấn Enter hoặc click xác nhận (nếu có)

Kết quả mong muốn:
1.1. Danh sách cập nhật hiển thị bản ghi của trang 3
1.2. Indicator trang hiện tại hiển thị 3
1.3. Chỉ 1 API GET được gọi
```

**TC-Px+4: Chuyển về trang đầu tiên**
```
Precondition: Đang ở trang 2 trở lên, UI có nút First (|‹) hoặc click số trang 1
Các bước:
1. Click nút "Trang đầu" (|‹) hoặc click số trang 1

Kết quả mong muốn:
1.1. Danh sách hiển thị bản ghi của trang 1
1.2. Indicator trang hiện tại hiển thị 1
1.3. Nút "Trang trước" / "First" bị vô hiệu hóa
1.4. Chỉ 1 API GET được gọi
```

**TC-Px+5: Chuyển đến trang cuối cùng**
```
Precondition: Đang ở trang 1, có nhiều hơn 1 trang; UI có nút Last (›|) hoặc hiển thị số trang cuối
Các bước:
1. Click nút "Trang cuối" (›|) hoặc click số trang cuối

Kết quả mong muốn:
1.1. Danh sách hiển thị bản ghi của trang cuối
1.2. Indicator trang hiện tại hiển thị số trang cuối
1.3. Nút "Trang tiếp" / "Last" bị vô hiệu hóa
1.4. Chỉ 1 API GET được gọi
```

**TC-Px+6: Trạng thái disabled đúng ở biên**
```
Precondition: Có ít nhất 2 trang
Các bước:
1. Quan sát khu vực phân trang khi ở trang 1
2. Navigate đến trang cuối, quan sát lại

Kết quả mong muốn:
1.1. [Trang 1]: nút "Trang trước" / "First" disabled; nút "Trang tiếp" / "Last" enabled
2.1. [Trang cuối]: nút "Trang tiếp" / "Last" disabled; nút "Trang trước" / "First" enabled
```

**TC-Px+7: Không đủ dữ liệu — không phân trang**
```
Precondition: CSDL có ≤ [page_size] bản ghi
Kết quả mong muốn:
1.1. Tất cả bản ghi hiển thị trên 1 trang duy nhất
1.2. Nút phân trang bị vô hiệu hóa hoặc khu vực pagination ẩn đi
```

**TC-Px+8: Đổi số item/trang qua dropdown** *(chỉ khi UI có dropdown page size)*
```
Dữ liệu mẫu: Chọn [20] từ dropdown (mặc định 10)
Các bước:
1. Mở dropdown chọn số item/trang
2. Chọn option [20]

Kết quả mong muốn:
1.1. Danh sách cập nhật hiển thị tối đa 20 item/trang
1.2. Tổng số trang giảm tương ứng (VD: 100 bản ghi → từ 10 trang còn 5 trang)
1.3. Indicator phản ánh đúng page size mới
1.4. Chỉ 1 API GET được gọi
```

---

### Quy tắc viết TC Pagination

- **Ghi rõ page_size** mặc định từ TLGP (10 / 20 / 50...)
- **Dữ liệu mẫu cụ thể**: `CSDL có 25 bản ghi, page size = 10 → 3 trang`
- **Kết quả**: luôn ghi tổng số trang kỳ vọng và bản ghi mỗi trang
- **Không duplicate API**: mọi TC navigate đều assert "chỉ 1 API GET được gọi"
- **Adapt theo UI thực tế**: nếu UI không có nút First/Last thì bỏ TC-Px+4/Px+5, ghi chú lý do
- **TC-Px+3** (trang bất kỳ): nếu UI không có input số trang → dùng click số trang trong thanh phân trang

---

## CHECKLIST bổ sung (áp dụng thêm vào checklist gốc)

- [ ] Kết quả sau redirect: mô tả trạng thái trên màn hình đích, không tách rời
- [ ] Loại thông báo ghi rõ: `inline message` / `toast message` / `dialog`
- [ ] Khi submit lỗi: có dòng "Người dùng vẫn ở lại màn hình [X]"
- [ ] Kết quả mong muốn nêu giá trị cụ thể, không nói chung "giá trị được lưu"
- [ ] Không có từ "truy vấn DB", "server", "API" trong kết quả
- [ ] Mỗi bước là action người dùng, không phải quan sát
- [ ] Bước outfocus tường minh trước assert inline message
- [ ] Action gọi API: có mô tả kết quả cho cả 200 và 400/error case (Rule 8)
- [ ] Màn hình danh sách có phân trang: đủ TC-Px ~ TC-Px+7, thêm TC-Px+8 nếu có dropdown page size (Rule 9)
- [ ] Pagination: có đủ case trang tiếp, trang trước, trang bất kỳ, trang đầu, trang cuối, trạng thái disabled ở biên
