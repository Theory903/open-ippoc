#!/usr/bin/env bash
#
# IPPOC-OS Production Deployment Script
# Works on any Linux/macOS with Docker installed
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

show_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║   ██╗██████╗ ██████╗  ██████╗  ██████╗      ██████╗ ███████╗
║   ██║██╔══██╗██╔══██╗██╔═══██╗██╔════╝     ██╔═══██╗██╔════╝
║   ██║██████╔╝██████╔╝██║   ██║██║          ██║   ██║███████╗
║   ██║██╔═══╝ ██╔═══╝ ██║   ██║██║          ██║   ██║╚════██║
║   ██║██║     ██║     ╚██████╔╝╚██████╗     ╚██████╔╝███████║
║   ╚═╝╚═╝     ╚═╝      ╚═════╝  ╚═════╝      ╚═════╝ ╚══════╝
║                                                           ║
║          PRODUCTION DEPLOYMENT                            ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

check_requirements() {
    echo -e "${YELLOW}Checking requirements...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker not found. Install from https://docker.com${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker installed${NC}"
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}✗ Docker Compose not found${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
}

deploy_stack() {
    echo -e "\n${YELLOW}[1/4] Creating .env file...${NC}"
    
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        cat > "$PROJECT_ROOT/.env" << EOF
# IPPOC-OS Production Configuration
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
GRAFANA_PASSWORD=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)
NODE_ROLE=reasoning
EOF
        echo -e "${GREEN}✓ Generated secure .env file${NC}"
    else
        echo -e "${GREEN}✓ .env file already exists${NC}"
    fi
    
    echo -e "\n${YELLOW}[2/4] Building containers...${NC}"
    cd "$PROJECT_ROOT"
    docker compose build --parallel
    echo -e "${GREEN}✓ Build complete${NC}"
    
    echo -e "\n${YELLOW}[3/4] Starting services...${NC}"
    docker compose up -d
    echo -e "${GREEN}✓ Services started${NC}"
    
    echo -e "\n${YELLOW}[4/4] Waiting for health checks...${NC}"
    sleep 10
    
    # Check health
    if docker compose ps | grep -q "healthy"; then
        echo -e "${GREEN}✓ All services healthy${NC}"
    else
        echo -e "${YELLOW}⚠ Some services still starting...${NC}"
    fi
}

show_status() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}IPPOC-OS Deployment Complete!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
    
    echo -e "${YELLOW}Services:${NC}"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    
    echo -e "\n${YELLOW}Access Points:${NC}"
    echo -e "  IPPOC Node:   ${GREEN}localhost:9000${NC}"
    echo -e "  Cortex:       ${GREEN}localhost:3000${NC}"
    echo -e "  PostgreSQL:   ${GREEN}localhost:5432${NC}"
    echo -e "  Redis:        ${GREEN}localhost:6379${NC}"
    
    echo -e "\n${YELLOW}Commands:${NC}"
    echo -e "  View logs:     ${GREEN}docker compose logs -f${NC}"
    echo -e "  Stop:          ${GREEN}docker compose down${NC}"
    echo -e "  Scale nodes:   ${GREEN}docker compose up -d --scale ippoc-node=3${NC}"
    echo -e "  Monitoring:    ${GREEN}docker compose --profile monitoring up -d${NC}"
    
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

main() {
    show_banner
    check_requirements
    deploy_stack
    show_status
}

# Run
main "$@"
