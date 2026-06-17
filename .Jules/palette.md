## 2025-05-15 - Chat Control Improvements
**Learning:** Icon-only buttons often lack accessible names, making them invisible to screen reader users. Additionally, async operations like refreshing data benefit significantly from visual loading states to prevent user frustration from lack of feedback.
**Action:** Always add `aria-label` to icon-only buttons. For async actions, replace the static icon with a loading spinner (using a `.icon-spin` utility) during the loading state to provide immediate feedback.
