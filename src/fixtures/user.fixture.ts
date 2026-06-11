import { test as base, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { UserListPage } from '../pages/UserListPage';
import { UserCreatePage } from '../pages/UserCreatePage';
import { UserDetailPage } from '../pages/UserDetailPage';
import { UserEditPage } from '../pages/UserEditPage';
import { account } from '../config';

export type UserFixtures = {
  userListPage: UserListPage;
  userCreatePage: UserCreatePage;
  userDetailPage: UserDetailPage;
  userEditPage: UserEditPage;
};

export const test = base.extend<UserFixtures>({
  userListPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    const admin = account('portalAdmin');
    await loginPage.login(admin.username, admin.password);
    const listPage = new UserListPage(page);
    await listPage.goto();
    await use(listPage);
  },

  userCreatePage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    const admin = account('portalAdmin');
    await loginPage.login(admin.username, admin.password);
    const createPage = new UserCreatePage(page);
    await createPage.goto();
    await use(createPage);
  },

  userDetailPage: async ({ page }, use) => {
    // Skip login if page is already authenticated (shared with userListPage fixture)
    const url = page.url();
    if (!url.includes('admin-1sme') || url.includes('/login') || url === 'about:blank') {
      const loginPage = new LoginPage(page);
      await loginPage.goto();
      const admin = account('portalAdmin');
      await loginPage.login(admin.username, admin.password);
    }
    await use(new UserDetailPage(page));
  },

  userEditPage: async ({ page }, use) => {
    const url = page.url();
    if (!url.includes('admin-1sme') || url.includes('/login') || url === 'about:blank') {
      const loginPage = new LoginPage(page);
      await loginPage.goto();
      const admin = account('portalAdmin');
      await loginPage.login(admin.username, admin.password);
    }
    await use(new UserEditPage(page));
  },
});

export { expect };
