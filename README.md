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

- **Génération des accès VPN** : Module de génération des accès VPN avec contrôle d'accès par rôle
- **Améliorations Signatures** : Notifications automatiques par email, rate limiting OTP, audit logs avancés
- **Tests Unitaires** : Couverture complète du module signature
- **Module de Reporting** : Tableaux de bord et statistiques avancées
- **Optimisation Mobile** : Amélioration de l'expérience utilisateur sur mobile
- **Optimisation Performance** : Analyse et amélioration des performances sur gros volumes
- **Sécurité Renforcée** : Audit sécurité et implémentation 2FA

> 📖 **Rapport détaillé** : Consultez le [rapport d'évolution des branches](./documentation/rapport-evolution-branches.md) pour un historique complet du développement.

## 📝 Description

Cette application web développée avec Flask permet la gestion complète d'un établissement scolaire. Elle offre des fonctionnalités avancées de gestion des utilisateurs, des contrats, des documents et des impressions à distance.

**Note** : Ce projet a été développé bénévolement pour un établissement scolaire secondaire (association à but non lucratif).

[Fichier d'Architecture](./documentation/architecture.md)

## 🚀 Installation et Déploiement

[Guide de l'environnement de production](./documentation/environnement.md)
[Guide d'installation rapide](./documentation/INSTALL.md)

## ⭐ Fonctionnalités Principales

[Détail des fonctionnalités](./documentation/fonctionnalites.md)

## 🔧 Maintenance et Monitoring

[Guide de maintenance](./documentation/maintenance.md)

## 🚀 Support et Développement

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
