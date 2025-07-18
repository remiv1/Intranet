# 🚀 Guide d'Installation Rapide - Intranet

## Installation en 5 minutes

### Méthode 1 : Installation automatique (Recommandée)

```bash
# 1. Cloner le projet
git clone https://github.com/remiv1/Intranet.git
cd Intranet

# 2. Démarrage automatique
./quick-start.sh

# 3. Accéder à l'application
# → http://localhost
```

### Méthode 2 : Avec Make

```bash
# 1. Cloner le projet
git clone https://github.com/remiv1/Intranet.git
cd Intranet

# 2. Installation complète
make install

# 3. Accéder à l'application
# → http://localhost
```

### Méthode 3 : Installation manuelle

```bash
# 1. Cloner le projet
git clone https://github.com/remiv1/Intranet.git
cd Intranet

# 2. Générer la configuration
./generate-env.sh

# 3. Personnaliser la configuration
nano .env

# 4. Créer les répertoires
mkdir -p $(grep FILES_LOCAL_PATH .env | cut -d'=' -f2)
mkdir -p $(grep PRINT_LOCAL_PATH .env | cut -d'=' -f2)

# 5. Démarrer l'application
docker-compose up -d

# 6. Accéder à l'application
# → http://localhost
```

## Installation pour le développement

```bash
# 1. Cloner le projet
git clone https://github.com/remiv1/Intranet.git
cd Intranet

# 2. Mode développement
./quick-start.sh dev
# OU
make dev

# 3. Accéder aux services
# → Application: http://localhost:5000
# → PhpMyAdmin: http://localhost:8080
```

## Vérification de l'installation

```bash
# Vérifier les services
docker-compose ps

# Vérifier les logs
docker-compose logs web

# Tester la connectivité
curl -I http://localhost
```

## Commandes utiles

```bash
# Voir toutes les commandes disponibles
make help

# Arrêter l'application
make stop

# Redémarrer l'application
make restart

# Voir les logs
make logs

# Créer une sauvegarde
make backup

# Mettre à jour
make update
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

## Contacts

- 🐙 **GitHub** : [Issues](https://github.com/remiv1/Intranet/issues)
- 📧 **Email** : [Contact développeur]
- 📚 **Documentation** : [README.md](README.md)
