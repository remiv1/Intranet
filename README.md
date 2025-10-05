# 🎓 Intranet - Application de Gestion d'Établissement

[![Version](https://img.shields.io/badge/Version-1.3.0-brightgreen.svg)](https://github.com/remiv1/Intranet/releases/tag/version-1.3.0)
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
[![PDF.js](https://img.shields.io/badge/PDF.js-3.11.174-blue.svg)](https://mozilla.github.io/pdf.js/)
[![jQuery](https://img.shields.io/badge/jQuery-3.7.1-blue.svg)](https://jquery.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-purple.svg)](https://getbootstrap.com/)
[![SignaturePad](https://img.shields.io/badge/SignaturePad-4.1.7-blue.svg)](https://github.com/szimek/signature_pad)

## 🛠️ Évolutions et Roadmap

### ✅ Évolutions Récentes (Septembre-Octobre 2025)

#### Version 1.3.0 (5 octobre 2025) - Module Signature Électronique ✨
- **🖋️ Signature Électronique Complète** : 
  - Placement interactif des points de signature sur PDF
  - Capture graphique haute fidélité avec SignaturePad
  - Génération automatique de PDF signés avec toutes les signatures
  - Sécurisation HMAC pour l'accès aux documents
  - Automatisme d'expiration des documents (événement MySQL CRON)
  - Journalisation complète des actions utilisateur
  - Architecture 3 classes métier : SignatureMaker, SignatureDoer, SignedDocumentCreator
  
#### Version 1.2.0 (Septembre 2025) - Modules de Gestion
- **👥 Gestion des Contacts** : CRUD complet pour les contacts liés aux contrats avec interface responsive
- **📧 Système d'Emails Avancé** : Templates HTML, tokens API sécurisés et logging amélioré
- **💰 Module de Factures** : Gestion complète des factures avec upload sécurisé et nomenclature automatique
- **⚙️ CI/CD et Tests** : Pipeline GitHub Actions complet avec validation Docker et tests automatisés
- **🔧 Refactorisation** : Nettoyage du code, migration snake_case, annotations de type et documentation API

### 🚧 En Cours de Développement

- **📊 Monitoring Avancé** : Intégration MongoDB pour les logs d'activité et dashboard de monitoring
- **� Notifications Signatures** : Email automatique avec PDF signé en pièce jointe aux signataires

### 📋 Prochaines Évolutions Prévues

- **� Améliorations Signatures** : Notifications automatiques par email, rate limiting OTP, audit logs avancés (T4 2025)
- **🧪 Tests Unitaires** : Couverture complète du module signature (T4 2025)
- **�📈 Module de Reporting** : Tableaux de bord et statistiques avancées (T4 2025)
- **📱 Optimisation Mobile** : Amélioration de l'expérience utilisateur sur mobile (T1 2026)
- **⚡ Optimisation Performance** : Analyse et amélioration des performances sur gros volumes (T1 2026)
- **🔐 Sécurité Renforcée** : Audit sécurité et implémentation 2FA (T1 2026)

> 📖 **Rapport détaillé** : Consultez le [rapport d'évolution des branches](./documentation/rapport-evolution-branches.md) pour un historique complet du développement.

## 📝 Description

Cette application web développée avec Flask permet la gestion complète d'un établissement scolaire. Elle offre des fonctionnalités avancées de gestion des utilisateurs, des contrats, des documents et des impressions à distance.

**Note** : Ce projet a été développé bénévolement pour un établissement scolaire secondaire (association à but non lucratif).

## 🏗️ Architecture

### Stack technologique

- **Backend** : Flask 3.1.0 (Python 3.12)
- **Base de données** : MariaDB (MySQL) 12.0.2
- **ORM** : SQLAlchemy 2.0.38
- **Migrations** : Alembic 1.16.5
- **Serveur web** : Waitress + Nginx (reverse proxy)
- **Conteneurisation** : Docker & Docker Compose
- **Sécurité** : Hachage SHA-256, sessions Flask, HTTPS

### Structure du projet

```text
.
├── alembic/                          # ⚗️ Migrations de la base de données
│   ├── versions/                     # Scripts de migration versionnés
│   │   ├── b5f240cb2287_renommage_des_champs_camelcase_en_snake_.py
│   │   └── c8293d28c674_ajout_de_la_table_13_factures.py
│   ├── env.py                        # Configuration de l'environnement Alembic
│   └── script.py.mako                # Template pour nouveaux scripts de migration
├── app/                              # 🐍 Application Flask principale
│   ├── __init__.py                   # 🚀 Initialisation Flask + configuration
│   ├── application.py                # 🛣️ Routes principales et logique métier
│   ├── bp_contracts.py               # 📋 Blueprint pour la gestion des contrats
│   ├── bp_signature.py               # ✍️ Blueprint pour le système de signatures
│   ├── config.py                     # ⚙️ Configuration Flask et variables d'environnement
│   ├── docs.py                       # 📄 Gestion des documents et téléchargements
│   ├── habilitations.py              # 🔐 Système d'habilitations et permissions
│   ├── impression.py                 # 🖨️ Système d'impression à distance
│   ├── models.py                     # 🗄️ Modèles SQLAlchemy et structure BDD
│   ├── rapport_echeances.py          # 📊 Génération des rapports d'échéances
│   ├── run.py                        # 🚀 Point d'entrée principal de l'application
│   ├── signatures.py                 # ✍️ Logique métier pour les signatures électroniques
│   ├── utilities.py                  # 🔧 Fonctions utilitaires et helpers
│   ├── json/                         # 📋 Fichiers de configuration JSON
│   │   ├── admin_modules.json        # Configuration des modules d'administration
│   │   ├── menus.json                # Structure et typologie des menus
│   │   └── modules.json              # Configuration des modules métier
│   ├── nginx/                        # 🌐 Configuration serveur web
│   │   └── nginx.conf                # Configuration principale Nginx
│   ├── static/                       # 🎨 Ressources statiques
│   │   ├── css/                      # 🎨 Feuilles de style CSS
│   │   │   ├── style-accueil.css     # Styles page d'accueil
│   │   │   ├── style-contrats.css    # Styles module contrats
│   │   │   ├── style-general.css     # Styles généraux de l'application
│   │   │   ├── style-impression.css  # Styles module impression
│   │   │   ├── style-login.css       # Styles page de connexion
│   │   │   ├── style-menu.css        # Styles navigation et menus
│   │   │   ├── style-signature.css   # Styles module signatures
│   │   │   └── style-tableau.css     # Styles tableaux de données
│   │   ├── js/                       # 📱 Scripts JavaScript côté client
│   │   └── img/                      # 🖼️ Images et icônes de l'interface
│   ├── templates/                    # 📄 Templates Jinja2
│   │   ├── contrats.html             # Liste des contrats
│   │   ├── contrat_detail.html       # Détail d'un contrat
│   │   ├── ea.html                   # Template EA (Évènements/Actions)
│   │   ├── ei.html                   # Template EI (Entités/Individus)
│   │   ├── ere.html                  # Template ERE (Événements/Rapports/Échéances)
│   │   ├── erp.html                  # Template ERP (Entreprise/Ressources/Planning)
│   │   ├── erpp.html                 # Template ERPP (extension ERP)
│   │   ├── gestion_droits.html       # Gestion des droits utilisateurs
│   │   ├── gestion_utilisateurs.html # Administration des utilisateurs
│   │   ├── index.html                # Tableau de bord principal
│   │   ├── login.html                # Page de connexion
│   │   ├── mail_echeance.html        # Template emails d'échéances
│   │   └── signatures/               # Templates module signatures
│   │       ├── signature_do.html     # Interface de signature
│   │       └── signature_make.html   # Création de signatures
│   ├── Dockerfile.app                # 🐳 Image Docker de l'application
│   └── entrypoint.sh                 # � Script de démarrage du conteneur
├── backup/                           # � Scripts et outils de sauvegarde
│   ├── README.md                     # Documentation des sauvegardes
│   ├── simple-backup.sh              # Script de sauvegarde simple
│   └── simple-restore.sh             # Script de restauration simple
├── database/                         # 🗄️ Configuration et scripts BDD
│   ├── CHANGELOG.md                  # Historique des versions de la BDD
│   ├── Dockerfile.mariadb            # 🐳 Image Docker MariaDB personnalisée
│   └── init_user.sql                 # Script de création utilisateur admin initial
├── documentation/                    # 📚 Documentation technique du projet
│   ├── rapport-evolution-branches.md # Rapport d'évolution des branches Git
│   ├── UML_BdD.dia                   # Diagramme UML de la base (format Dia)
│   └── UML_BdD.svg                   # Diagramme UML de la base (format SVG)
├── documents/                        # 📁 Stockage des fichiers uploadés
│   └── signatures/                   # Documents de signatures électroniques
│       └── temp/                     # Fichiers temporaires de signatures
├── print/                            # 🖨️ File d'attente d'impression
├── test/                             # 🧪 Tests unitaires et d'intégration
│   ├── conftest.py                   # Configuration pytest
│   ├── fixtures.py                   # Fixtures pour les tests
│   ├── pytest.ini                    # Configuration pytest
│   ├── README.md                     # Documentation des tests
│   ├── test_application.py           # Tests de l'application principale
│   └── test_mock_session_refactoring.py # Tests de refactoring des sessions
├── venveraudiere/                    # 🐍 Environnement virtuel Python
│   ├── Include/                      # Headers Python
│   ├── Lib/                          # Bibliothèques Python
│   │   └── site-packages/            # Packages installés
│   ├── Scripts/                      # Exécutables (Windows)
│   │   ├── activate                  # Script d'activation (Unix)
│   │   ├── activate.bat              # Script d'activation (Windows)
│   │   ├── Activate.ps1              # Script d'activation (PowerShell)
│   │   ├── flask.exe                 # Exécutable Flask
│   │   ├── python.exe                # Interpréteur Python
│   │   └── pip.exe                   # Gestionnaire de packages
│   └── pyvenv.cfg                    # Configuration de l'environnement virtuel
├── alembic.ini                       # ⚙️ Configuration des migrations Alembic
├── CODE_OF_CONDUCT.md                # 📜 Code de conduite du projet
├── CONTRIBUTING.md                   # 📋 Guide de contribution
├── docker-compose.dev.yaml           # 🐳 Composition Docker pour développement
├── docker-compose.yaml               # 🐳 Orchestration des services Docker (production)
├── generate-env.sh                   # 🔐 Script de génération automatique du .env
├── INSTALL.md                        # 📋 Guide d'installation détaillé
├── LICENCE.md                        # 📜 Licence MIT du projet
├── README.md                         # 📖 Documentation principale
├── requirements.txt                  # 🐍 Dépendances Python
├── SECURITY.md                       # 🔒 Politique de sécurité
└── todo.md                           # � Liste des tâches et améliorations à venir
```

### Structure de la base de données

![Schéma UML de la base de données](documentation/UML_BdD.svg)

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

#### 🗄️ Configuration Base de Données

| Variable             | Description                              | Exemple                           |
|----------------------|------------------------------------------|-----------------------------------|
| `ROOT_PASSWORD`      | Mot de passe root MySQL                  | `mot_de_passe_securise`           |
| `DB_USER`            | Utilisateur de la base de données        | `intranet_user`                   |
| `DB_PASSWORD`        | Mot de passe de la base de données       | `mot_de_passe_securise`           |
| `DB_HOST`            | Hôte de la base de données               | `db`                              |
| `DB_NAME`            | Nom de la base de données                | `intranet_db`                     |
| `DB_URL`             | URL de connexion à la base de données    | `mysql+mysqlconnector://...`      |
| `DB_DOCKER_PATH`     | Chemin Docker de la base de données      | `/var/lib/mysql`                  |
| `DB_LOCAL_PATH`      | Chemin local de la base de données       | `/var/lib/docker/volumes/...`     |

#### 🔐 Sécurité

| Variable             | Description                              | Exemple                           |
|----------------------|------------------------------------------|-----------------------------------|
| `SECRET_KEY`         | Clé secrète Flask (sessions, HMAC)      | `cle_secrete_32_chars_min`        |

> ⚠️ **Important** : `SECRET_KEY` est utilisée pour les sessions Flask ET la sécurisation HMAC des documents de signature. Changez-la régulièrement et utilisez minimum 32 caractères aléatoires.

#### 📁 Chemins de Stockage

| Variable                | Description                              | Exemple                           |
|-------------------------|------------------------------------------|-----------------------------------|
| `FILES_DOCKER_PATH`     | Chemin Docker des documents              | `/app/documents`                  |
| `FILES_LOCAL_PATH`      | Chemin local des documents               | `/var/www/intranet/documents`     |
| `PRINT_DOCKER_PATH`     | Chemin Docker des impressions            | `/app/print`                      |
| `PRINT_LOCAL_PATH`      | Chemin local des impressions             | `/var/www/intranet/print`         |
| `SIGNATURE_DOCKER_PATH` | Chemin Docker documents signés           | `/app/documents/signatures`       |
| `SIGNATURE_LOCAL_PATH`  | Chemin local documents signés            | `/var/www/intranet/documents/signatures` |
| `TEMP_DOCKER_PATH`      | Chemin Docker fichiers temporaires       | `/tmp`                            |

> 📝 **Note** : Les dossiers de signatures sont créés automatiquement. Le dossier `/tmp/signature` n'est pas monté dans Docker pour raisons de sécurité.

#### 🖨️ Configuration Impression

| Variable             | Description                              | Exemple                           |
|----------------------|------------------------------------------|-----------------------------------|
| `PRINTER_NAME`       | Nom de l'imprimante réseau               | `HP_LaserJet_Pro`                 |
| `SSH_PORT`           | Port SSH pour transfert fichiers         | `22`                              |
| `SSH_HOST`           | Hôte SSH du serveur d'impression         | `192.168.1.100`                   |
| `SSH_USER`           | Utilisateur SSH                          | `ssh_user`                        |
| `SSH_PASSWORD`       | Mot de passe SSH                         | `mot_de_passe_ssh_securise`       |

#### 📧 Configuration Email (SMTP)

| Variable             | Description                              | Exemple                           |
|----------------------|------------------------------------------|-----------------------------------|
| `EMAIL_USER`         | Adresse email d'envoi                    | `noreply@etablissement.fr`        |
| `EMAIL_PASSWORD`     | Mot de passe du compte email             | `mot_de_passe_email_securise`     |
| `EMAIL_SMTP`         | Serveur SMTP                             | `smtp.gmail.com`                  |
| `EMAIL_PORT`         | Port SMTP                                | `587` (TLS) ou `465` (SSL)        |
| `API_MAIL_TOKEN`     | Token API pour rapports par email        | `token_api_securise`              |

> 📧 **Usage** : Utilisé pour les notifications d'échéances, codes OTP de signature, et envoi des documents signés.

#### 🐳 Configuration Docker (Dev/CI)

| Variable             | Description                              | Exemple                           |
|----------------------|------------------------------------------|-----------------------------------|
| `DB_PORTS`           | Mapping ports base de données            | `3306:3306`                       |
| `WEB_PORTS`          | Mapping ports application web            | `5000:5000`                       |
| `EXPOSE_PORTS`       | Mode exposition des ports                | `Workflow` ou `Production`        |

---

> **⚠️ Sécurité** : 
> - Ne partagez **jamais** le fichier `.env` publiquement
> - Utilisez `./generate-env.sh` pour générer des valeurs sécurisées
> - Changez `SECRET_KEY` régulièrement (minimum tous les 6 mois)
> - Utilisez des mots de passe d'au moins 32 caractères
> - Sauvegardez le `.env` dans un endroit sûr et chiffré

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

### �️ Signatures Électroniques

- [x] **Création de documents à signer** avec placement interactif des points de signature
- [x] **Interface de signature** avec capture graphique haute fidélité (SignaturePad)
- [x] **Sécurisation des accès** avec cryptographie HMAC-SHA256
- [x] **Génération PDF signés** avec regroupement des signatures par page
- [x] **Gestion multi-signataires** avec suivi en temps réel
- [x] **Expiration automatique** des documents via événement MySQL (CRON horaire)
- [x] **Journalisation complète** des actions utilisateur
- [x] **Affichage des documents signés** dans la vue détail du contrat
- [x] **Support PDF.js** pour visualisation interactive
- [ ] **Notifications automatiques** par email avec PDF signé en pièce jointe

### �🖨️ Impression à Distance

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

#### Version actuelle : 1.3.0 (5 octobre 2025)

- [x] Gestion complète des contrats
- [x] Système d'impression à distance  
- [x] Module de signature électronique complet
- [x] Gestion des factures et contacts
- [x] Interface responsive
- [x] Sécurité renforcée (HMAC, HTTPS)
- [x] CI/CD avec GitHub Actions

#### Version 1.4.0 (Q4 2025)

- [ ] Notifications automatiques de signatures
- [ ] Tests unitaires complets (80%+ couverture)
- [ ] Rate limiting sur les OTP
- [ ] Audit logs avancés
- [ ] Monitoring MongoDB déployé

#### Version 2.0 (2026)

- [ ] API REST complète
- [ ] Application mobile (Flutter)
- [ ] Intégration calendrier
- [ ] Notifications push
- [ ] Dashboard analytics avancé
- [ ] Module de reporting étendu

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
