#!/bin/bash

# ============================================================
# FAST Email/Phone Checker - Complete VPS Setup
# Run this after copying your source files
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="/opt/fast-checker"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║        FAST Checker - Démarrage rapide                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas installé!${NC}"
    echo "Installez Docker d'abord: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# Check if source files exist
if [ ! -f "$INSTALL_DIR/backend/server.py" ]; then
    echo -e "${RED}❌ Fichiers source manquants!${NC}"
    echo "Copiez d'abord vos fichiers dans $INSTALL_DIR/backend/ et $INSTALL_DIR/frontend/"
    exit 1
fi

cd $INSTALL_DIR

echo -e "${GREEN}[1/2]${NC} Construction des images Docker..."
docker compose build

echo -e "${GREEN}[2/2]${NC} Démarrage des services..."
docker compose up -d

echo -e "\n${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ FAST Checker est maintenant en ligne!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📍 Frontend:${NC} http://localhost:3000"
echo -e "${BLUE}📍 Backend:${NC}  http://localhost:8001/api"
echo ""
echo -e "Commandes utiles:"
echo -e "  docker compose logs -f     - Voir les logs"
echo -e "  docker compose ps          - Statut"
echo -e "  docker compose restart     - Redémarrer"
echo -e "  docker compose down        - Arrêter"
