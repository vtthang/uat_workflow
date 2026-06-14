import { Page, expect } from '@playwright/test';
import * as fs from 'fs';

/**
 * BasePage — khung chung cho mọi Page Object (framework, giữ ở src/).
 * Feature POM kế thừa class này (đặt ở output/pages/).
 */
export class BasePage {
  protected evidenceDir = 'output/evidence';

  constructor(public readonly page: Page) {}

  /** Set thư mục evidence cho screenshot (gọi từ spec theo module/function). */
  setEvidenceDir(dir: string): void {
    this.evidenceDir = dir;
    fs.mkdirSync(dir, { recursive: true });
  }

  /** Đợi page ổn định: domcontentloaded + ẩn loading/skeleton (best-effort, không chờ networkidle lâu vì SPA poll). */
  async waitReady(): Promise<void> {
    await this.page.waitForLoadState('domcontentloaded', { timeout: 10_000 }).catch(() => {});
    await this.page.waitForLoadState('networkidle', { timeout: 6_000 }).catch(() => {});
    await this.page
      .locator('[class*="loading"], [class*="skeleton"], [aria-busy="true"]')
      .first()
      .waitFor({ state: 'hidden', timeout: 4_000 })
      .catch(() => {});
  }

  /**
   * Screenshot evidence — full nội dung ở 100% zoom (resize viewport theo scrollHeight thực tế,
   * fullPage:false), file `[tcId][stepLabel].png`, overwrite khi chạy lại. (theo memory rule)
   */
  async screenshot(tcId: string, stepLabel: string): Promise<void> {
    if (this.page.isClosed()) return;
    await this.waitReady();
    if (this.page.isClosed()) return;
    const orig = this.page.viewportSize() ?? { width: 1920, height: 1080 };
    const scrollH = await this.page
      .evaluate(() => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight))
      .catch(() => orig.height);
    const h = Math.min(Math.max(scrollH, orig.height), 8000);
    try {
      await this.page.setViewportSize({ width: orig.width, height: h });
      await this.page.waitForTimeout(150);
      fs.mkdirSync(this.evidenceDir, { recursive: true });
      await this.page.screenshot({ path: `${this.evidenceDir}/[${tcId}][${stepLabel}].png`, fullPage: false });
    } finally {
      await this.page.setViewportSize(orig).catch(() => {});
    }
  }
}

export { expect };
