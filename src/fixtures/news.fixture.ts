import { test as base } from './base.fixture';
import { NewsListPage } from '../pages/NewsListPage';
import { NewsReviewPage } from '../pages/NewsReviewPage';
import { NewsEditPage } from '../pages/NewsEditPage';
import { NewsCreatePage } from '../pages/NewsCreatePage';
import { ArticleApiHelper } from '../utils/ArticleApiHelper';

export type NewsFixtures = {
  newsListPage: NewsListPage;
  newsReviewPage: NewsReviewPage;
  newsEditPage: NewsEditPage;
  newsCreatePage: NewsCreatePage;
  articleApi: ArticleApiHelper;
};

export const test = base.extend<NewsFixtures>({
  newsListPage: async ({ authenticatedPage: _, page }, use) => {
    await use(new NewsListPage(page));
  },

  newsReviewPage: async ({ authenticatedPage: _, page }, use) => {
    await use(new NewsReviewPage(page));
  },

  newsEditPage: async ({ authenticatedPage: _, page }, use) => {
    await use(new NewsEditPage(page));
  },

  newsCreatePage: async ({ authenticatedPage: _, page }, use) => {
    await use(new NewsCreatePage(page));
  },

  articleApi: async ({ authenticatedPage: _, page }, use) => {
    const api = new ArticleApiHelper(page);
    await api.ensureOnApp();
    await use(api);
  },
});

export { expect } from '@playwright/test';
