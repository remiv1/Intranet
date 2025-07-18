#!/bin/bash

# Script de démarrage rapide de l'Intranet
# Usage: ./quick-start.sh [dev|prod]

set -e

MODE=${1:-prod}
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║               🎓 INTRANET - DÉMARRAGE RAPIDE                ║"
    echo "║                                                              ║"
    echo "║           Application de Gestion d'Établissement            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_prerequisites() {
    echo -e "${YELLOW}🔍 Vérification des prérequis...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker n'est pas installé${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose n'est pas installé${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker: $(docker --version)${NC}"
    echo -e "${GREEN}✅ Docker Compose: $(docker-compose --version)${NC}"
}

setup_environment() {
    echo -e "${YELLOW}⚙️ Configuration de l'environnement ($MODE)...${NC}"
    
    if [ "$MODE" = "dev" ]; then
        ENV_FILE=".env.dev"
        COMPOSE_FILE="docker-compose.dev.yml"
    else
        ENV_FILE=".env"
        COMPOSE_FILE="docker-compose.yaml"
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}📝 Génération du fichier de configuration...${NC}"
        if [ -f "./generate-env.sh" ]; then
            ./generate-env.sh
            if [ "$MODE" = "dev" ]; then
                cp .env .env.dev
                # Adaptations pour le développement
                sed -i 's|FILES_LOCAL_PATH=.*|FILES_LOCAL_PATH=./documents|g' .env.dev
                sed -i 's|PRINT_LOCAL_PATH=.*|PRINT_LOCAL_PATH=./print|g' .env.dev
                sed -i 's|DB_LOCAL_PATH=.*|DB_LOCAL_PATH=./data|g' .env.dev
            fi
        else
            echo -e "${RED}❌ Script generate-env.sh introuvable${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ Fichier $ENV_FILE existant${NC}"
    fi
}

create_directories() {
    echo -e "${YELLOW}📁 Création des répertoires...${NC}"
    
    # Lecture des variables d'environnement
    source $ENV_FILE
    
    mkdir -p "$FILES_LOCAL_PATH" 2>/dev/null || true
    mkdir -p "$PRINT_LOCAL_PATH" 2>/dev/null || true
    mkdir -p "$(dirname $DB_LOCAL_PATH)" 2>/dev/null || true
    
    echo -e "${GREEN}✅ Répertoires créés${NC}"
}

start_services() {
    echo -e "${YELLOW}🚀 Démarrage des services...${NC}"
    
    # Arrêter les services existants
    docker-compose -f $COMPOSE_FILE down 2>/dev/null || true
    
    # Construire et démarrer
    docker-compose -f $COMPOSE_FILE build
    docker-compose -f $COMPOSE_FILE up -d
    
    echo -e "${GREEN}✅ Services démarrés${NC}"
}

wait_for_services() {
    echo -e "${YELLOW}⏳ Attente de la disponibilité des services...${NC}"
    
    sleep 10
    
    # Vérifier la base de données
    echo -n "Base de données: "
    for i in {1..30}; do
        if docker-compose -f $COMPOSE_FILE exec -T db mysql -u root -p$(grep ROOT_PASSWORD $ENV_FILE | cut -d'=' -f2) -e "SELECT 1" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Prête${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Vérifier l'application web
    echo -n "Application web: "
    for i in {1..30}; do
        if [ "$MODE" = "dev" ]; then
            PORT=5000
        else
            PORT=80
        fi
        
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT | grep -q "200\|302"; then
            echo -e "${GREEN}✅ Prête${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
}

show_access_info() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🎉 DÉMARRAGE TERMINÉ                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    if [ "$MODE" = "dev" ]; then
        echo -e "${GREEN}🌐 Application web:      http://localhost:5000${NC}"
        echo -e "${GREEN}🗄️ PhpMyAdmin:           http://localhost:8080${NC}"
        echo -e "${GREEN}💾 Base de données:      localhost:3306${NC}"
    else
        echo -e "${GREEN}🌐 Application web:      http://localhost${NC}"
        echo -e "${GREEN}🔒 HTTPS:                https://localhost${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}📋 Commandes utiles:${NC}"
    echo -e "  ${BLUE}docker-compose -f $COMPOSE_FILE logs -f${NC}    # Voir les logs"
    echo -e "  ${BLUE}docker-compose -f $COMPOSE_FILE ps${NC}         # État des services"
    echo -e "  ${BLUE}docker-compose -f $COMPOSE_FILE down${NC}       # Arrêter"
    echo ""
    echo -e "${YELLOW}🔐 Identifiants par défaut:${NC}"
    echo -e "  ${BLUE}Admin: admin / admin${NC} (à changer lors de la première connexion)"
}

show_help() {
    echo "Usage: $0 [MODE]"
    echo ""
    echo "MODE:"
    echo "  prod    Démarrage en mode production (défaut)"
    echo "  dev     Démarrage en mode développement"
    echo ""
    echo "Exemples:"
    echo "  $0           # Mode production"
    echo "  $0 prod      # Mode production"
    echo "  $0 dev       # Mode développement"
}

# Fonction principale
main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    print_header
    check_prerequisites
    setup_environment
    create_directories
    start_services
    wait_for_services
    show_access_info
}

# Exécution
main "$@"
