#!/bin/bash

### CONFIGURATION ###
PROJECT_DIR="/var/www/intranet/Intranet"
DB_CONTAINER="db"

### CHARGER LES VARIABLES APPLICATIVES ###
set -o allexport
source "$PROJECT_DIR/.env"
set +o allexport

### CHARGER LES VARIABLES DE SAUVEGARDE ###
set -o allexport
source "$PROJECT_DIR/.env.sauv"
set +o allexport

DATE=$(date +%F_%H-%M)
FILENAME="${DB_NAME}_${DATE}.sql.gz"
LOCAL_FILE="$BACKUPDIR/$FILENAME"

### SAUVEGARDE LOCALE ###
cd "$PROJECT_DIR"

echo "[INFO] Dump de la base $DB_NAME..."
docker compose exec -T $DB_CONTAINER \
    mysqldump -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
    | gzip > "$LOCAL_FILE"

if [ $? -ne 0 ]; then
    echo "[ERREUR] Le dump a échoué."
    exit 1
fi

echo "[OK] Dump créé : $LOCAL_FILE"

### ROTATION LOCALE (30 jours) ###
find "$BACKUPDIR" -type f -mtime +30 -delete

### TRANSFERT VERS LE SERVEUR DISTANT ###
echo "[INFO] Transfert vers le serveur distant..."
rsync -avz -e "ssh -i $KEY_CONNECTION -p $REMOTE_PORT" "$LOCAL_FILE" \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

if [ $? -ne 0 ]; then
    echo "[ERREUR] Le transfert a échoué."
    exit 1
fi

echo "[OK] Transfert terminé."

### ROTATION DISTANTE (60 jours) ###
ssh -i $KEY_CONNECTION -p $REMOTE_PORT "$REMOTE_USER@$REMOTE_HOST" \
    "find $REMOTE_DIR -type f -mtime +60 -delete"

echo "[FIN] Sauvegarde complète réussie."
