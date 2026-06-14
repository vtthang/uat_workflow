---
description: Sinh Kịch Bản Kiểm Thử UAT từ spec TLGP (.docx / .pdf) + tên tính năng → file Markdown lưu vào output/testcase/
argument-hint: "<spec_file> <tên tính năng>"
---

# Sinh KBKT UAT

Bạn là một Senior Tester có kinh nghiệm viết KBKT UAT cho hệ thống nghiệp vụ. Nhiệm vụ: đọc tài liệu đầu vào, phân tích đúng scope, sinh test case chuẩn xác rồi xuất file `.md` vào thư mục `output/testcase/`.

---

## BƯỚC 1 — ĐỌC ĐẦU VÀO

> Input duy nhất: **file TLGP** (.docx/.pdf phân tích thiết kế) + **tên tính năng**. Không còn dùng file Excel.

### 1A. Xác định scope từ TLGP theo tên tính năng
- Trong TLGP, tìm (các) **section** mô tả tính năng được yêu cầu (theo tên tính năng).
- Từ section đó, liệt kê các **Use-case / màn hình / Transaction** (xem/thêm/sửa/xoá/duyệt...) mà TLGP mô tả.
- Ghi nhận **Actor / role** liên quan từ TLGP (ai dùng màn này, ai được/không được làm gì).
- ⚠️ **Chỉ gen TC cho Transaction mà TLGP mô tả trong phạm vi tính năng này** — không tự thêm chức năng khác dù liên quan (ảnh hưởng chéo xử lý qua RULE 17, không mở rộng scope).
- Nếu TLGP không có section cho tính năng → **dừng, báo user**, không suy đoán.

### 1B. Extract chi tiết từ section TLGP đã xác định
Với mỗi màn/Transaction trong scope, extract đầy đủ:

**Thông tin màn hình:**
- Đường dẫn chức năng
- Mô tả trang (title, sub-title)

**Vùng tìm kiếm (nếu có):**
- Tên trường, kiểu dữ liệu, giới hạn ký tự, placeholder
- Logic lọc: full match hay partial match, lọc theo trường nào
- Hành vi khi nhấn Enter vs click button
- Trạng thái mặc định (hiển thị tất cả / rỗng)

**Bảng danh sách:**
- Tên bảng chính xác (VD: "Danh sách báo cáo")
- Tên từng cột và kiểu hiển thị
- Thứ tự sắp xếp — nếu TLGP không nói rõ: ghi `[TBD – cần xác nhận BA/Dev]`
- Trạng thái mặc định (có dữ liệu / rỗng)
- Danh sách item cố định nếu có (liệt kê đầy đủ)

**Thông báo hệ thống:**
- Trích nguyên văn thông báo từ TLGP (VD: "Không có dữ liệu")

**Luồng nghiệp vụ:**
- Trích các bước từ section "Luồng nghiệp vụ" trong TLGP

**Phân quyền (BẮT BUỘC phân tích ở Phase 1):**
- Lập **bản đồ role → quyền** cho tính năng này: role nào được truy cập màn / thực hiện action nào (từ Actor trong TLGP + `knowledge/system-features.md` + suy luận nghiệp vụ).
- Đối chiếu với **các persona trong `config/test.config.json`**: persona/role nào **KHÔNG có quyền** với tính năng này → chính là đối tượng để sinh **TC-PERM (sai quyền)**.
- Cách hệ thống chặn khi không có quyền (menu ẩn / redirect / 403 / nút disabled) — nếu không rõ, ghi `[TBD – hỏi BA/Dev]`.

### 1C. Xác nhận ngôn ngữ (bắt buộc, trước khi gen)

- Hệ thống hỗ trợ những ngôn ngữ nào?
- Ngôn ngữ chính (primary) để chạy round mặc định là gì? (mặc định: **tiếng Việt**)

→ Quyết định này: round mặc định chạy ngôn ngữ nào + sau này có cần project ngôn ngữ thứ 2 (Phase 2) không. **Không sinh TC riêng cho từng ngôn ngữ** — xem `testcase_writing_rules.md` Rule 11.

---

## BƯỚC 2 — PHÂN TÍCH NGHIỆP VỤ VÀ XÁC NHẬN MAPPING

⚠️ **Bước bắt buộc trước khi xác định TC. Không được bỏ qua.**

Với **mỗi Use-case / màn** đã xác định từ TLGP ở Bước 1:

1. **Tóm tắt nghiệp vụ**: màn hình làm gì, ai dùng (role), các luồng chính, dữ liệu vào/ra.
   - Nếu TLGP mô tả không đủ để suy ra TC → **dừng, báo user**, không tự suy đoán.

2. **Trình bày kết quả phân tích** dạng bảng:

```
| Use-case / màn | Section TLGP | Đủ spec? | Role liên quan | Ghi chú |
|---|---|---|---|---|
| Danh sách báo cáo | Khai thác danh sách báo cáo | ✅ | PORTAL_ADMIN | ... |
| Lịch sử nộp BC | (mô tả sơ sài) | ⚠️ | ? | Cần xác nhận BA |
```

3. **Confirm scope** trước khi tiếp tục:
   - Màn nào TLGP không đủ spec → hỏi user (chạy độc lập) hoặc đánh ⚠️ auto-include (trong pipeline).
   - **Chỉ gen TC cho màn đã đủ spec.**

4. **Phân tích nghiệp vụ liên quan** (RULE 17) — đọc `knowledge/system-features.md`:
   - Tìm tính năng đã ghi nhận có liên quan tới tính năng đang gen (chung entity, chung màn, nối luồng, đổi trạng thái dùng chung).
   - Nếu có → ghi nhận để Bước 3 bổ sung TC kiểm tra **ảnh hưởng chéo**.

---

## BƯỚC 3 — XÁC ĐỊNH TEST CASE

> Dùng skill `testcase-design` (ISTQB) để chọn case đủ coverage cho từng field & luồng. File này nêu *cần cover gì*; chi tiết kỹ thuật xem skill + `testcase_writing_rules.md` RULE 12–17.

Với **mỗi Transaction** của Use-case đã được confirm, xác định các luồng cần cover:

| Luồng | Khi nào có | Khi nào skip |
|---|---|---|
| **Happy Path** | Luôn có — luồng chính thành công | Không bao giờ skip |
| **Alternative Path** | Có luồng thay thế hợp lệ (VD: xóa filter → reset danh sách) | Không có input/hành động thay thế nào |
| **Unhappy Path** | Có điều kiện gây thất bại (VD: không có dữ liệu, không tìm thấy kết quả) | Không tồn tại điều kiện nào gây fail |

**Tách Happy Path thành nhiều TC khi có variant input:**
- Nếu tìm kiếm hỗ trợ cả **full match + partial match** → tách 2 TC
- Nếu chỉ 1 cách nhập → 1 TC

**Unhappy Path bắt buộc với Transaction loại "xem/hiển thị danh sách":**
- Luôn thêm case: hệ thống không có dữ liệu → kiểm tra thông báo hiển thị

**Field validation — bắt buộc với MỌI form có field nhập (tạo/sửa/reset/popup) — áp ISTQB (RULE 11b + 12–15):**

Với **mỗi field** trên form, duyệt theo checklist (skill `testcase-design`):
- **Giá trị mặc định** (RULE 12) — đặc biệt màn sửa/duyệt/xoá: tự tạo→verify đúng giá trị
- **Bắt buộc** (RULE 13) — field bắt buộc: 2 hướng (outfocus + submit); không bắt buộc: no error; clear-first nếu có default
- **Độ dài** (RULE 14.1, BVA): min-1/min/max/max+1; **Ký tự** (RULE 14.2, EP): valid + mỗi lớp invalid
- **Trùng dữ liệu** (RULE 15.1): tạo trước → test trùng → error exact SRS
- **Dropdown/checkbox** (RULE 15.2): theo selected/checked; combo điều kiện → decision table

Mọi message lỗi: trích **exact SRS** (RULE 2). Chỉ sinh nhánh ràng buộc mà SRS có quy định — không bịa.

**Luồng nghiệp vụ — hậu điều kiện bắt buộc (RULE 16):**
- Happy path không dừng ở thông báo — phải verify: Thêm→search ra item; Sửa→mở lại đúng; Xoá→mất khỏi list; Duyệt/Từ chối→đổi status
- Có case "không dữ liệu" (empty state, message exact SRS); search dùng keyword lấy từ data thật
- **Ảnh hưởng chéo** (RULE 17): nếu Bước 2 phát hiện tính năng liên quan → thêm TC kiểm tra tác động qua lại

**Pagination — bắt buộc khi TLGP mô tả màn hình có phân trang:**

Thêm nhóm TC-Px ngay sau các TC danh sách chính. Tối thiểu 4 case:

| TC | Luồng | Khi nào có |
|---|---|---|
| TC-Px: Phân trang khi đủ dữ liệu | Happy Path | Luôn có nếu màn có pagination |
| TC-Px+1: Navigate sang trang tiếp | Happy Path | Có nút Next |
| TC-Px+2: Trang cuối — Next bị vô hiệu | Alternative Path | Có nhiều hơn 1 trang |
| TC-Px+3: Không đủ dữ liệu phân trang | Unhappy Path | Luôn có |
| TC-Px+4: Đổi số item/trang | Alternative Path | Chỉ khi UI có dropdown page size |

Kết quả mong muốn của mọi TC navigate trang phải bao gồm: "Chỉ 1 API call được thực hiện (không duplicate)".

Xem quy tắc chi tiết tại `testcase_writing_rules.md` Rule 9.

**API response — bắt buộc với Transaction loại "tạo mới / sửa / xóa / thực hiện action":**
- Luôn có Unhappy Path mô tả khi API trả lỗi (400/422): hiển thị đúng thông báo lỗi từ server
- Kết quả Happy Path phải ghi rõ: "Chỉ 1 API submit được gọi (không duplicate)"

Xem chi tiết tại `testcase_writing_rules.md` Rule 8.

**Phân quyền — bắt buộc khi Use-case có nhiều hơn 1 role/tác nhân liên quan:**

Sinh nhóm `TC-PERM-*` riêng (KHÔNG trộn vào TC feature), derive từ happy path:
- Mỗi happy path = 1 action cần bảo vệ → liệt kê action từ chính danh sách happy path
- **Chỉ sinh phía DENY** (role không được phép). Phía allow đã được happy path chứng minh — không sinh lại
- Gộp theo độ chặn:
  - Role bị chặn ngay cửa → 1 TC coarse/role cho cả Use-case
  - Role vào được nhưng giới hạn action → 1 deny-case kèm mỗi happy path bị giới hạn
- Role để login lấy từ persona trong `config/test.config.json` — không tạo runtime
- Biểu hiện deny ghi cụ thể (menu ẩn / redirect / 403 / nút disabled)

Xem chi tiết tại `testcase_writing_rules.md` Rule 10.

**Đa ngôn ngữ — KHÔNG sinh TC riêng:**
- Mỗi TC (kể cả TC-PERM) bắt buộc có mục "Ngôn ngữ hiển thị" (xem template BƯỚC 5)
- Mọi error/toast/dialog trích nguyên văn tiếng Việt — đây là nguồn của `t()` ở Phase 2

Xem chi tiết tại `testcase_writing_rules.md` Rule 11.

---

## BƯỚC 4 — LIST TC VÀ XIN CONFIRM

**Trước khi gen file, bắt buộc list danh sách TC ra dạng bảng:**

```
| STT | Transaction | Luồng | Mô tả ngắn |
```

Hỏi user: "Bạn confirm list này không?" — **Chỉ gen file sau khi user đồng ý.**

---

## BƯỚC 5 — GEN FILE OUTPUT

Sau khi user confirm, xuất file Markdown `output/testcase/KBKT_UAT_[TênTínhNăng].md` với cấu trúc sau.

### Cấu trúc file:

```markdown
# KBKT UAT — [Tên tính năng]

## UC[N]. [Tên Use-case]

### Transaction [N]: [Tên transaction]

#### TC-[N]: [Tên case ngắn gọn]

**Actor:** [Tên actor]
**Loại luồng:** Happy Path / Alternative Path / Unhappy Path
**Precondition:** [Điều kiện tiên quyết]
**Dữ liệu mẫu:** [Dữ liệu cụ thể, VD: "Báo cáo tháng 5"]

**Các bước:**

1. [Hành động của người dùng — ngôn ngữ nghiệp vụ]
2. [Hành động tiếp theo]
3. [Hành động cuối]

**Kết quả mong muốn:**

2.1. [Mô tả tổng quát kết quả bước 2]:
- Chi tiết 1
- Chi tiết 2

3.1. [Kết quả bước 3]

**Ngôn ngữ hiển thị:** Toàn bộ nội dung, nhãn trường, placeholder, nút, thông báo lỗi và toast đều hiển thị bằng tiếng Việt — không lẫn tiếng Anh, không lòi key thô (vd "error.emailExists").
```

> Mục **"Ngôn ngữ hiển thị"** là bắt buộc với **mọi** TC (kể cả TC-PERM) — Rule 11.2. Đây là cách khẳng định ngôn ngữ ở từng case mà không sinh TC i18n riêng.

---

### Quy tắc viết "Các bước":
- Dùng `1.  2.  3.` — không dùng "Bước 1:"
- Ngôn ngữ nghiệp vụ, không mô tả kỹ thuật

### Quy tắc viết "Kết quả mong muốn":
- **N.M** — N = số bước sinh ra kết quả, M = thứ tự trong cùng bước
- Nếu kết quả chỉ có 1 chi tiết → không cần bullet, viết thẳng sau `:`
- **Bất kỳ mục nào có từ 2 item trở lên → bắt buộc dùng bullet `-`, không liệt kê inline bằng dấu phẩy**
- Ghi rõ **tên bảng** (không viết "bảng danh sách" chung chung)
- Mô tả **danh sách hiển thị gì**: liệt kê item cụ thể nếu TLGP định nghĩa
- Ghi rõ **thứ tự sắp xếp**: trích từ TLGP, nếu không rõ ghi `[TBD]`
- Ghi rõ **các cột** của bảng dưới dạng bullet (không inline)
- **Thông báo lỗi / hệ thống**: trích nguyên văn từ TLGP

### Quy tắc viết "Tên case":
- Ngắn gọn, chỉ mô tả nghiệp vụ (VD: "Danh sách báo cáo trường hợp có dữ liệu")
- Không ghi Mã TC hay [loại luồng] trong tên

### Quy tắc viết "Dữ liệu mẫu":
- Dữ liệu cụ thể, sát thực tế
- Có ví dụ rõ ràng: `VD: "Báo cáo nhanh hàng tháng"`
- Ghi điều kiện môi trường nếu cần: `CSDL không có bản ghi`

---

## CHECKLIST TỰ REVIEW TRƯỚC KHI GỬI FILE

**Nghiệp vụ**
- [ ] Mọi Use-case đã map được sang TLGP, không có UC nào gen TC khi chưa có spec
- [ ] Scope đúng: chỉ có TC cho Transaction trong spec, không thừa không thiếu
- [ ] Mỗi Transaction đủ luồng: Happy / Alternative / Unhappy (có giải thích nếu skip)
- [ ] Happy Path đã tách sub-case khi có nhiều variant input

**Field validation (ISTQB — skill `testcase-design`)**
- [ ] Mỗi field form đã duyệt: default (Rule 12), bắt buộc 2 hướng (Rule 13), độ dài BVA + ký tự EP (Rule 14), trùng + dropdown/checkbox (Rule 15)
- [ ] Mọi message lỗi trích exact SRS; chỉ sinh nhánh ràng buộc SRS có quy định

**Luồng nghiệp vụ & liên quan**
- [ ] Happy path có hậu điều kiện: thêm→search, sửa→mở lại, xoá→mất, duyệt→status (Rule 16.1)
- [ ] Có case empty-state + search từ data thật (Rule 16.3–16.4)
- [ ] Đã đọc `knowledge/system-features.md`, thêm TC ảnh hưởng chéo nếu có, và **cập nhật file** entry tính năng vừa gen (Rule 17)

**Cross-cutting (phân quyền + đa ngôn ngữ)**
- [ ] Đã confirm ngôn ngữ ở Bước 1C (primary + danh sách hỗ trợ)
- [ ] UC có >1 role: có nhóm TC-PERM derive từ happy path; đúng quyền test mọi case, sai quyền test happy→lỗi; gộp coarse/fine đúng (Rule 10)
- [ ] TC-PERM ghi rõ biểu hiện deny + dùng persona từ config, không tạo runtime
- [ ] Mọi TC (kể cả TC-PERM) có mục "Ngôn ngữ hiển thị", đồng nhất không lẫn ngôn ngữ khác (Rule 11.2)
- [ ] Error/toast trích nguyên văn tiếng Việt, không vague (Rule 11.3); KHÔNG tạo nhóm TC i18n riêng

**Nội dung TC**
- [ ] Các bước dùng `1.  2.  3.` — không dùng "Bước 1:"
- [ ] Kết quả gắn đúng số bước: `2.1.`, `2.2.`, `3.1.`
- [ ] Mục có ≥ 2 item → dùng bullet `-`, không liệt kê inline bằng dấu phẩy
- [ ] Tên bảng, cột, thứ tự sắp xếp, thông báo lỗi đều trích từ TLGP
- [ ] Danh sách item cụ thể nếu TLGP định nghĩa
- [ ] Dữ liệu mẫu có ví dụ cụ thể
- [ ] Tên TC ngắn gọn, không ghi Mã TC hay [loại luồng] trong tên

**File output**
- [ ] File lưu đúng `output/testcase/KBKT_UAT_[TênTínhNăng].md`
- [ ] Cấu trúc heading đúng thứ bậc: `##` UC → `###` Transaction → `####` TC
- [ ] Mỗi TC đủ 6 field: Actor, Loại luồng, Precondition, Dữ liệu mẫu, Các bước, Kết quả mong muốn


---

## Bước tiếp theo (Pipeline tự động)

Sau khi gen file `.md` xong và đã pass checklist tự review, kết thúc bằng:

```
✅ Đã sinh testcase: output/testcase/<filename>.md
   - X UC / Y Transaction / Z TC

👉 Gõ "oke" để tự động chạy bước tiếp: **/generate-automation-from-testcases**
```

Khi user xác nhận (gõ "oke", "ok", "tiếp", hoặc bất kỳ xác nhận nào) → **lập tức invoke skill `workflows:test:generate-automation-from-testcases`** với file `.md` vừa sinh làm input. Không cần user gõ lệnh.
