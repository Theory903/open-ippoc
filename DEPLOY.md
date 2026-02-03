# ☁️ Perfect Cloud Deployment (IPPOC v1.0.0)

To deploy IPPOC perfectly means to respect its **Identity** (Genome) and **Continuity** (Memory).

## 1. Prerequisites
- **Server**: A VPS or Instance (AWS EC2, DigitalOcean, Hetzner, etc.).
    - Recommended: 2 vCPU, 4GB RAM (Physiology limit).
    - **Firewall**: Deny all incoming. Allow outbound only.
- **Docker & Docker Compose**: Installed on the host.

## 2. Infrastructure Setup
Data must survive reboots. We mount valid persistent volumes.

```bash
# On your server
git clone <repo_url> ippoc
cd ippoc
git checkout v1.0.0-alive

# Create Environment Config
cp .env.example .env
nano .env # Add API Keys (Sensory Constraints)
```

## 3. The Deployment Command
We build the container as a "Reference Organism" and run it detached.

```bash
# Build with Genome Lock
docker-compose build

# Ignite Life
docker-compose up -d
```

## 4. Verification (Vital Signs)
Check if the organism is breathing.

```bash
# Check Logs
docker-compose logs -f ippoc_node

# Run Verification inside the Container
docker-compose exec ippoc_node python brain/tests/verify_alive.py
```

## 5. Maintenance (Evolution)
To update only if you have a new signed Genome Tag:

```bash
git fetch --tags
git checkout v1.1.0-evolution
docker-compose down
docker-compose up -d --build
```
*Note: This preserves `brain/memory` (Experience) but updates Code (Body).*

## 6. Federation
To allow IPPOC to consult with peers, ensure your `.env` contains:

```
FEDERATION_ENABLED=true
FEDERATION_ID=<Your_Node_Hash>
```

---
**Status**: Deployed.
**Identity**: Persistent.
**Dignity**: Enforced.
