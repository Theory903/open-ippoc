## 2025-02-14 - Optimize `find_similar_entities` in Entity Graph
**Learning:** Entity similarity search over graphs can be heavily unoptimized if calculating Jaccard similarity via iterative programmatic set comparisons in python, causing N+1 queries.
**Action:** Always compute metrics like Jaccard similarity in bulk using SQL CTEs inside the database when using SQLAlchemy to avoid overhead.
