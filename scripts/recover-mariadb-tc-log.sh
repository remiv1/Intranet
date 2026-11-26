#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yaml"
SERVICE="db"
DATADIR_TARGET="/var/lib/mysql"
BACKUP_DIR="${MARIADB_TC_RECOVERY_BACKUP_DIR:-/var/backups/mariadb}"
CONFIRM_NO_XA=false
NEW_INCIDENT=false
ASSUME_YES=false
TMP_ARCHIVE=""

usage() {
    cat <<'EOF'
Usage: scripts/recover-mariadb-tc-log.sh --confirm-no-xa [--new-incident] [--yes]

Sauvegarde le datadir, met tc.log en quarantaine, démarre db normalement et
attend une réponse positive de mariadb-admin ping.

Options:
  --confirm-no-xa  Confirmer que cette base n'est pas utilisée pour des
                   transactions XA/distribuées.
  --new-incident   Autoriser un nouveau tc.log après une quarantaine précédente.
                   À utiliser seulement après confirmation d'une nouvelle
                   erreur "Bad magic header in tc log".
  --yes            Ne pas demander de confirmation interactive.
  --help           Afficher cette aide.

MARIADB_TC_RECOVERY_BACKUP_DIR peut remplacer le dossier de sauvegarde par
défaut (/var/backups/mariadb).
EOF
}

die() {
    printf '[ERROR] %s\n' "$*" >&2
    exit 1
}

log() {
    printf '[INFO] %s\n' "$*"
}

root_cmd() {
    if (( EUID == 0 )); then
        "$@"
    else
        sudo "$@"
    fi
}

cleanup() {
    if [[ -n "$TMP_ARCHIVE" ]]; then
        root_cmd rm -f -- "$TMP_ARCHIVE"
    fi
}
trap cleanup EXIT

while (($#)); do
    case "$1" in
        --confirm-no-xa) CONFIRM_NO_XA=true ;;
        --new-incident) NEW_INCIDENT=true ;;
        --yes) ASSUME_YES=true ;;
        --help|-h) usage; exit 0 ;;
        *) die "Option inconnue : $1 (utiliser --help)." ;;
    esac
    shift
done

[[ "$CONFIRM_NO_XA" == true ]] || die "Confirmer l'absence de transactions XA avec --confirm-no-xa."
[[ -f "$COMPOSE_FILE" ]] || die "Fichier Compose introuvable : $COMPOSE_FILE"
command -v docker >/dev/null 2>&1 || die "Docker est requis."
command -v python3 >/dev/null 2>&1 || die "Python 3 est requis pour lire la configuration Compose."

if (( EUID != 0 )); then
    command -v sudo >/dev/null 2>&1 || die "sudo est requis pour sauvegarder et renommer les fichiers du datadir."
    sudo -v
fi

cd "$PROJECT_DIR"

if ! docker compose -f "$COMPOSE_FILE" version >/dev/null 2>&1; then
    die "Docker Compose v2 n'est pas disponible."
fi
docker info >/dev/null 2>&1 || die "Le daemon Docker n'est pas accessible."

compose_config="$(docker compose -f "$COMPOSE_FILE" config --format json)" ||
    die "Impossible de résoudre la configuration Compose."

datadir="$(
    python3 -c '
import json
import os
import sys

config = json.load(sys.stdin)
service = config.get("services", {}).get("db")
if service is None:
    raise SystemExit("Le service Compose db est introuvable.")

for mount in service.get("volumes", []):
    if os.path.normpath(mount.get("target", "")) != "/var/lib/mysql":
        continue
    source = mount.get("source")
    if mount.get("type") == "bind" and source:
        print(os.path.realpath(source))
        raise SystemExit(0)

    volume = config.get("volumes", {}).get(source, {})
    options = volume.get("driver_opts", {})
    if options.get("device") and "bind" in options.get("o", "").split(","):
        print(os.path.realpath(options["device"]))
        raise SystemExit(0)

raise SystemExit("Aucun montage hôte vers /var/lib/mysql n’a été trouvé.")
' <<<"$compose_config"
)" || die "Impossible de déterminer le datadir hôte du service db."

[[ -d "$datadir" ]] || die "Datadir introuvable : $datadir"
datadir="$(realpath -- "$datadir")"

if [[ "$BACKUP_DIR" != /* ]]; then
    BACKUP_DIR="$PROJECT_DIR/$BACKUP_DIR"
fi
backup_dir_resolved="$(realpath -m -- "$BACKUP_DIR")"
case "$backup_dir_resolved/" in
    "$datadir/"*) die "Le dossier de sauvegarde doit être en dehors du datadir ($datadir)." ;;
esac

if docker compose -f "$COMPOSE_FILE" ps --status running -q "$SERVICE" | grep -q .; then
    if docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE" mariadb-admin ping --silent >/dev/null 2>&1; then
        log "MariaDB est déjà disponible ; aucune modification effectuée."
        exit 0
    fi
    die "Le service db tourne déjà mais ne répond pas. Consultez ses logs ; aucun fichier n'a été modifié."
fi

if pgrep -x mariadbd >/dev/null 2>&1; then
    die "Un processus mariadbd hôte est actif. Arrêtez-le avant d'intervenir sur $datadir."
fi

while IFS= read -r container_id; do
    [[ -n "$container_id" ]] || continue
    mounts="$(docker inspect --format '{{range .Mounts}}{{println .Source}}{{end}}' "$container_id")"
    if grep -Fqx -- "$datadir" <<<"$mounts"; then
        die "Le conteneur $container_id utilise encore $datadir. Arrêtez-le avant de continuer."
    fi
done < <(docker ps -q)

root_cmd mkdir -p -- "$BACKUP_DIR"
BACKUP_DIR="$(realpath -- "$BACKUP_DIR")"
case "$BACKUP_DIR/" in
    "$datadir/"*) die "Le dossier de sauvegarde doit être en dehors du datadir ($datadir)." ;;
esac

tc_log="$datadir/tc.log"
shopt -s nullglob
quarantined_logs=("$datadir"/tc.log.corrupt-script-*)
shopt -u nullglob

if [[ -e "$tc_log" ]]; then
    [[ -f "$tc_log" && ! -L "$tc_log" ]] || die "$tc_log n'est pas un fichier régulier."
    if ((${#quarantined_logs[@]})) && [[ "$NEW_INCIDENT" != true ]]; then
        die "Un ancien tc.log a déjà été mis en quarantaine par ce script. Pour un nouvel incident confirmé, utilisez --new-incident."
    fi

    if [[ "$ASSUME_YES" != true ]]; then
        [[ -t 0 ]] || die "Exécutez le script dans un terminal ou ajoutez --yes après vérification."
        printf 'Le script va sauvegarder %s, déplacer tc.log et démarrer db normalement. Continuer ? [y/N] ' "$datadir"
        read -r answer
        [[ "$answer" == "y" || "$answer" == "Y" ]] || die "Opération annulée ; aucun fichier modifié."
    fi

    tc_hash="$(root_cmd sha256sum "$tc_log" | awk '{print $1}')"
    tc_mtime="$(root_cmd stat -c '%Y' "$tc_log")"
    recovery_id="${tc_mtime}-${tc_hash:0:12}"
    archive="$BACKUP_DIR/intranet-datadir-before-tc-recovery-${recovery_id}.tar.gz"
    quarantine="$datadir/tc.log.corrupt-script-${recovery_id}"

    if [[ -e "$quarantine" ]]; then
        die "La destination de quarantaine existe déjà : $quarantine"
    fi

    if [[ -e "$archive" ]]; then
        root_cmd tar -tzf "$archive" >/dev/null ||
            die "L'archive existante n'est pas valide : $archive"
        log "Archive de cette récupération déjà vérifiée : $archive"
    else
        TMP_ARCHIVE="$(root_cmd mktemp "$BACKUP_DIR/.mariadb-tc-recovery.XXXXXX")"
        log "Sauvegarde du datadir vers $archive..."
        root_cmd tar --numeric-owner --sparse -czpf "$TMP_ARCHIVE" -C "$datadir" .
        root_cmd tar -tzf "$TMP_ARCHIVE" >/dev/null ||
            die "La vérification de l'archive a échoué ; tc.log n'a pas été déplacé."
        root_cmd mv -- "$TMP_ARCHIVE" "$archive"
        TMP_ARCHIVE=""
    fi

    root_cmd mv -- "$tc_log" "$quarantine"
    log "Journal d'origine conservé sous $quarantine"
    log "Sauvegarde vérifiée : $archive"
else
    ((${#quarantined_logs[@]})) ||
        die "$tc_log est absent et aucun journal mis en quarantaine par ce script n'a été trouvé."

    quarantine="${quarantined_logs[-1]}"
    recovery_id="${quarantine##*tc.log.corrupt-script-}"
    archive="$BACKUP_DIR/intranet-datadir-before-tc-recovery-${recovery_id}.tar.gz"
    [[ -f "$archive" ]] || die "Sauvegarde de reprise introuvable : $archive"
    root_cmd tar -tzf "$archive" >/dev/null ||
        die "La sauvegarde de reprise n'est pas valide : $archive"
    log "Reprise d'une récupération déjà préparée ; tc.log n'est pas déplacé à nouveau."
fi

if ! docker compose -f "$COMPOSE_FILE" up -d "$SERVICE"; then
    docker compose -f "$COMPOSE_FILE" logs --tail=80 "$SERVICE" >&2 || true
    die "Le démarrage de db a échoué. Les sauvegardes et journaux conservés n'ont pas été supprimés."
fi

log "Attente de MariaDB (maximum 120 secondes)..."
ready=false
for _ in {1..60}; do
    if docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE" mariadb-admin ping --silent >/dev/null 2>&1; then
        ready=true
        break
    fi
    sleep 2
done

if [[ "$ready" != true ]]; then
    docker compose -f "$COMPOSE_FILE" logs --tail=80 "$SERVICE" >&2 || true
    die "MariaDB n'a pas répondu après 120 secondes. Ne supprimez pas les fichiers de récupération."
fi

log "MariaDB est disponible."
log "Archive conservée : $archive"
if [[ -n "${quarantine:-}" ]]; then
    log "Journal original conservé : $quarantine"
fi
