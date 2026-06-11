import { Page } from '@playwright/test';
import { account, apiConfig, loadConfig } from '../config';

export interface ArticleData {
  id: string;
  title: string;
  slug: string;
  authorName: string;
  summary: string;
  content: string;
  /** Chỉ có khi tạo bằng createLuuNhapWithToggles */
  notificationName?: string;
  notificationNote?: string;
  notificationContent?: string;
  notificationPurpose?: string;
  notificationPayload?: string;
  actionButtonName?: string;
  actionButtonUrl?: string;
  actionButtonLink?: string;
}

export class ArticleApiHelper {
  private readonly page: Page;
  private readonly cfg = apiConfig();
  private token: string | null = null;
  private tokenExpiry = 0;

  constructor(page: Page) {
    this.page = page;
  }

  private async getToken(): Promise<string> {
    const now = Date.now() / 1000;
    if (this.token && now < this.tokenExpiry - 30) return this.token;

    const admin = account('portalAdmin');
    // Email → dùng trực tiếp; phone VN (bắt đầu 0) → chuyển sang +84
    const identifier = admin.username.includes('@')
      ? admin.username
      : `+84${admin.username.startsWith('0') ? admin.username.slice(1) : admin.username}`;

    const result = await this.page.evaluate(
      async ({ apiBase, loginPath, identifier, password, portalCode }) => {
        const resp = await fetch(`${apiBase}${loginPath}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Portal-Code': portalCode,
          },
          body: `identifier=${encodeURIComponent(identifier)}&password=${encodeURIComponent(password)}`,
        });
        const data = await resp.json();
        return { status: resp.status, data };
      },
      {
        apiBase: this.cfg.baseURL,
        loginPath: this.cfg.auth.loginEndpoint,
        identifier,
        password: admin.password,
        portalCode: this.cfg.portalCode,
      }
    );

    if (result.status !== 200) throw new Error(`Login API failed [${result.status}]`);

    const data = result.data as Record<string, unknown>;
    const inner = (data?.data ?? {}) as Record<string, unknown>;
    const token =
      (data?.access_token as string) ||
      (data?.token as string) ||
      (data?.accessToken as string) ||
      (inner?.access_token as string) ||
      (inner?.token as string) ||
      (inner?.accessToken as string) ||
      (inner?.tokenValue as string);
    if (!token) throw new Error('Token not found in login response');

    this.token = token;
    this.tokenExpiry = now + 3600;
    return token;
  }

  private async post(path: string, payload: object): Promise<{ status: number; data: unknown }> {
    const token = await this.getToken();
    return this.page.evaluate(
      async ({ apiBase, path, payload, token, portalCode }) => {
        const resp = await fetch(`${apiBase}${path}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
            'X-Portal-Code': portalCode,
          },
          body: JSON.stringify(payload),
        });
        const data = await resp.json();
        return { status: resp.status, data };
      },
      { apiBase: this.cfg.baseURL, path, payload, token, portalCode: this.cfg.portalCode }
    );
  }

  private isoDate(offsetMs = 0): string {
    return new Date(Date.now() + offsetMs).toISOString();
  }

  private toSlug(title: string): string {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 100);
  }

  /** Tạo bài Chờ duyệt. publishOffsetMs > 0 = tương lai, = 0 = ngay bây giờ (quá hạn sau vài phút). */
  async createChoDuyet(label: string, publishOffsetMs = 24 * 3600_000): Promise<ArticleData> {
    const ts = Date.now();
    const title = `${label}_${ts}`;
    const { fixtures } = this.cfg;

    const payload = {
      title,
      slug: this.toSlug(title),
      categoryId: fixtures.categoryId,
      scheduledPublishDate: this.isoDate(publishOffsetMs),
      scheduledUnpublishDate: this.isoDate(30 * 24 * 3600_000),
      authorName: `Auto ${label}`,
      summary: `Tóm tắt tự động ${label}`,
      content: `<p>Nội dung test tự động — ${label}</p>`,
      isSubmitForApproval: true,
      sendNotification: false,
      actionButton: false,
      thumbnailUrl: fixtures.thumbnailUrl,
      thumbnailPath: fixtures.thumbnailPath,
      thumbnailImage: fixtures.thumbnailMeta,
    };

    const result = await this.post(this.cfg.endpoints.articles.create, payload);
    if (result.status !== 200 && result.status !== 201) {
      throw new Error(`Create article failed [${result.status}]: ${JSON.stringify(result.data)}`);
    }

    const resData = result.data as Record<string, unknown>;
    const inner = ((resData?.data ?? resData) as Record<string, unknown>);
    const id = (inner?.id as string) ?? '';
    if (!id) throw new Error(`Article ID missing in response: ${JSON.stringify(result.data)}`);
    return { id, title, slug: '', authorName: '', summary: '', content: '' };
  }

  /** Tạo bài Lưu nháp với: đăng = tomorrow 14:xx, ẩn = midnight của ngày sau đăng (June 3 00:00).
   * Khi edit: chỉ cần click June 2 trong calendar → ẩn = June 2 00:00 → đăng(14:xx) > ẩn(00:00) = range error. */
  async createLuuNhapRangeError(label: string): Promise<ArticleData> {
    const publishOffset = 24 * 3600_000; // đăng = June 2 14:xx
    // ẩn = midnight of day AFTER đăng (June 3 00:00:00)
    const tomorrowDate = new Date(Date.now() + publishOffset);
    const dayAfterDate = new Date(tomorrowDate);
    dayAfterDate.setDate(dayAfterDate.getDate() + 1);
    dayAfterDate.setHours(0, 0, 0, 0);
    const unpublishOffset = dayAfterDate.getTime() - Date.now();
    return this.createLuuNhap(label, publishOffset, unpublishOffset);
  }

  /** Tạo bài với đăng = midnight June 2 (00:00), dùng cho S47.
   * Khi edit: click June 1 → đăng = June 1 00:00 < now (16:xx) → toast past date. */
  async createLuuNhapPastPublish(label: string): Promise<ArticleData> {
    // đăng = midnight of tomorrow (June 2 00:00)
    const tomorrow = new Date(Date.now() + 24 * 3600_000);
    tomorrow.setHours(0, 0, 0, 0);
    const publishOffset = tomorrow.getTime() - Date.now();
    return this.createLuuNhap(label, publishOffset);
  }

  /** Tạo bài cho S53:
   * đăng = now, ẩn = now + 1day + 1s (ẩn > đăng, cả hai future khi tạo).
   * Khi edit (sau ~35s setup): click ẩn - 1 day → ẩn = today + 1s < now → past.
   * ẩn (today+1s) > đăng (today) ✓ → không bị lỗi range, chỉ bị lỗi past. */
  async createLuuNhapPastUnpublish(label: string): Promise<ArticleData> {
    const publishOffset = 0;                              // đăng = now
    const unpublishOffset = 24 * 3600_000 + 1_000;       // ẩn = tomorrow + 1s
    return this.createLuuNhap(label, publishOffset, unpublishOffset);
  }

  /** Tạo bài Lưu nháp (isSubmitForApproval=false). Dùng cho test 1.1.1.11 Chỉnh sửa. */
  async createLuuNhap(label: string, publishOffsetMs = 24 * 3600_000, unpublishOffsetMs = 30 * 24 * 3600_000): Promise<ArticleData> {
    const ts = Date.now();
    const title = `${label}_${ts}`;
    const authorName = `Auto ${label}`;
    const summary = `Tóm tắt tự động ${label}`;
    const content = `<p>Nội dung test tự động — ${label}</p>`;
    const slug = this.toSlug(title);
    const { fixtures } = this.cfg;

    const payload = {
      title,
      slug,
      categoryId: fixtures.categoryId,
      scheduledPublishDate: this.isoDate(publishOffsetMs),
      scheduledUnpublishDate: this.isoDate(unpublishOffsetMs),
      authorName,
      summary,
      content,
      isSubmitForApproval: false,
      sendNotification: false,
      actionButton: false,
      thumbnailUrl: fixtures.thumbnailUrl,
      thumbnailPath: fixtures.thumbnailPath,
      thumbnailImage: fixtures.thumbnailMeta,
    };

    const result = await this.post(this.cfg.endpoints.articles.create, payload);
    if (result.status !== 200 && result.status !== 201) {
      throw new Error(`Create article (Lưu nháp) failed [${result.status}]: ${JSON.stringify(result.data)}`);
    }

    const resData = result.data as Record<string, unknown>;
    const inner = ((resData?.data ?? resData) as Record<string, unknown>);
    const id = (inner?.id as string) ?? '';
    if (!id) throw new Error(`Article ID missing in response: ${JSON.stringify(result.data)}`);
    return { id, title, slug, authorName, summary, content };
  }

  /**
   * Tạo bài Lưu nháp với toggle Gửi thông báo + Thêm nút hành động = ON.
   * Dùng cho test default-value của section thông báo và nút hành động.
   */
  async createLuuNhapWithToggles(
    label: string,
    notification: { name: string; note: string; content: string },
    actionBtn: { name: string; url: string },
    publishOffsetMs = 24 * 3600_000
  ): Promise<ArticleData> {
    const ts = Date.now();
    const title = `${label}_${ts}`;
    const authorName = `Auto ${label}`;
    const summary = `Tóm tắt tự động ${label}`;
    const content = `<p>Nội dung test tự động — ${label}</p>`;
    const slug = this.toSlug(title);
    const { fixtures } = this.cfg;

    const payload = {
      title,
      slug,
      categoryId: fixtures.categoryId,
      scheduledPublishDate: this.isoDate(publishOffsetMs),
      scheduledUnpublishDate: this.isoDate(30 * 24 * 3600_000),
      authorName,
      summary,
      content,
      isSubmitForApproval: false,
      sendNotification: true,
      notificationName: notification.name,
      notificationPurpose: notification.note,
      notificationPayload: notification.content,
      actionButton: true,
      actionButtonName: actionBtn.name,
      actionButtonLink: actionBtn.url,
      thumbnailUrl: fixtures.thumbnailUrl,
      thumbnailPath: fixtures.thumbnailPath,
      thumbnailImage: fixtures.thumbnailMeta,
    };

    const result = await this.post(this.cfg.endpoints.articles.create, payload);
    if (result.status !== 200 && result.status !== 201) {
      throw new Error(`Create article (Lưu nháp + toggles) failed [${result.status}]: ${JSON.stringify(result.data)}`);
    }

    const resData = result.data as Record<string, unknown>;
    const inner = ((resData?.data ?? resData) as Record<string, unknown>);
    const id = (inner?.id as string) ?? '';
    if (!id) throw new Error(`Article ID missing in response: ${JSON.stringify(result.data)}`);
    return {
      id, title, slug, authorName, summary, content,
      notificationName: notification.name,
      notificationNote: notification.note,
      notificationContent: notification.content,
      actionButtonName: actionBtn.name,
      actionButtonUrl: actionBtn.url,
      actionButtonLink: actionBtn.url,
    };
  }

  /** Tạo bài quá hạn: scheduledPublishDate = now → quá hạn sau vài phút. */
  async createQuaHan(label: string): Promise<ArticleData> {
    return this.createChoDuyet(label, 0);
  }

  /** Đảm bảo page đang ở app trước khi gọi API (cần thiết cho fetch trong browser context). */
  async ensureOnApp(): Promise<void> {
    const url = this.page.url();
    if (!url || url === 'about:blank') {
      const cfg = loadConfig('admin');
      await this.page.goto(cfg.baseURL, { waitUntil: 'domcontentloaded' });
    }
  }
}
