
## 2025-03-15 - ARIA Labels over Title Attributes for Icon Buttons
**Learning:** Found instances of icon-only buttons (like `×` for close/remove actions) using only `title` attributes for accessibility context instead of `aria-label`. Since screen readers do not reliably announce `title` attributes on HTML elements, this creates a significant accessibility gap for visually impaired users.
**Action:** Always add `aria-label` to icon-only buttons for consistent screen reader support, even if a `title` attribute is present for sighted users' tooltips.
