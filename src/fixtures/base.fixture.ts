import { test as base, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { account } from '../config';

export type Fixtures = {
  loginPage: LoginPage;
  authenticatedPage: LoginPage;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await use(loginPage);
  },

  // Fixture đã đăng nhập sẵn bằng admin account
  authenticatedPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    const admin = account('portalAdmin');
    await loginPage.login(admin.username, admin.password);
    await use(loginPage);
  },
});

export { expect };
