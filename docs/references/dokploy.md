# Dokploy - Référence Technique

**Date de dernière mise à jour** : 16 novembre 2025

---

## 1. Dockerfile Best Practices (Optimisation pour Dokploy)

**Description**
Dokploy supporte plusieurs types de build dont Dockerfile avec chemins configurables. Les meilleures pratiques recommandent d'utiliser des builds multi-stage avec Alpine Linux pour minimiser la taille des images et les ressources de production.

**Configuration**
```dockerfile
# Multi-stage build pour production
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
ENV NODE_ENV=production

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
CMD ["node", "dist/index.js"]
```

**Champs à configurer dans Dokploy**
- **Dockerfile Path** : `Dockerfile` (ou chemin personnalisé)
- **Docker Context Path** : `.` (répertoire racine)
- **Docker Build Stage** : Optionnel, pour les builds multi-stage

**Bonnes pratiques**
- Utiliser Alpine Linux pour réduire la taille des images
- Implémenter des builds multi-stage pour les applications de production
- Copier uniquement les fichiers nécessaires du stage de build au stage final
- Définir `NODE_ENV=production` pour optimiser les dépendances

**Source** : https://docs.dokploy.com/docs/core/applications/build-type

---

## 2. Gestion des Variables d'Environnement (Env Vars)

**Description**
Dokploy propose un système à trois niveaux pour gérer les variables d'environnement.

**Trois niveaux de variables**

**Niveau Projet (Partagé)**
```
Variables accessibles à tous les services du projet
Syntaxe de référence : ${{project.VARIABLE_NAME}}
Exemple : DATABASE_URL=postgresql://postgres:postgres@database:5432/postgres
```

**Niveau Environnement**
```
Spécifiques à un environnement (staging, production)
Syntaxe de référence : ${{environment.VARIABLE_NAME}}
Permet des configurations différentes par environnement
```

**Niveau Service**
```
Spécifiques à un service individuel
Affichage dans la section "Environment" de chaque service
Variable automatique : DOKPLOY_DEPLOY_URL (en preview deployments)
```

**Configuration des multiline variables**
```
Pour les clés SSH ou certificats, encadrer avec des guillemets doubles :
"-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQE...
-----END PRIVATE KEY-----"
```

**Meilleures pratiques**
- Utiliser les variables partagées pour les configurations répétitives (credentials, URLs)
- Nommer les variables de manière descriptive (ex: `DB_PRIMARY_HOST`)
- Documenter le rôle de chaque variable pour la maintenance
- Garder les secrets sensibles au niveau projet ou service

**Source** : https://docs.dokploy.com/docs/core/variables

---

## 3. Deployment Workflow (Flux de Déploiement)

**Description**
Dokploy recommande une approche de déploiement en production sans build sur le serveur. Utiliser une pipeline CI/CD (GitHub Actions, GitLab CI) pour construire et publier les images Docker, puis les déployer sur Dokploy avec contrôle de santé et rollback automatique.

**Architecture recommandée**

```
1. Développement local → Push vers Git
2. Pipeline CI/CD → Build Docker image
3. Registry (DockerHub, GitLab Registry) → Stockage image
4. Dokploy → Pull et déploiement du pre-built image
5. Health Checks → Validation de déploiement
6. Rollback automatique si défaillance
```

**Configuration de la Pipeline (exemple GitHub Actions)**
```yaml
# .github/workflows/deploy.yml
name: Build and Deploy
on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t registry/app:latest .
      - name: Push to registry
        run: docker push registry/app:latest
      - name: Trigger Dokploy deployment
        run: curl -X POST https://dokploy-instance/api/deploy
```

**Meilleures pratiques production**
- Construire les images en CI/CD
- Déployer des images pré-construites (pas de build sur le serveur)
- Configurer des health checks pour chaque service
- Implémenter des rollbacks automatiques
- Utiliser des volumes persistants pour les données
- Monitorer les déploiements et les logs en temps réel

**Sources**
- https://docs.dokploy.com/docs/core/applications/going-production
- https://docs.dokploy.com/docs/core/docker-compose
- https://docs.dokploy.com/docs/core/applications/advanced
