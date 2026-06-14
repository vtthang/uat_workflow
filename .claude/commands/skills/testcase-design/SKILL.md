---
name: testcase-design
description: Áp dụng kỹ thuật thiết kế test ISTQB (Equivalence Partitioning, Boundary Value, Decision Table, State Transition, Error Guessing, CRUD checklist) để sinh bộ testcase đủ coverage cho từng field và từng luồng nghiệp vụ. Auto-invoke khi đang viết KBKT UAT / xác định danh sách TC trong gen-uat.
allowed-tools: Read
---

# Test Case Design — Kỹ thuật Tester theo ISTQB

Mục tiêu: từ spec (SRS/TLGP) sinh ra **bộ TC đủ coverage, không thừa không thiếu**, bằng kỹ thuật chuẩn ISTQB thay vì liệt kê cảm tính. Dùng kèm `testcase_writing_rules.md` (RULE 12–17) — file này nói *kỹ thuật chọn case*, file kia nói *cách viết case*.

## 1. Chọn kỹ thuật theo loại đối tượng test

| Đối tượng | Kỹ thuật ISTQB | Sinh ra case gì |
|---|---|---|
| Field có range số/độ dài (min/max length, min/max value) | **Boundary Value Analysis (BVA)** | min-1, min, min+1, max-1, max, max+1 |
| Field có tập giá trị hợp lệ/không hợp lệ (ký tự, định dạng, email) | **Equivalence Partitioning (EP)** | 1 đại diện hợp lệ + 1 đại diện mỗi lớp không hợp lệ |
| Nhiều điều kiện kết hợp (combo field/checkbox/quyền) | **Decision Table** | mỗi tổ hợp điều kiện → 1 rule → 1 case |
| Field/đối tượng có trạng thái (duyệt/từ chối/kích hoạt/khoá) | **State Transition** | mỗi chuyển trạng thái hợp lệ + 1 chuyển không hợp lệ |
| Lỗi hay gặp theo kinh nghiệm (trùng data, khoảng trắng, paste, ký tự đặc biệt) | **Error Guessing** | case âm bổ sung |
| Luồng nghiệp vụ end-to-end | **Use-case Testing** | happy path + alternative + exception |

## 2. BVA — biên độ dài / giá trị

Với field SRS quy định `min..max` (ký tự hoặc số):

| Điểm | Giá trị | Kỳ vọng |
|---|---|---|
| Dưới biên dưới | `min-1` | ❌ error message exact SRS |
| Biên dưới | `min` | ✅ hợp lệ |
| Trên biên dưới | `min+1` | ✅ hợp lệ |
| Dưới biên trên | `max-1` | ✅ hợp lệ |
| Biên trên | `max` | ✅ hợp lệ |
| Trên biên trên | `max+1` | ❌ error message exact SRS |

Tối giản thực dụng: tối thiểu giữ **min-1, min, max, max+1**. Mỗi case invalid kiểm theo **2 hướng trigger** (outfocus + submit) — xem RULE 13.

## 3. EP — ký tự / định dạng hợp lệ

1. Xác định các **lớp tương đương** từ SRS: lớp hợp lệ + các lớp không hợp lệ (vd: chữ, số, ký tự đặc biệt, emoji, khoảng trắng).
2. Mỗi lớp → **1 case đại diện** (không cần test mọi giá trị trong lớp).
3. Nếu SRS **không ràng buộc** ký tự → 1 case "nhập đủ loại ký tự → không lỗi" (không sinh case invalid).

## 4. Decision Table — điều kiện kết hợp

Khi kết quả phụ thuộc ≥2 điều kiện (vd: checkbox A + dropdown B; quyền + trạng thái item):
1. Liệt kê điều kiện (cột) và kết quả (hàng action).
2. Mỗi cột tổ hợp T/F → 1 rule.
3. Gộp rule trùng kết quả; mỗi rule còn lại → 1 TC.

## 5. State Transition — đối tượng có vòng đời

Vẽ các trạng thái (vd: Nháp → Chờ duyệt → Đã duyệt/Từ chối → Gỡ xuống). Sinh:
- Mỗi **transition hợp lệ** → 1 TC happy (verify trạng thái đích — xem RULE 16 hậu điều kiện).
- Ít nhất 1 **transition không hợp lệ** → assert bị chặn / nút disabled.

## 6. CRUD checklist — hậu điều kiện bắt buộc (nối RULE 16)

| Thao tác | Hậu điều kiện phải verify |
|---|---|
| **Create** | Thông báo exact → item hiện ở list → search ra đúng item vừa tạo |
| **Read/Detail** | Mọi field hiển thị đúng giá trị nguồn (đối chiếu data đã tạo/API) |
| **Update** | Thông báo exact → mở lại item → mọi field đã đổi đúng |
| **Delete** | Thông báo exact → item không còn trong list (search không ra) |
| **Approve/Reject** | Thông báo exact → trạng thái item đổi đúng |

## 7. Quy trình áp dụng khi gen testcase

1. Với mỗi **field** trên màn → xác định loại (range / tập giá trị / bắt buộc / mặc định / dropdown) → áp BVA/EP/required (RULE 12–15).
2. Với mỗi **action nghiệp vụ** → áp Use-case + State Transition + CRUD checklist (RULE 16).
3. Với **kết hợp điều kiện** → Decision Table.
4. Bổ sung **Error Guessing**: trùng data (RULE 15), khoảng trắng/trim, paste, ký tự đặc biệt.
5. Đối chiếu **nghiệp vụ liên quan** từ `knowledge/system-features.md` (RULE 17) — có field/luồng nào ảnh hưởng chéo cần thêm case không.

> Nguyên tắc tối giản: đủ coverage với **số case ít nhất**. EP/BVA chính là để KHÔNG nổ tổ hợp — 1 đại diện mỗi lớp, không test thừa.
