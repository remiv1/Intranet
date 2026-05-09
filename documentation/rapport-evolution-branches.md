# Rapport d'Évolution des Branches - Projet Intranet

**Date du rapport :** 5 octobre 2025  
**Projet :** Intranet - Système de gestion des contrats et signatures électroniques  
**Auteur :** Rémi Verschuur  

---

## 1. Récapitulatif Général

| Branche | Période | Durée | Commits | Fonctionnalités Principales | État |
| --- | --- | --- | --- | --- | --- |
| **main** | Mars 2025 - Oct 2025 | 7 mois | 250+ | Base de l'application, gestion contrats | ✅ Stable |
| **sprint_signature** | 27 Sept - 5 Oct 2025 | 9 jours | 50+ | Module signature électronique complet | ✅ Mergé |
| **sprint_contacts** | 27 Sept 2025 | 1 jour | 3 | Gestion des contacts contrats | ✅ Mergé |
| **sprint_mails** | 19 Sept 2025 | 1 jour | 4 | Système d'envoi emails amélioré | ✅ Mergé |
| **sprint_bills** | 15-19 Sept 2025 | 4 jours | 25+ | Gestion des factures | ✅ Mergé |
| **sprint_workflows** | 20 Sept 2025 | 1 jour | 8 | CI/CD et tests automatisés | ✅ Mergé |
| **sprint_code_cleaner** | 11-15 Sept 2025 | 4 jours | 15+ | Refactorisation et nettoyage | ✅ Mergé |
| **monitoring** | Juil-Sept 2025 | 2 mois | 8 | Logs et monitoring MongoDB | 🔄 En dev |
| **secure-app** | 18 Juil 2025 | 1 jour | 2 | HTTPS et sécurisation Nginx | ✅ Mergé |
| **depot_devoirs** | 25 Mai 2025 | 1 jour | 1 | Module dépôt devoirs | ⏸️ Suspendu |
| **cloud** | 31 Mai 2025 | 1 jour | 2 | Fonctionnalités cloud | ❌ Annulé |

---

## 2. Analyse Détaillée par Branche

### 2.1 sprint_signature ✅

**Période :** 27 septembre - 5 octobre 2025  
**Durée d'exécution :** 9 jours  
**Commits :** 50+ commits majeurs  
**État :** Mergé dans main le 5 octobre 2025 (tag: version-1.3.0)  

#### Travail Réalisé (9 jours - Complet)

- **Module de signature électronique complet** avec PDF.js et SignaturePad
- **Sécurisation d'accès aux documents** avec système HMAC
- **Interface de création** : placement interactif des points de signature
- **Interface de signature** : capture graphique haute fidélité
- **Stockage temporaire sécurisé** avec variables d'environnement
- **Architecture JavaScript optimisée** en 3 fichiers modulaires
- **Gestion avancée des utilisateurs** avec soft-delete pour préserver l'intégrité des signatures
- **Classe SignatureMaker dédiée** pour la création de documents à signer
- **Classe SignedDocumentCreator** pour la génération des PDF signés avec toutes les signatures
- **Documentation technique approfondie** du code et des processus
- **Diagramme UML de base de données mis à jour** avec nouveau modèle SVG
- **Système de dossiers temporaires** non montés pour la sécurité
- **Journalisation complète des actions** utilisateur dans le système de signature
- **Automatisme d'expiration** des documents via événement MySQL (CRON)

#### Corrections Critiques (30 septembre 2025)

- **Résolution erreur SQLAlchemy** : Correction du conflit `ip_adresse` vs `ip_addresse` dans les modèles
- **Gestion cohérente des réponses** : API uniformisée retournant toujours du JSON pour les erreurs
- **Correction timestamp MySQL** : Remplacement des timestamps Unix par des objets DateTime natifs
- **Harmonisation des attributs** : `signe_at` au lieu de `signed_at` pour la cohérence du modèle
- **Gestion des erreurs améliorée** : Try/catch avec rollback automatique en cas d'erreur
- **Consolidation de la documentation** : Fusion des notes techniques dans le fichier todo.md central

#### Refactoring Majeur (3-4 octobre 2025)

- **Nettoyage complet de signatures.py** : Suppression des fonctions obsolètes et imports inutiles
  - Réorganisation alphabétique des imports par catégorie (stdlib, third-party, local)
  - Suppression de ~100 lignes de code obsolète (`_add_text_signature_fallback`, `_add_signature_metadata_to_page`)
  - Élimination des duplications d'imports (datetime, Config, MIME*)
  - Suppression de l'attribut inutilisé `signatory_name` dans SignatureDoer
  - Création de la classe **SignedDocumentCreator** pour la génération optimisée des PDF signés
  
- **Réduction drastique de la complexité cognitive** :
  - `_create_signature_overlay` : **207 lignes → 6 méthodes <50 lignes** (complexité 67/15 → <15/méthode)
    - `_create_signature_overlay()` : orchestration principale (~50 lignes)
    - `_add_single_signature_to_canvas()` : gestion signature unique (~30 lignes)
    - `_process_signature_image()` : traitement d'image (~35 lignes)
    - `_calculate_signature_position()` : calcul de position (~50 lignes)
    - `_draw_signature_on_canvas()` : dessin sur canvas (~15 lignes)
    - `_add_signature_metadata_text()` : métadonnées textuelles (~50 lignes)
  
  - `apply_signatures_to_pdf` : **100 lignes → 6 méthodes <25 lignes** (complexité 19/15 → <10/méthode)
    - `apply_signatures_to_pdf()` : orchestration (~20 lignes)
    - `_prepare_signed_document()` : initialisation (~20 lignes)
    - `_process_all_pages()` : traitement des pages (~20 lignes)
    - `_write_signed_pdf()` : écriture PDF (~18 lignes)
    - `_create_fallback_copy()` : copie de secours (~5 lignes)
    - `_update_document_hash()` : mise à jour hash (~9 lignes)

- **Corrections de typage Python** :
  - Ajout de `# type: ignore[call-arg]` pour compatibilité reportlab/Pillow
  - Validation systématique des types `Path | None` avec guards
  - Résolution complète des erreurs Pylance/Pyright (0 erreur)

- **Amélioration des templates HTML** :
  - Correction validation HTML du template `signed_document_mail.html`
  - Remplacement de `<ul>/<li>` par `<div>` avec classes CSS pour les signataires
  - Ajout de coches vertes (✓) via pseudo-éléments CSS pour améliorer le visuel
  - Conformité stricte HTML5 (pas de nœuds texte dans les listes)

#### Évolutions Techniques

- **Base de données** : 4 nouvelles tables finalisées (DocToSigne, Signatures, Points, Users améliorée)
- **Frontend** : Integration PDF.js 3.11.174 + SignaturePad 4.1.7
- **Backend** : Flask Blueprint avec classes SecureDocumentAccess et SignatureMaker
- **Sécurité** : Cryptographie HMAC-SHA256 + gestion d'identifiants utilisateur uniques
- **Architecture** : Classes métier dédiées et séparation des responsabilités
- **Documentation** : Modèle de données visuel en SVG et documentation technique

#### Finalisation (4-5 octobre 2025)

- ✅ **Automatisme d'expiration** : Événement MySQL (CRON) qui expire automatiquement les documents périmés toutes les heures
- ✅ **Génération PDF final** : Classe SignedDocumentCreator pour créer le PDF avec toutes les signatures regroupées par page
- ✅ **Gestion optimisée des signatures** : Regroupement des signatures par page pour améliorer les performances
- ✅ **Journalisation complète** : Logs détaillés de toutes les actions utilisateur dans le système de signature
- ✅ **Affichage des documents signés** : Intégration dans la vue détail du contrat avec liste des documents signés
- ✅ **Configuration Docker améliorée** : Synchronisation heure/fuseau horaire, optimisation des ports
- ✅ **Icônes Bootstrap** : Amélioration visuelle des templates HTML

#### Améliorations Futures Identifiées

- **Notifications automatiques** : Email avec PDF final en pièce jointe à tous les signataires (prévu T4 2025)
- **Sécurité renforcée** : Rate limiting OTP, audit logs avancés, validation intégrité signatures (prévu T4 2025)
- **Tests unitaires** : Couverture complète du module signature (prévu T4 2025)
- **Gestion des erreurs avancée** : Meilleure gestion des documents corrompus/supprimés (prévu T4 2025)

#### Fichiers Modifiés/Créés

```txt
+ app/bp_signature.py (route complète de gestion des signatures)
+ app/signatures.py (classes SignatureMaker, SignatureDoer, SignedDocumentCreator)
+ app/static/js/signatures-*.js (3 modules JavaScript optimisés)
+ app/templates/signatures/*.html (templates complets pour le workflow)
+ database/251003_MigrationScript.sql (événement MySQL expire_signatures)
~ app/models.py (tables DocToSigne, Signatures, Points, Users)
~ app/templates/contrat_detail.html (intégration liste documents signés)
~ docker-compose.yaml (synchronisation heure/fuseau horaire)
~ documentation/UML_BdD.svg (diagramme mis à jour)
~ documentation/rapport-evolution-branches.md (mise à jour 05/10)
```

---

### 2.2 sprint_contacts ✅

**Période :** 27 septembre 2025  
**Durée d'exécution :** 1 jour  
**État :** Mergé dans main  

#### Travail Réalisé (1 jour)

- **Gestion complète des contacts** pour les contrats
- **CRUD complet** : Ajout, modification, suppression (hard delete)
- **Interface utilisateur** avec confirmations JavaScript
- **Intégration** dans le système de contrats existant

#### Évolutions

- Nouvelle table `contacts` en base de données
- Routes RESTful pour la gestion des contacts
- Interface responsive intégrée au template `contrat_detail.html`

---

### 2.3 sprint_mails ✅

**Période :** 19 septembre 2025  
**Durée d'exécution :** 1 jour  
**État :** Mergé dans main  

#### Travail Réalisé pendant le sprint (1 jour)

- **Templates HTML pour emails** avec design responsive
- **Token API sécurisé** pour l'accès aux rapports
- **Amélioration des logs** d'envoi d'emails
- **Variables d'environnement dynamiques** relues à chaque requête
- **Documentation API** avec exemples curl

#### Évolutions (Majeures)

- Système de templates HTML pour les notifications
- Authentification par token pour les API
- Logging avancé des envois d'emails

---

### 2.4 sprint_bills ✅

**Période :** 15-19 septembre 2025  
**Durée d'exécution :** 4 jours  
**État :** Mergé dans main  

#### Travail Réalisé (4 jours)

- **Module de gestion des factures** complet
- **Upload et gestion de fichiers** sécurisée
- **Nomenclature automatique** des documents
- **Interface de consultation** et téléchargement
- **Migration Alembic** pour la nouvelle table `13_factures`

#### Évolutions Majeures

- Table `factures` avec relations vers les contrats
- Système de nommage automatique des fichiers
- Sécurisation des uploads avec validation de types
- Interface administrateur pour la gestion des factures

#### Statistiques

- 25+ commits sur 4 jours
- Nouvelle table en base de données
- +300 lignes de code Python
- Templates HTML pour l'interface

---

### 2.5 sprint_workflows ✅

**Période :** 20 septembre 2025  
**Durée d'exécution :** 1 jour intensif  
**État :** Mergé dans main  

#### Travail Réalisé durant le sprint (1 jour)

- **Pipeline CI/CD complet** avec GitHub Actions
- **Tests automatisés** avec pytest
- **Validation Docker** des conteneurs
- **Cache des dépendances** Python
- **Configuration multi-environnements**

#### Évolutions Principales

- Workflow Docker automatisé
- Tests unitaires avec fixtures
- Validation de l'environnement avant déploiement
- Support Python 3.12 exclusivement

---

### 2.6 sprint_code_cleaner ✅

**Période :** 11-15 septembre 2025  
**Durée d'exécution :** 4 jours  
**État :** Mergé dans main  

#### Travail Réalisé (5 jours)

- **Refactorisation complète** du codebase
- **Migration vers snake_case** pour la cohérence
- **Amélioration de la documentation** API
- **Nettoyage des imports** et dépendances obsolètes
- **Annotations de type** Python
- **Configuration Alembic** pour les migrations

#### Évolutions Correctives

- Standardisation du code selon PEP 8
- Documentation API complète
- Système de migration de base de données
- Amélioration de la lisibilité du code

---

### 2.7 monitoring 🔄

**Période :** Juillet - septembre 2025  
**Durée d'exécution :** 2 mois (développement continu)  
**État :** En développement  

#### Travail Réalisé (continu)

- **Intégration MongoDB** pour les logs d'activité
- **API FastAPI** pour le monitoring
- **Gestion des habilitations** avancée
- **Configuration Nginx** pour HTTP/HTTPS
- **Logs structurés** avec horodatage

#### Architecture

- Service MongoDB séparé
- API de monitoring en FastAPI
- Logs d'activité centralisés
- Dashboard de monitoring (en cours)

---

### 2.8 secure-app ✅

**Période :** 18 juillet 2025  
**Durée d'exécution :** 1 jour  
**État :** Mergé dans main  

#### Travail Réalisé sur le sprint (1 jour)

- **Configuration HTTPS** automatique
- **Redirection HTTP vers HTTPS**
- **Amélioration de la sécurité Nginx**
- **Gestion des certificats SSL**

#### Impact Sécurité

- Chiffrement TLS/SSL obligatoire
- Headers de sécurité HTTP
- Protection contre les attaques communes

---

### 2.9 Branches Abandonnées/Suspendues

#### depot_devoirs ❌

**Période :** 25 mai 2025  
**Raison :** Remplacement par une solution partage de documents  
**Travail :** Page HTML pour dépôt de devoirs (fonctionnalité éducative)

#### cloud ❌

**Période :** 31 mai 2025  
**Raison :** Complexité technique vs ROI  
**Travail :** Intégration services cloud (stockage, authentification)

---

## 3. Métriques de Développement

### 3.1 Évolution du Code Base

```txt
Mars 2025    : ~2000 lignes (base)
Juillet 2025 : ~4000 lignes (+sécurité, monitoring)
Sept 2025    : ~8500 lignes (+factures, contacts)
Oct 2025     : ~10000 lignes (+signatures électroniques complètes)
```

### 3.2 Complexité des Fonctionnalités

| Sprint | Complexité | Temps Réel | Réussite |
| --- | --- | --- | --- |
| Signature | Très Élevée | 9 jours | ✅ 100% |
| Bills | Élevée | 4 jours | ✅ 100% |
| Code Cleaner | Moyenne | 4 jours | ✅ 100% |
| Contacts | Faible | 1 jour | ✅ 100% |
| Mails | Moyenne | 1 jour | ✅ 100% |
| Workflows | Moyenne | 1 jour | ✅ 100% |

### 3.3 Technologies Intégrées par Sprint

- **sprint_signature** : PDF.js, SignaturePad, Cryptographie HMAC
- **sprint_bills** : Alembic, Gestion fichiers, SQLAlchemy avancé
- **sprint_workflows** : GitHub Actions, pytest, Docker validation
- **monitoring** : MongoDB, FastAPI, Logging structuré
- **secure-app** : SSL/TLS, Nginx security headers

---

## 4. Analyse des Performances de Développement

### 4.1 Vélocité par Sprint

```txt
sprint_signature : 9 jours → Module très complexe finalisé (excellent)
sprint_contacts  : 1 jour → Fonctionnalité complète (excellent)  
sprint_mails     : 1 jour → Amélioration majeure (excellent)
sprint_bills     : 4 jours → Module complexe (bon)
sprint_workflows : 1 jour → CI/CD complet (excellent)
```

### 4.2 Qualité du Code

- **Tests** : Intégrés depuis sprint_workflows, tests signatures fonctionnels
- **Documentation** : Améliorée à chaque sprint, documentation technique approfondie
- **Standards** : Cohérence depuis sprint_code_cleaner, complexité cognitive maîtrisée
- **Sécurité** : Renforcée progressivement, validation systématique des types
- **Maintenabilité** : Refactoring méthodique, fonctions courtes et focalisées (≤50 lignes)
- **Typage** : Type hints complets, 0 erreur Pylance/Pyright

### 4.3 Gestion des Risques

- ✅ **Docker** : Conteneurisation complète
- ✅ **Migrations DB** : Alembic intégré
- ✅ **Tests automatisés** : Pipeline CI/CD
- ✅ **Sécurité** : HTTPS, tokens, HMAC
- ✅ **Sauvegarde** : Scripts automatisés

---

## 5. Recommandations et Perspectives

### 5.1 Points Forts Identifiés

1. **Vélocité élevée** sur les sprints courts (1-2 jours)
2. **Architecture modulaire** bien pensée
3. **Intégration continue** efficace
4. **Sécurité** prise en compte dès la conception
5. **Documentation** maintenue à jour

### 5.2 Axes d'Amélioration

1. **Tests unitaires** à généraliser sur tous les modules (en cours pour signatures)
2. **Tests E2E** à implémenter
3. **Monitoring** à finaliser et déployer
4. **Performance** à analyser sur les gros volumes
5. **UX/UI** à améliorer sur mobile ou développement d'une app dédiée (flutter)
6. **Couverture de code** à mesurer et améliorer (objectif : 80%+)

### 5.3 Roadmap

#### Complété ✅

1. ~~**Module signature électronique complet**~~ (Finalisé - 5 octobre 2025)
   - ✅ Automatisme d'expiration des documents
   - ✅ Génération PDF final avec toutes les signatures
   - ✅ Journalisation complète des actions
   - ✅ Interface utilisateur complète

#### En cours et à venir

1. **Améliorations signature électronique**
   - Notifications automatiques par email avec PDF en pièce jointe
   - Rate limiting sur les OTP
   - Audit logs avancés
   - Tests unitaires du module signature
2. **Tests CI/CD automatisés**
3. **Partage de documents sécurisé**
4. **Génération de documents sur modèles**
5. **Automatisation des sauvegardes**
6. **Module reporting avancé**
7. **Tests E2E** à implémenter
8. **Déploiement monitoring**
9. **Création app mobile**

---

## 6. Conclusion

Le projet Intranet montre une **évolution exceptionnelle** sur les 7 derniers mois avec :

- **10 branches actives** avec des objectifs clairs
- **8 fonctionnalités majeures** intégrées avec succès
- **Architecture moderne** (Docker, CI/CD, tests automatisés)
- **Sécurité renforcée** à tous les niveaux
- **Vélocité de développement élevée** et constante

Le **sprint_signature**, finalisé et mergé le **5 octobre 2025**, représente le **défi technique le plus complexe** du projet avec une **architecture avancée** développée sur **9 jours**. Ce sprint a permis de :

### Réalisations Majeures du Sprint Signature

- ✅ **Module de signature électronique complet** avec PDF.js, SignaturePad et cryptographie HMAC
- ✅ **Architecture 3 classes métier** : SignatureMaker, SignatureDoer, SignedDocumentCreator
- ✅ **Automatisme d'expiration MySQL** : Événement CRON toutes les heures pour expirer automatiquement les documents
- ✅ **Génération PDF optimisée** : Regroupement des signatures par page pour améliorer les performances
- ✅ **Journalisation complète** : Logs détaillés de toutes les actions utilisateur
- ✅ **Refactoring majeur** : Réduction de la complexité cognitive (division par 4)
- ✅ **Code propre** : Suppression de ~100 lignes obsolètes, 0 erreur de typage
- ✅ **Documentation technique** : Diagramme UML mis à jour, documentation approfondie
- ✅ **Configuration Docker** : Synchronisation heure/fuseau horaire, optimisation des services

### Points Remarquables

- **Complexité cognitive maîtrisée** : Toutes les fonctions respectent le seuil de 15
- **Code propre** : 0 erreur de linting, typage strict avec validation systématique
- **Architecture modulaire** : Classes métier dédiées, séparation claire des responsabilités
- **Sécurité renforcée** : Cryptographie HMAC, soft-delete pour l'intégrité des données
- **Tests fonctionnels** : Validation des signatures de base et avancées
- **Design soigné** : Templates HTML validés HTML5, UX optimisée avec Bootstrap
- **Automatisation** : Expiration automatique des documents via événement MySQL

### Impact et Perspectives

Le module de signature électronique est **opérationnel et prêt en production**. Les améliorations futures (notifications automatiques, rate limiting OTP, tests unitaires) sont des optimisations qui n'affectent pas la fonctionnalité de base.

La **qualité du code** et la **discipline de développement** montrent une **maturité technique excellente** pour un projet de cette envergure, avec une **documentation technique approfondie**, un **modèle de données visuellement représenté** et une **dette technique activement réduite**.

**Statistiques du Sprint Signature :**

- **Durée :** 9 jours (27 septembre - 5 octobre 2025)
- **Commits :** 50+ commits structurés
- **Lignes de code :** ~1500 lignes ajoutées (net après refactoring)
- **Fichiers créés :** 15+ fichiers (Python, JavaScript, HTML, SQL)
- **Tag version :** version-1.3.0

---

**Rapport généré le :** 5 octobre 2025  
**Version :** 1.6 (sprint signature - finalisé et mergé)  
**Prochaine révision :** Fin octobre 2025
