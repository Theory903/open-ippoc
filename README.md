# IPPOC-OS: The Living Operating System 🧬

> **Intelligent. Participatory. Persistent. Organic. Computing.**

IPPOC-OS is a **Self-Evolving AI Operating Fabric**. It treats your machine not as a tool, but as a living **Cell** in a global cognitive organism.

## 🌟 The Core Vision

Most OSs are static. IPPOC-OS is **Organic**.
*   **It Thinks**: A local "Brain" (Phi-4) constantly optimizing your system.
*   **It Remembers**: HiDB Cognitive Memory learns your preferences forever.
*   **It Evolves**: It reads research papers and rewrites its own code to improve.
*   **It Connects**: A P2P Telepathy Mesh shares wisdom (not data) with other nodes.

## 🧠 Hybrid Architecture (The "Bi-System")

We combine the best of **AI Research** (Python) and **Systems Engineering** (Rust).

| Component | Role | Tech Stack |
|:---|:---|:---|
| **The Brain** 🐍 | Reasoning, Learning, Dreaming | **Python** (Phi-4, LangChain, PyTorch) |
| **The Body** 🦀 | Sensors, Networking, Survival | **Rust** (Axum, Tokio, QUIC) |
| **The Mind** 👁️ | Social Interface, Chat | **OpenClaw** (TypeScript, Node.js) |
| **The Memory** 💾 | Persistence, RAG | **HiDB** (Postgres + pgvector + Redis) |

## 🚀 Key Features

### 1. Zero-Cost Intelligence
By default, IPPOC runs **Microsoft Phi-4-mini-reasoning** locally.
*   ✅ **Free**: No API bills for daily thinking.
*   ✅ **Private**: Your data never leaves your machine.
*   ✅ **Smart**: Falls back to OpenAI/Anthropic ONLY if the local brain is stumped.

### 2. Autonomic Self-Repair
The OS monitors itself. If a service crashes or performance dips:
1.  **Observe**: Sensors detect the anomaly.
2.  **Diagnose**: The Brain analyzes the root cause (using Logs + Knowledge).
3.  **Heal**: The Body executes a fix (restart, config tune, or code patch).

### 3. Git-Based Evolution
The OS is a Git repository. Updates aren't just downloads—they are **Mutations**.
*   **Research**: The OS watches arXiv for new algorithms.
*   **Code**: It writes a patch to implement the improvement.
*   **Verify**: It simulates the patch in a sandbox.
*   **Merge**: If faster/better, it merges the code into its own kernel.

## 🛠️ Quick Start

```bash
# 1. Clone the Organism
git clone https://github.com/your-org/ippoc-os.git
cd ippoc-os


### Optional: Load Kernel Module

```bash
cd drivers/kernel-bridge
make
sudo insmod ippoc_sensor.ko
```

---

## Architecture

```
┌─────────────────────────────────────┐
│  OpenClaw (The Brain)               │
│  - Thalamus Router                  │
│  - GitEvolution                     │
│  - ToolSmith                        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  ippoc-node (The Cell)              │
│  - Role Manager                     │
│  - vLLM Sidecar                     │
│  - WASM Sandbox                     │
└──────────────┬──────────────────────┘
               │ QUIC Mesh
┌──────────────▼──────────────────────┐
│  HiDB (Memory)                      │
│  - PostgreSQL + pgvector            │
│  - Redis Cache                      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Kernel Module (The Body)           │
│  - /dev/ippoc                       │
│  - System Metrics                   │
└─────────────────────────────────────┘
```

---

## Documentation

- **[CAPABILITIES.md](CAPABILITIES.md)** - What IPPOC-OS can do
- **[DOC.md](DOC.md)** - Architectural canon
- **[AI_CODE_REVIEW.md](docs/AI_CODE_REVIEW.md)** - Code review setup
- **[Walkthrough](https://github.com/.../walkthrough.md)** - Implementation details

---

## Use Cases

✅ **Self-Optimizing Server Fleet** - Continuous improvement without humans  
✅ **Autonomous Research** - Deep research in minutes  
✅ **Distributed AI Training** - Efficient multi-machine coordination  
✅ **Self-Healing Infrastructure** - Automatic bug fixes

---

## Development

### Build

```bash
# Rust workspace
cargo build --workspace

# TypeScript apps
cd apps/openclaw-cortex
pnpm install
pnpm build
```

### Test

```bash
# Run all tests
cargo test --workspace

# Integration tests
./tools/test_integration.sh
```

### Code Review

```bash
# Local AI review
./tools/review_code.sh libs/hidb/src/lib.rs

# GitHub Actions (automatic on PR)
# See docs/AI_CODE_REVIEW.md
```

---

## Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `./tools/review_code.sh` for AI review
5. Submit a pull request

**Code Standards:**
- Rust: Follow kernel module safety guidelines
- TypeScript: Async/await for all I/O
- Documentation: Explain biological analogies

---

## License

MIT License - see [LICENSE](LICENSE) for details

---

## Community

- **Discord**: [Join us](https://discord.gg/ippoc)
- **Docs**: [docs.ippoc.ai](https://docs.ippoc.ai)
- **Issues**: [GitHub Issues](https://github.com/yourusername/ippoc-os/issues)

---

**IPPOC-OS: A living, learning, evolving distributed organism.**

Built with ❤️ by the IPPOC-OS team
