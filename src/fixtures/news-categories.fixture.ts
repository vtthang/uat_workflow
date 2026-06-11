import { test as base } from './base.fixture';
import { NewsCategoriesPage } from '../pages/NewsCategoriesPage';

export type NewsCategoriesFixtures = {
  newsCategoriesPage: NewsCategoriesPage;
};

export const test = base.extend<NewsCategoriesFixtures>({
  newsCategoriesPage: async ({ authenticatedPage: _, page }, use) => {
    await use(new NewsCategoriesPage(page));
  },
});

export { expect } from '@playwright/test';
