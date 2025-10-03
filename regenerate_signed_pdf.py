"""
Script pour re-générer un PDF signé avec les signatures graphiques
à partir du PDF original et du certificat existant.
"""
import sys
from pathlib import Path

# Ajouter le répertoire app au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent / 'app'))

from signatures import SignedDocumentCreator
from models import DocToSigne
from flask import g
from application import app
from sqlalchemy.orm import Session
from config import Config

def regenerate_signed_pdf(document_name: str):
    """
    Re-génère un PDF signé avec les signatures graphiques.
    
    Args:
        document_name: Nom du document (ex: "Offres_Head Connect.pdf")
    """
    with app.app_context():
        # Créer une session DB
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        SessionLocal = sessionmaker(bind=engine)
        db_session = SessionLocal()
        g.db_session = db_session
        
        try:
            # Chercher le document dans la base
            document = db_session.query(DocToSigne).filter_by(doc_nom=document_name).first()
            
            if not document:
                print(f"❌ Document '{document_name}' non trouvé en base de données")
                return False
            
            print(f"📄 Document trouvé: {document.doc_nom}")
            print(f"   ID: {document.id}")
            print(f"   Hash: {document.hash_fichier}")
            print(f"   Status: {document.status}")
            
            # Récupérer le chemin du fichier original
            original_path = Path("documents/signatures") / f"original_{document_name}"
            if not original_path.exists():
                print(f"❌ Fichier original non trouvé: {original_path}")
                return False
            
            print(f"\n🔄 Re-génération du PDF signé avec pypdf + reportlab...")
            
            # Créer le SignedDocumentCreator
            creator = SignedDocumentCreator(
                id_document=document.id,
                current_user_id=1  # Utilisateur système
            )
            
            # Charger et traiter le document
            creator.load_document()
            creator.load_signatures_and_points()
            creator.verify_all_signatures_completed()
            creator.verify_document_integrity()
            
            # Appliquer les signatures avec pypdf
            creator.document_path = original_path
            creator.apply_signatures_to_pdf()
            
            # Sauvegarder le document final
            creator.save_final_document()
            
            print(f"\n✅ PDF signé re-généré avec succès !")
            print(f"📁 Fichier: {creator.signed_document_path}")
            
            db_session.commit()
            return True
            
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            db_session.rollback()
            return False
            
        finally:
            db_session.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python regenerate_signed_pdf.py <nom_du_document>")
        print("Exemple: python regenerate_signed_pdf.py 'Offres_Head Connect.pdf'")
        sys.exit(1)
    
    document_name = sys.argv[1]
    success = regenerate_signed_pdf(document_name)
    sys.exit(0 if success else 1)
