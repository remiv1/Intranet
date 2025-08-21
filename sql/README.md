# Scripts SQL pour le développement

Ce dossier contient les scripts SQL utilisés pour initialiser et configurer la base de données en environnement de développement.

## Fichiers

### `01_init_database.sql`
- Script d'initialisation de la base de données
- Crée les tables principales si elles n'existent pas
- Ajoute les index nécessaires pour les performances
- **Ce fichier peut être mergé vers la branche principale**

### `test_user.sql`
- Script pour créer des données de test
- Contient un utilisateur de test avec des permissions élevées
- Inclut des exemples de contrats et documents
- **⚠️ CE FICHIER NE DOIT PAS ÊTRE MERGÉ VERS LA BRANCHE PRINCIPALE**
- Utilisé uniquement pour les tests en développement

## Utilisation

Les scripts sont automatiquement exécutés lors du démarrage du conteneur MariaDB en mode développement grâce au montage du volume dans `docker-compose.dev.yml`.

### Ordre d'exécution
1. `01_init_database.sql` - Initialise les tables
2. `test_user.sql` - Ajoute les données de test

### Utilisateur de test créé
- **Identifiant**: `testuser`
- **Mot de passe**: `testpassword`
- **Email**: `test.user@example.com`
- **Habilitation**: `9999` (niveau maximum)

## Note importante
Le fichier `test_user.sql` contient des données sensibles de test et ne doit jamais être intégré dans la branche de production. Assurez-vous qu'il reste uniquement dans les branches de développement.
