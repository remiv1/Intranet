#!/bin/bash

# Script de génération automatique du fichier .env
# Usage: ./generate-env.sh

set -e

echo "🔧 Génération du fichier de configuration .env..."

# Fonction pour générer un mot de passe aléatoire de 32 caractères
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Vérifier si .env existe déjà
if [ -f ".env" ]; then
    echo "⚠️  Le fichier .env existe déjà."
    read -p "Voulez-vous le remplacer ? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Opération annulée."
        exit 1
    fi
    echo "🗑️  Suppression de l'ancien fichier .env..."
    rm .env
fi

# Vérifier si .env.example existe
if [ ! -f ".env.example" ]; then
    echo "❌ Le fichier .env.example n'existe pas."
    exit 1
fi

echo "🔐 Génération des mots de passe aléatoires..."

# Générer les mots de passe
DB_PASSWORD=$(generate_password)
ROOT_PASSWORD=$(generate_password)
SECRET_KEY=$(generate_password)
SSH_PASSWORD=$(generate_password)
EMAIL_PASSWORD=$(generate_password)

echo "📝 Création du fichier .env..."

# Copier le fichier exemple et remplacer les mots de passe
cp .env.example .env

# Remplacer les mots de passe dans le fichier .env
sed -i "s/CHANGE_ME_32_CHARS_PASSWORD_1/$DB_PASSWORD/g" .env
sed -i "s/CHANGE_ME_32_CHARS_ROOT_PASSWORD/$ROOT_PASSWORD/g" .env
sed -i "s/CHANGE_ME_32_CHARS_SECRET_KEY/$SECRET_KEY/g" .env
sed -i "s/CHANGE_ME_32_CHARS_SSH_PASSWORD/$SSH_PASSWORD/g" .env
sed -i "s/CHANGE_ME_32_CHARS_EMAIL_PASSWORD/$EMAIL_PASSWORD/g" .env

# Mettre à jour l'URL de base de données avec le nouveau mot de passe
sed -i "s|mysql+mysqlconnector://intranet_user:CHANGE_ME_32_CHARS_PASSWORD_1@db:3306/intranet_db|mysql+mysqlconnector://intranet_user:$DB_PASSWORD@db:3306/intranet_db|g" .env

echo "✅ Fichier .env généré avec succès !"
echo ""
echo "🔒 Mots de passe générés :"
echo "   - Base de données: $DB_PASSWORD"
echo "   - Root MySQL: $ROOT_PASSWORD"
echo "   - Clé secrète Flask: $SECRET_KEY"
echo "   - SSH: $SSH_PASSWORD"
echo "   - Email: $EMAIL_PASSWORD"
echo ""
echo "⚠️  IMPORTANT :"
echo "   1. Sauvegardez ces mots de passe en lieu sûr"
echo "   2. Modifiez les autres variables dans .env selon votre environnement"
echo "   3. Ne commitez jamais le fichier .env dans votre dépôt Git"
echo ""
echo "🚀 Vous pouvez maintenant lancer: docker-compose up -d"
