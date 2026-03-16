## 2024-05-24 - Accessibility for Icon-only Sidebar Buttons
**Learning:** Icon-only buttons used for closing sidebars or panels need explicit screen reader support; without it, assistive technologies just read "button".
**Action:** Ensure all purely icon-based actions include `aria-label="Action description"` attributes.
