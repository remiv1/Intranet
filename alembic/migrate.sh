#!/bin/sh

set -eu

usage() {
    printf 'Usage: sh %s [fichier-compose]\n' "$0"
    printf '%s\n' 'Lance alembic upgrade head dans le conteneur web actif.'
    printf '%s\n' 'Par défaut : docker-compose.yaml à la racine du dépôt.'
}

if [ "$#" -gt 1 ]; then
    usage >&2
    exit 2
fi

case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
esac

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
COMPOSE_FILE=${1:-"$PROJECT_DIR/docker-compose.yaml"}
case "$COMPOSE_FILE" in
    /*) ;;
    *) COMPOSE_FILE="$PWD/$COMPOSE_FILE" ;;
esac

if [ ! -f "$COMPOSE_FILE" ]; then
    printf 'Fichier Compose introuvable : %s\n' "$COMPOSE_FILE" >&2
    exit 2
fi
if ! command -v docker >/dev/null 2>&1; then
    printf '%s\n' 'Docker est requis pour lancer la migration depuis cet hôte.' >&2
    exit 127
fi
if ! docker compose version >/dev/null 2>&1; then
    printf '%s\n' 'Le plugin Docker Compose est requis.' >&2
    exit 127
fi

printf 'Migration via %s, service web actif.\n' "$COMPOSE_FILE"
exec docker compose --project-directory "$PROJECT_DIR" -f "$COMPOSE_FILE" \
    exec -T web sh app/migrate.sh