# Tests pour l'Intranet API'Raudière

Les tests utilisent Python 3.14, pytest et une vraie MariaDB 12.0.2 dans des
conteneurs. Aucun serveur MySQL/MariaDB ni paquet Python n'est à installer sur
l'hôte. Docker Compose ou Podman Compose doit être disponible.

## Lancement

Depuis la racine du dépôt :

```bash
docker compose -f docker-compose.test.yaml up --build --force-recreate --abort-on-container-exit --exit-code-from test
```

Le code de sortie est celui de pytest. Les services s'arrêtent à la fin des
tests. `--force-recreate` garantit un nouveau démarrage des conteneurs, notamment
pour éviter la réutilisation d'un ancien état de santé avec Podman Compose.

La base est stockée en mémoire via `tmpfs` : ses données sont perdues à l'arrêt
du conteneur. Ce Compose autonome n'utilise aucun volume, identifiant, réseau
ou fichier d'environnement de développement ou de production. Aucun port n'est
publié. Ne pas le combiner avec les autres fichiers Compose du dépôt.

Pour retirer les conteneurs arrêtés et le réseau de test :

```bash
docker compose -f docker-compose.test.yaml down
```

Pour vérifier uniquement la collecte, sans démarrer MariaDB :

```bash
docker compose -f docker-compose.test.yaml build test
docker compose -f docker-compose.test.yaml run --rm --no-deps test python -m pytest -c test/pytest.ini test --collect-only -q
```

## Images

Le Dockerfile commun `app/Dockerfile.app` contient trois étapes :

- `runtime` : dépendances et code partagés.
- `test` : pytest, fixtures et tests, sans copie du fichier `.env` réel.
- `production` : cible par défaut conservant le lancement applicatif existant.

Les dépendances applicatives restent dans `requirements.txt`, et les dépendances
supplémentaires de test dans `test/requirements.txt`.

## Isolation

- Les fixtures refusent toute configuration ne ciblant pas `db-test/intranet_test`
    avec l'utilisateur de test. Le chargement dotenv est désactivé avant les imports.
- Le schéma historique est créé à partir des modèles SQLAlchemy, sans données
    réelles. La table `98_sessions` est exclue de cette création, puis créée par
    le véritable `upgrade()` de la révision Alembic `d4f3a20e9b71`.
- Chaque test dispose d'une transaction externe et de points de sauvegarde.
    Les appels applicatifs à `commit()` restent isolés ; la transaction externe est
    annulée à la fin du test.
- Les sessions des requêtes Flask sont de vraies sessions SQLAlchemy rattachées
    à cette même transaction. Les méthodes de la base ne sont pas mockées.
- Les identifiants auto-incrémentés ne sont pas remis à zéro par un rollback ;
    les tests utilisent les identifiants effectivement attribués.
- Les fichiers sont écrits dans des répertoires temporaires. Emails, SSH et
    impressions réels sont bloqués, et le réseau du Compose est interne.

Cette isolation couvre les écritures de données, pas les opérations DDL, qui
peuvent provoquer des commits implicites dans MariaDB. La migration de sessions
est exécutée et son schéma vérifié ; les autres migrations historiques et le
downgrade ne sont pas validés par cette suite.

## Fixtures

- `database_engine` : moteur connecté à MariaDB temporaire.
- `db_session` : session réelle isolée pour chaque test.
- `app`, `client` : application réelle et client Flask sans serveur HTTP externe.
- `sample_*_data` : dictionnaires de données valides.
- `create_test_*`, `create_admin_user`, `create_multiple_*` : objets persistants.
- `create_contract_with_documents_and_events` : contrat avec ses relations.
- `authenticated_session_data` : session de navigateur rattachée au compte de test.

Les fixtures sont chargées automatiquement ; les tests ne doivent pas les
importer directement. Pour respecter les cookies `Secure`, utiliser
`base_url="https://localhost"` avec le client Flask.

## Périmètre

`test_application.py` vérifie la persistance des modèles, les filtres SQL, les
relations et les routes d'accueil et de connexion existantes. `test_database.py`
remplace les anciens tests de MockSession par des vérifications des transactions,
des identifiants et des contraintes de clé étrangère MariaDB.

`test_rapport_contrats.py` couvre le jeton dedie, les statuts HTTP, l'exemption
CSRF ciblee, les pannes SMTP et le refus de demarrage avec alerte simulee.
`test_report_scheduler.py` verifie le crontab avec le vrai Supercronic, la requete
JSON sans secret dans les arguments et l'arret des processus supervises.

`test_login_redirects.py` couvre les destinations locales, leurs parametres et
fragments, les URL externes et les contournements encodes. Les connexions reelles
utilisent MariaDB avec CSRF actif et un Referer HTTPS. Une destination invalide
renvoie a l'accueil apres connexion reussie ; apres un echec, seule une
destination locale valide est conservee pour la prochaine tentative.

`test_password_migration.py` verifie la transition SHA-256 vers Argon2id a la
connexion, les comptes verrouilles ou expires, le renouvellement des parametres
et les formulaires de creation/modification. La panne de commit est declenchee
par un evenement SQLAlchemy sur les vraies sessions MariaDB : le test controle
le rollback, l'acces autorise, la conservation de l'ancien hash et les logs
`MIGR-AUTH` sans secrets. Les identifiants des fixtures restent volontairement
en SHA-256 afin de couvrir durablement la compatibilite historique.

Les emails de test ne sont jamais envoyes. Les autres tests de securite et les
corrections metier seront ajoutes chantier par chantier apres validation.

`test_auth_sessions.py` couvre le schema migre, les jetons haches, l'expiration
par inactivite, la rotation, la deconnexion et la revocation de tous les
navigateurs apres changement sensible. Des evenements SQLAlchemy declenchent
les pannes de lecture/ecriture sur les vraies sessions MariaDB pour verifier
les refus d'acces et les rollbacks. Les fixtures authentifiees possedent une
veritable ligne de session ; de simples champs d'identite ne suffisent plus.
