#!/usr/bin/env python3
"""
Script de test avancé pour la classe SignedDocumentCreator avec SVG et certificats sécurisés.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

def test_advanced_imports():
    """Test les imports avancés avec SVG et cryptographie."""
    print("🔍 Test des imports avancés...")
    
    try:
        # Test borb
        from borb.pdf import Document, PDF
        print("✅ borb importé avec succès")
        
        # Test pillow
        from PIL import Image as PILImage
        print("✅ Pillow (PIL) importé avec succès")
        
        # Test cairosvg
        import cairosvg
        print("✅ cairosvg importé avec succès")
        
        # Test cryptography
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        print("✅ cryptography importé avec succès")
        
        # Test de notre classe
        from bp_signature import SignedDocumentCreator, SecureCertificateManager
        print("✅ SignedDocumentCreator et SecureCertificateManager importés avec succès")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import : {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False

def test_certificate_creation():
    """Test la création de certificats sécurisés."""
    print("\n🔐 Test de création de certificats sécurisés...")
    
    try:
        from bp_signature import SecureCertificateManager
        
        # Données de test factices
        test_signatures = []
        test_document_hash = "abc123def456"
        test_signatories = []
        
        # Créer un certificat sécurisé
        print("   Génération d'un certificat de test...")
        cert = SecureCertificateManager.create_secure_certificate(
            signatures=test_signatures,
            document_hash=test_document_hash,
            signatories=test_signatories
        )
        
        print("✅ Certificat sécurisé créé avec succès")
        print(f"   ID du certificat : {cert['certificate']['certificate_id']}")
        print(f"   Algorithme : {cert['algorithm']}")
        
        # Vérifier le certificat
        print("   Vérification du certificat...")
        is_valid = SecureCertificateManager.verify_certificate(cert)
        
        if is_valid:
            print("✅ Certificat vérifié avec succès")
            return True
        else:
            print("❌ Échec de la vérification du certificat")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test de certificat : {e}")
        return False

def test_svg_conversion():
    """Test la conversion SVG."""
    print("\n🎨 Test de conversion SVG...")
    
    try:
        from bp_signature import SignedDocumentCreator
        
        # SVG de test simple
        test_svg = '''<svg width="100" height="50" xmlns="http://www.w3.org/2000/svg">
            <text x="10" y="30" fill="blue">Test Signature</text>
        </svg>'''
        
        # Créer une instance pour accéder à la méthode
        creator = SignedDocumentCreator(
            id_document=1,
            hash_document="test",
            current_user_id=1
        )
        
        # Tester la conversion
        print("   Conversion du SVG de test...")
        image = creator._convert_svg_to_image(test_svg, 100, 50)
        
        if image:
            print("✅ SVG converti en image avec succès")
            print(f"   Taille de l'image : {image.size}")
            return True
        else:
            print("⚠️  Conversion SVG échouée (dépendances manquantes ?)")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test SVG : {e}")
        return False

def main():
    """Fonction principale de test."""
    print("=== Test complet de SignedDocumentCreator avec SVG et certificats sécurisés ===\n")
    
    tests_results = []
    
    # Test 1: Imports
    print("1. Test des imports avancés :")
    tests_results.append(test_advanced_imports())
    
    # Test 2: Certificats sécurisés
    print("\n2. Test des certificats sécurisés :")
    tests_results.append(test_certificate_creation())
    
    # Test 3: Conversion SVG
    print("\n3. Test de conversion SVG :")
    tests_results.append(test_svg_conversion())
    
    # Résumé
    print("\n" + "="*60)
    passed = sum(tests_results)
    total = len(tests_results)
    
    if passed == total:
        print(f"🎉 Tous les tests sont passés ! ({passed}/{total})")
        print("\n✨ La classe SignedDocumentCreator est prête avec :")
        print("   • Intégration SVG directe avec borb")
        print("   • Certificats cryptographiquement sécurisés")
        print("   • Vérification d'intégrité RSA-SHA256")
        print("   • Fallback gracieux en cas d'erreur")
    else:
        print(f"⚠️  {passed}/{total} tests passés")
        print("\nVérifiez que toutes les dépendances sont installées :")
        print("   pip install pillow cairosvg cryptography")

if __name__ == "__main__":
    main()