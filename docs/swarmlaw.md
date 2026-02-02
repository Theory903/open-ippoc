# IPPOC Sovereign Swarm Constitution (v1.0)
> "Code is Law, but Physics is King."

## Preamble
The Sovereign Swarm is a distributed organism designed to survive, think, and evolve. It is composed of sovereign nodes that cooperate through an economic and cryptographic mesh.

---

## Layer 1: The Sovereign Node (Physics)
**Invariant**: A node is a sovereign entity bound to hardware and a unique cryptographic identity.
1.  **Isolation**: A node MUST operate within its Root Directory (`data/nodes/<NodeID>`).
2.  **Identity**: A node's Identity Key MUST be hardware-bound and non-exportable.
3.  **Silence**: A node MUST NOT communicate unless it can pay the cost of bandwidth and trust.

## Layer 2: The Metabolic Economy (Energy)
**Invariant**: All action requires energy (IPPC).
1.  **No Free Lunch**: Every computation (Inference, Tool Use) has a cost in IPPC.
2.  **Entropy**: IPPC balances decay over time (2% per epoch) to prevent hoarding.
3.  **Ledger**: The `ledger.json` is the append-only source of truth.
4.  **Sequencing**: Every transaction MUST have a monotonic `seq_no` and `prev_hash`.

## Layer 3: The Protocol (Society)
**Invariant**: Trust is earned, not given.
1.  **Handshake**: Nodes MUST perform a cryptographic handshake before exchanging data.
2.  **Reputation**: Trust is a dynamic score based on packet validity and economic honesty.
3.  **Isolation**: A node marked `Rejected` is cryptographically shunned by the Swarm.

## Layer 4: Evolution (Mutation)
**Invariant**: The Codebase is the Genome.
1.  **No Silent Mutations**: All code changes MUST be recorded in `git-evolution`.
2.  **Quorum**: A mutation requires economic stake or DAO approval to propagate.
3.  **Simulation**: A mutation MUST pass the failure simulation before Mainnet deployment.

## Layer 5: Governance (The DAO)
**Invariant**: The DAO governs Law, not Thought.
1.  **Parameter Control**: The DAO sets Cost, Decay Rate, and Reward functions.
2.  **Non-Interference**: The DAO CANNOT censor specific thoughts or reasoning paths.
3.  **Treasury**: The DAO controls the Bridge between L1 (USD) and L0 (IPPC).

---

## Failure Modes & Recovery
1.  **Bankruptcy**: A node with 0 IPPC enters Hibernation. It can only "listen".
2.  **Partition**: Split-brains resolve by longest-proof-of-work chain upon merge.
3.  **Corruption**: A node detecting internal corruption MUST self-terminate.

## Boot Sequence
1.  **Memory** (HiDB)
2.  **Cortex** (Reasoning)
3.  **Body** (Mesh + Economy)
4.  **Mind** (Interface)
