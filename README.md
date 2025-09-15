# 🎓 Intranet - Application de Gestion d'Établissement

[![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![MariaDB](https://img.shields.io/badge/MariaDB-latest-blue.svg)](https://mariadb.org/)
[![Docker](https://img.shields.io/badge/Docker-compose-blue.svg)](https://www.docker.com/)

## 📋 Description

Cette application web développée avec Flask permet la gestion complète d'un établissement scolaire. Elle offre des fonctionnalités avancées de gestion des utilisateurs, des contrats, des documents et des impressions à distance.

**Note** : Ce projet a été développé bénévolement pour un établissement scolaire secondaire (association à but non lucratif).

## 🏗️ Architecture

### Technologies utilisées
- **Backend** : Flask 3.1.0 (Python 3.12)
- **Base de données** : MariaDB (MySQL)
- **ORM** : SQLAlchemy 2.0.38
- **Serveur web** : Waitress + Nginx (reverse proxy)
- **Conteneurisation** : Docker & Docker Compose
- **Sécurité** : Hachage SHA-256, sessions Flask, HTTPS

### Structure du projet
```
├── app/                    # 🐍 Application Flask principale
│   ├── __init__.py        # Initialisation de l'application
│   ├── models.py          # Modèles de données SQLAlchemy
│   ├── routes.py          # Routes et logique métier
│   ├── docs.py            # Gestion des documents
│   ├── impression.py      # Gestion des impressions
│   ├── nginx/             # Configuration Nginx + certificats SSL
│   ├── static/            # Fichiers statiques (CSS, JS, images)
│   └── templates/         # Templates HTML Jinja2
├── documents/             # 📁 Stockage des documents uploadés
├── veraudiere/            # 🐍 Environnement virtuel Python
├── config.py              # ⚙️ Configuration de l'application
├── run.py                 # 🚀 Point d'entrée principal
├── requirements.txt       # 📦 Dépendances Python
├── .env.example           # 📋 Template de configuration
├── generate-env.sh        # 🔐 Script de génération de configuration
├── Dockerfile.app         # 🐳 Configuration Docker
├── docker-compose.yaml    # 🐳 Orchestration des services
└── entrypoint.sh          # 🚀 Script de démarrage
```

## 🚀 Installation et Déploiement

### ✅ Liste de contrôle pré-installation

Avant de commencer, assurez-vous d'avoir :

- [ ] **Docker** installé (version 20.10+)
- [ ] **Docker Compose** installé (version 2.0+)
- [ ] **Git** installé pour cloner le projet
- [ ] **Accès root/sudo** sur le serveur
- [ ] **Ports 80 et 443** disponibles sur votre serveur
- [ ] **Au moins 2GB** d'espace disque libre
- [ ] **Au moins 1GB** de RAM disponible

### 📋 Guide d'installation étape par étape

#### Étape 1 : Préparation de l'environnement

Vérifier les prérequis
```bash
docker --version
docker-compose --version
git --version
```

#### Étape 2 : Clonage du projet

Cloner le dépôt
```bash
git clone https://github.com/remiv1/Intranet.git
cd Intranet
```

#### Étape 3 : Configuration automatique

Générer automatiquement la configuration avec mots de passe sécurisés
```bash
./generate-env.sh
```

**Alternative manuelle :**
Copier le fichier de configuration exemple
```bash
cp .env.example .env
nano .env  # Éditer avec vos valeurs
```

#### Étape 4 : Personnalisation de la configuration

Éditez le fichier `.env` généré et modifiez selon vos besoins :

```bash
nano .env
```

**Variables importantes à vérifier :**
- [ ] `FILES_LOCAL_PATH` : Chemin local pour les documents
- [ ] `PRINT_LOCAL_PATH` : Chemin local pour les impressions
- [ ] `DB_LOCAL_PATH` : Chemin local pour la base de données
- [ ] `SSH_HOST`, `SSH_USER` : Configuration SSH si nécessaire
- [ ] `EMAIL_USER`, `EMAIL_SMTP` : Configuration email
- [ ] `PRINTER_NAME` : Nom de votre imprimante

#### Étape 5 : Création des répertoires

```bash
mkdir -p $(grep FILES_LOCAL_PATH .env | cut -d'=' -f2)
mkdir -p $(grep PRINT_LOCAL_PATH .env | cut -d'=' -f2)
mkdir -p $(grep DB_LOCAL_PATH .env | cut -d'=' -f2)

# Définir les permissions appropriées
sudo chown -R $USER:$USER $(grep FILES_LOCAL_PATH .env | cut -d'=' -f2)
sudo chown -R $USER:$USER $(grep PRINT_LOCAL_PATH .env | cut -d'=' -f2)
sudo chmod 755 $(grep FILES_LOCAL_PATH .env | cut -d'=' -f2)
```

#### Étape 6 : Configuration SSL (Optionnel mais recommandé)

Placer vos certificats SSL dans app/nginx/certs/
```bash
sudo cp votre-certificat.pem app/nginx/certs/cert.pem
sudo cp votre-cle-privee.pem app/nginx/certs/privkey.pem
sudo chmod 600 app/nginx/certs/privkey.pem
```

#### Étape 7 : Construction et lancement

Construire et lancer l'application
```bash
docker-compose build
docker-compose up -d
```

#### Étape 8 : Vérification du déploiement

Vérifier que tous les conteneurs sont en cours d'exécution
```bash
docker-compose ps

# Vérifier les logs en cas de problème
docker-compose logs web
docker-compose logs db
docker-compose logs nginx
```

#### Étape 9 : Premier accès

Accéder à l'application
```bash
Ouvrir http://localhost (ou https://localhost si SSL configuré)
Tester la connexion avec un compte administrateur
```

### 🔧 Commandes utiles

```bash
# Arrêter l'application
docker-compose down

# Redémarrer l'application
docker-compose restart

# Voir les logs en temps réel
docker-compose logs -f web

# Accéder au conteneur de l'application
docker-compose exec web bash

# Accéder à la base de données
docker-compose exec db mysql -u root -p

# Mise à jour de l'application
git pull
docker-compose build
docker-compose up -d

# Sauvegarde de la base de données
docker-compose exec db mysqldump -u root -p$(grep ROOT_PASSWORD .env | cut -d'=' -f2) $(grep DB_NAME .env | cut -d'=' -f2) > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 📋 Variables d'environnement détaillées

Le fichier `.env` contient toutes les variables de configuration nécessaires :
| Variable           | Description                        | Exemple                       |
|--------------------|------------------------------------|-------------------------------|
| `DB_USER`          | Utilisateur de la base de données  | `intranet_user`               |
| `DB_PASSWORD`      | Mot de passe de la base de données | *Généré automatiquement*      |
| `DB_HOST`          | Hôte de la base de données         | `db`                          |
| `DB_NAME`          | Nom de la base de données          | `intranet_db`                 |
| `ROOT_PASSWORD`    | Mot de passe root MySQL            | *Généré automatiquement*      |
| `SECRET_KEY`       | Clé secrète Flask                  | *Généré automatiquement*      |
| `FILES_LOCAL_PATH` | Chemin local des documents         | `/var/www/intranet/documents` |
| `PRINT_LOCAL_PATH` | Chemin local des impressions       | `/var/www/intranet/print`     |
| `SSH_HOST`         | Serveur SSH pour transferts        | `192.168.1.100`               |
| `PRINTER_NAME`     | Nom de l'imprimante                | `HP_LaserJet_Pro`             |
| `EMAIL_SMTP`       | Serveur SMTP                       | `smtp.gmail.com`              |

## 🗄️ Base de Données

### Architecture de la base de données

L'application utilise **MariaDB** avec 4 tables principales interconnectées :

```sql
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   99_Users      │    │  01_Contrats    │    │ 11_Documents    │
│                 │    │                 │    │                 │
│ ├─ id (PK)      │    │ ├─ id (PK)      │ ◄──┤ ├─ id_contrat(FK)│
│ ├─ identifiant  │    │ ├─ type_contrat │    │ ├─ type_document│
│ ├─ sha_mdp      │    │ ├─ Stype        │    │ ├─ Descriptif   │
│ ├─ habilitation │    │ ├─ entreprise   │    │ ├─ str_lien     │
│ └─ Locked       │    │ ├─ date_debut   │    │ └─ date_document│
└─────────────────┘    │ └─ date_fin     │    └─────────────────┘
                       └─────────────────┘
                                │
                                │
                       ┌──────────────────┐
                       │ 12_Evenements    │
                       │                  │
                       │ ├─ id_contrat(FK) │
                       │ ├─ type_evenement│
                       │ ├─ Stype         │
                       │ └─ Descriptif    │
                       └──────────────────┘
```

### 📊 Structure détaillée des tables

#### Table `99_Users` - Gestion des utilisateurs
| Champ          | Type         | Description                |
|----------------|--------------|----------------------------|
| `id`           | INT(11) PK   | Identifiant unique         |
| `Prenom`       | VARCHAR(255) | Prénom de l'utilisateur    |
| `Nom`          | VARCHAR(255) | Nom de l'utilisateur       |
| `mail`         | VARCHAR(255) | Adresse email              |
| `identifiant`  | VARCHAR(25)  | Login de connexion         |
| `sha_mdp`       | VARCHAR(255) | Mot de passe hashé SHA-256 |
| `habilitation` | INT(11)      | Niveau d'autorisation      |
| `Début`        | DATE         | Date de début d'accès      |
| `Fin`          | DATE         | Date de fin d'accès        |
| `Locked`       | BIT(1)       | Compte verrouillé (0/1)    |

#### Table `01_Contrats` - Gestion des contrats
| Champ               | Type         | Description               |
|---------------------|--------------|---------------------------|
| `id`                | INT(11) PK   | Identifiant unique        |
| `type_contrat`      | VARCHAR(50)  | Type de contrat           |
| `Stype`             | VARCHAR(50)  | Sous-type de contrat      |
| `entreprise`        | VARCHAR(255) | Nom de l'entreprise       |
| `id_externe_contrat`| VARCHAR(50)  | Numéro de contrat externe |
| `intitule`          | VARCHAR(255) | Intitulé du contrat       |
| `date_debut`        | DATE         | Date de début             |
| `date_fin_preavis`  | DATE         | Date de fin de préavis    |
| `dateFin`           | DATE         | Date de fin de contrat    |

#### Table `11_Documents` - Documents liés aux contrats

| Champ          | Type         | Description               |
|----------------|--------------|---------------------------|
| `id`           | INT(11) PK   | Identifiant unique        |
| `id_contrat`   | INT(11) FK   | Référence vers le contrat |
| `type_document`| VARCHAR(50)  | Type de document          |
| `SType`        | VARCHAR(50)  | Sous-type de document     |
| `Descriptif`   | VARCHAR(255) | Description du document   |
| `str_lien`     | VARCHAR(255) | Chemin vers le fichier    |
| `date_document`| DATE         | Date du document          |
| `Name`         | VARCHAR(30)  | Nom du créateur           |

#### Table `12_Evenements` - Événements liés aux contrats

| Champ           | Type         | Description                |
|-----------------|--------------|----------------------------|
| `id`            | INT(11) PK   | Identifiant unique         |
| `id_contrat`    | INT(11) FK   | Référence vers le contrat  |
| `date_evenement`| DATE         | Date de l'événement        |
| `type_evenement`| VARCHAR(50)  | Type d'événement           |
| `Stype`         | VARCHAR(50)  | Sous-type d'événement      |
| `Descriptif`    | VARCHAR(255) | Description de l'événement |

### 🔐 Système d'Habilitations

L'application utilise un système d'habilitations numérique flexible :

| Code  | Rôle                     | Permissions                      |
|-------|--------------------------|----------------------------------|
| **1** | 🔧 Super-administrateur  | Gestion des droits utilisateurs  |
| **2** | 👤 Administrateur        | Gestion utilisateurs et contrats |
| **3** | 🎓 Professeur principal  | Espace professeurs principaux    |
| **4** | 📚 Professeur            | Espace professeurs               |
| **5** | 🎒 Élève                 | Espace élèves                    |
| **6** | 🖨️ Impression            | Accès aux fonctions d'impression |

**Combinaisons possibles :**
- `126` = Super-admin + Admin + Impression
- `234` = Admin + Prof principal + Prof
- `56` = Élève + Impression

### 🗂️ Initialisation de la base de données

Les tables sont créées automatiquement au premier lancement
Vérification de la structure :
```bash
docker-compose exec db mysql -u root -p$(grep ROOT_PASSWORD .env | cut -d'=' -f2) $(grep DB_NAME .env | cut -d'=' -f2) -e "SHOW TABLES;"
```

## ⭐ Fonctionnalités Principales

### 🔐 Authentification et Sécurité
- [x] **Connexion sécurisée** avec hachage SHA-256
- [x] **Système anti-brute force** : limitation à 3 tentatives
- [x] **Verrouillage automatique** des comptes après échecs
- [x] **Gestion des sessions** Flask sécurisées
- [x] **HTTPS** avec certificats SSL/TLS
- [x] **Validation des entrées** côté serveur

### 👥 Gestion des Utilisateurs
- [x] **CRUD complet** : Création, lecture, modification, suppression
- [x] **Système d'habilitations** multi-niveaux (1-6)
- [x] **Déverrouillage de comptes** par les administrateurs
- [x] **Interface d'administration** intuitive
- [x] **Gestion des dates** de début/fin d'accès
- [x] **Recherche et filtres** avancés

### 📋 Gestion des Contrats
- [x] **Création de contrats** avec formulaires structurés
- [x] **Suivi des échéances** (début, préavis, fin)
- [x] **Classification** par type et sous-type
- [x] **Liaison avec entreprises** et partenaires
- [x] **Historique complet** des modifications
- [x] **Tableau de bord** avec indicateurs

### 📄 Gestion Documentaire
- [x] **Upload sécurisé** de fichiers multiples
- [x] **Nomenclature automatique** des documents
- [x] **Classification** par type et sous-type
- [x] **Téléchargement sécurisé** avec contrôle d'accès
- [x] **Support multi-formats** : PDF, images, Office
- [x] **Aperçu en ligne** pour certains formats
- [x] **Versioning** et historique des documents

### 📅 Gestion des Événements
- [x] **Ajout d'événements** liés aux contrats
- [x] **Chronologie interactive** des événements
- [x] **Classification** des types d'événements
- [x] **Notifications automatiques** d'échéances
- [x] **Recherche temporelle** par périodes
- [x] **Export** des données au format CSV/PDF

### 🖨️ Impression à Distance
- [x] **Upload et impression** de documents
- [x] **Configuration avancée** des paramètres :
  - Nombre de copies (1-100)
  - Recto/verso automatique
  - Format papier (A4, A3, Letter)
  - Orientation (Portrait/Paysage)
  - Mode couleur/noir et blanc
  - Qualité d'impression
- [x] **File d'attente** des impressions
- [x] **Suppression automatique** après impression
- [x] **Historique** des impressions par utilisateur

### 📊 Tableaux de Bord et Rapports
- [x] **Dashboard principal** avec métriques clés
- [x] **Graphiques interactifs** (contrats, échéances)
- [x] **Rapports automatisés** d'échéances
- [x] **Export de données** (CSV, PDF, Excel)
- [x] **Statistiques d'utilisation** par utilisateur
- [x] **Alertes visuelles** pour les actions urgentes

### 🌐 Interface Utilisateur
- [x] **Design responsive** adaptatif mobile/desktop
- [x] **Interface intuitive** avec navigation claire
- [x] **Thème sombre/clair** selon préférences
- [x] **Recherche globale** dans tous les modules
- [x] **Raccourcis clavier** pour actions fréquentes
- [x] **Notifications toast** pour feedback utilisateur

## 🔧 Maintenance et Monitoring

### 📋 Liste de contrôle maintenance

#### Vérifications quotidiennes
- [ ] **État des conteneurs** : `docker-compose ps`
- [ ] **Espace disque** disponible : `df -h`
- [ ] **Logs d'erreurs** : `docker-compose logs --tail=50 web`
- [ ] **Connexions base de données** actives
- [ ] **Certificats SSL** (validité restante)

#### Vérifications hebdomadaires
- [ ] **Sauvegarde base de données** testée
- [ ] **Rotation des logs** (si configurée)
- [ ] **Mises à jour de sécurité** Docker
- [ ] **Performance** de l'application
- [ ] **Nettoyage** des fichiers temporaires

#### Vérifications mensuelles
- [ ] **Sauvegarde complète** du système
- [ ] **Test de restauration** des sauvegardes
- [ ] **Mise à jour** des dépendances Python
- [ ] **Audit de sécurité** des accès
- [ ] **Optimisation** base de données

### 📊 Monitoring et Logs

Consulter les logs en temps réel
```bash
docker-compose logs -f web          # Logs application
docker-compose logs -f db           # Logs base de données  
docker-compose logs -f nginx        # Logs serveur web

# Logs spécifiques par service
docker-compose logs --tail=100 web  # 100 dernières lignes
docker-compose logs --since=1h web  # Logs de la dernière heure

# Monitoring des ressources
docker stats                        # Utilisation CPU/RAM
docker-compose top                  # Processus actifs
```

### 💾 Stratégie de Sauvegarde

#### Sauvegarde automatique quotidienne
```bash
#!/bin/bash
# Script de sauvegarde à programmer dans crontab

BACKUP_DIR="/var/backups/intranet"
DATE=$(date +%Y%m%d_%H%M%S)

# Créer le répertoire de sauvegarde
mkdir -p $BACKUP_DIR

# Sauvegarde de la base de données
docker-compose exec -T db mysqldump -u root -p$(grep ROOT_PASSWORD .env | cut -d'=' -f2) $(grep DB_NAME .env | cut -d'=' -f2) > $BACKUP_DIR/db_$DATE.sql

# Sauvegarde des documents
tar -czf $BACKUP_DIR/documents_$DATE.tar.gz $(grep FILES_LOCAL_PATH .env | cut -d'=' -f2)

# Sauvegarde de la configuration
cp .env $BACKUP_DIR/env_$DATE.backup

# Nettoyage des anciennes sauvegardes (garder 30 jours)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

#### Restauration d'urgence
```bash
# Restaurer la base de données
docker-compose exec -T db mysql -u root -p$(grep ROOT_PASSWORD .env | cut -d'=' -f2) $(grep DB_NAME .env | cut -d'=' -f2) < backup_file.sql

# Restaurer les documents  
tar -xzf documents_backup.tar.gz -C /

# Redémarrer l'application
docker-compose restart
```

### 🔄 Mise à jour de l'Application

#### Procédure de mise à jour
```bash
# 1. Sauvegarder avant mise à jour
./backup-script.sh

# 2. Arrêter l'application
docker-compose down

# 3. Sauvegarder la configuration actuelle
cp .env .env.backup

# 4. Mettre à jour le code source
git stash                    # Sauvegarder modifications locales
git pull origin main         # Récupérer dernière version
git stash pop               # Restaurer modifications si nécessaire

# 5. Vérifier les nouvelles variables d'environnement
diff .env.example .env      # Comparer configurations

# 6. Reconstruire les images
docker-compose build --no-cache

# 7. Relancer l'application
docker-compose up -d

# 8. Vérifier le bon fonctionnement
docker-compose ps
curl -I http://localhost    # Test de connectivité
```

### 🛡️ Sécurité et Bonnes Pratiques

#### Configuration sécurisée
- [ ] **Mots de passe forts** : utilisez `generate-env.sh`
- [ ] **SECRET_KEY unique** : changez régulièrement
- [ ] **HTTPS activé** : certificats SSL valides
- [ ] **Firewall configuré** : ports 80, 443 uniquement
- [ ] **Mises à jour régulières** : système et conteneurs

#### Permissions fichiers
```bash
# Sécuriser les fichiers de configuration
chmod 600 .env
chmod 600 app/nginx/certs/privkey.pem
chmod 644 app/nginx/certs/cert.pem

# Sécuriser les répertoires de données
chown -R 999:999 $(grep DB_LOCAL_PATH .env | cut -d'=' -f2)
chmod 755 $(grep FILES_LOCAL_PATH .env | cut -d'=' -f2)
```

#### Audit de sécurité
```bash
# Vérifier les ports ouverts
netstat -tlnp | grep :80
netstat -tlnp | grep :443

# Vérifier les conteneurs actifs
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Analyser les logs de sécurité
grep "Failed login" docker-compose logs web
grep "403\|404\|500" docker-compose logs nginx
```

### 🚨 Procédures d'Urgence

#### En cas de panne
1. **Diagnostic rapide**
   ```bash
   - [ ] docker-compose ps                    # État des conteneurs
   - [ ] docker-compose logs --tail=20 web    # Erreurs récentes
   - [ ] df -h                                # Espace disque
   - [ ] free -h                              # Mémoire disponible
   ```

2. **Redémarrage d'urgence**
   ```bash
   - [ ] docker-compose down
   - [ ] docker-compose up -d
   ```

3. **Restauration complète**
   ```bash
   - [ ] docker-compose down -v              # Arrêt + suppression volumes
   - [ ] docker system prune -a              # Nettoyage complet
   - [ ] Restaurer depuis sauvegarde
   - [ ] docker-compose up -d
   ```

#### Contacts d'urgence
- [ ] **Administrateur système** : [Rémi Verschuur, remiv1@gmail.com]
- [ ] **Développeur** : [Rémi Verschuur, remiv1@gmail.com]
- [ ] **Support infrastructure** : [Rémi Verschuur, remiv1@gmail.com]

## 🚀 Support et Développement

### 🏗️ Architecture du Code

#### Structure modulaire
```
app/
├── __init__.py          # 🚀 Initialisation Flask + configuration
├── models.py            # 🗄️ Modèles SQLAlchemy (Tables BDD)
├── routes.py            # 🛣️ Routes principales + logique métier
├── docs.py              # 📄 Gestion des documents
├── impression.py        # 🖨️ Système d'impression
├── static/              # 🎨 Assets front-end
│   ├── css/            # Styles CSS par module
│   ├── js/             # Scripts JavaScript
│   └── img/            # Images et icônes
└── templates/           # 📄 Templates Jinja2
    ├── base.html       # Template de base
    ├── login.html      # Page de connexion
    ├── index.html      # Tableau de bord
    └── *.html          # Pages spécialisées
```

#### Patterns utilisés
- [x] **MVC** : Séparation Models/Views/Controllers
- [x] **Repository Pattern** : Accès aux données centralisé
- [x] **Factory Pattern** : Création de l'application Flask
- [x] **Decorator Pattern** : Gestion des permissions
- [x] **Observer Pattern** : Événements et notifications

### 🔧 Guide de Développement

#### Configuration de l'environnement de développement
```bash
# Cloner le projet
git clone https://github.com/remiv1/Intranet.git
cd Intranet

# Créer l'environnement virtuel Python
python3 -m venv veraudiere
source veraudiere/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configuration pour le développement
cp .env.example .env.dev
nano .env.dev  # Adapter pour environnement local
```

#### Lancement en mode développement
```bash
# Variables d'environnement de développement
export FLASK_ENV=development
export FLASK_DEBUG=1

# Lancement direct (sans Docker)
python run.py

# Ou avec Docker en mode dev
docker-compose -f docker-compose.dev.yml up
```

### 📝 Ajout de Nouvelles Fonctionnalités

#### 1. Nouveau modèle de données
```python
# Dans app/models.py
class NouveauModele(db.Model):
    __tablename__ = 'nouveau_modele'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255), nullable=False)
    # ... autres champs
```

#### 2. Nouvelles routes
```python
# Dans app/routes.py
@app.route('/nouvelle-fonctionnalite')
@login_required
@permission_required(['2', '6'])  # Droits requis
def nouvelle_fonctionnalite():
    # Logique métier
    return render_template('nouvelle_page.html')
```

#### 3. Nouveau template
```html
<!-- Dans app/templates/nouvelle_page.html -->
{% extends "base.html" %}
{% block title %}Nouvelle Fonctionnalité{% endblock %}
{% block content %}
    <!-- Contenu de la page -->
{% endblock %}
```

#### 4. Tests unitaires
```python
# Dans tests/test_nouvelle_fonctionnalite.py
import unittest
from app import create_app

class TestNouvelleFonctionnalite(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
    
    def test_nouvelle_route(self):
        response = self.client.get('/nouvelle-fonctionnalite')
        self.assertEqual(response.status_code, 200)
```

### 🔍 Débogage et Tests

#### Logs de développement
```python
# Utilisation du logger Flask
import logging
logging.basicConfig(level=logging.DEBUG)

# Dans le code
app.logger.debug("Message de débogage")
app.logger.info("Information")
app.logger.warning("Avertissement")
app.logger.error("Erreur")
```

#### Tests automatisés
```bash
# Exécution des tests
python -m pytest tests/
python -m pytest tests/ -v --coverage

# Tests spécifiques
python -m pytest tests/test_models.py
python -m pytest tests/test_routes.py
```

### 📊 Métriques et Performance

#### Monitoring de performance
```python
# Profiling des requêtes SQL
from flask_sqlalchemy import get_debug_queries

@app.after_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= app.config['SLOW_DB_QUERY_TIME']:
            app.logger.warning(f'Requête lente: {query.statement}')
    return response
```

#### Optimisations recommandées
- [ ] **Index BDD** : sur les clés étrangères et champs de recherche
- [ ] **Cache Redis** : pour les requêtes fréquentes
- [ ] **Compression** : GZIP pour les réponses HTTP
- [ ] **CDN** : pour les assets statiques
- [ ] **Pool de connexions** : optimiser l'accès BDD

### 🐛 Résolution de Problèmes Courants

#### Problème : Base de données inaccessible
```bash
# Diagnostic
docker-compose ps db                           # Conteneur actif ?
docker-compose logs db                         # Logs d'erreur ?
docker-compose exec db mysql -u root -p        # Connexion directe
```

* Solution
- [ ] Vérifier les variables d'environnement
- [ ] Redémarrer le conteneur : docker-compose restart db

#### Problème : Permissions insuffisantes
```sql
// Vérifier les habilitations utilisateur
SELECT habilitation FROM 99_Users WHERE identifiant='user';

// Modifier les permissions
UPDATE 99_Users SET habilitation=126 WHERE identifiant='admin';
```

#### Problème : Certificats SSL expirés
```bash
# Vérifier l'expiration
openssl x509 -in app/nginx/certs/cert.pem -text -noout | grep "Not After"

# Renouveler avec Let's Encrypt
-certbot renew
docker-compose restart nginx
```

### 📞 Support et Communauté

#### Canaux de support
- [x] **GitHub Issues** : Bugs et demandes de fonctionnalités
- [x] **Documentation** : Wiki du projet
- [x] **Email** : Contact direct développeur
- [x] **Chat** : Support temps réel (si configuré)

#### Contribution au projet

* Fork et contribution :

- [ ] Fork du projet sur GitHub
- [ ] git checkout -b nouvelle-fonctionnalite
- [ ] # Développement et tests
- [ ] git commit -m "feat: ajout nouvelle fonctionnalité"
- [ ] git push origin nouvelle-fonctionnalite
- [ ] # Créer une Pull Request

#### Standards de code

- [ ] **PEP 8** : Style de code Python
- [ ] **Type hints** : Documentation des types
- [ ] **Docstrings** : Documentation des fonctions
- [ ] **Tests** : Couverture minimum 80%
- [ ] **Security** : Validation des entrées utilisateur

---

## 🎯 Informations Projet

*Développé avec ❤️ pour l'éducation*

Ce projet open-source a été créé bénévolement pour répondre aux besoins spécifiques de gestion d'un établissement scolaire. Il évoluera selon les retours d'expérience et les contributions de la communauté.

### 📈 Roadmap

#### Version actuelle : 1.0
- [x] Gestion complète des contrats
- [x] Système d'impression à distance  
- [x] Interface responsive
- [x] Sécurité renforcée

#### Version future : 2.0
- [ ] API REST complète
- [ ] Application mobile
- [ ] Intégration calendrier
- [ ] Notifications push
- [ ] Dashboard analytics avancé

### 🤝 Remerciements

Merci à tous les contributeurs qui ont permis à ce projet de voir le jour et d'évoluer :
- Équipe pédagogique de l'établissement
- Développeurs bénévoles
- Testeurs et utilisateurs finaux

---

**Pour toute question, suggestion ou problème :**
📧 [github.com/remiv1](https://github.com/remiv1)  
🐙 [GitHub Issues](https://github.com/remiv1/Intranet/issues)  
📚 [Documentation complète](https://github.com/remiv1/Intranet/wiki)
