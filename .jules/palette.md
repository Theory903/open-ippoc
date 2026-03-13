## 2024-05-14 - Add ARIA labels to chat control buttons
**Learning:** Screen readers do not reliably read `title` attributes on buttons, making icon-only buttons inaccessible even if they have a tooltip/title.
**Action:** Always add `aria-label` attributes to icon-only buttons to ensure proper screen reader support.