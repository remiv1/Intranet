# Intranet
This Intranet project has been developed for a secondary boys school.
I do it for nothing, this school is an non-profit association. I git it to them.

# Informations - Global design
## Global Design
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