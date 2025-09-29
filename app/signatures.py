"""
Page des gestion des fonctions liées à la signature électronique.
Fonctions:
- Ajout de la signature graphique sur un document PDF.
- Ajout d'un certificat de signature numérique.
- Stockage temporaire des documents avant signature.
- Enregistrement des ashages des documents signés pour vérification ultérieure.
"""
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, Text, Numeric
from sqlalchemy.orm import relationship, declarative_base, mapped_column
from sqlalchemy.sql import func
Base = declarative_base()

PK_DOC_TO_SIGNE = '20_documents_a_signer.id'

class Points(Base):
    __tablename__ = '21_points'
    
    id = mapped_column(Integer, primary_key=True)
    id_document = mapped_column(Integer, ForeignKey(PK_DOC_TO_SIGNE), nullable=False)
    
    # Position sur le PDF
    x = mapped_column(Numeric(10, 2), nullable=False)           # position X en pixels (1/72 inch)
    y = mapped_column(Numeric(10, 2), nullable=False)           # position Y en pixels (1/72 inch)
    page_num = mapped_column(Integer, nullable=False)           # numéro de page (1-indexed)
    
    # Signataire assigné
    #TODO: prévoir un soft_delete des utilisateurs pour conservation pendant la durée de validité des documents
    id_utilisateur = mapped_column(Integer, ForeignKey('99_users.id'), nullable=False)
    
    # Statut
    status = mapped_column(String(20), default='pending')  # pending, signed, expired
    signed_at = mapped_column(DateTime, nullable=True)
    
    # Relations
    document = relationship("DocToSigne", back_populates="points")
    user = relationship("User")
    signature = relationship("Signatures", back_populates="points", uselist=False)


class Signatures(Base):
    __tablename__ = '22_signatures'
    
    id = mapped_column(Integer, primary_key=True)
    document_id = mapped_column(Integer, ForeignKey('signature_documents.id'), nullable=False)
    signature_point_id = mapped_column(Integer, ForeignKey('signature_points.id'), nullable=False)
    user_id = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Données de signature
    signed_at = mapped_column(DateTime, default=func.now())
    signature_hash = mapped_column(String(128), nullable=False)     # hash de la signature
    ip_address = mapped_column(String(45), nullable=True)
    user_agent = mapped_column(String(500), nullable=True)
    
    # Signature graphique - AJOUT
    signature_svg = mapped_column(Text, nullable=True)              # Format SVG de la signature tracée
    signature_data = mapped_column(Text, nullable=True)             # JSON coordinates (alternatif/backup)
    signature_width = mapped_column(Integer, nullable=True)         # Largeur de la zone de signature
    signature_height = mapped_column(Integer, nullable=True)        # Hauteur de la zone de signature
    signature_timestamp = mapped_column(DateTime, default=func.now()) # Horodatage de la signature graphique
    
    # Certificat (si requis)
    certificate_data = mapped_column(String(2000), nullable=True)
    
    # Statut
    is_valid = mapped_column(Boolean, default=True)
    
    # Relations
    document = relationship("DocToSigne", back_populates="signatures")
    points = relationship("Points", back_populates="signature")
    user = relationship("User")

class SignatureInvitation(Base):
    __tablename__ = '23_invitations'
    
    id = mapped_column(Integer, primary_key=True)
    document_id = mapped_column(Integer, ForeignKey('20_documents_a_signer.id'), nullable=False)
    user_id = mapped_column(Integer, ForeignKey('99_users.id'), nullable=False)
    
    # Token sécurisé pour le lien
    invitation_token = mapped_column(String(128), unique=True, nullable=False)
    
    # Statuts et dates
    sent_at = mapped_column(DateTime, default=func.now())
    expires_at = mapped_column(DateTime, nullable=False)
    accessed_at = mapped_column(DateTime, nullable=True)          # première consultation
    signed_at = mapped_column(DateTime, nullable=True)
    
    # Méta-données
    email_sent = mapped_column(Boolean, default=False)
    reminder_count = mapped_column(Integer, default=0)
    
    # Relations
    document = relationship("SignatureDocument")
    user = relationship("User")

class AuditLog(Base):
    __tablename__ = '24_audit_logs'
    
    id = mapped_column(Integer, primary_key=True)
    document_id = mapped_column(Integer, ForeignKey('20_documents_a_signer.id'), nullable=False)
    user_id = mapped_column(Integer, ForeignKey('99_users.id'), nullable=True)
    
    # Événement
    action = mapped_column(String(50), nullable=False)  # created, viewed, signed, expired, etc.
    details = mapped_column(String(1000), nullable=True)
    
    # Contexte technique
    ip_address = mapped_column(String(45), nullable=True)
    user_agent = mapped_column(String(500), nullable=True)
    timestamp = mapped_column(DateTime, default=func.now())
    
    # Relations
    document = relationship("DocToSigne")
    user = relationship("User")