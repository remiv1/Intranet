#!/bin/bash

# Script de sauvegarde simple de la base de données MariaDB
# Usage: ./simple-backup.sh [nom_fichier_optionnel]

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

# Vérification du fichier .env
if [ ! -f "$ENV_FILE" ]; then
    error "Le fichier .env n'existe pas dans $PROJECT_DIR"
    error "Exécutez d'abord ./generate-env.sh pour créer la configuration"
    exit 1
fi

# Chargement des variables d'environnement
source "$ENV_FILE"

# Vérification des variables requises
if [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ]; then
    error "Variables d'environnement de base de données manquantes"
    error "Vérifiez DB_USER, DB_PASSWORD et DB_NAME dans .env"
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

# Configuration du fichier de sauvegarde
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$PROJECT_DIR/backup"
mkdir -p "$BACKUP_DIR"

# Nom du fichier de sauvegarde (personnalisable)
if [ -n "$1" ]; then
    BACKUP_FILE="$BACKUP_DIR/$1"
    # Ajouter l'extension .sql.gz si elle n'est pas présente
    if [[ ! "$BACKUP_FILE" =~ \.(sql\.gz|sql)$ ]]; then
        BACKUP_FILE="${BACKUP_FILE}.sql.gz"
    fi
else
    BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_${DATE}.sql.gz"
fi

log "Démarrage de la sauvegarde de la base de données"
log "Base de données: $DB_NAME"
log "Conteneur: $DB_CONTAINER"
log "Fichier de destination: $BACKUP_FILE"

# Effectuer la sauvegarde
log "Création de la sauvegarde..."

if docker exec "$DB_CONTAINER" mysqldump \
    --user="$DB_USER" \
    --password="$DB_PASSWORD" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --complete-insert \
    --add-drop-database \
    --databases "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    
    success "Sauvegarde créée avec succès !"
    
    # Affichage des informations sur le fichier
    file_size=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Fichier: $(basename "$BACKUP_FILE")"
    log "Taille: $file_size"
    log "Chemin complet: $BACKUP_FILE"
    
    # Vérification que le fichier n'est pas vide
    if [ -s "$BACKUP_FILE" ]; then
        success "Sauvegarde valide (fichier non vide)"
    else
        warning "Attention: le fichier de sauvegarde semble vide"
    fi
    
else
    error "Échec de la sauvegarde"
    rm -f "$BACKUP_FILE"
    exit 1
fi

echo ""
echo "📁 Sauvegardes disponibles dans $BACKUP_DIR:"
ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null | while read -r line; do
    echo "  $line"
done

echo ""
success "Sauvegarde terminée avec succès !"
echo ""
echo "💡 Pour restaurer cette sauvegarde plus tard:"
echo "   docker exec -i $DB_CONTAINER mysql -u\$DB_USER -p\$DB_PASSWORD < <(gunzip -c $BACKUP_FILE)"