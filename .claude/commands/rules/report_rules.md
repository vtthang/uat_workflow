# Report Rules — API Response & Data Evidence

> Áp dụng khi sinh report cho mọi tính năng. Kết hợp với `test_execution_rules.md § 12e` (capture pattern).

---

## 1. Cấu trúc JSON evidence bắt buộc

Mỗi TC phải lưu đủ các file JSON vào `evidence/<env>/<portal>/<module>/<function>/`:

| File | TC type | Nội dung |
|---|---|---|
| `TC-XX_network-log.json` | **Mọi TC** | Tất cả API calls trong test (method, url, status, isMain) |
| `TC-XX_api-response.json` | Mọi TC có main API | Full response body (pagination + items) |
| `TC-XX_data-mapping.json` | TC xem danh sách (TC-01 type) | So sánh field-by-field API ↔ UI |
| `TC-XX_search-count.json` | TC tìm kiếm (kể cả không có kết quả) | keyword, apiTotal, uiRowCount, note |
| `TC-XX_filter-count.json` | TC lọc | filter, apiTotal, uiRowCount, note |

**Quan trọng:** `TC-XX_search-count.json` và `TC-XX_filter-count.json` bắt buộc có kể cả khi `apiTotal = 0`.

---

## 2. Cấu trúc từng file

### `network-log.json`
```json
{
  "tcId": "TC-LIST-XX",
  "calls": [
    { "method": "GET", "url": "https://...", "status": 200, "isMain": false },
    { "method": "GET", "url": "https://.../admin-members?page=0&size=10", "status": 200, "isMain": true }
  ]
}
```
- `isMain: true` — API chính của màn hình (list endpoint, search endpoint...)
- Sinh tự động qua `test.afterEach` — không cần gọi thủ công trong từng test

### `api-response.json`
```json
{
  "tcId": "TC-LIST-XX",
  "description": "Raw API response — <mô tả ngắn>",
  "capturedAt": "<ISO timestamp>",
  "pagination": { "totalItems": N, "totalPages": N, "page": 0, "size": 10 },
  "items": [ ... ]
}
```

### `data-mapping.json` (TC xem danh sách)
```json
{
  "tcId": "TC-LIST-XX",
  "apiTotal": 100, "uiRowCount": 10,
  "apiFirstItem": { "field1": "value", ... },
  "uiFirstRow":   { "field1": "value", ... },
  "mappingResult": [
    { "field": "Họ tên", "api": "Nguyễn A", "ui": "Nguyễn A", "match": true }
  ]
}
```

### `search-count.json`
```json
{
  "tcId": "TC-LIST-XX",
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
  "tcId": "TC-LIST-XX",
  "filter": "Trạng thái: Kích hoạt",
  "apiTotal": 85,
  "uiRowCount": 10,
  "note": "API total: 85 | UI hiển thị: 10 (trang 1)"
}
```

---

## 3. Network log — sinh tự động qua fixture + afterEach

### Trong fixture (`src/fixtures/<module>.fixture.ts`)
```typescript
// Bắt đầu log TRƯỚC goto() để capture cả initial page load
type ApiCall = { method: string; url: string; status: number; isMain: boolean };
const networkLog: ApiCall[] = [];
const networkHandler = (res: Response) => {
  const url = res.url();
  if (!/\/api\/|\/iam\/|\/v1\//.test(url)) return;
  if (/\.(js|css|png|jpg|ico|woff|svg)$/i.test(url)) return;
  networkLog.push({
    method: res.request().method(),
    url,
    status: res.status(),
    isMain: /MAIN_API_PATTERN/i.test(url) && res.request().method() === 'GET',
  });
};
page.on('response', networkHandler);
// ... goto() ...
(listPage as any).networkLog = networkLog;
await use(listPage);
page.off('response', networkHandler);
```
> Thay `MAIN_API_PATTERN` bằng regex khớp với API list chính của màn hình.

### Trong test file (describe block)
```typescript
test.afterEach(async ({ loggedInXxxList }, testInfo) => {
  const networkLog: any[] = (loggedInXxxList as any).networkLog ?? [];
  if (networkLog.length === 0) return;
  const match = testInfo.title.match(/^(TC-\d+)/);
  if (!match) return;
  const tcListId = `TC-LIST-${match[1].slice(3).padStart(2, '0')}`;
  saveJson(`${tcListId}_network-log.json`, { tcId: tcListId, calls: networkLog });
});
```

---

## 4. Report generator — cách đọc và render

### `loadJsonEvidence()` — phân loại theo suffix
```javascript
if (file.includes('network-log'))    map[tcId].networkLog   = data;
else if (file.includes('api-response'))  map[tcId].apiResponse = data;
else if (file.includes('data-mapping'))  map[tcId].mapping     = data;
else if (file.includes('search-count'))  map[tcId].searchCount = data;
else if (file.includes('filter-count'))  map[tcId].filterCount = data;
```

### `networkPanel(ev)` — render trong TC card
Hiển thị:
1. **Bảng API Calls** — method, endpoint (rút gọn), status. Row `isMain` highlight tím.
2. **Main API detail** — lấy call `isMain` CUỐI CÙNG (test action, không phải fixture load):
   ```javascript
   const mainCall = [...calls].reverse().find(c => c.isMain);
   ```
3. **Detail panel** (bên dưới bảng):
   - `mapping` → bảng so sánh field-by-field API ↔ UI
   - `searchCount` → keyword + API total + UI rows + note
   - `filterCount` → filter + API total + UI rows + note
   - `apiResponse` → collapsible `<details>` với full JSON response body

### Thứ tự ưu tiên hiển thị detail
```
mapping > searchCount > filterCount
```
Cùng với `apiResponse` luôn hiển thị (collapsible) nếu có.

---

## 5. Checklist trước khi gen report

- [ ] Mỗi TC có `network-log.json` (sinh tự động qua `afterEach`)
- [ ] TC xem danh sách: có `data-mapping.json` + `api-response.json`
- [ ] TC tìm kiếm (kể cả không có kết quả): có `search-count.json` + `api-response.json`
- [ ] TC lọc: có `filter-count.json` + `api-response.json`
- [ ] TC không có main API (sort, clear, navigate): chỉ cần `network-log.json`

---

## 6. HTML Report — Khi nào cần, khi nào không

**Mặc định pipeline KHÔNG sinh HTML report.** Output mặc định:
- `pipeline_report.md` — bảng PASS/FAIL/SKIP + link evidence
- `evidence/<TC_ID>/` — screenshots + api-calls.json

**Playwright HTML report (`playwright-report/index.html`)** chỉ sinh khi:
- User yêu cầu rõ ràng: "tạo HTML report", "mở report"
- Hoặc cần share bằng chứng dạng interactive cho stakeholder

```bash
# Sinh HTML report sau khi chạy
npx playwright show-report
# hoặc
npx playwright test --reporter=html
```

**Không tự động sinh HTML report** rồi upload Drive mà chưa hỏi user — file có thể rất lớn và user chưa cần.
