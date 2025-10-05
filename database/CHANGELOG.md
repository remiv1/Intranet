# Evolutions de la base de données

## Version 1.1.0 [2025-10-15]

- Ajouts des tables nécessaires pour la gestion des signatures électroniques mutli-signatires, multi-signatures dans les documents :
  - `20_documents_à signer` : pour répertorier les documents nécessitant une signature électronique.
  - `21_points` : pour stocker les informations sur les points de signature dans les documents.
  - `22_signatures` : pour enregistrer les signatures rattachées aux points de signatures (une signature peut être liée à plusieurs points de signature).
  - `23_invitations` : pour gérer les invitations envoyées aux signataires.
  - `24_audit_logs` : pour conserver un historique des actions liées aux signatures électroniques.

## Version 1.0.1 [2025-10-01]

- Mise à jour des champs de tables pour être en format snake_case :
  - `99_users` :
    - `sha_mdp` --> `sha_mdp`
    - `false_test` en `false_test`
  - `01_contrats` :
    - `Type` --> `type_contrat`
    - `SType` --> `sous_type_contrat`
    - `numContratExterne` --> `id_externe_contrat`
    - `dateDebut` --> `date_debut`
    - `dateFinPreavis` --> `date_fin_preavis`
    - `dateFin` --> `date_fin`
  - `11_documents` :
    - `idContrat` --> `id_contrat`
    - `Type` --> `type_document`
    - `SType` --> `sous_type_document`
    - `strLien` --> `str_lien`
    - `dateDocument` --> `date_document`
  - `12_evenements` :
    - `idContrat` --> `id_contrat`
    - `dateEvenement` --> `date_evenement`
    - `Type` --> `type_evenement`
    - `SType` --> `sous_type_evenement`

## Version 1.0.0 [2024-06-27]

- Initialisation de la base de données avec les tables suivantes :
  - `99_users` : pour stocker les informations des utilisateurs.
  - `01_contrats` : pour stocker les informations des contrats.
  - `11_documents` : pour stocker les informations des documents des contrats.
  - `12_evenements` : pour stocker les informations des événements liés aux contrats.
