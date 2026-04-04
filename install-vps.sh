#!/bin/bash

# ============================================================
# FAST Email/Phone Checker - Installation Script for Ubuntu 22
# One-command installation for VPS
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     FAST Email/Phone Checker - Installation VPS          ║"
echo "║     Ubuntu 22.04 - Docker + MongoDB + App                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠ Ce script doit être exécuté avec sudo${NC}"
    echo "Relance avec: sudo $0"
    exit 1
fi

INSTALL_DIR="/opt/fast-checker"
CURRENT_USER=${SUDO_USER:-$USER}

echo -e "\n${GREEN}[1/6]${NC} Mise à jour du système..."
apt-get update -qq
apt-get install -y -qq curl git ca-certificates gnupg lsb-release > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Système mis à jour"

# Install Docker if not present
echo -e "\n${GREEN}[2/6]${NC} Installation de Docker..."
if ! command -v docker &> /dev/null; then
    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Add the repository to Apt sources
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin > /dev/null 2>&1
    
    # Add user to docker group
    usermod -aG docker $CURRENT_USER
    echo -e "${GREEN}✓${NC} Docker installé"
else
    echo -e "${GREEN}✓${NC} Docker déjà installé"
fi

# Start Docker
systemctl start docker
systemctl enable docker > /dev/null 2>&1

echo -e "\n${GREEN}[3/6]${NC} Création du répertoire d'installation..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Create docker-compose.yml for localhost
echo -e "\n${GREEN}[4/6]${NC} Création de la configuration Docker..."

cat > docker-compose.yml << 'DOCKERCOMPOSE'
version: '3.8'

services:
  mongodb:
    image: mongo:7
    container_name: fast-mongo
    restart: always
    volumes:
      - mongo_data:/data/db
    networks:
      - fast-network
    # MongoDB only accessible internally

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: fast-backend
    restart: always
    environment:
      - MONGO_URL=mongodb://mongodb:27017/fast_checker
      - DB_NAME=fast_checker
      - CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
    depends_on:
      - mongodb
    ports:
      - "127.0.0.1:8001:8001"
    networks:
      - fast-network
    volumes:
      - job_results:/tmp/fast_jobs

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - REACT_APP_BACKEND_URL=http://localhost:8001
    container_name: fast-frontend
    restart: always
    ports:
      - "127.0.0.1:3000:80"
    depends_on:
      - backend
    networks:
      - fast-network

volumes:
  mongo_data:
  job_results:

networks:
  fast-network:
    driver: bridge
DOCKERCOMPOSE

# Create backend directory and files
mkdir -p backend
cat > backend/Dockerfile << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright browsers for some checks
RUN playwright install-deps chromium || true
RUN playwright install chromium || true

# Copy application code
COPY . .

# Create jobs directory
RUN mkdir -p /tmp/fast_jobs

# Expose port
EXPOSE 8001

# Start server with more workers for massive processing
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
DOCKERFILE

# Create frontend directory and files
mkdir -p frontend
cat > frontend/Dockerfile << 'DOCKERFILE'
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package.json yarn.lock* ./

# Install dependencies
RUN yarn install --frozen-lockfile || yarn install

# Copy source
COPY . .

# Build argument for backend URL
ARG REACT_APP_BACKEND_URL=http://localhost:8001
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Build
RUN yarn build

# Production image
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
DOCKERFILE

cat > frontend/nginx.conf << 'NGINXCONF'
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINXCONF

echo -e "${GREEN}✓${NC} Configuration créée"

echo -e "\n${GREEN}[5/6]${NC} Copie des fichiers source..."
echo -e "${YELLOW}Veuillez copier vos fichiers source dans:${NC}"
echo -e "  - Backend: ${BLUE}$INSTALL_DIR/backend/${NC}"
echo -e "  - Frontend: ${BLUE}$INSTALL_DIR/frontend/${NC}"
echo ""
echo -e "${YELLOW}Commandes pour copier depuis votre machine locale:${NC}"
echo -e "  scp -r ./backend/* user@votre-vps:$INSTALL_DIR/backend/"
echo -e "  scp -r ./frontend/* user@votre-vps:$INSTALL_DIR/frontend/"

# Create management script
echo -e "\n${GREEN}[6/6]${NC} Création du script de gestion..."

cat > /usr/local/bin/fast-checker << 'SCRIPT'
#!/bin/bash

INSTALL_DIR="/opt/fast-checker"
cd $INSTALL_DIR

case "$1" in
    start)
        echo "🚀 Démarrage de FAST Checker..."
        docker compose up -d --build
        echo "✅ Application démarrée!"
        echo "📍 Frontend: http://localhost:3000"
        echo "📍 Backend API: http://localhost:8001/api"
        ;;
    stop)
        echo "🛑 Arrêt de FAST Checker..."
        docker compose down
        echo "✅ Application arrêtée"
        ;;
    restart)
        echo "🔄 Redémarrage de FAST Checker..."
        docker compose restart
        echo "✅ Application redémarrée"
        ;;
    logs)
        docker compose logs -f ${2:-}
        ;;
    status)
        docker compose ps
        ;;
    update)
        echo "🔄 Mise à jour de FAST Checker..."
        docker compose down
        docker compose build --no-cache
        docker compose up -d
        echo "✅ Application mise à jour!"
        ;;
    *)
        echo "Usage: fast-checker {start|stop|restart|logs|status|update}"
        echo ""
        echo "Commands:"
        echo "  start   - Démarre l'application"
        echo "  stop    - Arrête l'application"
        echo "  restart - Redémarre l'application"
        echo "  logs    - Affiche les logs (optionnel: fast-checker logs backend)"
        echo "  status  - Affiche le statut des containers"
        echo "  update  - Met à jour et redémarre"
        exit 1
        ;;
esac
SCRIPT

chmod +x /usr/local/bin/fast-checker

echo -e "\n${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Installation terminée!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📁 Répertoire d'installation:${NC} $INSTALL_DIR"
echo ""
echo -e "${YELLOW}Prochaines étapes:${NC}"
echo -e "1. Copiez vos fichiers source dans $INSTALL_DIR/backend/ et $INSTALL_DIR/frontend/"
echo -e "2. Lancez l'application avec: ${GREEN}fast-checker start${NC}"
echo ""
echo -e "${BLUE}Commandes disponibles:${NC}"
echo -e "  fast-checker start   - Démarre l'application"
echo -e "  fast-checker stop    - Arrête l'application"
echo -e "  fast-checker restart - Redémarre"
echo -e "  fast-checker logs    - Affiche les logs"
echo -e "  fast-checker status  - Statut des containers"
echo ""
echo -e "${BLUE}URLs (localhost):${NC}"
echo -e "  Frontend: http://localhost:3000"
echo -e "  Backend:  http://localhost:8001/api"
echo ""
echo -e "${YELLOW}Note:${NC} Si vous voulez accéder depuis l'extérieur, modifiez docker-compose.yml"
echo -e "      pour remplacer 127.0.0.1 par 0.0.0.0"
