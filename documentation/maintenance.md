# Guide de Maintenance et Monitoring

[<- Retour à la page d'accueil](../README.md)

## 📋 Liste de contrôle maintenance

### Vérifications quotidiennes

- [ ] **État des conteneurs** : `docker-compose ps`
- [ ] **Espace disque** disponible : `df -h`
- [ ] **Logs d'erreurs** : `docker-compose logs --tail=50 web`
- [ ] **Connexions base de données** actives
- [ ] **Certificats SSL** (validité restante)

### Vérifications hebdomadaires

- [ ] **Sauvegarde base de données** testée
- [ ] **Rotation des logs** (si configurée)
- [ ] **Mises à jour de sécurité** Docker
- [ ] **Performance** de l'application
- [ ] **Nettoyage** des fichiers temporaires

### Vérifications mensuelles

- [ ] **Sauvegarde complète** du système
- [ ] **Test de restauration** des sauvegardes
- [ ] **Mise à jour** des dépendances Python
- [ ] **Audit de sécurité** des accès
- [ ] **Optimisation** base de données

## 📊 Monitoring et Logs

Consulter les logs en temps réel

```bash
docker-compose logs -f web          # Logs application
docker-compose logs -f db           # Logs base de données  
docker-compose logs -f nginx        # Logs serveur web

# Logs spécifiques par service
docker-compose logs --tail=100 web  # 100 dernières lignes
docker-compose logs --since=1h web  # Logs de la dernière heure

# Monitoring des ressources
docker stats                        # Utilisation CPU/RAM
docker-compose top                  # Processus actifs
```

## 💾 Stratégie de Sauvegarde

### Sauvegarde automatique quotidienne

```bash
#!/bin/bash
# Script de sauvegarde à programmer dans crontab

BACKUP_DIR="/var/backups/intranet"
DATE=$(date +%Y%m%d_%H%M%S)

# Créer le répertoire de sauvegarde
mkdir -p $BACKUP_DIR

# Sauvegarde de la base de données
docker-compose exec -T db mariadb-dump -u root -p$(grep ROOT_PASSWORD .env | cut -d'=' -f2) $(grep DB_NAME .env | cut -d'=' -f2) > $BACKUP_DIR/db_$DATE.sql

# Sauvegarde des documents
tar -czf $BACKUP_DIR/documents_$DATE.tar.gz $(grep FILES_LOCAL_PATH .env | cut -d'=' -f2)

# Sauvegarde de la configuration
cp .env $BACKUP_DIR/env_$DATE.backup

# Nettoyage des anciennes sauvegardes (garder 30 jours)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### Restauration d'urgence

```bash
# Restaurer la base de données
docker-compose exec -T db mariadb -u root -p$(grep ROOT_PASSWORD .env | cut -d'=' -f2) $(grep DB_NAME .env | cut -d'=' -f2) < backup_file.sql

# Restaurer les documents  
tar -xzf documents_backup.tar.gz -C /

# Redémarrer l'application
docker-compose restart
```

## Pages de secours Nginx

Nginx sert deux pages statiques indépendantes de Flask :
[panne](../app/nginx/maintenance/outage.html) et [maintenance planifiée](../app/nginx/maintenance/planned.html). Le logo est le fichier existant `app/static/img/favicone.svg`, monté séparément dans le proxy. Les pages et leur CSS ne dépendent d'aucun CDN. Les liens de support ciblent `rverschuur@audit-io.fr` avec l'objet « Panne de l'Intranet de la Péraudière ».

Les erreurs amont `502`, `503` et `504` déclenchent la page de panne et une réponse HTTP `503` sans cache. Les autres erreurs, dont `404` et `500`, ne sont pas remplacées. Les délais réseau Nginx existants sont conservés : en cas de serveur inaccessible, la page peut attendre l'expiration du timeout de connexion.

Une requête reçoit du JSON si son en-tête `Accept` ou `Content-Type` annonce `application/json` ou un type `application/...+json`. Le chemin URL n'entre pas dans cette décision. Les clients API doivent donc annoncer le format JSON. Les réponses contiennent `error`, `message` et `contact`, avec HTTP `503` et `Cache-Control: no-store`.

### Maintenance manuelle

Depuis la racine du dépôt sur l'hôte du proxy :

```bash
# Activer
touch app/nginx/maintenance/maintenance.enabled

# Désactiver
rm -- app/nginx/maintenance/maintenance.enabled
```

Le fichier témoin est exclu de Git et lu à chaque nouvelle requête, sans redémarrage ni rechargement. La maintenance s'applique à HTTP et HTTPS. Seuls les chemins du logo et du CSS de secours restent accessibles pour que la page s'affiche ; les URLs internes des pages HTML/JSON ne sont pas directement consultables. Les requêtes déjà en cours ne sont pas annulées par le fichier témoin.

### Mise en place initiale

Les fichiers Compose principal et de développement montent la configuration de secours, les pages et le logo dans le service `nginx`. Il faut recréer ce service une première fois pour appliquer ces nouveaux montages, avec le fichier Compose adapté au déploiement. Aucun proxy réel n'a été redémarré lors de l'implémentation.

Conserver Nginx actif pendant les interventions : arrêter uniquement les services nécessaires, plutôt que toute la stack avec `docker compose down`, qui rendrait aussi la page de maintenance indisponible. Valider toute nouvelle configuration avec `nginx -t` avant son rechargement.

Les tests de secours s'exécutent séparément sur l'hôte avec Docker, OpenSSL et l'image `nginx:latest` déjà disponible :

```bash
.venv/bin/python -m unittest test.test_nginx_maintenance -v
```

Ils utilisent des conteneurs, certificats et réseau temporaires ; les ports sont liés uniquement à localhost. Ils ne contactent ni l'Intranet réel, ni la base, ni le routeur VPN. Seul le délai de connexion du proxy de test est raccourci.

## 🔄 Mise à jour de l'Application

### Migration du carnet de contacts

Avant le démarrage de cette version, appliquer la révision Alembic
`a7c9d2e4f601` (après `f1a2b3c4d5e6`) via le script existant `app/migrate.sh`,
en utilisant le fichier Compose du déploiement concerné. Sauvegarder les données
auparavant et suspendre les écritures pendant la migration : le DDL MariaDB
peut effectuer des commits implicites.

La migration crée `02_contacts_contrats`, copie chaque rattachement existant puis
retire la colonne `02_contacts.id_contrat`. Il faut exécuter la migration avant
de démarrer l'application ; la création automatique des tables ne convertit pas
le schéma historique.

Le downgrade est refusé si une fiche est sans contrat ou liée à plusieurs
contrats. Il ne choisit aucun contrat arbitrairement et ne supprime aucune fiche.
Préparer explicitement les données avant un retour arrière, ou restaurer une
sauvegarde compatible. L'implémentation ne lance aucune migration sur la base
réelle automatiquement.

### Lanceur depuis l'hôte

Lorsque le conteneur `web` est déjà actif, le [lanceur Alembic](../alembic/migrate.sh)
permet d'exécuter `alembic upgrade head` à l'intérieur de ce conteneur :

```bash
sh alembic/migrate.sh
sh alembic/migrate.sh docker-compose.dev.yaml
```

Le fichier par défaut est `docker-compose.yaml` à la racine du dépôt. Un fichier fourni en argument est résolu depuis le répertoire courant. Le lanceur ne démarre aucun conteneur et transmet les erreurs de Docker ou d'Alembic. Sauvegarder la base et suspendre les écritures avant de l'utiliser.

Si le nouveau code ne peut pas démarrer sur l'ancien schéma, conserver la procédure ci-dessous avec `docker compose run --rm --no-deps` avant de lancer web.

### Procédure de mise à jour

```bash
# 1. Sauvegarder avant mise à jour
./backup-script.sh

# 2. Arrêter l'application
docker-compose down

# 3. Sauvegarder la configuration actuelle
cp .env .env.backup

# 4. Mettre à jour le code source
git stash                    # Sauvegarder modifications locales
git pull origin main         # Récupérer dernière version
git stash pop               # Restaurer modifications si nécessaire

# 5. Vérifier les nouvelles variables d'environnement
diff .env.example .env      # Comparer configurations

# 6. Reconstruire les images
docker-compose build --no-cache

# 7. Démarrer la base, appliquer les migrations manuellement, puis lancer l'application
docker compose up -d db
docker compose run --rm --no-deps --entrypoint sh web app/migrate.sh
docker compose up -d web

# 8. Vérifier le bon fonctionnement
docker-compose ps
curl -I http://localhost    # Test de connectivité
```

## 🛡️ Sécurité et Bonnes Pratiques

### Configuration sécurisée

- [ ] **Mots de passe forts** : utilisez `generate-env.sh`
- [ ] **SECRET_KEY unique** : changez régulièrement
- [ ] **HTTPS activé** : certificats SSL valides
- [ ] **Firewall configuré** : ports 80, 443 uniquement
- [ ] **Mises à jour régulières** : système et conteneurs

### Permissions fichiers

```bash
# Sécuriser les fichiers de configuration
chmod 600 .env
chmod 600 /etc/nginx/certs/intraraudiere.crt
chmod 644 /etc/nginx/certs/intraraudiere.key

# Sécuriser les répertoires de données
chown -R 999:999 $(grep DB_LOCAL_PATH .env | cut -d'=' -f2)
chmod 755 $(grep FILES_LOCAL_PATH .env | cut -d'=' -f2)
```

### Audit de sécurité

```bash
# Vérifier les ports ouverts
netstat -tlnp | grep :80
netstat -tlnp | grep :443

# Vérifier les conteneurs actifs
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Analyser les logs de sécurité
grep "Failed login" docker-compose logs web
grep "403\|404\|500" docker-compose logs nginx
```

## 🚨 Procédures d'Urgence

### Erreur de récupération MariaDB (`Bad magic header in tc log`)

Après un arrêt brutal, MariaDB peut ne pas démarrer si son journal `tc.log` est
corrompu. Consultez la [procédure détaillée et le script de récupération
idempotent](./recovery-mariadb-tc-log.md). Ne supprimez pas les fichiers InnoDB
et ne choisissez pas `--tc-heuristic-recover=COMMIT` ou `ROLLBACK` sans avoir
vérifié l'usage des transactions XA.

### En cas de panne

1. **Diagnostic rapide**

   ```bash
   - [ ] docker-compose ps                    # État des conteneurs
   - [ ] docker-compose logs --tail=20 web    # Erreurs récentes
   - [ ] df -h                                # Espace disque
   - [ ] free -h                              # Mémoire disponible
   ```

2. **Redémarrage d'urgence**

   ```bash
   - [ ] docker-compose down
   - [ ] docker-compose up -d
   ```

3. **Restauration complète**

   ```bash
   - [ ] docker-compose down -v              # Arrêt + suppression volumes
   - [ ] docker system prune -a              # Nettoyage complet
   - [ ] Restaurer depuis sauvegarde
   - [ ] docker-compose up -d
   ```

### Contacts d'urgence

- [ ] **Administrateur système** : [Rémi Verschuur, remiv1@gmail.com]
- [ ] **Développeur** : [Rémi Verschuur, remiv1@gmail.com]
- [ ] **Support infrastructure** : [Rémi Verschuur, remiv1@gmail.com]

[<- Retour à la page d'accueil](../README.md)
