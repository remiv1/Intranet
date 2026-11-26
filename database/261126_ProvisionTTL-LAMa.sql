-- Provisioning manuel de la base dediee a TTL-LAMa sur le serveur MariaDB existant.
-- Remplacer les deux occurrences de CHANGE_ME_TTL_LAMA_DB_PASSWORD par la valeur
-- de TTL_LAMA_DB_PASSWORD dans ttlama/config/.env avant execution.
-- Si DB_USER differe de intranet_user, adapter aussi le compte dans le GRANT ci-dessous.
-- Depuis la racine du depot, executer avec l'environnement ROOT_PASSWORD du conteneur:
-- docker compose -f docker-compose.dev.yaml exec -T db sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mariadb -uroot' < database/provision_ttl_lama.sql

-- HELP
-- ```bash
-- export DB_NAME="your_database_name"
-- export DB_USER="your_database_user"
-- export DB_PASSWORD="your_database_password"
-- export MARIADB_ROOT_PASSWORD="your_mariadb_root_password"
-- sed \
--   -e "s|__DB_NAME__|${DB_NAME}|g" \
--   -e "s|__DB_USER__|${DB_USER}|g" \
--   -e "s|__DB_PASSWORD__|${DB_PASSWORD}|g" \
--   database/provision_ttl_lama.sql \
-- | docker exec -T db mariadb -u root -p"${MARIADB_ROOT_PASSWORD}"
-- ```


-- 1. Création de la base de données TTL-LAMa
CREATE DATABASE IF NOT EXISTS `__DB_NAME__`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 2. Création de l'utilisateur TTL-LAMa et attribution du mot de passe
CREATE USER IF NOT EXISTS '__DB_USER__'@'%'
  IDENTIFIED BY '__DB_PASSWORD__';

-- 3. Modification du mot de passe de l'utilisateur TTL-LAMa si necessaire
ALTER USER '__DB_USER__'@'%'
  IDENTIFIED BY '__DB_PASSWORD__';

-- 4. Attribution des privileges a l'utilisateur TTL-LAMa
GRANT CREATE, INDEX, SELECT, INSERT, UPDATE, DELETE
  ON `__DB_NAME__`.* TO '__DB_USER__'@'%';

FLUSH PRIVILEGES;
