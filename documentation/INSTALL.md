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
