---
name: smart-locator
description: Sinh locator ổn định, dễ bảo trì cho UI automation (Playwright/Selenium/Appium) từ HTML/DOM element. Proactive — dùng khi cần locator cho element mới trong lúc thiết kế POM. Auto-invoke khi đang sinh Page class và gặp element chưa có locator.
allowed-tools: Read, Bash, Glob
---

# Smart Locator

Sinh locator ổn định cho element mới (proactive). Khác `locator-healer` (reactive, sửa khi fail).

## Trách nhiệm

1. Inspect DOM / mobile hierarchy (NEVER guess)
2. Xác định thuộc tính ổn định
3. Sinh locator tin cậy
4. Verify uniqueness (match đúng 1 element)
5. Cung cấp fallback nếu primary mong manh

## Priority (xem `.claude/commands/rules/locator_strategy.md`)

1. Accessibility (`aria-label`, `role`)
2. `data-testid` / `data-test` / `data-qa`
3. `id` (ổn định, không auto-gen) / `name`
4. Framework semantic (Playwright `getByRole`/`getByLabel`)
5. CSS selector
6. XPath (cuối cùng, tương đối — không theo vị trí)

**Playwright** ưu tiên: `getByRole` → `getByLabel` → `getByPlaceholder` → `getByText` → `getByTestId`.
**Selenium** ưu tiên: `id` → `data-testid` → `name` → css → xpath.
**Appium**: `accessibility id` → `resource-id` → `id` → iOS predicate → class chain → xpath.

## Validation (trước khi dùng)
- [ ] Match đúng 1 element
- [ ] Element visible & interactable
- [ ] Ổn định qua reload
- [ ] Sống sót thay đổi cosmetic (layout/style)
- [ ] KHÔNG dùng class động / positional xpath

## Output
Primary locator + Fallback locator + lý do chọn.
