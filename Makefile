# Makefile pour l'Intranet
# Usage: make [target]

.PHONY: help install dev prod stop clean logs backup test

# Couleurs pour l'affichage
BLUE=\033[0;34m
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

# Variables
COMPOSE_PROD = docker-compose.yaml
COMPOSE_DEV = docker-compose.dev.yml

help: ## Afficher cette aide
	@echo -e "$(BLUE)🎓 Intranet - Commandes disponibles$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Installation complète (génère .env et démarre)
	@echo -e "$(YELLOW)🔧 Installation de l'Intranet...$(NC)"
	@chmod +x generate-env.sh quick-start.sh
	@./quick-start.sh prod

dev: ## Démarrage en mode développement
	@echo -e "$(YELLOW)🚀 Démarrage en mode développement...$(NC)"
	@chmod +x quick-start.sh
	@./quick-start.sh dev

prod: ## Démarrage en mode production
	@echo -e "$(YELLOW)🚀 Démarrage en mode production...$(NC)"
	@docker-compose -f $(COMPOSE_PROD) up -d

stop: ## Arrêter tous les services
	@echo -e "$(YELLOW)⏹️ Arrêt des services...$(NC)"
	@docker-compose -f $(COMPOSE_PROD) down 2>/dev/null || true
	@docker-compose -f $(COMPOSE_DEV) down 2>/dev/null || true

restart: ## Redémarrer les services
	@echo -e "$(YELLOW)🔄 Redémarrage des services...$(NC)"
	@make stop
	@make prod

build: ## Reconstruire les images Docker
	@echo -e "$(YELLOW)🔨 Construction des images...$(NC)"
	@docker-compose -f $(COMPOSE_PROD) build

clean: ## Nettoyage complet (images, volumes, etc.)
	@echo -e "$(YELLOW)🧹 Nettoyage complet...$(NC)"
	@make stop
	@docker system prune -a -f
	@docker volume prune -f

logs: ## Afficher les logs
	@echo -e "$(YELLOW)📜 Logs de l'application...$(NC)"
	@docker-compose -f $(COMPOSE_PROD) logs -f

logs-dev: ## Afficher les logs en mode développement
	@echo -e "$(YELLOW)📜 Logs de développement...$(NC)"
	@docker-compose -f $(COMPOSE_DEV) logs -f

status: ## Afficher le statut des services
	@echo -e "$(YELLOW)📊 Statut des services...$(NC)"
	@docker-compose -f $(COMPOSE_PROD) ps 2>/dev/null || echo "Services production arrêtés"
	@docker-compose -f $(COMPOSE_DEV) ps 2>/dev/null || echo "Services développement arrêtés"

backup: ## Créer une sauvegarde de la base de données
	@echo -e "$(YELLOW)💾 Sauvegarde de la base de données...$(NC)"
	@mkdir -p backups
	@docker-compose -f $(COMPOSE_PROD) exec -T db mysqldump -u root -p$$(grep ROOT_PASSWORD .env | cut -d'=' -f2) $$(grep DB_NAME .env | cut -d'=' -f2) > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo -e "$(GREEN)✅ Sauvegarde créée dans backups/$(NC)"

restore: ## Restaurer une sauvegarde (Usage: make restore FILE=backup.sql)
	@echo -e "$(YELLOW)🔄 Restauration de la base de données...$(NC)"
	@if [ -z "$(FILE)" ]; then echo -e "$(RED)❌ Usage: make restore FILE=backup.sql$(NC)"; exit 1; fi
	@docker-compose -f $(COMPOSE_PROD) exec -T db mysql -u root -p$$(grep ROOT_PASSWORD .env | cut -d'=' -f2) $$(grep DB_NAME .env | cut -d'=' -f2) < $(FILE)
	@echo -e "$(GREEN)✅ Base de données restaurée$(NC)"

test: ## Exécuter les tests
	@echo -e "$(YELLOW)🧪 Exécution des tests...$(NC)"
	@docker-compose -f $(COMPOSE_DEV) exec web python -m pytest tests/ -v

shell: ## Accéder au shell du conteneur web
	@echo -e "$(YELLOW)🐚 Accès au shell du conteneur...$(NC)"
	@docker-compose -f $(COMPOSE_PROD) exec web bash

shell-dev: ## Accéder au shell du conteneur web en développement
	@echo -e "$(YELLOW)🐚 Accès au shell du conteneur de développement...$(NC)"
	@docker-compose -f $(COMPOSE_DEV) exec web bash

db-shell: ## Accéder au shell MySQL
	@echo -e "$(YELLOW)🗄️ Accès à la base de données...$(NC)"
	@docker-compose -f $(COMPOSE_PROD) exec db mysql -u root -p$$(grep ROOT_PASSWORD .env | cut -d'=' -f2) $$(grep DB_NAME .env | cut -d'=' -f2)

update: ## Mettre à jour l'application
	@echo -e "$(YELLOW)🔄 Mise à jour de l'application...$(NC)"
	@git pull
	@make build
	@make restart
	@echo -e "$(GREEN)✅ Application mise à jour$(NC)"

env: ## Générer un nouveau fichier .env
	@echo -e "$(YELLOW)⚙️ Génération du fichier .env...$(NC)"
	@chmod +x generate-env.sh
	@./generate-env.sh

watch-logs: ## Surveiller les logs en temps réel
	@echo -e "$(YELLOW)👀 Surveillance des logs...$(NC)"
	@docker-compose -f $(COMPOSE_PROD) logs -f --tail=100

health: ## Vérifier la santé de l'application
	@echo -e "$(YELLOW)🏥 Vérification de la santé...$(NC)"
	@echo -n "Application web: "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302" && echo -e "$(GREEN)✅ OK$(NC)" || echo -e "$(RED)❌ KO$(NC)"
	@echo -n "Base de données: "
	@docker-compose -f $(COMPOSE_PROD) exec -T db mysql -u root -p$$(grep ROOT_PASSWORD .env | cut -d'=' -f2) -e "SELECT 1" > /dev/null 2>&1 && echo -e "$(GREEN)✅ OK$(NC)" || echo -e "$(RED)❌ KO$(NC)"

quick-backup: ## Sauvegarde rapide (BDD + fichiers)
	@echo -e "$(YELLOW)⚡ Sauvegarde rapide...$(NC)"
	@mkdir -p backups
	@make backup
	@tar -czf backups/files_$$(date +%Y%m%d_%H%M%S).tar.gz $$(grep FILES_LOCAL_PATH .env | cut -d'=' -f2) 2>/dev/null || true
	@echo -e "$(GREEN)✅ Sauvegarde rapide terminée$(NC)"

monitor: ## Surveiller les ressources système
	@echo -e "$(YELLOW)📊 Surveillance des ressources...$(NC)"
	@docker stats --no-stream

# Cible par défaut
all: help
