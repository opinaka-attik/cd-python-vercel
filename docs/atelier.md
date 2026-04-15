

## 🚀 Atelier DevOps Complet — CD : Du commit à la prod automatiquement

---

## 🎯 Scénario réel (accroche)

> _"Les tests passent. Le code est validé. Et maintenant… le dev doit se connecter, lancer le déploiement à la main, croiser les doigts. C'est long, c'est risqué, c'est humain — donc faillible."_

**Ce qu'on va construire :** un pipeline qui déploie **automatiquement** sur Vercel dès qu'un merge est fait — avec un environnement **staging** pour valider, et un environnement **prod** pour livrer.

---

## 🗺️ Vision globale de ce qu'on va construire

```
[Dev local]
     |
     |-- push --> branche feature
                      |
              [Pull Request ouverte]
                      |
              ✅ CI : tests passent
                      |
              🔀 Merge vers develop
                      |
              🚀 CD : déploiement auto → STAGING
                      |
              👀 Validation humaine sur staging
                      |
              🔀 Merge develop → main
                      |
              🚀 CD : déploiement auto → PRODUCTION
```

---

## 🏗️ PARTIE 1 — Préparer le repo GitHub

### Étape 1 — Créer le repo

Sur [github.com](https://github.com/) → **"New repository"**

|Champ|Valeur|
|---|---|
|Repository name|`cd-python-vercel`|
|Visibility|Public|
|Initialize with README|✅ Cocher|

Cliquer **"Create repository"**

---

### Étape 2 — Créer les deux branches de travail

```bash
git clone https://github.com/TON_USERNAME/cd-python-vercel.git
cd cd-python-vercel

# Créer la branche develop (environnement staging)
git checkout -b develop
git push origin develop
```

> ✅ Tu as maintenant deux branches :
> 
> - `main` → déploie en **production**
> - `develop` → déploie en **staging**

---

### Étape 3 — Définir develop comme branche par défaut _(recommandé)_

Sur GitHub → Settings → Branches → **Default branch** → changer pour `develop`

---

## 📝 PARTIE 2 — Créer l'application Python

### Étape 4 — Créer la structure du projet

```bash
# Tu es sur la branche develop
mkdir api
mkdir tests
mkdir -p .github/workflows
touch api/index.py
touch requirements.txt
touch vercel.json
touch tests/test_app.py
touch tests/__init__.py
touch .github/workflows/ci.yml
touch .github/workflows/cd.yml
```

Structure finale :

```
cd-python-vercel/
├── api/
│   └── index.py          ← l'application Flask
├── tests/
│   ├── __init__.py
│   └── test_app.py
├── requirements.txt
├── vercel.json            ← config Vercel
└── .github/
    └── workflows/
        ├── ci.yml         ← tests (atelier précédent)
        └── cd.yml         ← déploiement (cet atelier)
```

---

### Étape 5 — Écrire l'application Flask

**`api/index.py`**

```python
from flask import Flask, jsonify
import os

app = Flask(__name__)

# Variable d'environnement injectée par Vercel
ENVIRONMENT = os.getenv("APP_ENV", "local")

@app.route("/")
def home():
    return jsonify({
        "message": "Hello depuis l'API Python !",
        "environment": ENVIRONMENT,
        "version": "1.0.0"
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "environment": ENVIRONMENT
    })

@app.route("/sum/<int:a>/<int:b>")
def sum_route(a, b):
    return jsonify({
        "operation": f"{a} + {b}",
        "result": a + b
    })
```

> **Pourquoi `APP_ENV` ?** C'est la variable qu'on va injecter différemment sur staging et prod — les apprenants voient concrètement que le **même code** se comporte différemment selon l'environnement.

---

**`tests/test_app.py`**

```python
import pytest
from api.index import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert "message" in data
    assert "environment" in data

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"

def test_sum(client):
    response = client.get("/sum/3/4")
    assert response.status_code == 200
    assert response.get_json()["result"] == 7
```

---

**`requirements.txt`**

```
flask==3.0.3
pytest==8.2.0
pytest-cov==5.0.0
```

---

**`vercel.json`**

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

---

## ⚙️ PARTIE 3 — Écrire les workflows GitHub Actions

### Étape 6 — CI (rappel de l'atelier précédent)

**`.github/workflows/ci.yml`**

```yaml
name: CI - Tests Python

on:
  pull_request:
    branches: [ main, develop ]   # ← surveille les deux branches

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Récupération du code
        uses: actions/checkout@v4

      - name: Installation Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Installation des dépendances
        run: pip install -r requirements.txt

      - name: Lancement des tests
        run: pytest --cov=api --cov-report=term-missing --cov-fail-under=80
```

---

### Étape 7 — CD (le cœur de cet atelier)

**`.github/workflows/cd.yml`**

```yaml
name: CD - Déploiement automatique Vercel

on:
  push:
    branches:
      - develop   # → déploie sur STAGING
      - main      # → déploie sur PRODUCTION

jobs:

  # ─────────────────────────────────────────
  # JOB 1 : Déploiement STAGING
  # Déclenché uniquement sur la branche develop
  # ─────────────────────────────────────────
  deploy-staging:
    name: 🚧 Déploiement Staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'

    environment:
      name: staging
      url: ${{ steps.deploy.outputs.url }}

    steps:
      - name: Récupération du code
        uses: actions/checkout@v4

      - name: Installation de Vercel CLI
        run: npm install -g vercel

      - name: Déploiement sur Staging (preview)
        id: deploy
        run: |
          url=$(vercel deploy \
            --token=${{ secrets.VERCEL_TOKEN }} \
            --env APP_ENV=staging)
          echo "url=$url" >> $GITHUB_OUTPUT

      - name: Affichage de l'URL de staging
        run: echo "✅ Staging disponible → ${{ steps.deploy.outputs.url }}"

  # ─────────────────────────────────────────
  # JOB 2 : Déploiement PRODUCTION
  # Déclenché uniquement sur la branche main
  # ─────────────────────────────────────────
  deploy-production:
    name: 🚀 Déploiement Production
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    environment:
      name: production
      url: https://cd-python-vercel.vercel.app

    steps:
      - name: Récupération du code
        uses: actions/checkout@v4

      - name: Installation de Vercel CLI
        run: npm install -g vercel

      - name: Déploiement en Production
        run: |
          vercel deploy --prod \
            --token=${{ secrets.VERCEL_TOKEN }} \
            --env APP_ENV=production
        
      - name: Confirmation de déploiement
        run: echo "🎉 Production mise à jour avec succès !"
```

> **Point clé :** le même fichier gère les deux environnements. La condition `if: github.ref ==` sépare les comportements. C'est la logique réelle des équipes DevOps.

---

## ☁️ PARTIE 4 — Configurer Vercel

### Étape 8 — Créer un compte Vercel

1. Aller sur [vercel.com](https://vercel.com/)
2. **"Sign up"** → choisir **"Continue with GitHub"**
3. Autoriser Vercel à accéder à GitHub

---

### Étape 9 — Récupérer le token Vercel

Sur Vercel → **Account Settings** → **Tokens**

1. Cliquer **"Create Token"**
2. Nom : `github-actions-cd`
3. Scope : **Full Account**
4. Cliquer **"Create"**
5. **Copier le token immédiatement** — il ne s'affiche qu'une fois

---

### Étape 10 — Importer le projet sur Vercel

Sur Vercel → **"Add New Project"**

1. Sélectionner le repo `cd-python-vercel`
2. Cliquer **"Import"**
3. Framework Preset : **Other**
4. Cliquer **"Deploy"**

> ✅ Vercel connaît maintenant ton projet.

---

## 🔑 PARTIE 5 — Configurer les secrets GitHub

### Étape 11 — Ajouter le token Vercel dans GitHub

Sur GitHub → ton repo → **Settings** → **Secrets and variables** → **Actions**

Cliquer **"New repository secret"**

|Champ|Valeur|
|---|---|
|Name|`VERCEL_TOKEN`|
|Secret|_(coller le token copié à l'étape 9)_|

Cliquer **"Add secret"**

> ✅ Le token est chiffré. GitHub Actions peut l'utiliser, mais personne ne peut le lire.

---

### Étape 12 — Créer les environnements GitHub

Sur GitHub → Settings → **Environments**

**Créer "staging" :**

1. Cliquer **"New environment"**
2. Nom : `staging`
3. Pas de protection requise
4. Sauvegarder

**Créer "production" :**

1. Cliquer **"New environment"**
2. Nom : `production`
3. Cocher **"Required reviewers"** → ajouter ton nom
4. _(Optionnel)_ Cocher **"Wait timer"** → 5 minutes
5. Sauvegarder

> 🎯 **Point pédagogique :** la prod nécessite une approbation humaine. C'est le dernier filet de sécurité avant le vrai déploiement.

---

## 🚀 PARTIE 6 — Premier push et déploiement staging

### Étape 13 — Pousser le code sur develop

```bash
git add .
git commit -m "feat: ajout app Flask + pipeline CI/CD"
git push origin develop
```

---

### Étape 14 — Observer le pipeline CD se déclencher

Sur GitHub → ton repo → onglet **"Actions"**

Tu vois :

```
🟡 CD - Déploiement automatique Vercel    (en cours)
   └── 🚧 Déploiement Staging             (en cours...)
```

Cliquer sur le workflow pour voir les logs en direct :

```
✅ Récupération du code          → OK
✅ Installation de Vercel CLI    → OK
🟡 Déploiement sur Staging...   → En cours
   Vercel CLI 34.x
   Deploying...
   ✅ Preview: https://cd-python-vercel-git-develop-tonuser.vercel.app
   
✅ Staging disponible → https://cd-python-vercel-git-develop-tonuser.vercel.app
```

---

### Étape 15 — Vérifier le staging

Ouvrir l'URL dans le navigateur :

```json
// GET https://cd-python-vercel-git-develop-xxxx.vercel.app/
{
  "message": "Hello depuis l'API Python !",
  "environment": "staging",
  "version": "1.0.0"
}

// GET /health
{
  "status": "ok",
  "environment": "staging"
}
```

> ✅ **Staging vivant.** L'environnement est clairement identifié. On peut tester sans risque.

---

## 🔀 PARTIE 7 — Valider et pousser en production

### Étape 16 — Ouvrir une Pull Request develop → main

Sur GitHub → ton repo → **"Compare & pull request"**

|Champ|Valeur|
|---|---|
|Title|`release: v1.0.0 — mise en production`|
|Base|`main`|
|Compare|`develop`|

Cliquer **"Create pull request"**

---

### Étape 17 — Observer le CI se déclencher sur la PR

Section **"Checks"** de la PR :

```
🟡 CI - Tests Python / test    → En cours...
✅ CI - Tests Python / test    → Passed
```

---

### Étape 18 — Merger vers main

Le bouton de merge est actif :

```
🟢  Merge pull request   ← CLIQUABLE
✅  "All checks have passed"
```

1. Cliquer **"Merge pull request"**
2. Cliquer **"Confirm merge"**

---

### Étape 19 — Observer le déploiement production

Sur GitHub → Actions :

```
🟡 CD - Déploiement automatique Vercel    (déclenché par le merge)
   └── 🚀 Déploiement Production         (en attente d'approbation...)
```

**Si tu as activé "Required reviewers" :**

```
⏸️  Waiting for review
    This deployment is waiting for your approval.
    [Review deployments]
```

Cliquer **"Review deployments"** → **"Approve and deploy"**

Logs :

```
✅ Récupération du code          → OK
✅ Installation de Vercel CLI    → OK
🟡 Déploiement en Production...
   Vercel CLI 34.x
   Deploying to production...
   ✅ Production: https://cd-python-vercel.vercel.app
   
🎉 Production mise à jour avec succès !
```

---

### Étape 20 — Vérifier la production

```json
// GET https://cd-python-vercel.vercel.app/
{
  "message": "Hello depuis l'API Python !",
  "environment": "production",
  "version": "1.0.0"
}
```

> ✅ **Même code, environnement différent.** La variable `APP_ENV` distingue staging de prod — sans toucher au code.

---

## 🧨 PARTIE 8 — Scénario pédagogique : bug en staging, prod sauvée

### Étape 21 — Introduire un bug sur develop

```bash
git checkout develop
```

Modifier `api/index.py` :

```python
@app.route("/sum/<int:a>/<int:b>")
def sum_route(a, b):
    return jsonify({
        "operation": f"{a} + {b}",
        "result": a - b   # 🐛 BUG VOLONTAIRE
    })
```

```bash
git add api/index.py
git commit -m "feat: amélioration du calcul (bugué)"
git push origin develop
```

---

### Étape 22 — Observer le résultat

**CD déclenché → staging mis à jour automatiquement :**

```
🟢 Staging déployé → https://cd-python-vercel-git-develop-xxxx.vercel.app
```

Tester sur staging :

```json
// GET /sum/3/4
{
  "operation": "3 + 4",
  "result": -1     ← ❌ BUG VISIBLE SUR STAGING
}
```

**La PR develop → main est bloquée :**

```
❌ CI - Tests Python / test — FAILED
   test_sum FAILED: assert -1 == 7

🔴 Merge pull request   ← GRISÉ
⚠️  "Some checks were not successful"
```

> 🎯 **Moment pédagogique clé :** _"Le bug est sur staging. La prod n'a jamais été touchée. C'est exactement le rôle du staging — absorber les erreurs avant qu'elles atteignent les utilisateurs."_

---

### Étape 23 — Corriger et redéployer

```bash
# Corriger le bug
# api/index.py → return a + b

git add api/index.py
git commit -m "fix: correction du calcul dans sum_route"
git push origin develop
```

```
✅ CI passe
✅ Staging redéployé automatiquement
🟢 Merge vers main autorisé
🚀 Production mise à jour
```

---

## 🗺️ Récapitulatif visuel du flux complet

```
[Local - branche develop]
         |
         |── git push origin develop
         |
[GitHub Actions - CI]
         |
         ├── ✅ Tests OK
         |
[GitHub Actions - CD]
         |
         ├── 🚧 Déploiement STAGING auto
         |         |
         |    URL staging disponible
         |    → Test manuel / validation
         |
[Pull Request develop → main]
         |
         ├── ✅ CI passe
         ├── 👀 Review humaine (optionnel)
         ├── 🔀 Merge autorisé
         |
[GitHub Actions - CD]
         |
         ├── (optionnel) ⏸️  Approbation requise
         |
         └── 🚀 Déploiement PRODUCTION auto
                   |
              ✅ Prod vivante
```

---

## 🎓 Débrief final (15 min)

|Question à poser|Ce qu'on veut entendre|
|---|---|
|Quelle est la différence entre CI et CD ?|CI valide, CD livre|
|Pourquoi deux environnements ?|Tester sans risquer la prod|
|Qu'est-ce qu'un secret GitHub ?|Une variable chiffrée, jamais visible dans les logs|
|Pourquoi une approbation humaine sur la prod ?|Dernier filet avant l'impact réel|
|Que se passe-t-il si on push directement sur main ?|Le CD déploie en prod sans passer par staging — dangereux|

---

## 📚 Vocabulaire installé

|Terme|Définition vécue|
|---|---|
|**CD**|Le pipeline qui livre automatiquement après validation|
|**Staging**|La prod "fausse" où on teste sans risque|
|**Production**|L'environnement réel, celui que voient les utilisateurs|
|**Environment secret**|Une clé d'accès chiffrée injectée au runtime|
|**Approval gate**|Un humain qui dit "go" avant le dernier déploiement|
|**Preview URL**|L'URL unique générée par Vercel pour chaque branche|

---

## 🚀 Suite naturelle — Atelier 3

```
Atelier 1  →  CI  : bloquer le code cassé
Atelier 2  →  CD  : livrer automatiquement (cet atelier)
Atelier 3  →  Monitoring : savoir quand la prod est cassée
               → Sentry + alertes + rollback automatique
```