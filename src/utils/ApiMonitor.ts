import * as fs from 'fs';
import { Page } from '@playwright/test';
import type { TestInfo } from '@playwright/test';

export interface ApiLogEntry {
  method: string;
  url: string;
  status: number;
  time: number;
  responseBody?: unknown;
}

type ResponseLike = {
  url(): string;
  status(): number;
  request(): { method(): string };
  json(): Promise<unknown>;
};

/** API bootstrap (đăng nhập → vào màn) — KHÔNG ghi vào evidence (Rule 21.1). */
const BOOTSTRAP_API = /auth\/(login|refresh|logout)|me\/userinfo|me\/permissions|groups\/checkbox|\/iam\/me\b|notifications?(\b|\/|\?)/i;

/**
 * Gắn listener lên page để capture mọi API response trong suốt test.
 * - Bỏ qua static assets (js/css/font/image).
 * - Với main API (isMainApi = true): parse và lưu responseBody.
 *
 * Gọi trong beforeEach({ page }) — TRƯỚC khi bất kỳ action nào.
 */
export function setupApiMonitor(
  page: Page,
  apiLog: ApiLogEntry[],
  isMainApi: (res: ResponseLike) => boolean,
): void {
  page.on('response', async res => {
    // CHỈ Fetch/XHR (Rule 21.1) — bỏ document/script/css/img/font
    const rtype = (res.request() as { resourceType?: () => string }).resourceType?.();
    if (rtype && rtype !== 'fetch' && rtype !== 'xhr') return;
    if (/\.(js|css|png|jpg|jpeg|ico|woff2?|ttf|eot|svg|map|gif|webp)$/i.test(res.url())) return;
    if (/\/(static|assets|_next|__webpack)\//.test(res.url())) return;
    // Bỏ API bootstrap (login → vào màn)
    if (BOOTSTRAP_API.test(res.url())) return;

    const entry: ApiLogEntry = {
      method: res.request().method(),
      url: res.url(),
      status: res.status(),
      time: Date.now(),
    };

    if (isMainApi(res)) {
      entry.responseBody = await res.json().catch(() => null);
    }

    apiLog.push(entry);
  });
}

/**
 * Ghi evidence sau mỗi test (cả PASS và FAIL):
 *   <evidenceDir>/<slug>_api-calls.json  — toàn bộ calls;
 *                                           main API entry có thêm responseBody,
 *                                           background calls thì responseBody = undefined.
 *
 * Nếu test FAIL → attach thêm api-calls.txt vào Playwright report.
 *
 * Gọi trong afterEach({}, testInfo) — LUÔN reset apiLog cuối hàm.
 */
export async function teardownApiMonitor(
  apiLog: ApiLogEntry[],
  testInfo: TestInfo,
  evidenceDir: string,
): Promise<void> {
  try {
    if (apiLog.length > 0) {
      fs.mkdirSync(evidenceDir, { recursive: true });
      const tcId = (testInfo.title.match(/TC-[A-Z]+-\d+/i) ?? [testInfo.title.replace(/[^a-zA-Z0-9]/g, '_').slice(0, 30)])[0];

      fs.writeFileSync(
        `${evidenceDir}/${tcId}_api-calls.json`,
        JSON.stringify(apiLog, null, 2),
      );
    }

    if (testInfo.status === 'failed' && apiLog.length > 0) {
      const logContent = apiLog
        .map(e =>
          `[${e.method}] ${e.url} → ${e.status}` +
          (e.responseBody ? `\n  body: ${JSON.stringify(e.responseBody).slice(0, 300)}` : ''),
        )
        .join('\n');
      await testInfo.attach('api-calls.txt', {
        body: Buffer.from(logContent),
        contentType: 'text/plain',
      });
    }
  } finally {
    apiLog.length = 0;
  }
}

/**
 * Phát hiện duplicate API call trong khoảng withinMs milliseconds.
 * Throw Error nếu có duplicate — dùng trong test sau khi trigger action.
 */
export function assertNoDuplicateApiCall(log: ApiLogEntry[], withinMs = 1000): void {
  const seen = new Map<string, number>();
  const duplicates: string[] = [];
  for (const entry of log) {
    if (!/\/api\//.test(entry.url)) continue;
    if (entry.method === 'GET') continue; // chỉ check write ops (POST/PUT/PATCH/DELETE)
    const key = `${entry.method}:${entry.url}`;
    const prev = seen.get(key);
    if (prev !== undefined && entry.time - prev < withinMs) {
      duplicates.push(`DUPLICATE: ${key} (${entry.time - prev}ms apart)`);
    }
    seen.set(key, entry.time);
  }
  if (duplicates.length > 0) {
    throw new Error(`API duplicate calls detected:\n${duplicates.join('\n')}`);
  }
}
