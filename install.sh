#!/bin/bash
set -e

# ==============================================
# IPPOC/OpenClaw Native Installer
# ==============================================

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

log "Detected OS: $MACHINE"

# ----------------------------------------------
# System Dependencies (Native Postgres & Redis)
# ----------------------------------------------

install_deps_mac() {
    if ! command -v brew &> /dev/null; then
        log "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    log "Installing System Dependencies (Node, Postgres, Redis)..."
    brew install node postgresql redis
    
    log "Starting Services..."
    brew services start postgresql || true
    brew services start redis || true
}

install_deps_linux() {
    log "Installing System Dependencies (Node, Postgres, Redis)..."
    sudo apt-get update
    sudo apt-get install -y nodejs npm postgresql redis-server
    
    log "Starting Services..."
    sudo systemctl start postgresql || true
    sudo systemctl start redis-server || true
    
    # Ensure postgres user exists for current user
    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$(whoami)'" | grep -q 1; then
        log "Creating Postgres user $(whoami)..."
        sudo -u postgres createuser -s "$(whoami)"
    fi
    
    # Create DB if not exists
    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='ippoc_hidb'" | grep -q 1; then
        log "Creating Database ippoc_hidb..."
        sudo -u postgres createdb -O "$(whoami)" ippoc_hidb || true
    fi
}

if [ "$MACHINE" == "Mac" ]; then
    install_deps_mac
elif [ "$MACHINE" == "Linux" ]; then
    install_deps_linux
else
    log "Unsupported OS for automatic dependency installation."
fi

# ----------------------------------------------
# Models (Ollama)
# ----------------------------------------------
log "Checking for Ollama (AI Model Runtime)..."
if ! command -v ollama &> /dev/null; then
    log "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Start Ollama in background to pull models
    log "Starting Ollama Server..."
    ollama serve > /dev/null 2>&1 &
    OLLAMA_PID=$!
    sleep 5
else
    log "Ollama detected."
    if ! pgrep -x "ollama" > /dev/null; then
        log "Starting Ollama Server..."
        ollama serve > /dev/null 2>&1 &
        OLLAMA_PID=$!
        sleep 5
    fi
fi

log "Pulling default model: gemma:2b (Gemma 3n)..."
ollama pull gemma:2b || log "Failed to pull gemma:2b."
log "Pulling coding model: codegemma..."
ollama pull codegemma || log "Failed to pull codegemma."

# Install pnpm
if ! command -v pnpm &> /dev/null; then
    log "Installing pnpm..."
    npm install -g pnpm
fi

# ----------------------------------------------
# Project Setup
# ----------------------------------------------
PROJECT_DIR="$(pwd)"
OPENCLAW_DIR="$PROJECT_DIR/mind/openclaw"

if [ ! -d "$OPENCLAW_DIR" ]; then
    error "Could not find mind/openclaw directory. Please run this script from the project root."
    exit 1
fi

log "Setting up OpenClaw in $OPENCLAW_DIR..."
cd "$OPENCLAW_DIR" || exit

log "Installing Node Dependencies..."
pnpm install

# Database Configuration
log "Configuring Environment..."

# Allow user to specify custom DB URL or default to local interactive
DB_USER="$(whoami)"
DB_NAME="ippoc_hidb"
DB_URL_DEFAULT="postgresql://$DB_USER@localhost:5432/$DB_NAME"

# Create Database on Mac (Linux handled above)
if [ "$MACHINE" == "Mac" ]; then
    if ! psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        createdb "$DB_NAME" || log "Database creation failed or already exists (check logs)."
    fi
fi

if [ ! -f .env ]; then
    cat > .env <<EOF
DATABASE_URL="$DB_URL_DEFAULT"
REDIS_URL="redis://localhost:6379"
NODE_ENV="development"
# Model Config
OPENCLAW_MODELS_CONFIG="./models.json"
OPENCLAW_DEFAULT_MODEL="ollama/gemma:2b"
# Point IPPOC Brain to Ollama (mimicking VLLM/OpenAI)
VLLM_ENDPOINT="http://localhost:11434/v1"
EOF
    log "Created .env with default settings."
else
    log ".env already exists, skipping creation."
fi

# Optional Prisma Setup
log "Prisma is installed. To set up the database schema, run:"
success "  cd mind/openclaw && pnpm db:push"
echo
success "Installation Complete! Services (Postgres, Redis) should be running."
