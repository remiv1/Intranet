#!/bin/bash

# Script de restauration simple de la base de données MariaDB
# Usage: ./simple-restore.sh <fichier_sauvegarde>

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de log
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Fonction d'aide
show_help() {
    cat << EOF
Usage: $0 <fichier_sauvegarde>

Script de restauration de la base de données MariaDB à partir d'une sauvegarde.

Arguments:
  fichier_sauvegarde    Chemin vers le fichier de sauvegarde (.sql.gz ou .sql)

Options:
  --help, -h           Affiche cette aide
  --list, -l           Liste les sauvegardes disponibles

Exemples:
  $0 backup/test_backup.sql.gz
  $0 backup/backup_Peraudiere_20250915_151435.sql.gz
  $0 --list

⚠️  ATTENTION: Cette opération va REMPLACER complètement la base de données actuelle !

EOF
}

# Fonction pour lister les sauvegardes disponibles
list_backups() {
    local backup_dir="$PROJECT_DIR/backup"
    
    echo "📁 Sauvegardes disponibles dans $backup_dir:"
    echo ""
    
    if [ -d "$backup_dir" ] && [ "$(ls -A "$backup_dir"/*.sql.gz 2>/dev/null)" ]; then
        ls -lh "$backup_dir"/*.sql.gz 2>/dev/null | while read -r line; do
            echo "  $line"
        done
    else
        echo "  Aucune sauvegarde trouvée"
        echo "  Créez une sauvegarde avec: ./scripts/simple-backup.sh"
    fi
    echo ""
}

# Vérification des arguments
if [ $# -eq 0 ]; then
    error "Fichier de sauvegarde requis"
    echo ""
    show_help
    exit 1
fi

case "$1" in
    --help|-h)
        show_help
        exit 0
        ;;
    --list|-l)
        list_backups
        exit 0
        ;;
esac

BACKUP_FILE="$1"

# Vérification du fichier de sauvegarde
if [ ! -f "$BACKUP_FILE" ]; then
    # Essayer avec le chemin relatif depuis backup/
    if [ ! -f "$PROJECT_DIR/backup/$BACKUP_FILE" ]; then
        error "Fichier de sauvegarde introuvable: $BACKUP_FILE"
        echo ""
        list_backups
        exit 1
    else
        BACKUP_FILE="$PROJECT_DIR/backup/$BACKUP_FILE"
    fi
fi

# Vérification du fichier .env
if [ ! -f "$ENV_FILE" ]; then
    error "Le fichier .env n'existe pas dans $PROJECT_DIR"
    exit 1
fi

# Chargement des variables d'environnement
source "$ENV_FILE"

# Vérification des variables requises
if [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ] || [ -z "$ROOT_PASSWORD" ]; then
    error "Variables d'environnement de base de données manquantes"
    exit 1
fi

# Nom du conteneur de base de données
DB_CONTAINER="intranet_db"

# Vérification si le conteneur est en cours d'exécution
if ! docker ps --format "table {{.Names}}" | grep -q "^$DB_CONTAINER$"; then
    error "Le conteneur $DB_CONTAINER n'est pas en cours d'exécution"
    error "Démarrez l'application avec: docker-compose up -d"
    exit 1
fi

log "Démarrage de la restauration de la base de données"
log "Fichier de sauvegarde: $BACKUP_FILE"
log "Base de données: $DB_NAME"
log "Conteneur: $DB_CONTAINER"

# Affichage des informations sur le fichier
file_size=$(du -h "$BACKUP_FILE" | cut -f1)
log "Taille du fichier: $file_size"

# Confirmation de l'utilisateur
echo ""
warning "⚠️  ATTENTION: Cette opération va REMPLACER complètement la base de données '$DB_NAME' !"
echo ""
read -p "Êtes-vous sûr de vouloir continuer ? (tapez 'OUI' en majuscules): " -r
if [[ $REPLY != "OUI" ]]; then
    log "Opération annulée par l'utilisateur"
    exit 0
fi

echo ""
log "Restauration en cours..."

# Déterminer la commande de décompression selon l'extension
if [[ "$BACKUP_FILE" =~ \.gz$ ]]; then
    DECOMPRESS_CMD="gunzip -c"
else
    DECOMPRESS_CMD="cat"
fi

# Effectuer la restauration
if $DECOMPRESS_CMD "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" mysql --user="root" --password="$ROOT_PASSWORD"; then
    success "Restauration terminée avec succès !"
    
    # Vérification de la restauration
    log "Vérification de la restauration..."
    if docker exec "$DB_CONTAINER" mysql --user="$DB_USER" --password="$DB_PASSWORD" --database="$DB_NAME" -e "SHOW TABLES;" >/dev/null 2>&1; then
        success "Base de données accessible après restauration"
        
        # Affichage du nombre de tables
        table_count=$(docker exec "$DB_CONTAINER" mysql --user="$DB_USER" --password="$DB_PASSWORD" --database="$DB_NAME" -e "SHOW TABLES;" 2>/dev/null | wc -l)
        log "Nombre de tables dans la base: $((table_count - 1))"
    else
        warning "Impossible de vérifier la base de données après restauration"
    fi
    
else
    error "Échec de la restauration"
    exit 1
fi

echo ""
success "Restauration de la base de données terminée !"
echo ""
echo "💡 La base de données '$DB_NAME' a été restaurée depuis:"
echo "   $BACKUP_FILE"