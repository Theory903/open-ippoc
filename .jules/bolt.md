## 2025-03-05 - [SQL Cycle Pruning for Graph Pathfinding]
**Learning:** [In-SQL cycle check inside a recursive CTE significantly speeds up graph traversal by pruning cyclic paths early, avoiding heavy Python-level filtering overhead. This results in a massive speedup on dense graphs (e.g. from 0.78s to 0.009s).]
**Action:** [Always leverage database-level filtering or pruning inside CTEs for recursive operations rather than pulling raw recursive results into Python and filtering them.]
