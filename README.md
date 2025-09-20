# 🎓 Intranet - Application de Gestion d'Établissement

[![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.38-green.svg)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Alembic-1.11.1-green.svg)](https://alembic.sqlalchemy.org/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![MariaDB](https://img.shields.io/badge/MariaDB-latest-blue.svg)](https://mariadb.org/)
[![Docker](https://img.shields.io/badge/Docker-compose-blue.svg)](https://www.docker.com/)
[![CSS](https://img.shields.io/badge/CSS-3-blue.svg)](https://developer.mozilla.org/fr/docs/Web/CSS)
[![HTML5](https://img.shields.io/badge/HTML5-orange.svg)](https://developer.mozilla.org/fr/docs/Web/HTML)
[![JavaScript](https://img.shields.io/badge/JavaScript-yellow.svg)](https://developer.mozilla.org/fr/docs/Web/JavaScript)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Description

Cette application web développée avec Flask permet la gestion complète d'un établissement scolaire. Elle offre des fonctionnalités avancées de gestion des utilisateurs, des contrats, des documents et des impressions à distance.

**Note** : Ce projet a été développé bénévolement pour un établissement scolaire secondaire (association à but non lucratif).

## 🏗️ Architecture

### Technologies utilisées

- **Backend** : Flask 3.1.0 (Python 3.12)
- **Base de données** : MariaDB (MySQL) 12.0.2
- **ORM** : SQLAlchemy 2.0.38
- **Migrations** : Alembic 1.16.5
- **Serveur web** : Waitress + Nginx (reverse proxy)
- **Conteneurisation** : Docker & Docker Compose
- **Sécurité** : Hachage SHA-256, sessions Flask, HTTPS

### Structure du projet

```txt
.
├── alembic/                # ⚗️ Migrations de la base de données
├── app/                    # 🐍 Application Flask principale
│   ├── nginx/              # 🔐 Configuration Nginx
│   ├── static/             # Fichiers statiques (CSS, JS, images)
│   │    ├── css/           # Styles CSS
│   │    ├── js/            # Scripts JavaScript
│   │    └── img/           # Images et icônes
│   ├── templates/          # Templates HTML Jinja2
│   ├── __init__.py         # 🐍 Initialisation de l'application
│   ├── application.py      # 🐍 Application et routes flask
│   ├── config.py           # 🔐 Configuration Flask
│   ├── Dockerfile          # 🐳 Dockerfile pour l'application
│   ├── docs.py             # 📁 Gestion des documents
│   ├── entrypoint.sh       # 🔐 Script de démarrage
│   ├── habilitations.py    # 🔐 Gestion des habilitations et permissions
│   ├── impression.py       # 🖨️ Gestion des impressions
│   ├── models.py           # ⚗️ Modèles de données SQLAlchemy
│   ├── rapport_echeance.py # ⚙️ Création des rapports d'échéances
│   └── run.py              # ⚙️ Point d'entrée principal
├── backup/                 # 🗄️ Sauvegarde Base de données MariaDB et scripts de sauvegardes
├── database/               # 🗄️ Dossier de la base de données
│   ├── CHANGELOG.md        # ⚗️ Historique des versions de la base de données
│   ├── Dockerfile.mariadb  # 🐳 Fichier Docker pour MariaDB
│   └── init_user.sql       # 🗄️ Création du premier utilisateur admin
├── documents/              # 📁 Stockage des documents uploadés (peut être mis ailleurs)
├── print/                  # 🖨️ Stockage des documents à imprimer (peut être mis ailleurs)
├── veraudiere/             # 🐍 Environnement virtuel Python
├── .env.example            # ⚙️ Fichier de configuration exemple
├── alembic.ini             # ⚙️ Fichier de configuration des migrations
├── docker-compose.yaml     # 🐳 Orchestration des services
├── generate-env.sh         # 🔐 Script de génération de configuration
├── INSTALL                 # 📋 Guide d'installation
├── LICENSE                 # 📜 Licence Apache
├── requirements.txt        # 🐍 Dépendances Python
└── todo.md                 # 🚀 Liste des tâches à réaliser
```

## 🚀 Installation et Déploiement

Voir le fichier [INSTALL.md](INSTALL.md) pour un guide d'installation détaillé.

### 🔧 Commandes utiles

```bash
# Arrêter l'application + arrêt et suppression des données
docker compose down
docker compose down -v

# Redémarrer l'application
docker compose restart

# Voir les logs en temps réel
docker compose logs -f web

# Accéder au conteneur de l'application
docker compose -it exec web bash

# Accéder à la base de données
docker compose -it exec db mysql -u root -p

# Mise à jour de l'application
git pull
docker compose build
docker compose up -d

# Sauvegarde de la base de données
./backup/backup-script.sh
```

### 📋 Variables d'environnement détaillées

Le fichier `.env` contient toutes les variables de configuration nécessaires :

| Variable             | Description                              | Exemple                           |
|----------------------|------------------------------------------|-----------------------------------|
| `ROOT_PASSWORD`      | Mot de passe root MySQL                  | `mot_de_passe_securise`           |
| `DB_USER`            | Utilisateur de la base de données        | `lsorueidpr`                      |
| `DB_PASSWORD`        | Mot de passe de la base de données       | `mot_de_passe_securise`           |
| `DB_HOST`            | Hôte de la base de données               | `intranet_db`                     |
| `DB_NAME`            | Nom de la base de données                | `msldkfjgury`                     |
| `DB_URL`             | URL de connexion à la base de données    | `mysql+mysqlconnector://...`            |
| `SECRET_KEY`         | Clé secrète Flask                        | `cle_secrete_a_generer`           |
| `FILES_DOCKER_PATH`  | Chemin Docker des documents              | `/documents`                      |
| `PRINT_DOCKER_PATH`  | Chemin Docker des impressions            | `/print`                          |
| `FILES_LOCAL_PATH`   | Chemin local des documents               | `/home/partage/documents`         |
| `PRINT_LOCAL_PATH`   | Chemin local des impressions             | `/home/partage/print`             |
| `DB_DOCKER_PATH`     | Chemin Docker de la base de données      | `/var/lib/mysql`                  |
| `DB_LOCAL_PATH`      | Chemin local de la base de données       | `/var/lib/mysql`                  |
| `PRINTER_NAME`       | Nom de l'imprimante                      | `Imprim_name`                     |
| `SSH_PORT`           | Port SSH                                 | `22`                              |
| `SSH_HOST`           | Hôte SSH                                 | `adresse_ip_a_tester`             |
| `SSH_USERNAME`       | Utilisateur SSH                          | `mqlskdjfhg`                      |
| `SSH_PASSWORD`       | Mot de passe SSH                         | `mqlskdjfhdueirpcl`               |
| `EMAIL_USER`         | Adresse email d'envoi                    | `mail@domaine.com`                |
| `EMAIL_PASSWORD`     | Mot de passe email                       | `msdokgnôpqioghn`                 |
| `EMAIL_SMTP`         | Serveur SMTP                             | `adresse_smtp`                    |
| `EMAIL_PORT`         | Port SMTP                                | `587`                             |

> **Remarque** : Adaptez les chemins et identifiants selon votre environnement. Ne partagez jamais le fichier `.env` publiquement.

## 🗄️ Base de Données

### Architecture de la base de données

L'application utilise **MariaDB** avec 5 tables principales interconnectées :

```sql
┌──────────────────────┐    ┌──────────────────────┐    ┌───────────────────────┐
│   99_Users           │    │  01_Contrats         │    │ 11_Documents          │
│                      │    │                      │    │ ├─ id (PK)            │
│ ├─ id (PK)           │    │ ├─ id (PK)           │ ◄──┤ ├─ id_contrat(FK)     │
│ ├─ identifiant       │    │ ├─ type_contrat      │    │ ├─ type_document      │
│ ├─ sha_mdp           │    │ ├─ sous_type_contrat │    │ ├─ sous_type_document │
│ ├─ habilitation      │    │ ├─ entreprise        │    │ ├─ descriptif         │
│ └─ locked            │    │ ├─ date_debut        │    │ ├─ str_lien           │
└──────────────────────┘    │ └─ date_fin          │    │ └─ date_document      │
                            └──────────────────────┘    └───────────────────────┘
                                │             |
                                │             │       
            ┌───────────────────────┐       ┌───────────────────────┐
            │ 12_Evenements         │       │  13_factures          │
            │ ├─ id (PK)            │       │ ├─ id (PK)            │
            │ ├─ id_contrat(FK)     │       │ ├─ id_contrat(FK)     │
            │ ├─ type_evenement     │       │ ├─ date_facture       │
            │ ├─ sous_type_evenement│       │ ├─ titre_facture      │
            │ ├─ date_evenement     │       │ ├─ str_lien           │
            │ └─ descriptif         │       │ ├─ montant            │
            │                       │       │ └─ name               │
            └───────────────────────┘       └───────────────────────┘
```

### 📊 Structure détaillée des tables

#### Table `99_Users` - Gestion des utilisateurs

| Champ          | Type         | Description                |
|----------------|--------------|----------------------------|
| `id`           | INT(11) PK   | Identifiant unique         |
| `prenom`       | VARCHAR(255) | Prénom de l'utilisateur    |
| `nom`          | VARCHAR(255) | Nom de l'utilisateur       |
| `mail`         | VARCHAR(255) | Adresse email              |
| `identifiant`  | VARCHAR(25)  | Login de connexion         |
| `sha_mdp`      | VARCHAR(255) | Mot de passe hashé SHA-256 |
| `habilitation` | INT(11)      | Niveau d'autorisation      |
| `debut`        | DATE         | Date de début d'accès      |
| `fin`          | DATE         | Date de fin d'accès        |
| `locked`       | BIT(1)       | Compte verrouillé (0/1)    |

#### Table `01_Contrats` - Gestion des contrats

| Champ               | Type         | Description               |
|---------------------|--------------|---------------------------|
| `id`                | INT(11) PK   | Identifiant unique        |
| `type_contrat`      | VARCHAR(50)  | Type de contrat           |
| `sous_type_contrat` | VARCHAR(50)  | Sous-type de contrat      |
| `entreprise`        | VARCHAR(255) | Nom de l'entreprise       |
| `id_externe_contrat`| VARCHAR(50)  | Numéro de contrat externe |
| `intitule`          | VARCHAR(255) | Intitulé du contrat       |
| `date_debut`        | DATE         | Date de début             |
| `date_fin_preavis`  | DATE         | Date de fin de préavis    |
| `date_fin`          | DATE         | Date de fin de contrat    |

#### Table `11_Documents` - Documents liés aux contrats

| Champ               | Type         | Description               |
|---------------------|--------------|---------------------------|
| `id`                | INT(11) PK   | Identifiant unique        |
| `id_contrat`        | INT(11) FK   | Référence vers le contrat |
| `type_document`     | VARCHAR(50)  | Type de document          |
| `sous_type_document`| VARCHAR(50)  | Sous-type de document     |
| `Descriptif`        | VARCHAR(255) | Description du document   |
| `str_lien`          | VARCHAR(255) | Chemin vers le fichier    |
| `date_document`     | DATE         | Date du document          |

#### Table `12_Evenements` - Événements liés aux contrats

| Champ                  | Type         | Description                |
|------------------------|--------------|----------------------------|
| `id`                   | INT(11) PK   | Identifiant unique         |
| `id_contrat`           | INT(11) FK   | Référence vers le contrat  |
| `date_evenement`       | DATE         | Date de l'événement        |
| `type_evenement`       | VARCHAR(50)  | Type d'événement           |
| `sous_type_evenement`  | VARCHAR(50)  | Sous-type d'événement      |
| `descriptif`           | VARCHAR(255) | Description de l'événement |

### 🔐 Système d'Habilitations

L'application utilise un système d'habilitations numérique flexible :

| Code  | Rôle                     | Permissions                      |
|-------|--------------------------|----------------------------------|
| **1** | 🔧 Super-administrateur  | Gestion des droits utilisateurs  |
| **2** | 👤 Administrateur étab.  | Gestion utilisateurs et contrats |
| **3** | 🎓 Professeur principal  | Espace professeurs principaux    |
| **4** | 📚 Professeur            | Espace professeurs               |
| **5** | 🎒 Élève                 | Espace élèves                    |
| **6** | 🖨️ Impression            | Accès aux fonctions d'impression |

**Combinaisons possibles :**

- `126` = Super-admin + Admin + Impression
- `234` = Admin + Prof principal + Prof
- `56` = Élève + Impression

## ⭐ Fonctionnalités Principales

### 🔐 Authentification et Sécurité

- [x] **Connexion sécurisée** avec hachage SHA-256 (modifications à venir Argon2)
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

### 📄 Gestion Documentaire

- [x] **Upload sécurisé** de fichiers multiples
- [x] **Nomenclature automatique** des documents
- [x] **Classification** par type et sous-type
- [x] **Téléchargement sécurisé** avec contrôle d'accès
- [x] **Support multi-formats** : PDF, images, Office
- [x] **Gestion parallèle** des documents et des liens en base

### 📅 Gestion des Événements

- [x] **Ajout d'événements** liés aux contrats
- [x] **Chronologie interactive** des événements
- [x] **Classification** des types d'événements
- [x] **Notifications automatiques** d'échéances
- [ ] **Recherche temporelle** par périodes
- [ ] **Export** des données au format CSV/PDF

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

- [ ] **Dashboard principal** avec métriques clés
- [ ] **Graphiques interactifs** (contrats, échéances)
- [x] **Rapports automatisés** d'échéances
- [ ] **Export de données** (CSV, PDF, Excel)
- [ ] **Statistiques d'utilisation** par utilisateur
- [ ] **Alertes visuelles** pour les actions urgentes

### 🌐 Interface Utilisateur

- [x] **Design responsive** adaptatif mobile/desktop
- [x] **Interface intuitive** avec navigation claire
- [x] **Thème sombre/clair** selon préférences
- [ ] **Recherche globale** dans tous les modules
- [ ] **Raccourcis clavier** pour actions fréquentes
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

#### Sauvegarde automatique quotidienne (à venir)

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
chmod 600 /etc/nginx/certs/intraraudiere.crt
chmod 644 /etc/nginx/certs/intraraudiere.key

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

```txt
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
python -m pytest test/

# Tests spécifiques
python -m pytest tests/test_application.py
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
docker-compose exec db mariadb -u root -p      # Connexion directe
```

**Solution** :

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
openssl x509 -in /etc/nginx/certs/intraraudiere.crt -text -noout | grep "Not After"

# Renouveler avec Let's Encrypt
certbot renew
docker-compose restart nginx
```

### 📞 Support et Communauté

#### Canaux de support

- [x] **GitHub Issues** : Bugs et demandes de fonctionnalités
- [x] **Documentation** : Wiki du projet
- [x] **Email** : [contact](remiv1@gmail.com)

#### Contribution au projet

Fork et contribution :

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

**Développé avec ❤️ pour l'éducation** :

Ce projet open-source a été créé bénévolement pour répondre aux besoins spécifiques de gestion d'un établissement scolaire. Il évoluera selon les retours d'expérience et les contributions de la communauté.

### 📈 Roadmap

#### Version actuelle : 1.x

- [x] Gestion complète des contrats
- [x] Système d'impression à distance  
- [x] Interface responsive
- [x] Sécurité renforcée

#### Version future : 2.x

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
