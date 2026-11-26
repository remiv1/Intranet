# 🚀 Guide d'Installation Rapide - Intranet

[<- Retour à la page d'accueil](../README.md)

## Installation en 5 minutes

### ✅ Liste de contrôle pré-installation

Avant de commencer, assurez-vous d'avoir :

- [ ] **Docker** installé (version 20.10+)
- [ ] **Docker Compose** installé (version 2.0+)
- [ ] **Git** installé pour cloner le projet
- [ ] **Accès root/sudo** sur le serveur
- [ ] **Ports 80 et 443** disponibles sur votre serveur
- [ ] **Au moins 2GB** d'espace disque libre
- [ ] **Au moins 1GB** de RAM disponible

#### Étape 1 : Préparation de l'environnement

Vérifier les prérequis

```bash
docker --version
docker compose version
git --version
```

#### Étape 2 : Clonage du projet

Cloner le dépôt

```bash
git clone https://github.com/remiv1/Intranet.git
cd Intranet
```

#### Étape 3 : Configuration automatique

Générer automatiquement la configuration avec mots de passe sécurisés

```bash
./generate-env.sh
```

#### Étape 4 : Personnalisation de la configuration

Éditez le fichier `.env` généré et modifiez selon vos besoins :

```bash
nano .env
```

Le rapport automatise exige un `API_MAIL_TOKEN` non vide, distinct de
`SECRET_KEY`, dans l'environnement du conteneur. Generer une valeur aleatoire
avec `openssl rand -hex 32` et la renseigner dans `.env`, sans la commiter ni
la copier dans le crontab. Configurer aussi `EMAIL_USER`, `EMAIL_PASSWORD`,
`EMAIL_SMTP` et `EMAIL_PORT` pour les rapports et les alertes.

Sans jeton, le demarrage est refuse avec un code de sortie non nul, apres une
tentative d'alerte a `rverschuur@audit-io.fr`. Une panne SMTP n'autorise pas le
demarrage. Aucun statut HTTP ne peut etre renvoye tant que le serveur ne tourne
pas ; une requete avec un jeton absent ou incorrect recoit ensuite un `401` JSON.

Supercronic execute le rapport le premier jour de chaque mois a 03:00, dans le
fuseau du conteneur (`TZ` ou `/etc/localtime`), sans fuseau force dans le crontab.
Le script `app/rapport_cron.sh` envoie un POST JSON a
`http://localhost:5000/rapport-contrats` pour `direction@peraudiere.com`.
Seule cette route est exemptee de CSRF et le jeton reste obligatoire, meme avec
une session connectee. Le jeton est transmis a curl par son entree standard,
pas dans ses arguments. Les erreurs HTTP rendent la tache en echec et les
sorties sont masquees ; Supercronic conserve le statut de la tache dans ses logs.

Gunicorn et Supercronic s'executent sans root et s'arretent ensemble. Si le
conteneur est arrete au moment prevu, la tache mensuelle n'est pas rattrapee.
Avec plusieurs repliques applicatives, chacune planifie son propre rapport :
ce lancement est prevu pour un seul conteneur applicatif.

#### Migration des mots de passe

Les mots de passe existants restent utilisables : la premiere connexion reussie
verifie le SHA-256 historique puis le remplace par Argon2id dans la colonne
`sha_mdp` existante de 255 caracteres. Aucune conversion de masse ni remise a zero
des mots de passe n'est executee. Les creations et changements de mot de passe
utilisent directement Argon2id ; un champ de modification vide conserve le hash.
Les parametres Argon2id obsoletes sont recalcules apres une verification reussie.

Si l'ecriture de migration echoue, un rollback conserve l'ancien hash et la
connexion reste autorisee apres verification du mot de passe et de l'etat du
compte, a condition de pouvoir enregistrer la nouvelle session en base. Si cette
creation echoue aussi, la connexion est refusee avec un `503`. Une tentative
ulterieure pourra migrer le hash. Le log de niveau WARNING
`MIGR-AUTH` contient l'identifiant du compte, l'operation, la classe d'erreur et
le code du pilote s'il est disponible, sans mot de passe, hash ou exception SQL
brute. Pour le filtrer :

```bash
docker compose logs web | grep MIGR-AUTH
```

Tous les processus applicatifs doivent lire SHA-256 et Argon2id avant que des
comptes soient migres. Un retour arriere doit conserver cette double lecture :
l'ancien code uniquement SHA-256 ne peut plus authentifier les comptes migres.
Les comptes qui ne se reconnectent pas conservent leur ancien hash.

Les parametres actuels sont ceux d'argon2-cffi : 64 Mio par calcul, 3 passes et
un parallelisme de 4. Les wheels Python 3.14 ARM64 d'Argon2 et de CFFI sont
disponibles ; mesurer toutefois la latence et la memoire sur le Raspberry Pi
avec le nombre de connexions simultanees attendu avant de modifier ces parametres.

#### Sessions persistantes et migration obligatoire

La revision Alembic `d4f3a20e9b71`, apres `c8293d28c674`, cree `98_sessions`.
Appliquer cette migration avec la nouvelle image avant de relancer l'application :

```bash
docker compose build web
docker compose run --rm --no-deps --entrypoint sh web app/migrate.sh
docker compose up -d web
```

La base doit etre disponible et `DB_URL` doit cibler la base voulue. Ces commandes
ne sont pas executees automatiquement par l'assistant sur le deploiement reel.
L'initialisation applicative ne cree pas `98_sessions` a la place d'Alembic et
refuse le demarrage si cette table manque. Le premier deploiement impose une
nouvelle connexion aux navigateurs dont le cookie est anterieur a cette table.

Chaque navigateur recoit un jeton aleatoire ; seule son empreinte SHA-256 est
enregistree en base, avec le compte, la creation, la derniere activite et
l'expiration en UTC. Toute requete protegee relit le compte et prolonge la session
de 20 minutes. Les informations de compatibilite presentes dans le cookie sont
reecrites depuis la base et ne constituent pas une preuve d'authentification.
Les ressources statiques ne prolongent pas l'activite. Le rapport automatise
reste independant, protege par `API_MAIL_TOKEN`.

Un changement de mot de passe ou d'habilitation supprime toutes les sessions du
compte dans la meme transaction, y compris sa session courante. Une modification
annulee ne les revoque pas. Une deconnexion ne supprime que le navigateur courant.
Le compte est aussi refuse s'il a disparu, est verrouille, expire ou pas encore
actif. Une panne de verification en base donne un `503` et n'autorise pas les
anciens droits du cookie. Les erreurs techniques sont filtrables par `SESSION-AUTH`.

Apres une modification SQL directe des droits, du mot de passe ou du statut,
supprimer manuellement dans la meme transaction les lignes de `98_sessions`
dont `id_user` correspond au compte concerne. Aucun trigger n'est installe.
Les lignes expirees sont rejetees et supprimees lorsqu'elles sont presentees ;
un nettoyage periodique des lignes qui ne sont plus jamais utilisees reste une
operation de maintenance a prevoir. Un downgrade supprimant cette table invalide
toutes les connexions et n'est pas compatible avec cette version de l'application.

Les delais de connexion, le passage aux threads et la limitation des tentatives
ne font pas partie de ce changement et restent a valider separement.

#### Raspberry Pi 5 ARM64

Supercronic 0.2.50 dispose d'un binaire Linux ARM64. Le Dockerfile choisit le
binaire selon `dpkg --print-architecture` et verifie son empreinte SHA-256.
Les images Python et MariaDB utilisees proposent aussi une variante ARM64.

Construire directement sur le Raspberry Pi avec un systeme et un moteur Docker
64 bits selectionne automatiquement ARM64. Pour une construction sur une autre
machine, cibler `linux/arm64` ou publier une image multiarchitecture ; ne pas
transferer une image construite uniquement pour AMD64. Les tests sur AMD64 ne
remplacent pas la validation de toutes les dependances sur le Raspberry Pi.

#### Étape 5 : Création des répertoires

```bash
mkdir -p $(grep FILES_LOCAL_PATH .env | cut -d'=' -f2)
mkdir -p $(grep PRINT_LOCAL_PATH .env | cut -d'=' -f2)
mkdir -p $(grep DB_LOCAL_PATH .env | cut -d'=' -f2)
mkdir -p $(grep SIGNATURE_LOCAL_PATH .env | cut -d'=' -f2)

# Définir les permissions appropriées
sudo chown -R $USER:$USER $(grep FILES_LOCAL_PATH .env | cut -d'=' -f2)
sudo chown -R $USER:$USER $(grep PRINT_LOCAL_PATH .env | cut -d'=' -f2)
sudo chown -R $USER:$USER $(grep DB_LOCAL_PATH .env | cut -d'=' -f2)
sudo chown -R $USER:$USER $(grep SIGNATURE_LOCAL_PATH .env | cut -d'=' -f2)
sudo chmod 755 $(grep FILES_LOCAL_PATH .env | cut -d'=' -f2)
```

#### Étape 6 : Configuration SSL (Optionnel mais recommandé)

Faire une demande de certificats SSL via Let's Encrypt ou utiliser vos propres certificats.

```bash
openssl version
```

Si vous utilisez Let's Encrypt, vous pouvez configurer Certbot après le déploiement initial.

```bash
sudo apt-get install certbot
sudo certbot certonly --standalone -d votre-domaine.com
```

Placer vos certificats SSL dans /etc/nginx/certs/ et ajuster les noms de fichiers dans nginx.conf

```bash
sudo cp votre-certificat.pem /etc/nginx/certs/__cert__.pem
sudo cp votre-cle-privee.pem /etc/nginx/certs/__privkey__.pem
sudo chmod 600 /etc/nginx/certs/__privkey__.pem
sudo nano app/nginx/nginx.conf
```

#### Étape 7 : Construction et lancement

Construire et lancer l'application

```bash
docker compose up --build -d
```

#### Étape 8 : Vérification du déploiement

Vérifier que tous les conteneurs sont en cours d'exécution

```bash
docker compose ps

# Vérifier les logs en cas de problème
docker compose logs web
docker compose logs db
docker compose logs nginx
```

#### Étape 9 : Premier accès

Accéder à l'application

```txt
Ouvrir http://localhost (ou https://localhost si SSL configuré)
Tester la connexion avec un compte administrateur
```

## Dépannage rapide

### Problème : Port déjà utilisé

```bash
# Trouver le processus utilisant le port 80
sudo lsof -i :80
# Arrêter le processus ou changer le port dans docker-compose.yaml
```

### Problème : Permissions insuffisantes

```bash
# Corriger les permissions
sudo chown -R $USER:$USER .
chmod +x *.sh
```

### Problème : Base de données inaccessible

```bash
# Redémarrer uniquement la base de données
docker-compose restart db
# Vérifier les logs
docker-compose logs db
```

### Problème : Erreurs de lecture des fichiers *.sh

#### Sous Linux / macOS

```bash
# Utiliser dos2unix pour convertir les fins de ligne
# Version Debian/Ubuntu
sudo apt-get install dos2unix
dos2unix *.sh

# Version macOS
brew install dos2unix
dos2unix *.sh
```

#### Sous Windows

```Powershell (Administrateur)
# Version Windows (Git Bash)
# Installation de Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force; `
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; `
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Vérification de l'installation
choco --version

# Installation de dos2unix
choco install dos2unix

# Conversion des fichiers
dos2unix *.sh
```

## Contacts

- 🐙 **GitHub** : [Issues](https://github.com/remiv1/Intranet/issues)
- 📧 **Email** : [remiv1@gmail.com]
- 📚 **Documentation** : [README.md](README.md)

[<- Retour à la page d'accueil](../README.md)
