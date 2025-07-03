# Intranet - Application de Gestion d'Établissement

## Description

Cette application web développée avec Flask permet la gestion complète d'un établissement scolaire. Elle offre des fonctionnalités de gestion des utilisateurs, des contrats, des documents et des impressions à distance.

**Note** : Ce projet a été développé bénévolement pour un établissement scolaire secondaire (association à but non lucratif).

## Architecture

### Technologies utilisées
- **Backend** : Flask 3.1.0 (Python)
- **Base de données** : MariaDB (MySQL)
- **ORM** : SQLAlchemy 2.0.38
- **Serveur web** : Waitress
- **Conteneurisation** : Docker & Docker Compose
- **Sécurité** : Hachage SHA-256 pour les mots de passe, sessions Flask

### Structure du projet
```
├── app/                    # Application Flask principale
│   ├── __init__.py        # Initialisation de l'application
│   ├── models.py          # Modèles de données SQLAlchemy
│   ├── routes.py          # Routes et logique métier
│   ├── docs.py            # Gestion des documents
│   ├── impression.py      # Gestion des impressions
│   ├── static/            # Fichiers statiques (CSS, JS, images)
│   └── templates/         # Templates HTML Jinja2
├── documents/             # Stockage des documents uploadés
├── config.py              # Configuration de l'application
├── run.py                 # Point d'entrée principal
├── requirements.txt       # Dépendances Python
├── Dockerfile.app         # Configuration Docker
├── docker-compose.yaml    # Orchestration des services
└── entrypoint.sh          # Script de démarrage
```

## Installation et Déploiement

### Prérequis
- Docker et Docker Compose
- Variables d'environnement configurées dans `.env`

### Variables d'environnement requises

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```env
# Base de données
DB_USER=votre_utilisateur_db
DB_PASSWORD=votre_mot_de_passe_db
DB_HOST=db
DB_NAME=nom_de_votre_base
ROOT_PASSWORD=mot_de_passe_root_mysql
DB_URL=mysql+mysqlconnector://user:password@db:3306/database
DB_LOCAL_PATH=/chemin/local/vers/donnees
DB_DOCKER_PATH=/var/lib/mysql

# Sécurité
SECRET_KEY=votre_cle_secrete_flask

# Fichiers
FILES_LOCAL_PATH=/chemin/local/vers/documents
FILES_DOCKER_PATH=/app/documents
PRINT_LOCAL_PATH=/chemin/local/vers/impressions
PRINT_DOCKER_PATH=/app/print

# SSH (pour transferts de fichiers)
SSH_PORT=22
SSH_HOST=adresse_serveur_ssh
SSH_USER=utilisateur_ssh
SSH_PASSWORD=mot_de_passe_ssh

# Impression
PRINTER_NAME=nom_de_votre_imprimante

# Email
EMAIL_USER=votre_email@domaine.com
EMAIL_PASSWORD=mot_de_passe_email
EMAIL_SMTP=serveur.smtp.com
EMAIL_PORT=587
```

### Déploiement avec Docker

1. **Cloner le projet**
   ```bash
   git clone <url-du-projet>
   cd Intranet
   ```

2. **Configurer les variables d'environnement**
   ```bash
   cp .env.example .env
   # Éditer le fichier .env avec vos valeurs
   ```

3. **Lancer l'application**
   ```bash
   docker-compose up -d
   ```

4. **Accéder à l'application**
   - URL : `http://localhost` (port 80)
   - L'application sera accessible une fois la base de données initialisée

### Structure de la base de données

L'application utilise 4 tables principales :

- **99_users** : Gestion des utilisateurs et permissions
- **01_contrats** : Gestion des contrats avec les entreprises
- **11_documents** : Documents liés aux contrats
- **12_evenements** : Événements liés aux contrats

## Système d'Habilitations

L'application utilise un système d'habilitations basé sur des chiffres :

- **1** : Gestion des droits utilisateurs (super-administrateur)
- **2** : Gestion des utilisateurs et contrats (administrateur)
- **3** : Espace professeurs principaux
- **4** : Espace professeurs
- **5** : Espace élèves
- **6** : Espace impressions

Les habilitations peuvent être combinées (ex: 126 = droits 1, 2 et 6).

## Fonctionnalités Principales

### 🔐 Authentification et Sécurité
- Connexion sécurisée avec hachage SHA-256
- Système de tentatives limitées (3 essais)
- Verrouillage automatique des comptes
- Gestion des sessions Flask

### 👥 Gestion des Utilisateurs
- Création, modification, suppression d'utilisateurs
- Gestion des habilitations
- Déverrouillage de comptes
- Interface d'administration complète

### 📋 Gestion des Contrats
- Création et modification de contrats
- Suivi des dates (début, fin, préavis)
- Classification par type et sous-type
- Liaison avec les entreprises

### 📄 Gestion Documentaire
- Upload de documents liés aux contrats
- Nomenclature automatique des fichiers
- Téléchargement sécurisé
- Support multi-formats (PDF, images, etc.)

### 📅 Gestion des Événements
- Ajout d'événements liés aux contrats
- Historique chronologique
- Classification des événements

### 🖨️ Impression à Distance
- Upload et impression de documents
- Configuration des paramètres d'impression :
  - Nombre de copies
  - Recto/verso
  - Format papier
  - Orientation
  - Couleur/noir et blanc
- Suppression automatique après impression

## Maintenance et Monitoring

### Logs
Les logs de l'application sont disponibles via Docker :
```bash
docker-compose logs web
docker-compose logs db
```

### Sauvegarde
Sauvegardez régulièrement :
- Le dossier de données MySQL (défini par `DB_LOCAL_PATH`)
- Le dossier des documents (défini par `FILES_LOCAL_PATH`)

### Mise à jour
1. Arrêter les services : `docker-compose down`
2. Mettre à jour le code source
3. Reconstruire les images : `docker-compose build`
4. Redémarrer : `docker-compose up -d`

## Sécurité

### Bonnes pratiques
- Changez régulièrement la `SECRET_KEY`
- Utilisez des mots de passe forts pour la base de données
- Configurez un reverse proxy (nginx) pour la production
- Activez HTTPS en production
- Limitez l'accès réseau aux ports nécessaires

### Permissions fichiers
Assurez-vous que les dossiers de documents ont les bonnes permissions :
```bash
chmod 755 /chemin/vers/documents
chown -R www-data:www-data /chemin/vers/documents
```

## Support et Développement

### Structure du code
- **Routes** : `app/routes.py` - Logique des endpoints
- **Modèles** : `app/models.py` - Définition des tables
- **Configuration** : `config.py` - Paramètres d'application
- **Templates** : `app/templates/` - Interface utilisateur

### Ajout de fonctionnalités
1. Définir les nouveaux modèles dans `models.py`
2. Créer les routes dans `routes.py`
3. Ajouter les templates HTML
4. Mettre à jour les permissions si nécessaire

Pour toute question ou problème, consultez les logs ou contactez l'équipe de développement.
Intraraudiere/
├── __pycache__/
│   └── config.cpython-311.pyc
├── app/
│   └── __pycache__/
│       ├── __init__.cpython-311.pyc
│       ├── docs.cpython-311.pyc
│       ├── load_doc.cpython-311.pyc
│       ├── models.cpython-311.pyc
│       ├── routes_ovh.cpython-311.pyc
│       └── routes.cpython-311.pyc
├── static/
│   ├── css/
│   │   ├── style-accueil.css
│   │   ├── style-contrats.css
│   │   ├── style-documents.css
│   │   ├── style-echeances.css
│   │   ├── style-general.css
│   │   ├── style-impression.css
│   │   ├── style-login.css
│   │   ├── style-menu.css
│   │   └── style-tableau.css
│   ├── img/
│   │   └── favicone.svg
│   └── js/
│       ├── accueil.js
│       ├── contrats.js
│       ├── documents.js
│       ├── echeances.js
│       ├── evenements.js
│       └── impression.js
├── templates/
│   ├── contrat_detail.html
│   ├── contrats.html
│   ├── ei.html
│   ├── ere.html
│   ├── erp.html
│   ├── erpp.html
│   ├── gestion_droits.html
│   ├── gestion_utilisateurs.html
│   ├── index.html
│   ├── login_error.html
│   └── login.html
├── __init__.py
├── docs.py
├── models.py
├── routes.py
├── venv/
├── .env (présent dans le gitignore)
├── .gitignore
├── config.py
├── README.md
└── run.py

## Informations
Le projet était au départ de pouvoir gérer les contrats de l'école.
Nous avons au fur et à mesure travaillé sur des fonctionnalités supplémentaires pour intégrer des fonctions comme l'impression à distance.

# Base de données
## Tables
+----------------------+
| Tables_in_Peraudiere |
+----------------------+
| 01_Contrats          |
| 11_Documents         |
| 12_Evenements        |
| 91_Menus             |
| 99_Users             |
+----------------------+

## 01_Contrats
+-------------------+--------------+------+-----+---------+----------------+
| Field             | Type         | Null | Key | Default | Extra          |
+-------------------+--------------+------+-----+---------+----------------+
| id                | int(11)      | NO   | PRI | NULL    | auto_increment |
| Type              | varchar(50)  | NO   |     | NULL    |                |
| Stype             | varchar(50)  | NO   |     | NULL    |                |
| Entreprise        | varchar(255) | NO   |     | NULL    |                |
| numContratExterne | varchar(50)  | NO   |     | NULL    |                |
| Intitule          | varchar(255) | NO   |     | NULL    |                |
| dateDebut         | date         | NO   |     | NULL    |                |
| dateFinPreavis    | date         | NO   |     | NULL    |                |
| dateFin           | date         | NO   |     | NULL    |                |
+-------------------+--------------+------+-----+---------+----------------+

CREATE TABLE `01_Contrats` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Type` varchar(50) NOT NULL,
  `SType` varchar(50) NOT NULL,
  `Entreprise` varchar(255) NOT NULL,
  `numContratExterne` varchar(50) NOT NULL,
  `Intitule` varchar(255) NOT NULL,
  `dateDebut` date NOT NULL,
  `dateFinPreavis` date NOT NULL,
  `dateFin` date DEFAULT NULL,
  PRIMARY KEY (`id`)
)

## 11_Documents
+--------------+--------------+------+-----+---------+----------------+
| Field        | Type         | Null | Key | Default | Extra          |
+--------------+--------------+------+-----+---------+----------------+
| id           | int(11)      | NO   | PRI | NULL    | auto_increment |
| idContrat    | int(11)      | NO   | MUL | NULL    |                |
| Type         | varchar(50)  | NO   |     | NULL    |                |
| SType        | varchar(50)  | YES  |     | NULL    |                |
| Descriptif   | varchar(255) | NO   |     | NULL    |                |
| strLien      | varchar(255) | YES  |     | NULL    |                |
| dateDocument | date         | NO   |     | NULL    |                |
| Name         | varchar(30)  | NO   |     | NULL    |                |
+--------------+--------------+------+-----+---------+----------------+

CREATE TABLE `11_Documents` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `idContrat` int(11) NOT NULL,
  `Type` varchar(50) NOT NULL,
  `SType` varchar(50) DEFAULT NULL,
  `Descriptif` varchar(255) NOT NULL,
  `strLien` varchar(255) DEFAULT NULL,
  `dateDocument` date NOT NULL,
  `Name` varchar(30) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_contrat_document` (`idContrat`),
  CONSTRAINT `fk_contrat_document` FOREIGN KEY (`idContrat`) REFERENCES `01_Contrats` (`id`)
)

## 12_Evenements
+---------------+--------------+------+-----+---------+----------------+
| Field         | Type         | Null | Key | Default | Extra          |
+---------------+--------------+------+-----+---------+----------------+
| id            | int(11)      | NO   | PRI | NULL    | auto_increment |
| idContrat     | int(11)      | NO   | MUL | NULL    |                |
| dateEvenement | date         | NO   |     | NULL    |                |
| Type          | varchar(50)  | NO   |     | NULL    |                |
| Stype         | varchar(50)  | NO   |     | NULL    |                |
| Descriptif    | varchar(255) | NO   |     | NULL    |                |
+---------------+--------------+------+-----+---------+----------------+

CREATE TABLE `12_Evenements` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `idContrat` int(11) NOT NULL,
  `dateEvenement` date NOT NULL,
  `Type` varchar(50) NOT NULL,
  `Stype` varchar(50) NOT NULL,
  `Descriptif` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_evenement` (`idContrat`),
  CONSTRAINT `fk_evenement` FOREIGN KEY (`idContrat`) REFERENCES `01_Contrats` (`id`)
)

## 99_Users
+--------------+--------------+------+-----+-----------+----------------+
| Field        | Type         | Null | Key | Default   | Extra          |
+--------------+--------------+------+-----+-----------+----------------+
| id           | int(11)      | NO   | PRI | NULL      | auto_increment |
| Prenom       | varchar(255) | NO   |     | NULL      |                |
| Nom          | varchar(255) | NO   |     | NULL      |                |
| mail         | varchar(255) | NO   |     | NULL      |                |
| identifiant  | varchar(25)  | YES  |     | NULL      |                |
| shaMdp       | varchar(255) | NO   |     | NULL      |                |
| habilitation | int(11)      | YES  |     | NULL      |                |
| Début        | date         | YES  |     | curdate() |                |
| Fin          | date         | YES  |     | NULL      |                |
| Locked       | bit(1)       | YES  |     | b'0'      |                |
+--------------+--------------+------+-----+-----------+----------------+

CREATE TABLE `99_Users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Prenom` varchar(255) NOT NULL,
  `Nom` varchar(255) NOT NULL,
  `mail` varchar(255) NOT NULL,
  `identifiant` varchar(25) DEFAULT NULL,
  `shaMdp` varchar(255) NOT NULL,
  `habilitation` int(11) DEFAULT NULL,
  `Début` date DEFAULT curdate(),
  `Fin` date DEFAULT NULL,
  `Locked` bit(1) DEFAULT b'0',
  PRIMARY KEY (`id`)
)