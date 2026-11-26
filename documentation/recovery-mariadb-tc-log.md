# Récupération MariaDB après corruption de `tc.log`

[<- Retour à la page de maintenance](./maintenance.md)

## Symptômes

Après un arrêt brutal (par exemple une microcoupure), MariaDB peut s'arrêter au
démarrage avec des messages similaires à :

```text
Recovering after a crash using tc.log
Bad magic header in tc log
Crash recovery failed
Can't init tc log
Aborting
```

`tc.log` est le journal du coordinateur de transactions. Il ne s'agit pas du
journal InnoDB (`ib_logfile*` ou `ibdata*`) : ne supprimez ni ne modifiez ces
fichiers. Dans le cas décrit ici, InnoDB avait terminé son initialisation ; le
blocage venait de `tc.log`. Les avertissements `io_uring` et `memory.pressure`
observés dans le conteneur n'empêchaient pas MariaDB de démarrer.

## Incident du 16 octobre 2026

Le service `db` du fichier `docker-compose.yaml` utilisait le datadir hôte
`/var/lib/mysql`, monté dans le conteneur sur `/var/lib/mysql`. Après l'arrêt
du projet Compose sans option `-v`, les données étaient toujours présentes.

La récupération a été effectuée ainsi :

1. Vérification que les services MariaDB de l'hôte et les conteneurs étaient
   arrêtés.
2. Création et vérification de
   `/var/backups/mariadb/intranet-datadir-20261016.tar.gz`.
3. Conservation du journal corrompu sous
   `/var/lib/mysql/tc.log.corrupt-20261016` (aucun fichier `ib*` n'a été touché).
4. Un premier démarrage avec `--tc-heuristic-recover=ROLLBACK` s'est arrêté
   avec `Please restart without --tc-heuristic-recover` puis `Can't init tc
   log`. Cette tentative n'a pas démarré le service.
5. Le démarrage normal, sans option heuristique, a atteint `ready for
   connections`. Le service Compose a ensuite été relancé normalement.

L'option heuristique ne doit pas être choisie automatiquement : elle force un
COMMIT ou un ROLLBACK des transactions préparées et peut désynchroniser une
transaction distribuée avec un autre système. Les logs de l'incident montraient
une récupération via `tc.log`, et l'application n'utilisait pas XA.

## Script de récupération

Le script [`recover-mariadb-tc-log.sh`](../scripts/recover-mariadb-tc-log.sh)
automatise le chemin de récupération normal testé pour cet incident. Il :

- résout le chemin du datadir depuis la configuration Compose ;
- refuse d'agir si MariaDB ou un conteneur utilise encore ce datadir ;
- demande une confirmation explicite que les transactions XA ne sont pas
  utilisées ;
- archive et vérifie le datadir complet avant toute modification ;
- déplace `tc.log` vers un nom de quarantaine sans l'effacer ;
- démarre uniquement le service `db`, sans option heuristique, puis attend
  qu'il réponde à `mariadb-admin ping`.

Depuis le répertoire du projet, et seulement après avoir constaté l'erreur
`Bad magic header in tc log` :

```bash
./scripts/recover-mariadb-tc-log.sh --confirm-no-xa
```

Le script demande une confirmation avant d'effectuer les opérations. Pour une
exécution sans invite interactive, ajouter `--yes` après vérification :

```bash
./scripts/recover-mariadb-tc-log.sh --confirm-no-xa --yes
```

L'exécution est idempotente pour le même incident : si le service est déjà
disponible, elle ne change rien ; si `tc.log` est toujours absent et que le
script a déjà créé une quarantaine et son archive vérifiée, elle reprend sans
déplacer à nouveau le journal ni recréer la sauvegarde. Si un nouveau `tc.log`
est apparu après une tentative infructueuse, le script s'arrête pour éviter de
le déplacer sans diagnostic. Si un journal existe après une récupération
précédente, un nouvel incident exige `--new-incident` :

```bash
./scripts/recover-mariadb-tc-log.sh --confirm-no-xa --new-incident
```

N'utilisez `--new-incident` qu'après avoir confirmé dans les logs qu'il s'agit
d'un nouveau `Bad magic header in tc log`.

Par défaut, l'archive est créée dans `/var/backups/mariadb`. Un autre
emplacement peut être fourni via `MARIADB_TC_RECOVERY_BACKUP_DIR`, à condition
qu'il soit en dehors du datadir et qu'il ait assez d'espace.

## Cas où il faut s'arrêter

- Si XA, un gestionnaire de transactions distribuées ou des transactions
  préparées sont utilisés ou possibles, ne lancez pas ce script : faites
  déterminer par l'administrateur de la transaction s'il faut COMMIT ou
  ROLLBACK.
- Si le script signale un autre processus utilisant le datadir, ne contournez
  pas le contrôle ; arrêtez proprement ce processus d'abord.
- Si MariaDB ne répond pas après la récupération, conservez l'archive et les
  fichiers `tc.log.corrupt-*`, ne supprimez pas les fichiers InnoDB et
  examinez les logs avant toute nouvelle tentative.
- Ne lancez pas `docker compose down -v` ni `docker system prune` pendant la
  récupération.

Après le démarrage, vérifiez `docker compose ps`, les logs de `db` et le bon
fonctionnement de l'application. Gardez l'archive et le journal mis en
quarantaine jusqu'à validation des données.
