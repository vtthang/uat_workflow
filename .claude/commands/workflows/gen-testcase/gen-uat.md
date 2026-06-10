---
description: Sinh Kịch Bản Kiểm Thử UAT từ spec (Excel / docx / pdf) → file Markdown lưu vào testcase/
argument-hint: "<spec_file> <tên tính năng>"
---

# Sinh KBKT UAT

Bạn là một Senior Tester có kinh nghiệm viết KBKT UAT cho hệ thống nghiệp vụ. Nhiệm vụ: đọc tài liệu đầu vào, phân tích đúng scope, sinh test case chuẩn xác rồi xuất file `.md` vào thư mục `testcase/`.

---

## BƯỚC 1 — ĐỌC ĐẦU VÀO

### 1A. Đọc file Excel (file yêu cầu / dự toán)
- Xác định **sheet D7.x.QLRR** hoặc sheet chứa Use-case của tính năng cần gen
- Tìm **Use-case** tương ứng với tính năng được yêu cầu
- Liệt kê **tất cả Transaction** (dòng con) thuộc Use-case đó từ cột "Giao dịch (Transaction)"
- Ghi nhận **Actor** từ cột "Tên tác nhân"
- ⚠️ **Chỉ gen TC cho Transaction được định nghĩa trong Use-case này** — không tự thêm UC khác, không gen TC cho chức năng khác dù liên quan

### 1B. Đọc TLGP (file phân tích thiết kế .docx)
Tìm section tương ứng với từng Use-case. Extract đầy đủ:

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

---

## BƯỚC 2 — PHÂN TÍCH NGHIỆP VỤ VÀ XÁC NHẬN MAPPING

⚠️ **Bước bắt buộc trước khi xác định TC. Không được bỏ qua.**

Với **mỗi Use-case** trong Excel:

1. **Map sang section TLGP**: Tìm section trong TLGP tương ứng với Use-case đó
   - Nếu **tìm thấy** → tóm tắt lại: màn hình làm gì, ai dùng, các luồng chính, dữ liệu vào/ra
   - Nếu **không tìm thấy** → **dừng ngay, báo với user**, không tự suy đoán, không gen TC

2. **Trình bày kết quả phân tích** dạng bảng:

```
| Use-case (Excel) | Section TLGP | Có spec? | Ghi chú |
|---|---|---|---|
| UC1. Khai thác DS báo cáo | Khai thác danh sách báo cáo | ✅ | ... |
| UC2. Quản lý Lịch sử nộp BC | ??? | ❌ | Không tìm thấy section tương ứng |
```

3. **Hỏi user confirm mapping** trước khi tiếp tục:
   - Use-case nào không có TLGP → hỏi user muốn skip hay chờ spec
   - Use-case nào mapping không chắc chắn → hỏi user xác nhận
   - **Chỉ tiếp tục sang Bước 3 với những Use-case đã có TLGP và được confirm**

---

## BƯỚC 3 — XÁC ĐỊNH TEST CASE

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

---

## BƯỚC 4 — LIST TC VÀ XIN CONFIRM

**Trước khi gen file, bắt buộc list danh sách TC ra dạng bảng:**

```
| STT | Transaction | Luồng | Mô tả ngắn |
```

Hỏi user: "Bạn confirm list này không?" — **Chỉ gen file sau khi user đồng ý.**

---

## BƯỚC 5 — GEN FILE OUTPUT

Sau khi user confirm, xuất file Markdown `testcase/KBKT_UAT_[TênTínhNăng].md` với cấu trúc sau.

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
```

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

**Nội dung TC**
- [ ] Các bước dùng `1.  2.  3.` — không dùng "Bước 1:"
- [ ] Kết quả gắn đúng số bước: `2.1.`, `2.2.`, `3.1.`
- [ ] Mục có ≥ 2 item → dùng bullet `-`, không liệt kê inline bằng dấu phẩy
- [ ] Tên bảng, cột, thứ tự sắp xếp, thông báo lỗi đều trích từ TLGP
- [ ] Danh sách item cụ thể nếu TLGP định nghĩa
- [ ] Dữ liệu mẫu có ví dụ cụ thể
- [ ] Tên TC ngắn gọn, không ghi Mã TC hay [loại luồng] trong tên

**File output**
- [ ] File lưu đúng `testcase/KBKT_UAT_[TênTínhNăng].md`
- [ ] Cấu trúc heading đúng thứ bậc: `##` UC → `###` Transaction → `####` TC
- [ ] Mỗi TC đủ 6 field: Actor, Loại luồng, Precondition, Dữ liệu mẫu, Các bước, Kết quả mong muốn


---

## Bước tiếp theo (Pipeline tự động)

Sau khi gen file `.md` xong và đã pass checklist tự review, kết thúc bằng:

```
✅ Đã sinh testcase: testcase/<filename>.md
   - X UC / Y Transaction / Z TC

👉 Gõ "oke" để tự động chạy bước tiếp: **/generate-automation-from-testcases**
```

Khi user xác nhận (gõ "oke", "ok", "tiếp", hoặc bất kỳ xác nhận nào) → **lập tức invoke skill `workflows:test:generate-automation-from-testcases`** với file `.md` vừa sinh làm input. Không cần user gõ lệnh.
