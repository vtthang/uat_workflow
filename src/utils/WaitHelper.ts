import { Page, Locator, expect } from '@playwright/test';

export class WaitHelper {
  /**
   * Chờ locator visible (wrapper rõ nghĩa hơn cho POM)
   */
  static async forVisible(locator: Locator, timeout?: number): Promise<void> {
    await expect(locator).toBeVisible(timeout ? { timeout } : undefined);
  }

  /**
   * Chờ locator ẩn / biến mất
   */
  static async forHidden(locator: Locator, timeout?: number): Promise<void> {
    await expect(locator).toBeHidden(timeout ? { timeout } : undefined);
  }

  /**
   * Chờ URL khớp pattern
   */
  static async forURL(page: Page, pattern: string | RegExp, timeout?: number): Promise<void> {
    await expect(page).toHaveURL(pattern, timeout ? { timeout } : undefined);
  }

  /**
   * Chờ toast / thông báo xuất hiện rồi kiểm tra exact text
   */
  static async forToast(toastLocator: Locator, expectedText: string): Promise<void> {
    await expect(toastLocator).toBeVisible();
    await expect(toastLocator).toHaveText(expectedText);
  }

  /**
   * Chờ response từ API call — dùng kết hợp với action trigger
   * Ví dụ: const resp = await WaitHelper.forResponse(page, '/api/users', async () => { await submitBtn.click(); });
   */
  static async forResponse(
    page: Page,
    urlPattern: string,
    trigger: () => Promise<void>,
    method: string = 'POST',
  ) {
    const [response] = await Promise.all([
      page.waitForResponse(
        r => r.url().includes(urlPattern) && r.request().method() === method,
      ),
      trigger(),
    ]);
    return response;
  }

  /**
   * Chờ request được gửi đi — dùng để verify trim/body payload
   */
  static async forRequest(
    page: Page,
    urlPattern: string,
    trigger: () => Promise<void>,
    method: string = 'POST',
  ) {
    const [request] = await Promise.all([
      page.waitForRequest(
        r => r.url().includes(urlPattern) && r.method() === method,
      ),
      trigger(),
    ]);
    return request;
  }
}
