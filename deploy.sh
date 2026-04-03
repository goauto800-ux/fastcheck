#!/bin/bash

# ============================================
#   FAST Identity Checker - Deploy Script
#   Usage: ./deploy.sh
# ============================================

set -e

echo ""
echo "  ⚡ FAST Identity Checker - Déploiement"
echo "  ======================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker n'est pas installé.${NC}"
    echo -e "${YELLOW}  Installe Docker avec: curl -fsSL https://get.docker.com | sh${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker trouvé${NC}"

# Check Docker Compose
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo -e "${RED}✗ Docker Compose n'est pas installé.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose trouvé ($COMPOSE_CMD)${NC}"
echo ""

# Get server IP/domain
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
echo -e "${BLUE}  IP du serveur: ${SERVER_IP}${NC}"
echo ""

# Build and start
echo -e "${YELLOW}▶ Construction des images...${NC}"
$COMPOSE_CMD build --no-cache

echo ""
echo -e "${YELLOW}▶ Démarrage des services...${NC}"
$COMPOSE_CMD up -d

echo ""
echo -e "${GREEN}✓ Déploiement terminé !${NC}"
echo ""
echo -e "  ⚡ FAST est accessible sur:"
echo -e "  ${BLUE}  → http://${SERVER_IP}${NC}"
echo -e "  ${BLUE}  → http://localhost${NC}"
echo ""
echo -e "  Commandes utiles:"
echo -e "  ${YELLOW}  $COMPOSE_CMD logs -f        ${NC} # Voir les logs"
echo -e "  ${YELLOW}  $COMPOSE_CMD down            ${NC} # Arrêter"
echo -e "  ${YELLOW}  $COMPOSE_CMD up -d           ${NC} # Redémarrer"
echo -e "  ${YELLOW}  $COMPOSE_CMD pull && $COMPOSE_CMD up -d ${NC} # Mettre à jour"
echo ""
