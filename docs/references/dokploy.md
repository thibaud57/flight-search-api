---
title: "Dokploy - Hosting & Deployment Platform"
description: "Référence complète Dokploy pour déploiement production : build types (Dockerfile, docker-compose), gestion variables environnement (3 niveaux : projet/env/service), deployment workflow (CI/CD → pre-built images → health checks → rollback), multi-stage optimization, secrets management. Consulter pour configuration déploiements, variables, pipelines CI/CD, best practices production."
date: "2025-17-11"
keywords: ["dokploy", "deployment", "hosting", "docker", "dockerfile", "docker-compose", "env-vars", "environment-variables", "production", "ci-cd", "health-checks", "rollback", "secrets", "docker-registry"]
scope: ["deploy"]
technologies: ["dokploy", "docker"]
---

# Dockerfile Best Practices (Optimisation pour Dokploy)

## Description

Dokploy supporte plusieurs types de build dont Dockerfile avec chemins configurables. Les meilleures pratiques recommandent d'utiliser des builds multi-stage avec Alpine Linux pour minimiser la taille des images et les ressources de production.

## Exemple

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

**Champs Dokploy** :
- **Dockerfile Path** : `Dockerfile` (ou chemin personnalisé)
- **Docker Context Path** : `.` (répertoire racine)
- **Docker Build Stage** : Optionnel, pour builds multi-stage

## Points clés

- **Alpine Linux** : Réduit taille images (~60% économie vs images standard)
- **Multi-stage builds** : Sépare build et runtime pour images optimisées production
- **Copie sélective** : Copier uniquement fichiers nécessaires du builder au final stage
- **NODE_ENV=production** : Optimise dépendances et performances runtime

# Gestion des Variables d'Environnement (Env Vars)

## Description

Dokploy propose un système à trois niveaux pour gérer les variables d'environnement.

## Exemple

**Niveau Projet (Partagé)** :
```
Variables accessibles à tous les services du projet
Syntaxe de référence : ${{project.VARIABLE_NAME}}
Exemple : DATABASE_URL=postgresql://postgres:postgres@database:5432/postgres
```

**Niveau Environnement** :
```
Spécifiques à un environnement (staging, production)
Syntaxe de référence : ${{environment.VARIABLE_NAME}}
Permet des configurations différentes par environnement
```

**Niveau Service** :
```
Spécifiques à un service individuel
Affichage dans la section "Environment" de chaque service
Variable automatique : DOKPLOY_DEPLOY_URL (en preview deployments)
```

**Configuration multiline variables** :
```
Pour les clés SSH ou certificats, encadrer avec des guillemets doubles :
"-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQE...
-----END PRIVATE KEY-----"
```

## Points clés

- **Trois niveaux** : Projet (partagé), Environnement (staging/prod), Service (individuel)
- **Syntaxe référence** : `${{project.VAR}}`, `${{environment.VAR}}` pour réutilisation
- **Variables partagées** : Utiliser niveau projet pour credentials et URLs répétitives
- **Nommage descriptif** : Préférer `DB_PRIMARY_HOST` à `HOST` pour clarté
- **Secrets** : Garder au niveau projet ou service (pas environnement public)

# Deployment Workflow (Flux de Déploiement)

## Description

Dokploy recommande une approche de déploiement en production sans build sur le serveur. Utiliser une pipeline CI/CD (GitHub Actions, GitLab CI) pour construire et publier les images Docker, puis les déployer sur Dokploy avec contrôle de santé et rollback automatique.

## Exemple

**Architecture recommandée** :
```
1. Développement local → Push vers Git
2. Pipeline CI/CD → Build Docker image
3. Registry (DockerHub, GitLab Registry) → Stockage image
4. Dokploy → Pull et déploiement du pre-built image
5. Health Checks → Validation de déploiement
6. Rollback automatique si défaillance
```

**Configuration Pipeline (GitHub Actions)** :
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

## Points clés

- **Build externe** : Construire images en CI/CD (pas sur serveur Dokploy)
- **Pre-built images** : Déployer images pré-construites pour rapidité et fiabilité
- **Health checks** : Configurer pour validation automatique déploiements
- **Rollback automatique** : Implémenté nativement par Dokploy si health checks échouent
- **Volumes persistants** : Utiliser pour données (éviter perte lors redéploiements)
- **Monitoring requis** : Surveiller logs et métriques en temps réel

# Ressources

## Documentation Officielle

- **Dokploy Documentation** : https://docs.dokploy.com
- **Build Types** : https://docs.dokploy.com/docs/core/applications/build-type
- **Environment Variables** : https://docs.dokploy.com/docs/core/variables
- **Going to Production** : https://docs.dokploy.com/docs/core/applications/going-production
- **Docker Compose** : https://docs.dokploy.com/docs/core/docker-compose
- **Advanced Configuration** : https://docs.dokploy.com/docs/core/applications/advanced
