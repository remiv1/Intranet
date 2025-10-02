#!/usr/bin/env python3
"""
Script de test pour la classe SignedDocumentCreator.
Ce script permet de tester la création de documents PDF signés.
"""

import sys
import os
# Ajouter le répertoire app au PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

def test_borb_import():
    """Test si borb peut être importé et utilisé."""
    try:
        from borb.pdf import Document, PDF
        print("✅ Borb importé avec succès")
        
        # Test de création d'un document vide
        doc = Document()
        print("✅ Document borb créé avec succès")
        
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import borb : {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test borb : {e}")
        return False

def test_signed_document_creator_imports():
    """Test si notre classe peut être importée."""
    try:
        from bp_signature import SignedDocumentCreator, BORB_AVAILABLE
        print("✅ SignedDocumentCreator importé avec succès")
        print(f"✅ Borb disponible : {BORB_AVAILABLE}")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import SignedDocumentCreator : {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test d'import : {e}")
        return False

def main():
    """Fonction principale de test."""
    print("=== Test de la classe SignedDocumentCreator ===\n")
    
    print("1. Test d'import de borb :")
    borb_ok = test_borb_import()
    print()
    
    print("2. Test d'import de SignedDocumentCreator :")
    class_ok = test_signed_document_creator_imports()
    print()
    
    if borb_ok and class_ok:
        print("✅ Tous les tests d'import sont passés !")
        print("\n🎉 La classe SignedDocumentCreator est prête à être utilisée.")
        print("\nProchaines étapes :")
        print("- Créer un document PDF de test")
        print("- Tester la création d'un document signé")
        print("- Implémenter l'ajout de signatures SVG avec borb")
    else:
        print("❌ Certains tests ont échoué.")
        print("Vérifiez que borb est correctement installé et que les imports sont corrects.")

if __name__ == "__main__":
    main()