import { BasePage } from './BasePage';

/** LoginPage — dùng chung (framework). Locator từ output/locators/login.screen.json. */
export class LoginPage extends BasePage {
  readonly usernameInput = this.page.getByPlaceholder('Nhập email/số điện thoại');
  readonly passwordInput = this.page.getByPlaceholder('Nhập mật khẩu');
  readonly loginButton = this.page.getByRole('button', { name: 'Đăng nhập' });

  async goto(): Promise<void> {
    await this.page.goto('/login');
    await this.waitReady();
  }

  async login(username: string, password: string): Promise<void> {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await Promise.all([
      this.page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 30_000 }).catch(() => {}),
      this.loginButton.click(),
    ]);
    await this.waitReady();
  }
}
