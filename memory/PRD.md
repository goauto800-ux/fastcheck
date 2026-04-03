# FAST - Identity Verification Tool

## Original Problem Statement
Créer un outil pour vérifier si des emails et numéros de téléphone sont associés à des comptes sur Uber Eats, Amazon, Netflix, Binance et Coinbase.

## User Choices
- Interface avec vérification en masse (upload fichier CSV/TXT ou coller)
- Toutes les 5 plateformes
- Pas d'historique
- Accessible à tous (pas de login)
- Thème bleu/mauve masonry
- Nom: FAST

## Architecture
- **Frontend**: React avec Tailwind CSS, Framer Motion, react-icons
- **Backend**: FastAPI (Python)
- **Database**: MongoDB (non utilisé - pas d'historique)

## Core Requirements (Static)
1. Upload de fichiers (CSV, TXT)
2. Zone de texte pour coller des données
3. Vérification sur 5 plateformes
4. Affichage des résultats en temps réel (masonry grid)
5. Export CSV des résultats

## What's Been Implemented (Jan 2026)
- [x] Backend API avec endpoints /verify, /verify/file, /verify/single
- [x] Frontend avec zones upload et texte
- [x] Masonry grid pour affichage des résultats
- [x] Statistiques en temps réel (total, trouvés, non trouvés)
- [x] Export CSV
- [x] Boutons effacer
- [x] Thème bleu/mauve avec glassmorphism

## Prioritized Backlog
### P0 (Critical)
- ✅ Toutes les fonctionnalités critiques implémentées

### P1 (Important)
- Intégration avec vraies APIs des plateformes (nécessite API keys)

### P2 (Nice to have)
- Mode sombre/clair toggle
- Historique optionnel avec authentification
- Notifications par email des résultats

## Technical Notes
- La vérification est actuellement **MOCKÉE** (résultats basés sur hash pour cohérence)
- Pour intégrer de vraies APIs, il faudra des clés API pour chaque plateforme
