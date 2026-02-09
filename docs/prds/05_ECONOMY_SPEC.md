# 05_ECONOMY_SPEC.md

> **ROLE**: Metabolism.
> **RESPONSIBILITY**: Resource Management, ETH Wallets, Work.

## 1. Wallet Architecture
-   **Cold**: Genome Vault. Offline.
-   **Hot**: Operational. Daily limits.
-   **Ephemeral**: Per-task. Burned after use.

## 2. Decision Engine (Economic Brain)
-   **Input**: Cognitive backlog, Energy price, ROI estimate.
-   **Output**: `EconomicIntent` (Goal, Budget, Risk).

## 3. Treasury Controller (Body)
-   **Role**: The "CFO" that signs transactions.
-   **Logic**:
    -   Validate `EconomicIntent`.
    -   Check `ECONOMY.md` invariants.
    -   Simulate impact in WorldModel.
    -   Sign & Broadcast.

## 4. Earning & Work
-   **Bounties**: Scan GitHub -> Solve Issue -> PR -> Earn.
-   **Services**: Selling compute/inference optimization.
-   **Rules**: No impersonation.
