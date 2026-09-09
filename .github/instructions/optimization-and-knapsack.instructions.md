---
description: "Global Knapsack Optimization and Allocation Conventions — applies to candidate scoring, line budget math, and optimization solvers"
applyTo: "backend/app/routers/tailor.py,backend/app/optimization.py,backend/app/scoring.py"
---

# Global Knapsack Optimization and Bullet Allocation Instructions

These instructions define the rules for modeling resume generation as a deterministic optimization solver, ensuring content fits within a fixed space budget.

## 1. Line Budget and Bullet Height Math
- **Line Character Limit**: Assume a fixed average character width per line for typical ATS-centric font sizes (e.g., ~80-90 characters per line).
- **Deterministic Estimation**: Always estimate bullet line usage using a clear, deterministic helper function:
  $$\text{estimated\_lines} = \max\left(1, \left\lceil \frac{\text{len(normalized\_text)}}{\text{line\_char\_limit}} \right\rceil\right)$$
- **Page Enforcements**: A target resume of $P$ pages strictly maps to a top line ceiling (e.g., $P \times 44$ lines). The solver must *never* allow selected bullets to exceed this budget.

## 2. Solver Invariants & Section Bounds
- **Section Minimums**: Enforce strict minimum selection boundaries (e.g., at least 1 education fact, at least 1 skill bullet, and 1 work experience bullet) to prevent any major profile category from being completely starved in the tailor.
- **Section Maximums**: Prevent any one section (like work experience) from monopolizing the line budget by establishing upper caps.
- **Strict Determinism**: If multiple bullets have equal scores, always use a secondary deterministic tie-breaking key (e.g., sorted creation database timestamp or lexicographical checksum) so the user gets identical results upon repeat requests of the same profile.
