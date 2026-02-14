## 2024-05-22 - [Missing Accessible Names in Core Navigation]
**Learning:** Core navigation elements (tabs) and primary action buttons (refresh, session select) were missing explicit accessible names or state indicators (`aria-current`), relying on visual cues or `title` attributes which are insufficient for screen reader users.
**Action:** Always verify that icon-only buttons have `aria-label` and active navigation states use `aria-current="page"`.
