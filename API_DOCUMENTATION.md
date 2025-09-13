# Documentation API - Routes et Paramètres

## Table des matières
1. [Authentification](#authentification)
2. [Gestion des utilisateurs](#gestion-des-utilisateurs)
3. [Gestion des contrats](#gestion-des-contrats)
4. [Gestion des documents](#gestion-des-documents)
5. [Gestion des événements](#gestion-des-événements)
6. [Impression](#impression)
7. [Espaces réservés](#espaces-réservés)

---

## Authentification

### 🏠 Page d'accueil
**Route :** `GET /`
- **Description :** Page d'accueil de l'application, affiche le tableau de bord
- **Authentification :** Requise (session)
- **Habilitations :** Toutes
- **Paramètres :** Aucun
- **Réponse :** Template `index.html` avec les sections disponibles selon les habilitations
- **Redirection :** `/login` si non authentifié

### 🔐 Connexion
**Route :** `GET/POST /login`
- **Description :** Page de connexion utilisateur
- **Méthode GET :**
  - **Paramètres :** `message` (optionnel) - Message d'erreur à afficher
  - **Réponse :** Template `login.html`

- **Méthode POST :**
  - **Paramètres :**
    - `username` (string, requis) - Identifiant utilisateur
    - `password` (string, requis) - Mot de passe (haché en SHA-256)
  - **Réponse :** Redirection vers `/` ou `/login` avec message d'erreur
  - **Logique :** 
    - Vérification des identifiants
    - Gestion des tentatives (3 max)
    - Verrouillage automatique du compte

### 🚪 Déconnexion
**Route :** `GET /logout`
- **Description :** Déconnexion et suppression de la session
- **Authentification :** Requise
- **Paramètres :** Aucun
- **Réponse :** Redirection vers `/login`

---

## Gestion des Utilisateurs

### 👑 Gestion des droits
**Route :** `GET /gestion_droits`
- **Description :** Interface de gestion des habilitations utilisateurs
- **Authentification :** Requise
- **Habilitations :** Niveau 1 (super-administrateur)
- **Paramètres :** Aucun
- **Réponse :** Template `gestion_droits.html` avec liste des utilisateurs

**Route :** `POST /gestion_droits`
- **Description :** Modification des droits d'un utilisateur
- **Authentification :** Requise
- **Habilitations :** Niveau 1 ou 2
- **Paramètres :**
  - `identifiant` (string, requis) - Identifiant de l'utilisateur
  - `mdp` (string, optionnel) - Nouveau mot de passe
  - `habil[1-6]` (string, optionnel) - Niveaux d'habilitation (1-6)
- **Réponse :** Redirection vers `/gestion_droits`

### 👥 Gestion des utilisateurs
**Route :** `GET /gestion_utilisateurs`
- **Description :** Interface de gestion des utilisateurs
- **Authentification :** Requise
- **Habilitations :** Niveau 2 (administrateur)
- **Paramètres :** Aucun
- **Réponse :** Template `gestion_utilisateurs.html` avec liste triée par nom/prénom

### ➕ Ajout d'utilisateur
**Route :** `POST /ajout_utilisateurs`
- **Description :** Création d'un nouvel utilisateur
- **Authentification :** Requise
- **Habilitations :** Niveau 1
- **Paramètres :**
  - `prenom` (string, requis) - Prénom
  - `nom` (string, requis) - Nom de famille
  - `mail` (string, requis) - Adresse email
  - `identifiant` (string, requis) - Identifiant unique
  - `mdp` (string, requis) - Mot de passe
  - `habil[1-6]` (string, optionnel) - Niveaux d'habilitation
- **Réponse :** Redirection vers `/gestion_utilisateurs`

### ❌ Suppression d'utilisateur
**Route :** `POST /suppr_utilisateurs`
- **Description :** Suppression d'un utilisateur
- **Authentification :** Requise
- **Habilitations :** Niveau 1
- **Paramètres :**
  - `identifiant` (string, requis) - Identifiant de l'utilisateur à supprimer
- **Réponse :** Redirection vers `/gestion_utilisateurs`

### ✏️ Modification d'utilisateur
**Route :** `POST /modif_utilisateurs`
- **Description :** Modification des informations d'un utilisateur
- **Authentification :** Requise
- **Habilitations :** Niveau 1 ou 2
- **Paramètres :**
  - `prenom` (string, requis) - Prénom
  - `nom` (string, requis) - Nom de famille
  - `mail` (string, requis) - Adresse email
  - `identifiant` (string, requis) - Identifiant
  - `mdp` (string, optionnel) - Nouveau mot de passe
  - `unlock` (int, optionnel) - Déverrouillage du compte (1 = oui)
  - `habil[1-6]` (string, optionnel) - Niveaux d'habilitation
- **Réponse :** Redirection vers `/gestion_utilisateurs`

---

## Gestion des Contrats

### 📋 Liste des contrats
**Route :** `GET /contrats`
- **Description :** Affichage de la liste des contrats
- **Authentification :** Requise
- **Habilitations :** Niveau 2
- **Paramètres :** Aucun
- **Réponse :** Template `contrats.html` avec liste des contrats

### ➕ Création de contrat
**Route :** `POST /contrats`
- **Description :** Création d'un nouveau contrat
- **Authentification :** Requise
- **Habilitations :** Niveau 2
- **Paramètres :**
  - `Type0` (string, requis) - Type principal du contrat
  - `SType0` (string, requis) - Sous-type du contrat
  - `Entreprise` (string, requis) - Nom de l'entreprise
  - `numContratExterne` (string, requis) - Numéro de contrat externe
  - `Intitule` (string, requis) - Intitulé du contrat
  - `dateDebut` (date, requis) - Date de début (YYYY-MM-DD)
  - `dateFinPreavis` (date, requis) - Date de fin de préavis (YYYY-MM-DD)
  - `dateFin` (date, optionnel) - Date de fin (YYYY-MM-DD)
- **Réponse :** Redirection vers `/contrats`

### 📄 Détail d'un contrat
**Route :** `GET /contrats/<num_contrat>`
- **Description :** Affichage des détails d'un contrat avec ses événements et documents
- **Authentification :** Requise
- **Habilitations :** Niveau 2
- **Paramètres :**
  - `numContrat` (int, URL) - ID du contrat
- **Réponse :** Template `contrat_detail.html` avec contrat, événements et documents

### ✏️ Modification de contrat
**Route :** `POST /contrats/<num_contrat>`
- **Description :** Modification d'un contrat existant (méthode PUT simulée)
- **Authentification :** Requise
- **Habilitations :** Niveau 2
- **Paramètres :**
  - `numContrat` (int, URL) - ID du contrat
  - `_method` (string, requis) - Doit être "PUT"
  - `Type{numContrat}` (string, requis) - Type principal
  - `SType{numContrat}` (string, requis) - Sous-type
  - `Entreprise{numContrat}` (string, requis) - Nom de l'entreprise
  - `numContratExterne{numContrat}` (string, requis) - Numéro externe
  - `Intitule{numContrat}` (string, requis) - Intitulé
  - `dateDebut{numContrat}` (date, requis) - Date de début
  - `dateFinPreavis{numContrat}` (date, requis) - Date de fin de préavis
  - `dateFin{numContrat}` (date, optionnel) - Date de fin
- **Réponse :** Redirection vers `/contrats`

---

## Gestion des Événements

### ➕ Ajout d'événement à un contrat
**Route :** `POST /contrats/<num_contrat>/evenement`
- **Description :** Ajout d'un événement lié à un contrat
- **Authentification :** Requise
- **Habilitations :** Niveau 2
- **Paramètres :**
  - `numContrat` (int, URL) - ID du contrat
  - `idContratE` (int, requis) - ID du contrat (confirmation)
  - `dateEvenementE` (date, requis) - Date de l'événement (YYYY-MM-DD)
  - `TypeE0` (string, requis) - Type principal de l'événement
  - `STypeE0` (string, requis) - Sous-type de l'événement
  - `descriptifE` (string, requis) - Description de l'événement
- **Réponse :** Redirection vers `/contrats/<num_contrat>`

### ✏️ Modification d'événement
**Route :** `POST /contrats/numContrat/<num_contrat>/numEvenement/<num_event>`
- **Description :** Modification d'un événement existant
- **Authentification :** Requise
- **Habilitations :** Niveau 2
- **Paramètres :**
  - `numContrat` (int, URL) - ID du contrat
  - `num_event` (int, URL) - ID de l'événement
  - `_method` (string, requis) - Doit être "PUT"
  - `idContratE{num_event}` (int, requis) - ID du contrat
  - `dateEvenementE{num_event}` (date, requis) - Date de l'événement
  - `TypeE{num_event}` (string, requis) - Type principal
  - `STypeE{num_event}` (string, requis) - Sous-type
  - `descriptifE{num_event}` (string, requis) - Description
- **Réponse :** Redirection vers `/contrats/<num_contrat>`

---

## Gestion des Documents

### ➕ Ajout de document à un contrat
**Route :** `POST /contrats/<num_contrat>/document`
- **Description :** Upload et ajout d'un document lié à un contrat
- **Authentification :** Requise
- **Habilitations :** Niveau 2
- **Paramètres :**
  - `numContrat` (int, URL) - ID du contrat
  - `idContratD` (int, requis) - ID du contrat (confirmation)
  - `dateDocumentD` (date, requis) - Date du document (YYYY-MM-DD)
  - `TypeD0` (string, requis) - Type principal du document
  - `STypeD0` (string, requis) - Sous-type du document
  - `descriptifD` (string, requis) - Description du document
  - `documentD` (file, requis) - Fichier à uploader
- **Traitement automatique :**
  - Génération du nom : `{YYMMDD}_{idContrat}_{idDocument}_{sousType}.{extension}`
  - Sauvegarde sur le serveur
  - Enregistrement en base de données
- **Réponse :** Redirection vers `/contrats/<num_contrat>`

### ✏️ Modification de document
**Route :** `POST /contrats/numContrat/<num_contrat>/num_document/<num_doc>`
- **Description :** Modification d'un document existant
- **Authentification :** Requise
- **Habilitations :** Niveau 2
- **Paramètres :**
  - `numContrat` (int, URL) - ID du contrat
  - `num_doc` (int, URL) - ID du document
  - `_method` (string, requis) - Doit être "PUT"
  - `idContratD{num_doc}` (int, requis) - ID du contrat
  - `dateDocumentD{num_doc}` (date, requis) - Date du document
  - `TypeD{num_doc}` (string, requis) - Type principal
  - `STypeD{num_doc}` (string, requis) - Sous-type
  - `descriptifD{num_doc}` (string, requis) - Description
  - `documentD{num_doc}` (file, optionnel) - Nouveau fichier
  - `strLienD{num_doc}` (string, conditionnel) - Lien existant si pas de nouveau fichier
- **Réponse :** Redirection vers `/contrats/<num_contrat>`

### 📥 Téléchargement de document
**Route :** `GET /contrats/numContrat/<num_contrat>/num_document/<num_doc>/download/<name>`
- **Description :** Téléchargement d'un document
- **Authentification :** Requise
- **Habilitations :** Niveau 2
- **Paramètres :**
  - `numContrat` (int, URL) - ID du contrat
  - `num_doc` (int, URL) - ID du document
  - `name` (string, URL) - Nom complet du fichier avec extension
- **Réponse :** Fichier en téléchargement

---

## Impression

### 🖨️ Espace d'impression
**Route :** `GET /ei`
- **Description :** Interface d'impression à distance
- **Authentification :** Requise
- **Habilitations :** Niveau 6
- **Paramètres :** Aucun
- **Réponse :** Template `ei.html`

### 📄 Impression de document
**Route :** `POST /print_doc`
- **Description :** Upload et impression d'un document
- **Authentification :** Requise
- **Habilitations :** Niveau 6
- **Paramètres :**
  - `document` (file, requis) - Fichier à imprimer
  - `copies` (int, requis) - Nombre de copies
  - `recto_verso` (string, requis) - Mode d'impression ("recto" ou "recto_verso")
  - `format` (string, requis) - Format papier ("A4", "A3", etc.)
  - `orientation` (string, requis) - Orientation ("portrait" ou "landscape")
  - `couleur` (string, requis) - Mode couleur ("couleur" ou "nb")
- **Traitement :**
  - Upload temporaire du fichier
  - Envoi à l'imprimante configurée
  - Suppression automatique du fichier
- **Réponse :** Redirection vers `/ei` avec message de confirmation

---

## Espaces Réservés

### 🎓 Espace Professeurs Principaux
**Route :** `GET /erpp`
- **Description :** Espace réservé aux professeurs principaux (en construction)
- **Authentification :** Requise
- **Habilitations :** Niveau 3
- **Paramètres :** Aucun
- **Réponse :** Template `erpp.html`

### 👨‍🏫 Espace Professeurs
**Route :** `GET /erp`
- **Description :** Espace réservé aux professeurs (en construction)
- **Authentification :** Requise
- **Habilitations :** Niveau 4
- **Paramètres :** Aucun
- **Réponse :** Template `erp.html`

### 🎒 Espace Élèves
**Route :** `GET /ere`
- **Description :** Espace réservé aux élèves (en construction)
- **Authentification :** Requise
- **Habilitations :** Niveau 5
- **Paramètres :** Aucun
- **Réponse :** Template `ere.html`

---

## Modèles de Données

### 👤 User (99_users)
```python
{
    "id": int,                    # Clé primaire auto-incrémentée
    "prenom": string(255),        # Prénom (obligatoire)
    "nom": string(255),           # Nom de famille (obligatoire)
    "mail": string(255),          # Adresse email (obligatoire)
    "identifiant": string(25),    # Identifiant de connexion
    "shaMdp": string(255),        # Mot de passe haché SHA-256 (obligatoire)
    "habilitation": int,          # Niveau d'habilitation (combinable)
    "debut": date,                # Date de création (auto)
    "fin": date,                  # Date de fin d'accès
    "falseTest": int,             # Nombre de tentatives échouées (défaut: 0)
    "locked": bool                # Compte verrouillé (défaut: false)
}
```

### 📋 Contract (01_contrats)
```python
{
    "id": int,                    # Clé primaire auto-incrémentée
    "Type": string(50),           # Type principal (obligatoire)
    "SType": string(50),          # Sous-type (obligatoire)
    "entreprise": string(255),    # Nom de l'entreprise (obligatoire)
    "numContratExterne": string(50), # Numéro externe (obligatoire)
    "intitule": string(255),      # Intitulé du contrat (obligatoire)
    "dateDebut": date,            # Date de début (obligatoire)
    "dateFinPreavis": date,       # Date de fin de préavis (obligatoire)
    "dateFin": date               # Date de fin (optionnel)
}
```

### 📄 Document (11_documents)
```python
{
    "id": int,                    # Clé primaire auto-incrémentée
    "idContrat": int,             # ID du contrat lié (obligatoire)
    "Type": string(50),           # Type principal (obligatoire)
    "SType": string(50),          # Sous-type
    "descriptif": string(255),    # Description (obligatoire)
    "strLien": string(255),       # Chemin du fichier
    "dateDocument": date,         # Date du document (obligatoire)
    "name": string(30)            # Nom normalisé du fichier
}
```

### 📅 Event (12_evenements)
```python
{
    "id": int,                    # Clé primaire auto-incrémentée
    "idContrat": int,             # ID du contrat lié (obligatoire)
    "dateEvenement": date,        # Date de l'événement (obligatoire)
    "Type": string(50),           # Type principal (obligatoire)
    "SType": string(50),          # Sous-type (obligatoire)
    "descriptif": string(255)     # Description (obligatoire)
}
```

---

## Codes de Réponse HTTP

- **200 OK** : Requête réussie, page affichée
- **302 Found** : Redirection (utilisée pour toutes les redirections)
- **403 Forbidden** : Accès refusé (habilitations insuffisantes)
- **404 Not Found** : Route non trouvée
- **500 Internal Server Error** : Erreur serveur

---

## Sécurité et Validation

### Authentification
- Toutes les routes (sauf `/login`) nécessitent une session active
- Vérification des habilitations pour chaque niveau d'accès
- Redirection automatique vers `/logout` en cas d'accès non autorisé

### Validation des données
- Hachage SHA-256 automatique des mots de passe
- Validation des types de fichiers pour l'upload
- Génération automatique des noms de fichiers pour éviter les conflits
- Protection contre les injections SQL via SQLAlchemy ORM

### Gestion des erreurs
- Tentatives de connexion limitées (3 max)
- Verrouillage automatique des comptes
- Messages d'erreur informatifs mais sécurisés
- Logs des erreurs côté serveur

---

## Extensions de Fichiers Supportées

**Upload de documents :** `.jpg`, `.png`, `.gif`, `.jpeg`, `.tif`, `.tiff`, `.pdf`

**Impression :** Tous formats supportés par CUPS (PDF recommandé)

---

## Notes de Développement

- L'application utilise des sessions Flask pour la gestion de l'authentification
- Les mots de passe sont automatiquement hachés en SHA-256 avant stockage
- La nomenclature des documents suit le format : `{YYMMDD}_{ContratID}_{DocumentID}_{SousType}.{extension}`
- Les habilitations sont stockées sous forme d'entier et peuvent être combinées
- L'application est prête pour la production avec Docker et Waitress
