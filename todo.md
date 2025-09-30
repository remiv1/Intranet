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

### 1. Validation des statuts lors des demandes de signature (GET)

**Problème** : Actuellement, la route GET `/signature/signer/<doc_id>/<hash>` ne vérifie pas :

- Si le document est déjà signé (statut != 0)
- Si le document est périmé (expire_at < maintenant)

**Solution à implémenter** :

```python
# Dans la route GET de signature_do()
if doer.document.status != 0:
    return render_template(ADMINISTRATION, error_message="Ce document a déjà été traité.")

if doer.invitation.expire_at < datetime.now():
    return render_template(ADMINISTRATION, error_message="Cette invitation a expiré.")
```

### 2. Automatisme base de données pour expiration

**Problème** : Pas d'automatisme pour passer les documents expirés en statut -1

**Solutions possibles** :

1. **Trigger MySQL** : Automatisme au niveau base de données
2. **Tâche CRON** : Script Python exécuté périodiquement
3. **Middleware Flask** : Vérification à chaque requête (moins performant)

**Recommandation** : Tâche CRON quotidienne + vérification temps réel dans les routes

### 3. Génération PDF final avec signatures + certificat

**Fonctionnalité manquante** : Route pour générer le PDF final quand tous les points sont signés

**À implémenter** :

- Route : `/signature/generer-pdf-final/<doc_id>`
- Vérifier que tous les points sont signés (status = 1)
- Générer PDF avec signatures incrustées
- Ajouter certificat de signatures
- Envoyer par email à tous les signataires + créateur

### 4. Notification email automatique

**À implémenter** :

- Email automatique quand document entièrement signé
- PDF final en pièce jointe
- Liste des signataires et dates de signature

## Autres améliorations identifiées

### 5. Sécurité et validation

- [ ] Validation de l'intégrité des signatures (hash)
- [ ] Vérification anti-rejeu des tokens
- [ ] Rate limiting sur les tentatives OTP
- [ ] Audit log des tentatives d'accès

### 6. Gestion des erreurs

- [ ] Meilleure gestion des documents supprimés/corrompus
- [ ] Nettoyage des fichiers temporaires
- [ ] Gestion des erreurs d'envoi email

### 7. Performance

- [ ] Cache des documents fréquemment consultés
- [ ] Optimisation des requêtes base de données
- [ ] Compression des données de signature

### 8. Interface utilisateur

- [ ] Prévisualisation des signatures avant validation
- [ ] Historique des signatures pour chaque utilisateur
- [ ] Dashboard administrateur

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

### Table Points

- Index composite (id_document, status) pour vérification rapide
- Contraintes d'intégrité
