# IPPOC Project Structure

## Core Directories

### `/src` - Source Code
- **core/** - Shared utilities and system-wide components
- **network/** - Mesh networking and distributed communication
- **memory/** - Storage systems and cognitive memory
- **cognition/** - Reasoning engines and decision-making
- **economy/** - Resource allocation and economic systems
- **evolution/** - Adaptive learning and policy enforcement
- **security/** - Identity management and access control

### `/docs` - Documentation
- **architecture/** - System design and architecture documents
- **api/** - API references and endpoint documentation
- **design/** - Design documents and specifications
- **specifications/** - Technical specifications and standards
- **tutorials/** - Getting started guides and tutorials

### `/config` - Configuration
- Environment configurations
- Component settings
- Deployment parameters

### `/data` - Data Storage
- **models/** - ML models and trained weights
- **logs/** - System logs and audit trails
- **cache/** - Cached data and temporary storage
- **temp/** - Temporary files and working directories

### `/tests` - Testing
- **unit/** - Unit tests for individual components
- **integration/** - Integration tests between components
- **e2e/** - End-to-end system tests

### `/scripts` - Utilities
- **setup/** - Installation and setup scripts
- **deploy/** - Deployment and orchestration scripts
- **utils/** - Utility and helper scripts
- **monitoring/** - Monitoring and health check scripts

### `/deployments` - Deployment Configurations
- Docker configurations
- Kubernetes manifests
- Cloud deployment templates

## Key Files

- **README.md** - Project overview and getting started guide
- **Cargo.toml** - Rust workspace configuration
- **requirements.txt** - Python dependencies
- **.env.example** - Environment variable template
- **LICENSE** - License information