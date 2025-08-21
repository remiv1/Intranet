#!/usr/bin/env python3
"""
Script pour générer un hash de mot de passe bcrypt
Utilisé pour créer des mots de passe sécurisés pour les utilisateurs de test
"""

import bcrypt

def generate_password_hash(password: str) -> str:
    """Génère un hash bcrypt pour le mot de passe donné"""
    # Générer un salt et hasher le mot de passe
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Vérifie si le mot de passe correspond au hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

if __name__ == "__main__":
    # Générer le hash pour le mot de passe de test
    test_password = "testpassword"
    hash_result = generate_password_hash(test_password)
    
    print(f"Mot de passe: {test_password}")
    print(f"Hash bcrypt: {hash_result}")
    
    # Vérifier que le hash fonctionne
    if verify_password(test_password, hash_result):
        print("✓ Vérification du hash réussie")
    else:
        print("✗ Erreur dans la vérification du hash")
