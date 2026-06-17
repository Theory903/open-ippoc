## 2024-05-23 - Accessibility for Icon-Only Buttons
**Learning:** Icon-only buttons (like refresh, settings toggles) are often implemented using SVG icons without text labels. This makes them inaccessible to screen readers, which may announce them as "button" or try to read the SVG paths.
**Action:** Always add `aria-label` to buttons that only contain an icon. This provides a clear, accessible name for screen reader users. Additionally, use `aria-pressed` for toggle buttons to indicate their state.
