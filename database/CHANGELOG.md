# Evolutions de la base de données

## Version 1.0.1 [2025-10-01]

- Mise à jour des champs de tables pour être en format snake_case :
  - `99_users` :
    - `shaMdp` --> `sha_mdp`
    - `falseTest` en `false_test`
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
