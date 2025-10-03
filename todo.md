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

## Authentification

- [ ] Modification du mode d'authentification (Argon2)

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
