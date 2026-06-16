## 2026-03-09 - Added missing ARIA labels to chat controls
**Learning:** Icon-only buttons in the chat UI require explicit aria-labels, even if a title attribute is present, to ensure proper screen reader accessibility.
**Action:** Always verify that buttons lacking text content use aria-labels, especially in dynamically rendered Lit components like app-render.helpers.ts.
