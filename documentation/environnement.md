# Environnement de production avant déploiement

[<- Retour à la page d'accueil](../README.md)

## 🔧 Commandes utiles

```bash
# Arrêter l'application + arrêt et suppression des données
docker compose down
docker compose down -v

# Redémarrer l'application
docker compose restart

# Voir les logs en temps réel
docker compose logs -f web

# Accéder au conteneur de l'application
docker compose -it exec web bash

# Accéder à la base de données
docker compose -it exec db mysql -u root -p

# Mise à jour de l'application
git pull
docker compose build
docker compose up -d

# Sauvegarde de la base de données
./backup/backup-script.sh
```

## 📋 Variables d'environnement détaillées

Le fichier `.env` contient toutes les variables de configuration nécessaires :

### 🗄️ Configuration Base de Données

| Variable | Description | Exemple |
| --- | --- | --- |
| `ROOT_PASSWORD` | Mot de passe root MySQL | `mot_de_passe_securise` |
| `DB_USER` | Utilisateur de la base de données | `intranet_user` |
| `DB_PASSWORD` | Mot de passe de la base de données | `mot_de_passe_securise` |
| `DB_HOST` | Hôte de la base de données | `db` |
| `DB_NAME` | Nom de la base de données | `intranet_db` |
| `DB_URL` | URL de connexion à la base de données | `mysql+mysqlconnector://...` |
| `DB_DOCKER_PATH` | Chemin Docker de la base de données | `/var/lib/mysql` |
| `DB_LOCAL_PATH` | Chemin local de la base de données | `/var/lib/docker/volumes/...` |

### 🔐 Sécurité

| Variable | Description | Exemple |
| --- | --- | --- |
| `SECRET_KEY` | Clé secrète Flask (sessions, HMAC) | `cle_secrete_32_chars_min` |

> ⚠️ **Important** : `SECRET_KEY` est utilisée pour les sessions Flask ET la sécurisation HMAC des documents de signature. Changez-la régulièrement et utilisez minimum 32 caractères aléatoires.

### 📁 Chemins de Stockage

| Variable | Description | Exemple |
| --- | --- | --- |
| `FILES_DOCKER_PATH` | Chemin Docker des documents | `/app/documents` |
| `FILES_LOCAL_PATH` | Chemin local des documents | `/var/www/intranet/documents` |
| `PRINT_DOCKER_PATH` | Chemin Docker des impressions | `/app/print` |
| `PRINT_LOCAL_PATH` | Chemin local des impressions | `/var/www/intranet/print` |
| `SIGNATURE_DOCKER_PATH` | Chemin Docker documents signés | `/app/documents/signatures` |
| `SIGNATURE_LOCAL_PATH` | Chemin local documents signés | `/var/www/intranet/documents/signatures` |
| `TEMP_DOCKER_PATH` | Chemin Docker fichiers temporaires | `/tmp` |

> 📝 **Note** : Les dossiers de signatures sont créés automatiquement. Le dossier `/tmp/signature` n'est pas monté dans Docker pour raisons de sécurité.

### 🖨️ Configuration Impression

| Variable | Description | Exemple |
| --- | --- | --- |
| `PRINTER_NAME` | Nom de l'imprimante réseau | `HP_LaserJet_Pro` |
| `SSH_PORT` | Port SSH pour transfert fichiers | `22` |
| `SSH_HOST` | Hôte SSH du serveur d'impression | `192.168.1.100` |
| `SSH_USER` | Utilisateur SSH | `ssh_user` |
| `SSH_PASSWORD` | Mot de passe SSH | `mot_de_passe_ssh_securise` |

### 📧 Configuration Email (SMTP)

| Variable | Description | Exemple |
| --- | --- | --- |
| `EMAIL_USER` | Adresse email d'envoi | `noreply@etablissement.fr` |
| `EMAIL_PASSWORD` | Mot de passe du compte email | `mot_de_passe_email_securise` |
| `EMAIL_SMTP` | Serveur SMTP | `smtp.gmail.com` |
| `EMAIL_PORT` | Port SMTP | `587` (TLS) ou `465` (SSL) |
| `API_MAIL_TOKEN` | Token API pour rapports par email | `token_api_securise` |

> 📧 **Usage** : Utilisé pour les notifications d'échéances, codes OTP de signature, et envoi des documents signés.

### 🐳 Configuration Docker (Dev/CI)

| Variable | Description | Exemple |
| --- | --- | --- |
| `DB_PORTS` | Mapping ports base de données | `3306:3306` |
| `WEB_PORTS` | Mapping ports application web | `5000:5000` |
| `EXPOSE_PORTS` | Mode exposition des ports | `Workflow` ou `Production` |

---

> **⚠️ Sécurité** :
>
> - Ne partagez **jamais** le fichier `.env` publiquement
> - Utilisez `./generate-env.sh` pour générer des valeurs sécurisées
> - Changez `SECRET_KEY` régulièrement (minimum tous les 6 mois)
> - Utilisez des mots de passe d'au moins 32 caractères
> - Sauvegardez le `.env` dans un endroit sûr et chiffré

## 🔐 Système d'Habilitations

L'application utilise un système d'habilitations numérique flexible :

| Code | Rôle | Permissions |
| --- | --- | --- |
| **1** | 🔧 Super-administrateur | Gestion des droits utilisateurs |
| **2** | 👤 Administrateur étab. | Gestion utilisateurs et contrats |
| **3** | 🎓 Professeur principal | Espace professeurs principaux |
| **4** | 📚 Professeur | Espace professeurs |
| **5** | 🎒 Élève | Espace élèves |
| **6** | 🖨️ Impression | Accès aux fonctions d'impression |

**Combinaisons possibles (exemples) :**

- `126` = Super-admin + Admin + Impression
- `234` = Admin + Prof principal + Prof
- `56` = Élève + Impression

[<- Retour à la page d'accueil](../README.md)
