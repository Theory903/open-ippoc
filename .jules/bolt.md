## 2025-02-12 - Optimizing dataclass serialization in high-frequency paths

**Learning:** `dataclasses.asdict` introduces massive overhead (up to ~20x slower) in high-frequency operations because it performs deep copies of all nested structures. In systems like the EconomyManager and Ledger that frequently take snapshots or return state, this creates a significant performance bottleneck.
**Action:** Replace `dataclasses.asdict` with manual dictionary construction (`.to_dict()`) and shallow copies (where appropriate) in performance-critical serialization paths.

