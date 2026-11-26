# TODO List

## Tests CI/CD

- [ ] Création des tests ci/cd
  - [ ] test d'ajout d'utilisateurs
  - [ ] test de modification d'utilisateurs
  - [ ] test de suppression d'utilisateurs
  - [ ] test d'ajout de contrats
  - [ ] test de modification de contrats
  - [ ] test d'ajout d'évènements
  - [ ] test de modification d'évènements
  - [ ] test d'ajout de documents
  - [ ] test de modification de documents

## Authentification & Sécurité

- [x] Passage à l'authentification Argon2
  - [x] Migration SHA-256 vers Argon2id à la première connexion réussie
  - [x] Création et modification des mots de passe directement en Argon2id
  - [x] Autorisation après rollback en cas d'échec d'écriture et logs MIGR-AUTH
- [x] Gestion du jeton de rapport qui n'empêche pas l'accès non autorisé
  - [x] Utiliser un jeton dédié
  - [x] Retour explicite en cas d'accès non autorisé
  - [x] Refus du démarrage sans jeton et tentative d'alerte par email
  - [x] Planification mensuelle avec Supercronic, binaire AMD64 ou ARM64
- [x] Gestion des redirections après authentification
  - [x] Limiter à une URL relative
  - [x] Destination invalide : retour à l'accueil après connexion réussie
  - [x] Échec de connexion : conserver uniquement une destination locale valide
- [x] Validation systématique des droits pour éviter les droits ouverts mais périmés.
  - [x] Table de sessions et migration Alembic dédiée
  - [x] Expiration après 20 minutes d'inactivité
  - [x] Révocation de toutes les sessions après changement de droits ou de mot de passe
  - [x] Refus de connexion si l'enregistrement de la session échoue
- [ ] Délais de connexion et limitation des tentatives : stratégie à valider
- [ ] Implémenter la protection CSRF dans les formulaires.

## Système de signature - Issues identifiées et à corriger

## Prochaines étapes prioritaires

1. **Immédiat** : Validation statuts + expiration (GET)
2. **Court terme** : Automatisme expiration + génération PDF final
3. **Moyen terme** : Améliorations sécurité et performance
4. **Long terme** : Dashboard et conformité légale

## Structure des tables à vérifier

### Table Signatures

- Vérifier les index pour les performances
- Considérer la partition par date

### Table Invitations

- Index sur expire_at pour l'automatisme d'expiration
- Nettoyage périodique des invitations expirées
