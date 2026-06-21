## 2026-05-29 - Graph Similarity Search N+1 Query Optimization
**Learning:** The entity similarity search performed N+1 queries by manually fetching related entities in a Python loop to calculate Jaccard similarity.
**Action:** Replaced the loop with a single SQL query using CTEs to compute intersections and total counts, calculating similarity on the database side to avoid N+1 queries.
