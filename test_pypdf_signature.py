"""
Script de test pour vérifier que pypdf + reportlab fonctionnent correctement
"""
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PIL import Image as PILImage

def test_pypdf_overlay():
    """Test de création d'un overlay avec pypdf"""
    print("🔬 Test pypdf + reportlab...")
    
    # Créer un PDF de test simple
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(595, 842))  # A4
    
    # Ajouter du texte
    can.setFont("Helvetica", 12)
    can.drawString(100, 700, "Test de signature avec pypdf + reportlab")
    can.drawString(100, 680, "Si vous voyez ce texte, l'overlay fonctionne !")
    
    # Créer une image de test
    test_img = PILImage.new('RGB', (200, 100), color='lightblue')
    img_reader = ImageReader(test_img)
    can.drawImage(img_reader, 100, 500, width=200, height=100)
    
    can.save()
    packet.seek(0)
    
    print("✅ Overlay créé avec succès")
    print(f"📦 Taille de l'overlay: {len(packet.getvalue())} bytes")
    
    return packet.getvalue()

if __name__ == "__main__":
    try:
        overlay_bytes = test_pypdf_overlay()
        print(f"\n✨ Test réussi ! pypdf et reportlab fonctionnent correctement.")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
