# Report Rules — API Response & Data Evidence

> Áp dụng khi sinh report cho mọi tính năng. Kết hợp với `test_execution_rules.md § 12e` (capture pattern).

---

## 1. Cấu trúc JSON evidence bắt buộc

Mỗi TC phải lưu đủ các file JSON vào `output/evidence/<env>/<portal>/<module>/<function>/`:

| File | TC type | Sinh bởi | Nội dung |
|---|---|---|---|
| `TC-LIST-01_api-calls.json` | **Mọi TC** | `teardownApiMonitor` (auto) | Tất cả API calls; main API entry có thêm `responseBody` |
| `TC-LIST-01_data-mapping.json` | TC danh sách / chi tiết / sửa / phê duyệt | Test code (manual) | fields[], mỗi field: field, apiValue, uiDisplay, match |
| `TC-LIST-02_search-count.json` | TC tìm kiếm (kể cả không có kết quả) | Test code (manual) | keyword, apiTotal, uiRowCount, note |
| `TC-LIST-06_filter-count.json` | TC lọc | Test code (manual) | filter, apiTotal, uiRowCount, note |

**Quan trọng:** `_search-count.json` và `_filter-count.json` bắt buộc có kể cả khi `apiTotal = 0`.

---

## 2. Cấu trúc từng file

### `api-calls.json` (auto — `teardownApiMonitor`)
```json
[
  { "method": "GET", "url": "https://.../me/userinfo", "status": 200, "time": 1749470894948 },
  { "method": "GET", "url": "https://.../admin-members?page=0&size=10", "status": 200, "time": 1749470895001,
    "responseBody": { "page": 0, "size": 10, "totalItems": 100, "items": [...] }
  }
]
```
- Sinh tự động bởi `teardownApiMonitor` — tên file: `{tcId}_api-calls.json`
- Main API entry có thêm `responseBody` (phân biệt qua `entry.responseBody != null`)
- TC ID theo format `TC-{FUNC}-{NN}` (xem `html_report_rules.md` mục 1)

### `data-mapping.json`
```json
{
  "tcId": "TC-LIST-01",
  "fields": [
    { "field": "Họ tên",    "apiValue": "Nguyễn Văn A",  "uiDisplay": "Nguyễn Văn A",  "match": true },
    { "field": "Email",     "apiValue": "a@example.com", "uiDisplay": "a@example.com", "match": true },
    { "field": "Trạng thái","apiValue": "ACTIVE",        "uiDisplay": "Kích hoạt",     "match": true }
  ]
}
```
> Capture từ row đầu tiên (TC danh sách) hoặc toàn bộ fields (TC chi tiết / sửa / phê duyệt).  
> `apiValue` = giá trị thô từ API response; `uiDisplay` = text hiển thị trên UI.

### `search-count.json`
```json
{
  "tcId": "TC-LIST-02",
  "keyword": "từ khóa",
  "apiTotal": 5,
  "uiRowCount": 5,
  "note": "UI hiển thị 5/5 kết quả (trang 1)"
}
```
> Case không có kết quả: `apiTotal: 0, uiRowCount: 0, note: "API total: 0 — empty state hiển thị đúng"`

### `filter-count.json`
```json
{
  "tcId": "TC-LIST-06",
  "filter": "Trạng thái: Kích hoạt",
  "apiTotal": 85,
  "uiRowCount": 10,
  "note": "API total: 85 | UI hiển thị: 10 (trang 1)"
}
```

---

## 3. API Calls log — sinh tự động qua `setupApiMonitor` + `teardownApiMonitor`

> Xem chi tiết pattern tại `test_execution_rules.md` §12 và `automation_rules.md` §12.

**Setup trong `beforeEach`:**
```typescript
import { setupApiMonitor, teardownApiMonitor, ApiLogEntry } from '../../src/utils/ApiMonitor';

const EVIDENCE_DIR = 'output/evidence/uat/admin/<module>/<function>';
const apiLog: ApiLogEntry[] = [];
const isMainApi = (res: { url(): string; request(): { method(): string } }) =>
  /\/admin-members/.test(res.url()) && res.request().method() === 'GET';

test.beforeEach(async ({ page }) => {
  apiLog.length = 0;
  setupApiMonitor(page, apiLog, isMainApi);
});
```

**Teardown trong `afterEach`:**
```typescript
test.afterEach(async ({}, testInfo) => {
  await teardownApiMonitor(apiLog, testInfo, EVIDENCE_DIR);
  // Ghi: <EVIDENCE_DIR>/TC-LIST-01_api-calls.json
  // TC ID extract bằng regex /TC-[A-Z]+-\d+/i từ testInfo.title
});
```

**Test title PHẢI bắt đầu bằng TC ID** để teardownApiMonitor extract đúng:
```typescript
test('TC-LIST-01 Danh sách hiển thị đúng khi có dữ liệu', async ({}) => { ... });
test('TC-CREATE-01 Tạo tài khoản thành công', async ({}) => { ... });
```

---

## 4. Report generator — xem `html_report_rules.md`

> Toàn bộ spec sinh HTML report (cấu trúc, TC card, API Calls table, count-box, Response body, embedding ảnh base64) được mô tả trong `html_report_rules.md`.

Tóm tắt mapping evidence → HTML:

| File evidence | Render trong TC card |
|---|---|
| `{tcId}_api-calls.json` | API Calls table; entry có `responseBody` → isMain row highlight tím + badge MAIN + `<details>` Response body |
| `{tcId}_data-mapping.json` | Data Mapping table: Field / Giá trị API / Hiển thị UI / Khớp (list/detail TCs) |
| `{tcId}_search-count.json` | count-box: Keyword + API total + UI rows + note |
| `{tcId}_filter-count.json` | count-box: Filter + API total + UI rows + note |
| `[{tcId}][{stepLabel}].png` | Screenshots carousel (embed base64) — zoom 75% trước khi chụp |

**Thứ tự render trong TC body:**
```
1. Screenshots carousel
2. API Calls table
3. count-box (search/filter TCs)
4. Data Mapping table (list/detail TCs)
5. Response body collapsible
```

---

## 4b. Nội dung report mỗi TC (BẮT BUỘC — từ feedback)

Mỗi TC card trong HTML report phải có đủ:
1. **Tiêu đề TC** (lấy từ tên TC trong file testcase, không chỉ mã TC).
2. **Full steps** (các bước) + **Expected result** (kết quả mong muốn) — lấy từ file testcase `.md`.
3. **Actual result** — kết quả thực tế (PASS/FAIL + mô tả quan sát; với case API-2xx-kèm-lỗi thì nêu rõ body).
4. **Ảnh đầy đủ** để người đọc hiểu trọn case: với action mutating phải có ảnh **trước** + **sau**; bảng phải thấy **đủ cột + pagination** (đã scroll).
5. **Data Mapping đủ mọi cột/field**; **count-box** (search/filter/pagination: total, item/page, số trang tính được vs UI).
6. **API Calls**: CHỈ Fetch/XHR, CHỈ API hành động chính (không có login/refresh/userinfo/permissions/groups). Main API có Full response collapsible.

→ Generator report đọc file testcase `.md` để lấy title/steps/expected; đọc evidence để lấy actual + ảnh + API.

## 5. Evidence Completeness Gate — BẮT BUỘC chạy TRƯỚC khi gen report

> Đây là **cổng chặn**, không phải checklist đọc cho vui. Mục tiêu: không bao giờ gen report với evidence thiếu (đã từng xảy ra: TC PASS nhưng thiếu data-mapping/full-response).

**Quy trình gate (tự động, sau Phase 3, trước Phase 4):**
1. Với **mỗi TC PASS**, kiểm tra đủ file evidence bắt buộc theo loại:
   - Mọi TC: `{tcId}_api-calls.json` tồn tại VÀ (nếu là TC có main API) có ≥1 entry `responseBody != null`.
   - TC danh sách / chi tiết / sửa / phê duyệt: `{tcId}_data-mapping.json`.
   - TC tìm kiếm (kể cả 0 kết quả): `{tcId}_search-count.json`.
   - TC lọc: `{tcId}_filter-count.json`.
2. **Thiếu bất kỳ file nào → coi TC đó là CHƯA ĐẠT** (dù đã PASS) → **re-run đúng TC đó** (không chỉ TC fail — đây là ngoại lệ của `test_execution_rules.md` Rule 15). Nếu re-run vẫn thiếu → predicate/assertion sai → sửa rồi chạy lại.
3. Chỉ khi gate **xanh hoàn toàn** mới sang Phase 4 gen report.

- [ ] Test title bắt đầu bằng TC ID đúng format `TC-{FUNC}-{NN}`
- [ ] Gate xanh: mọi TC PASS có đủ evidence (api-calls + responseBody main API + data-mapping/count theo loại)

## 6. UI ELEMENT COVERAGE GATE — đối chiếu UI thật ↔ testcase (cưỡng chế)

> Lỗi từng gặp: sinh testcase **top-down từ SRS** nên element CÓ trên UI nhưng SRS không tả (vd nút "Xóa bộ lọc", dropdown page-size) bị bỏ sót. Gate này đối chiếu **bottom-up**.

**Sau recon (locator repo đã có), TRƯỚC khi chốt testcase:** liệt kê **mọi element TƯƠNG TÁC** trong `output/locators/*.screen.json` (button / toggle / dropdown / filter / icon-action / tab / pagination...) → đối chiếu với danh sách TC. **Mỗi element phải được ≥1 TC chạm tới**, nếu chưa → **flag, bổ sung TC hoặc ghi `N/A — lý do`**. Không để element tương tác nào "trắng" coverage.

Reconcile **2 chiều**: (a) top-down SRS field/transaction → TC; (b) **bottom-up UI element (recon) → TC**.

