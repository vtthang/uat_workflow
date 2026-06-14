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

## QUY TẮC PIPELINE — Sinh file testcase ngay, không hỏi confirm

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

## RULE 10 — Phân quyền: sinh deny-case từ happy path (cross-cutting)

Phân quyền là quan hệ **role × action**, không thuộc riêng Transaction nào. Vì vậy **không gen lẫn vào TC feature** — sinh thành nhóm TC riêng `TC-PERM-*`, derive trực tiếp từ happy path của chính Use-case.

### 10.1 — Nguồn: mỗi happy path = một action cần bảo vệ

Liệt kê các happy path của Use-case → đó chính là danh sách action cần check quyền (view / create / edit / delete / action nghiệp vụ). Không cần khai báo ma trận quyền tay — lấy thẳng từ happy path.

### 10.2 — Đúng quyền test mọi case; sai quyền chỉ test happy → assert lỗi

| Phía | Test gì | Sinh ở đâu |
|---|---|---|
| **Đúng quyền** (role được phép) | **Mọi case** của tính năng (đầy đủ field validation, luồng, biên...) | Chính các **TC feature** chạy bằng role được phép — không sinh lại trong TC-PERM |
| **Sai quyền** (role không được phép) | **Chỉ 1 case happy** mỗi action → assert **bị chặn / hiển thị lỗi** | Nhóm **TC-PERM** |

→ TC-PERM chỉ mô tả **role KHÔNG được phép** thực hiện happy path và kỳ vọng bị chặn (không cần lặp lại các nhánh validate/biên ở phía sai quyền — chặn ở cửa thì các nhánh con vô nghĩa).

### 10.3 — Gộp theo độ chặn (coarse vs fine)

| Trường hợp | Cách sinh TC |
|---|---|
| **A — Role bị chặn ngay cửa** (không vào được màn) | **1 TC coarse/role** cho cả Use-case. Bỏ qua action lẻ — đã bị chặn từ vòng ngoài thì không cần check từng nút |
| **B — Role vào được màn nhưng giới hạn action** (vd: xem được nhưng không sửa được) | **1 deny-case kèm mỗi happy path** của action bị giới hạn |

### 10.4 — Biểu hiện "deny" phải ghi rõ trong kết quả mong muốn

Trích đúng cách hệ thống chặn (hỏi BA/Dev nếu spec không nói, ghi `[TBD]`):
- Menu/route ẩn → "Mục [X] không hiển thị trong menu của role [Y]"
- Redirect/403 → "Gõ thẳng URL [route] → bị đẩy về [trang], hoặc hiển thị trang 403"
- Nút ẩn/disabled → "Nút [Thêm/Sửa/Xóa] không hiển thị / ở trạng thái disabled"
- API 403 → "API [endpoint] trả 403, UI hiển thị [thông báo không có quyền]"

### 10.5 — Account đóng vai (persona) lấy từ config, không tạo runtime

- Role để login lấy từ `config/test.config.json` (`accounts.<persona>.role`) — xem `config_management.md`.
- **Actor account là bất biến**: TC feature (toggle/xóa/sửa) chỉ được thao tác lên **test-data account tự tạo**, TUYỆT ĐỐI không đụng persona dùng để login.
- Cross-portal (3 domain riêng): "role kia không vào được" thực chất là **account đó không đăng nhập được vào portal này** → deny ở tầng đăng nhập, TC ghi rõ.

### 10.6 — Format nhóm TC-PERM

```
### Phân quyền (TC-PERM)

#### TC-PERM-01: [Role] không có quyền [action/truy cập màn]

**Actor:** [Role bị từ chối — vd PORTAL_PARTNER]
**Loại luồng:** Unhappy Path (Authorization)
**Precondition:** Đăng nhập bằng account role [Y] (persona: partner)
**Dữ liệu mẫu:** —

**Các bước:**
1. Đăng nhập bằng account role [Y]
2. Truy cập [đường dẫn màn / gõ URL trực tiếp]

**Kết quả mong muốn:**
2.1. [Biểu hiện deny cụ thể theo 10.4]
```

---

## RULE 11 — Đa ngôn ngữ: không sinh case mới, mỗi TC khẳng định ngôn ngữ (cross-cutting)

Đa ngôn ngữ **không phải case mới** — cùng một testcase chạy lại ở ngôn ngữ khác, chỉ chữ hiển thị đổi. **Không** viết lại TC cho từng ngôn ngữ.

### 11.1 — Confirm ngôn ngữ ở đầu (Bước 1 của gen-uat)

Trước khi gen: xác nhận hệ thống hỗ trợ những ngôn ngữ nào + ngôn ngữ chính (primary) để chạy round mặc định. Mặc định primary = tiếng Việt.

### 11.2 — Mọi TC bắt buộc có mục "Ngôn ngữ hiển thị"

Thêm vào "Kết quả mong muốn" của **mọi** TC một mục chuẩn (template cố định, gen-uat tự chèn):

```
**Ngôn ngữ hiển thị:** Toàn bộ nội dung, nhãn trường, placeholder, nút, thông báo lỗi và toast đều hiển thị ĐỒNG NHẤT bằng ngôn ngữ đang chọn (tiếng Việt) — KHÔNG lẫn bất kỳ ngôn ngữ khác (tiếng Anh), không lòi key thô (vd "error.emailExists").
```

**Nguyên tắc cốt lõi (A4):** khi đang ở 1 ngôn ngữ, **tuyệt đối không có chữ của ngôn ngữ khác xuất hiện** trên màn — kể cả 1 nút/label sót. Đây là điểm kiểm bắt buộc, không chỉ "label chính đúng".

### 11.3 — Error / toast trích nguyên văn ngôn ngữ chính

Mọi thông báo lỗi/toast/dialog phải ghi **nguyên văn tiếng Việt** (đã yêu cầu ở RULE 2/8) — không vague kiểu "hiển thị thông báo lỗi". Các chuỗi này chính là **nguồn của `t()`** khi sinh code (Phase 2): muốn chạy được ngôn ngữ thứ 2 sau này, expected result tiếng Việt phải đủ và chính xác ngay từ Phase 1.

### 11.4 — Verify ngôn ngữ thứ 2 = gate "no-leak" nhẹ, KHÔNG re-run cả suite

Khi user yêu cầu chạy ngôn ngữ khác (vd EN), **không** parameterize lại toàn bộ assertion / không nhân bản script. Mục tiêu thực tế thường chỉ là: **ở ngôn ngữ đang chọn, NGOÀI dữ liệu từ API ra, không còn chữ của ngôn ngữ gốc trên màn.** Cách enforce:

- Sinh 1 spec mỏng `i18n-<locale>.spec.ts` (ví dụ `TC-I18N-01..N`), mỗi màn chính (list / create / detail / edit / history / popup) = 1 TC: đổi ngôn ngữ → screenshot → **quét text tĩnh (chrome)** → assert KHÔNG còn ký tự ngôn ngữ gốc.
- **Phát hiện tiếng Việt** = regex ký tự có dấu đặc trưng (ă â đ ê ô ơ ư + nguyên âm có dấu) — tiếng Anh không có.
- **LOẠI dữ liệu API (bắt buộc)** khỏi vùng quét, nếu không sẽ false-positive: `tbody` (giá trị dòng), `input/textarea` value, `select`/`[role=combobox]`/`[role=listbox]`/`[role=option]` (giá trị đã chọn), `[role=switch]`, **trigger dropdown** (`[aria-haspopup]` / class field) hiển thị giá trị đã chọn, và **label của checkbox/radio** (liên kết qua `label.control`, qua `for=`, hoặc sibling kiểu Tailwind `peer` trong cùng parent) — đây là tên nhóm quyền/role do user tạo. Tên ngôn ngữ trong dropdown (vd "Tiếng Việt") hiển thị dạng bản địa là **chuẩn UX**, không tính lỗi.
- Quét vào các selector chrome: `thead th`, `button` (action), `label` (field), `[placeholder]`, `[role=tab]`, `h1..h4`, `nav a`, toast/empty-state/pagination.
- Helper tái dùng đặt trong POM: `switchToEnglish()` + `findVietnameseInChrome()` (xem `UserManagementPage`). Navigation trong round EN phải **EN-robust** (mở row trực tiếp/qua URL, không locate theo text/placeholder tiếng Việt vì chúng đã đổi).

**11.4b — Bắt buộc phủ ERROR / TOAST / DIALOG, không chỉ màn tĩnh.** Quét chrome màn tĩnh là CHƯA đủ — phần lớn chuỗi i18n nằm ở message động chỉ hiện khi trigger. Sinh thêm spec `i18n-<locale>-errors.spec.ts` trigger **từng họ message** ở ngôn ngữ đích rồi assert không còn ngôn ngữ gốc:
- **Inline validation:** required (submit rỗng), sai định dạng (email), maxlength (>max), ký tự không hợp lệ.
- **Business message (server):** trùng email/SĐT, ... — đọc message trả về sau submit.
- **Dialog xác nhận:** reset / toggle / xóa — **loại tên/đối tượng (data)** khỏi text trước khi soi (vd `dialogText.replace(accountName,'')`).
- **Toast tự biến mất:** dùng MutationObserver spy (`installToastSpy()` TRƯỚC khi trigger, `collectedToasts()` sau) vì toast thường không có class `toast`/`role=alert` và biến mất nhanh — phải bắt lúc đang hiện + assert toast CÓ xuất hiện (proof) và không phải ngôn ngữ gốc.
- Trigger ở locale đích cần locator **EN-robust** (theo `input[name=...]`, `type`, regex `VI|EN` cho nút) vì locator theo text/placeholder tiếng Việt đã đổi. Setup data có thể tạo ở ngôn ngữ gốc rồi mới đổi locale.

Việc verify ngôn ngữ đồng nhất (mục 11.2) vẫn ghi trong từng TC chức năng; nhưng **enforcement** cho ngôn ngữ thứ 2 = gate no-leak (11.4) **+** phủ message động (11.4b).

---

## RULE 11b — VALIDATION COVERAGE GATE (cưỡng chế — không được thiếu)

> Lỗi từng gặp: RULE 12–15 chỉ là mô tả "phải làm" → khi gen bị rút gọn theo phán đoán, thiếu field mà không ai phát hiện. Rule này biến coverage thành **bắt buộc kiểm**.

**Áp dụng cho MỌI form có field nhập** — tạo / sửa / **reset mật khẩu** / popup nhập liệu (vd "nhập lại mật khẩu phải khớp" cũng là validate). Với MỖI field sinh đủ ô ma trận sau (mỗi ô = 1 TC **hoặc** ghi `N/A — lý do`, KHÔNG để trống):

| Ràng buộc field | Case bắt buộc sinh |
|---|---|
| **Bắt buộc** | (1) để trống + **outfocus** → lỗi · (2) để trống + **submit** → lỗi — **2 TC TÁCH BIỆT** |
| **Không bắt buộc** | (1) để trống → **không** có lỗi |
| **Max/min length** | (1) biên hợp lệ ok · (2) quá biên + **outfocus** → lỗi · (3) quá biên + **submit** → lỗi — **tách biệt** |
| **Ký tự hợp lệ** | (1) hợp lệ ok · (2) không hợp lệ → lỗi |
| **Trùng (unique)** | tạo trước → nhập trùng → lỗi exact SRS |
| **Default value** | màn sửa/duyệt: tự tạo → mở lại verify đúng giá trị |
| **Dropdown/checkbox** | theo selected/checked |

**Nguyên tắc 2 hướng = 2 case tách biệt** (CRITICAL theo yêu cầu): chỗ nào có "outfocus" và "submit" → **PHẢI là 2 TC riêng**, không gộp — để verify được từng hướng độc lập.

**Clear-first**: màn sửa (field có sẵn giá trị) → mọi case validate phải **clear field trước** rồi mới trigger.

**Gate (trước Phase 2):** đối chiếu danh sách field SRS ↔ testcase. Field nào thiếu ô bắt buộc → **fail gate, bổ sung** trước khi sang automation. Cô lập field: khi test 1 field, mọi field khác điền hợp lệ (xem `test_execution_rules.md` mục 2).

---

## RULE 12 — Validate field: Giá trị mặc định

Áp dụng cho **mọi field** có giá trị mặc định theo SRS. Đặc biệt bắt buộc với màn **Sửa / Phê duyệt / Xoá / Chi tiết** — nơi default phải là **đúng giá trị của bản ghi**.

- **Cách kiểm (edit/duyệt/xoá):** Tự tạo mới một bản ghi với giá trị đã biết → vào màn đang test → verify từng field hiển thị **đúng giá trị vừa tạo** (không chỉ "khác rỗng").
- TC ghi rõ giá trị mặc định kỳ vọng cụ thể (RULE 4), không viết "hiển thị giá trị mặc định" chung chung.
- Triển khai automation: xem `test_execution_rules.md` mục 2b (tạo qua API → `toBe(value)`).

---

## RULE 13 — Validate field: Trường bắt buộc / không bắt buộc

Với **mỗi field**, xác định bắt buộc hay không theo SRS:

**Field bắt buộc → sinh 2 TC theo 2 hướng trigger:**
| Hướng | Thao tác | Kỳ vọng |
|---|---|---|
| Outfocus | Để trống → click ra ngoài field | inline message **exact SRS** |
| Submit | Để trống → nhấn Confirm/Submit | message lỗi **exact SRS** + ở lại màn (RULE 3) |

**Field KHÔNG bắt buộc → 1 TC:** để trống → submit → **không hiển thị error message** cho field đó.

**Chú ý đặc biệt (clear-first):** nếu field đang có giá trị mặc định khác rỗng → TC phải có bước **clear field trước** rồi mới thực hiện 2 hướng trên (xem `generate-automation-from-testcases.md` Bước 5 cách clear theo loại field).

---

## RULE 14 — Validate field: Độ dài & Ký tự (ISTQB BVA + EP)

Dùng skill `testcase-design` (ISTQB). Áp dụng cho field có ràng buộc trong SRS.

**14.1 — Min/max length (Boundary Value Analysis):**
- Sinh case: `min-1` (❌), `min` (✅), `max` (✅), `max+1` (❌). (Thêm `min+1`/`max-1` nếu cần coverage cao.)
- Mỗi case **invalid** kiểm theo **2 hướng** như RULE 13 (outfocus + submit), kèm clear-first nếu có default.
- **Khi nhập QUÁ max — kiểm 2 thứ (BẮT BUỘC, gõ thật bằng `pressSequentially` chứ không `fill` để không bypass maxlength):**
  1. **Đếm lại độ dài thực tế** sau khi nhập → field có bị **cắt = max** không (`actualLength`).
  2. **Nếu `actualLength > max` → PHẢI có error message.** (Không cắt mà cũng không báo lỗi = **defect**.)
- Ghi `actualLength` vào evidence (`<tc>_maxlength.json`). Message lỗi **exact SRS**.

**14.2 — Ký tự hợp lệ (Equivalence Partitioning):**
- SRS **không ràng buộc** ký tự → 1 TC: nhập đủ loại ký tự → **không lỗi**.
- SRS **có ràng buộc** → mỗi lớp tương đương 1 đại diện: 1 case valid + 1 case mỗi lớp invalid (chữ/số/ký tự đặc biệt/khoảng trắng...) → error exact SRS.

---

## RULE 15 — Validate: Trùng dữ liệu & Dropdown / Checkbox

**15.1 — Trùng dữ liệu (unique constraint):**
- **Tạo trước** một bản ghi → dùng chính giá trị đã tồn tại để test trùng → assert error message **exact SRS**.
- Không giả định data có sẵn trong hệ thống — tự tạo để chủ động (xem `test_execution_rules.md` mục 8 + API helper).

**15.2 — Dropdown / Checkbox:**
- Kết quả phụ thuộc **giá trị được chọn (selected) / được tick (checked)** — TC ghi rõ option chọn và kỳ vọng tương ứng.
- Nhiều điều kiện kết hợp (combo dropdown + checkbox) → dùng **Decision Table** (skill `testcase-design`) để phủ tổ hợp.

---

## RULE 16 — Luồng nghiệp vụ: hậu điều kiện bắt buộc + case không dữ liệu

**16.1 — Happy path phải verify HẬU ĐIỀU KIỆN (không dừng ở thông báo):**

| Thao tác | TC phải verify thêm sau thông báo |
|---|---|
| **Thêm mới** | Item hiện ở danh sách → **search ra đúng item vừa thêm** |
| **Sửa** | **Mở lại item** → mọi field đã cập nhật đúng giá trị mới |
| **Xoá** | Item **không còn** trong danh sách (search không ra) |
| **Phê duyệt / Từ chối** | **Trạng thái item** đổi đúng (kiểm lại trên list/detail) |

Mọi happy path: thông báo thành công **exact SRS** (RULE 2).

**16.2 — Invalid path:** sinh các nhánh thất bại theo SRS (validate, lỗi server) — đối chiếu RULE 8 (API response).

**16.3 — Case "không có dữ liệu":** màn danh sách luôn có TC empty-state. Khi môi trường khó tạo trạng thái rỗng → automation **chặn/giả response API** để ép empty (xem `test_execution_rules.md` mục 19). TC ghi rõ thông báo empty **exact SRS**.

**16.4 — Search dựa trên dữ liệu có thật:** keyword tìm kiếm phải lấy từ item đang có trong danh sách để đảm bảo tìm đúng (không hardcode keyword) — triển khai xem `test_execution_rules.md` mục 14c.

---

## RULE 17 — Nghiệp vụ liên quan & System Knowledge

Test một tính năng không tách rời — phải xét **ảnh hưởng chéo** với tính năng khác.

- **Trước khi xác định TC:** đọc `knowledge/system-features.md` → tìm tính năng liên quan tới tính năng đang test (chung entity, chung màn, nối luồng, đổi trạng thái dùng chung). Bổ sung TC kiểm tra ảnh hưởng chéo nếu có.
- **Sau khi gen/test xong:** **cập nhật** `knowledge/system-features.md` — thêm/sửa entry cho tính năng vừa làm + ghi quan hệ với tính năng khác (theo template trong file đó).
- Khi có tính năng mới → luôn soi lại bản đồ này để biết nó có thể bị ảnh hưởng / gây ảnh hưởng tới đâu.

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
- [ ] Phân quyền: có nhóm TC-PERM derive từ happy path; đúng quyền test mọi case (TC feature), sai quyền test happy→lỗi; gộp coarse/fine đúng (Rule 10)
- [ ] Phân quyền: role lấy từ persona trong config, không tạo runtime; TC feature không đụng persona account (Rule 10.5)
- [ ] Đa ngôn ngữ: đã confirm ngôn ngữ ở đầu; mọi TC có mục "Ngôn ngữ hiển thị" (đồng nhất, không lẫn ngôn ngữ khác); error/toast nguyên văn tiếng Việt; KHÔNG tạo nhóm TC i18n riêng (Rule 11)

**Field validation (ISTQB — skill `testcase-design`)**
- [ ] Giá trị mặc định: mọi field; màn sửa/duyệt/xoá tự tạo→verify đúng giá trị (Rule 12)
- [ ] Trường bắt buộc: 2 hướng (outfocus + submit); không bắt buộc → no error; clear-first nếu có default (Rule 13)
- [ ] Độ dài: BVA min-1/min/max/max+1; ký tự: EP valid + mỗi lớp invalid; message exact SRS (Rule 14)
- [ ] Trùng dữ liệu: tạo trước rồi test trùng, message exact; dropdown/checkbox theo selected/checked, combo → decision table (Rule 15)

**Luồng nghiệp vụ & liên quan**
- [ ] Happy path verify hậu điều kiện: thêm→search ra, sửa→mở lại đúng, xoá→mất, duyệt→đổi status (Rule 16.1)
- [ ] Có case không-dữ-liệu (empty state) + search dùng keyword từ data thật (Rule 16.3–16.4)
- [ ] Đã đọc & cập nhật `knowledge/system-features.md`; bổ sung TC ảnh hưởng chéo nếu có (Rule 17)
