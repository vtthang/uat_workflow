# Quy Tắc Locator Repository (Element Map theo màn hình)

> Mục tiêu: locator thu thập một lần được **lưu bền vững theo màn hình** để tái sử dụng, thay vì recon lại mỗi lần test. Áp dụng cho mọi framework.

## 1. Vai trò (Cách B — cache, KHÔNG thay POM)

- File repository là **kết quả recon đã verify gần nhất** — nguồn để sinh/đối chiếu Page Object.
- **Page Object vẫn là nơi locator chính thức chạy** (đúng POM trong `automation_rules.md`). File KHÔNG được Page class load lúc runtime.
- Quan hệ: file = "đã verify", Page class = "đang chạy". Khi lệch → file là nguồn để đồng bộ lại.

## 2. Vị trí & tổ chức

- **Mỗi màn hình một file**: `locators/<screen>.screen.json` (vd `locators/login.screen.json`).
- Tên screen theo Page class tương ứng (LoginPage → `login.screen.json`).
- KHÔNG gộp mọi màn vào một file (tránh xung đột parallel, diff bẩn, đọc thừa).

## 3. Format file (JSON)

```json
{
  "screen": "LoginPage",
  "url": "/admin/authentication",
  "framework": "playwright",
  "lastVerified": "2026-05-29",
  "elements": {
    "emailInput": {
      "primary": "getByLabel('Email Address')",
      "fallback": "input[name='email']",
      "action": "type",
      "stability": "high",
      "verifiedStates": ["loaded"],
      "note": ""
    }
  }
}
```

### Trường bắt buộc mỗi element
| Trường | Ý nghĩa |
|---|---|
| `primary` | Locator chính, theo priority `locator_strategy.md` |
| `fallback` | Locator dự phòng khi primary hỏng |
| `action` | `type` / `click` / `assert` / `check` / `select` |
| `stability` | `high` / `medium` / `low` (xem mục 4) |
| `verifiedStates` | Danh sách state đã verify (vd `loaded`, `after-invalid-login`, `modal-open`) |
| `note` | Ghi chú cho element xuất hiện có điều kiện |

## 4. Chấm điểm Stability

| Mức | Khi nào | Hành động |
|---|---|---|
| `high` | `data-testid`/`data-qa`, hoặc `getByRole`+name ổn định, hoặc `id` không auto-gen | Dùng tự tin |
| `medium` | Dựa trên text dễ đổi (i18n), `getByLabel` với label có thể đổi | Cảnh báo: test dễ vỡ khi đổi text/ngôn ngữ |
| `low` | css/xpath theo cấu trúc, không có thuộc tính ngữ nghĩa | ⚠️ Đánh dấu rủi ro cao, đề xuất team thêm `data-testid` |

`low` không bị cấm, nhưng PHẢI ghi cảnh báo trong báo cáo cuối.

## 5. Quy tắc đồng bộ (CRITICAL — tránh 2 nơi lệch nhau)

1. **Recon** (`ui-debug-agent`) → ghi/cập nhật file repository.
2. **Sinh Page class** → đọc locator TỪ file repository (không tự đoán lại).
3. **Healer** (`locator-healer`) sửa locator hỏng → cập nhật **CẢ file lẫn Page class**, và cập nhật `lastVerified`.
4. File thiếu element cần thiết → trigger recon bổ sung, KHÔNG đoán.

## 6. Khi nào đọc cache vs recon lại

- Trước khi recon một màn: **đọc file repository trước**.
  - File có đủ element cần + `verifiedStates` phù hợp với case → **dùng luôn, bỏ qua mở browser**.
  - File thiếu element / thiếu state cần / `lastVerified` quá cũ (>14 ngày, tùy team) → recon bổ sung phần thiếu.
- Mục tiêu: mỗi màn chỉ recon đầy đủ **một lần**, các case sau tái sử dụng.
