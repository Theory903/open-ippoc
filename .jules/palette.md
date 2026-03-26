## 2024-03-26 - Dynamic ARIA and Tooltips for Multi-State Buttons
**Learning:** Buttons that change function (e.g., Send/Queue or Stop/New Session) and have complex disabled states (e.g., disconnected vs sending) require dynamic `aria-label` and `title` attributes. Without them, users relying on screen readers or tooltips lack crucial context about *why* a button is disabled or *what* its current function is.
**Action:** Always provide dynamic `aria-label` and `title` attributes that update in sync with the button's visual text and disabled state, explaining the "why" when disabled.
