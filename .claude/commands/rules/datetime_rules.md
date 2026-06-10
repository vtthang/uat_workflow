# Quy Tắc Test Datetime Field

> Bổ sung cho `test_execution_rules.md` mục 7. Áp dụng khi form có field datetime, đặc biệt khi có nhiều field ràng buộc nhau.

---

## 1. Phân tích ràng buộc trước khi thiết kế data

Datetime field thường có nhiều lớp ràng buộc đồng thời:

| Loại | Ví dụ |
|------|-------|
| Độc lập | `value > now` (phải là tương lai) |
| Tương đối | `fieldA < fieldB` (đăng trước ẩn) |
| Ngưỡng | `fieldB > fieldA + Xh` (ẩn sau đăng ít nhất X tiếng) |

**Quy tắc:** Khi test ràng buộc X, tất cả ràng buộc còn lại phải **được thỏa trong data**. Vi phạm ràng buộc khác sẽ trigger validation trước và che mất lỗi cần kiểm tra.

---

## 2. Test "giá trị quá khứ" — Không dùng waitForTimeout

API thường từ chối past datetime → tạo **future qua API, convert sang past qua UI**.

Tận dụng setup_time (~35-60s) thay vì chờ:

```
Tạo qua API:  fieldB = now + 1day + Δ  (Δ = vài giây, đảm bảo fieldB > fieldA)
Edit (sau ~60s setup): change fieldB về ngày hôm nay
→ fieldB = today + Δ < now + 60s  ✓  past
→ fieldB > fieldA                  ✓  ràng buộc tương đối vẫn thỏa
```

---

## 3. Test "vi phạm range" (fieldA > fieldB) — Tạo sẵn qua API, chỉ click 1 field

Tạo data với khoảng cách giờ sẵn, chỉ thao tác UI tối thiểu:

```
Tạo:  fieldA = ngày X 14:xx,  fieldB = ngày X+1 00:00  (A < B ✓)
Edit: click fieldB → ngày X
→ fieldB = ngày X 00:00 < fieldA = ngày X 14:xx  ✓  range error
```

**Mẹo:** Tạo fieldB = **midnight (00:00)** ngày tiếp theo. Khi click về cùng ngày fieldA, tự động tạo vi phạm range mà không cần thao tác time picker.

---

## 4. Error message — Capture actual text từ screenshot

Mỗi loại vi phạm có error text riêng. Chạy 1 lần capture thực tế trước khi hardcode assertion, không tự đoán.

---

## 5. Checklist

```
□ Liệt kê tất cả ràng buộc của field (độc lập + tương đối + ngưỡng)
□ Khi test ràng buộc X: data có thỏa mọi ràng buộc còn lại chưa?
□ API nhận past date không? → nếu không: tạo future, convert qua UI
□ Dùng setup_time (~35-60s) thay waitForTimeout
□ Có thể dùng midnight 00:00 để tạo range violation không?
□ Đã capture actual error text chưa?
```
