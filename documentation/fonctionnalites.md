# Fonctionnalités de l'Intranet

[<- Retour à la page d'accueil](../README.md)

## 🔐 Authentification et Sécurité

- [x] **Connexion sécurisée** avec hachage SHA-256 (modifications à venir Argon2)
- [x] **Système anti-brute force** : limitation à 3 tentatives
- [x] **Verrouillage automatique** des comptes après échecs
- [x] **Gestion des sessions** Flask sécurisées
- [x] **HTTPS** avec certificats SSL/TLS
- [x] **Validation des entrées** côté serveur

## 👥 Gestion des Utilisateurs

- [x] **CRUD complet** : Création, lecture, modification, suppression
- [x] **Système d'habilitations** multi-niveaux (1-6)
- [x] **Déverrouillage de comptes** par les administrateurs
- [x] **Interface d'administration** intuitive
- [x] **Gestion des dates** de début/fin d'accès
- [x] **Recherche et filtres** avancés

## 📋 Gestion des Contrats

- [x] **Création de contrats** avec formulaires structurés
- [x] **Suivi des échéances** (début, préavis, fin)
- [x] **Classification** par type et sous-type
- [x] **Liaison avec entreprises** et partenaires
- [x] **Historique complet** des modifications

## 📄 Gestion Documentaire

- [x] **Upload sécurisé** de fichiers multiples
- [x] **Nomenclature automatique** des documents
- [x] **Classification** par type et sous-type
- [x] **Téléchargement sécurisé** avec contrôle d'accès
- [x] **Support multi-formats** : PDF, images, Office
- [x] **Gestion parallèle** des documents et des liens en base

## 📅 Gestion des Événements

- [x] **Ajout d'événements** liés aux contrats
- [x] **Chronologie interactive** des événements
- [x] **Classification** des types d'événements
- [x] **Notifications automatiques** d'échéances
- [ ] **Recherche temporelle** par périodes
- [ ] **Export** des données au format CSV/PDF

## 🖋️ Signatures Électroniques

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

## 🖨️ Impression à Distance

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

## 📊 Tableaux de Bord et Rapports

- [ ] **Dashboard principal** avec métriques clés
- [ ] **Graphiques interactifs** (contrats, échéances)
- [x] **Rapports automatisés** d'échéances
- [ ] **Export de données** (CSV, PDF, Excel)
- [ ] **Statistiques d'utilisation** par utilisateur
- [ ] **Alertes visuelles** pour les actions urgentes

## 🌐 Interface Utilisateur

- [x] **Design responsive** adaptatif mobile/desktop
- [x] **Interface intuitive** avec navigation claire
- [x] **Thème sombre/clair** selon préférences
- [ ] **Recherche globale** dans tous les modules
- [ ] **Raccourcis clavier** pour actions fréquentes
- [x] **Notifications toast** pour feedback utilisateur

[<- Retour à la page d'accueil](../README.md)
