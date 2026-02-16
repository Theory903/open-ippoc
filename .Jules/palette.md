## 2025-02-16 - Accessibility Gaps in Icon-Only Buttons
**Learning:** Icon-only buttons (like refresh, thinking, focus toggles) often rely solely on `title` attributes, which are insufficient for screen readers and touch devices. Inline SVGs also frequently miss `aria-hidden="true"`, potentially causing screen readers to announce them as "graphic" or read their internal paths if not properly labelled.
**Action:** Systematically check all icon-only buttons for `aria-label` and ensure their icon children are hidden with `aria-hidden="true"`.
