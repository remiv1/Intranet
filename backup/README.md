# Scripts de Sauvegarde et Restauration - Base de Données MariaDB

Ce répertoire contient les scripts pour sauvegarder et restaurer la base de données MariaDB de l'intranet.

## 📋 Prérequis

- Conteneurs de l'intranet en cours d'exécution (`docker-compose up -d`)
- Fichier `.env` configuré dans le répertoire parent

## 🔄 Sauvegarde

### Script de sauvegarde simple

```bash
# Sauvegarde avec nom automatique (date/heure)
./backup/simple-backup.sh

# Sauvegarde avec nom personnalisé
./backup/simple-backup.sh ma_sauvegarde
./backup/simple-backup.sh sauvegarde_avant_migration
```

**Caractéristiques :**

- Utilise `mysqldump` pour une sauvegarde complète
- Compression automatique en `.gz`
- Sauvegarde des routines, triggers et événements
- Fichiers stockés dans le dossier `backup/`

### Exemples d'utilisation

```bash
# Sauvegarde quotidienne
./backup/simple-backup.sh backup_$(date +%Y%m%d)

# Sauvegarde avant maintenance
./backup/simple-backup.sh avant_maintenance_$(date +%Y%m%d)
```

## 🔙 Restauration

### Script de restauration simple

```bash
# Restaurer une sauvegarde spécifique
./backup/simple-restore.sh backup/test_backup.sql.gz

# Lister les sauvegardes disponibles
./backup/simple-restore.sh --list

# Afficher l'aide
./backup/simple-restore.sh --help
```

**⚠️ Attention :** La restauration remplace complètement la base de données existante !

## 📁 Structure des fichiers

```txt
backup/
├── simple-backup.sh    # Script de sauvegarde manuelle
├── simple-restore.sh   # Script de restauration
├── test_backup.sql.gz
├── backup_Peraudiere_20250915_151435.sql.gz
├── ...
└── README.md          # Cette documentation
```
