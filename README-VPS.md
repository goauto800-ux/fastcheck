# FAST Email/Phone Checker

Vérifiez des millions d'emails et numéros de téléphone sur 35+ plateformes (Netflix, Uber Eats, Binance, Coinbase, Deliveroo, Discord, Instagram, etc.)

## 🚀 Installation sur VPS Ubuntu 22

### Option 1: Installation rapide (recommandée)

```bash
# 1. Connectez-vous à votre VPS
ssh user@votre-vps

# 2. Installez Docker si pas encore fait
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Déconnectez-vous et reconnectez-vous pour appliquer le groupe docker

# 3. Créez le répertoire et copiez les fichiers
sudo mkdir -p /opt/fast-checker
sudo chown $USER:$USER /opt/fast-checker

# 4. Copiez les fichiers depuis votre machine locale (sur votre PC)
scp -r ./backend/* user@votre-vps:/opt/fast-checker/backend/
scp -r ./frontend/* user@votre-vps:/opt/fast-checker/frontend/
scp docker-compose.yml user@votre-vps:/opt/fast-checker/

# 5. Lancez l'application (sur le VPS)
cd /opt/fast-checker
docker compose up -d --build
```

### Option 2: Utiliser le script d'installation

```bash
# Sur votre VPS
sudo bash install-vps.sh
```

## 📍 Accès à l'application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001/api

## 🔧 Commandes utiles

```bash
# Démarrer
docker compose up -d

# Arrêter
docker compose down

# Voir les logs
docker compose logs -f

# Voir les logs du backend uniquement
docker compose logs -f backend

# Reconstruire après modifications
docker compose up -d --build

# Statut des containers
docker compose ps
```

## 💡 Fonctionnalités

### Traitement de masse (jusqu'à 1 million+ d'emails)
- Les fichiers de plus de 5000 identifiants sont traités **en arrière-plan**
- Vous pouvez fermer le navigateur, le traitement continue
- Téléchargez les résultats quand c'est terminé (CSV, TXT, ou JSONL)

### Formats d'export
- **CSV**: Identifiants valides avec les plateformes trouvées
- **TXT**: Liste simple des identifiants valides (1 par ligne)
- **JSONL**: Résultats complets avec tous les détails

### Plateformes vérifiées
- **Email**: Netflix, Uber Eats, Binance, Coinbase, Deliveroo, Discord, Instagram, Twitter, Amazon, eBay, Spotify, GitHub, Google, Yahoo, et 20+ autres
- **Téléphone**: Snapchat, Instagram, Amazon, Uber, Deliveroo

## ⚠️ Notes importantes

1. **Proxies recommandés**: Netflix, Uber, Binance, Coinbase et Deliveroo nécessitent des proxies résidentiels pour des résultats fiables.

2. **Performance**: 
   - Sans proxies: ~50-100 vérifications/seconde
   - Avec proxies: ~200-500 vérifications/seconde

3. **Mémoire**: Pour 1 million d'emails, prévoyez ~4-8 Go de RAM disponible.

## 🔒 Accès externe (optionnel)

Pour accéder depuis l'extérieur, modifiez `docker-compose.yml`:

```yaml
ports:
  - "0.0.0.0:3000:80"   # au lieu de 127.0.0.1:3000:80
  - "0.0.0.0:8001:8001" # au lieu de 127.0.0.1:8001:8001
```

⚠️ **Attention**: Configurez un firewall et/ou une authentification si vous ouvrez l'accès externe.

## 📁 Structure

```
/opt/fast-checker/
├── docker-compose.yml
├── backend/
│   ├── server.py
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── src/
    ├── package.json
    └── Dockerfile
```
