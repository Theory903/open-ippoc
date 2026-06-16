## 2024-04-08 - Icon-only Button Accessibility
**Learning:** Icon-only buttons without `aria-label` or `aria-expanded` attributes are completely silent to screen readers. In the OpenClaw UI, several core navigation and chat control buttons were inaccessible because they relied entirely on visual icons (like SVG components) without text alternatives.
**Action:** Always add descriptive `aria-label` attributes to icon-only buttons. When a button acts as a toggle, ensure its label dynamically reflects its state or purpose (e.g., "Toggle assistant thinking").
