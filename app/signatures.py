"""
Page des gestion des fonctions liées à la signature électronique.
Fonctions:
- Ajout de la signature graphique sur un document PDF.
- Ajout d'un certificat de signature numérique.
- Stockage temporaire des documents avant signature.
- Enregistrement des ashages des documents signés pour vérification ultérieure.
"""

class SignatureDocument(Base):
    __tablename__ = 'signature_documents'
    
    id = mapped_column(Integer, primary_key=True)
    original_filename = mapped_column(String(255), nullable=False)  # doc_id
    document_name = mapped_column(String(255), nullable=False)      # new_name
    document_type = mapped_column(String(50), nullable=False)       # contrat, convention, etc.
    document_subtype = mapped_column(String(100), nullable=True)
    priority = mapped_column(String(20), default='normale')         # basse, normale, haute, urgente
    signing_deadline_days = mapped_column(Integer, nullable=False)  # 1-15 jours
    validity_days = mapped_column(Integer, nullable=True)           # durée d'archivage
    description = mapped_column(String(1000), nullable=True)
    
    # Métadonnées techniques
    file_path = mapped_column(String(500), nullable=False)          # chemin du fichier
    file_hash = mapped_column(String(64), nullable=False)           # hash du fichier pour intégrité
    created_by = mapped_column(String(100), nullable=True)          # identifiant créateur
    created_at = mapped_column(DateTime, default=func.now())
    
    # Statuts et dates
    status = mapped_column(String(20), default='pending')           # pending, in_progress, completed, expired
    signing_deadline = mapped_column(DateTime, nullable=False)      # date limite calculée
    completed_at = mapped_column(DateTime, nullable=True)
    
    # Relations
    signature_points = relationship("SignaturePoint", back_populates="document", cascade="all, delete-orphan")
    signatures = relationship("DocumentSignature", back_populates="document", cascade="all, delete-orphan")

class SignaturePoint(Base):
    __tablename__ = 'signature_points'
    
    id = mapped_column(Integer, primary_key=True)
    id_document = mapped_column(Integer, ForeignKey('signature_documents.id'), nullable=False)
    
    # Position sur le PDF
    x = mapped_column(Numeric(10, 2), nullable=False)
    y = mapped_column(Numeric(10, 2), nullable=False)
    page_num = mapped_column(Integer, nullable=False)
    
    # Signataire assigné
    id_utilisateur = mapped_column(Integer, ForeignKey('99_users.id'), nullable=False)
    
    # Statut
    status = mapped_column(String(20), default='pending')  # pending, signed, expired
    signed_at = mapped_column(DateTime, nullable=True)
    
    # Relations
    document = relationship("SignatureDocument", back_populates="signature_points")
    user = relationship("User")
    signature = relationship("DocumentSignature", back_populates="signature_point", uselist=False)


class DocumentSignature(Base):
    __tablename__ = 'document_signatures'
    
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
    document = relationship("SignatureDocument", back_populates="signatures")
    signature_point = relationship("SignaturePoint", back_populates="signature")
    user = relationship("User")

class SignatureInvitation(Base):
    __tablename__ = 'signature_invitations'
    
    id = mapped_column(Integer, primary_key=True)
    document_id = mapped_column(Integer, ForeignKey('signature_documents.id'), nullable=False)
    user_id = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
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

class SignatureAuditLog(Base):
    __tablename__ = 'signature_audit_log'
    
    id = mapped_column(Integer, primary_key=True)
    document_id = mapped_column(Integer, ForeignKey('signature_documents.id'), nullable=False)
    user_id = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Événement
    action = mapped_column(String(50), nullable=False)  # created, viewed, signed, expired, etc.
    details = mapped_column(String(1000), nullable=True)
    
    # Contexte technique
    ip_address = mapped_column(String(45), nullable=True)
    user_agent = mapped_column(String(500), nullable=True)
    timestamp = mapped_column(DateTime, default=func.now())
    
    # Relations
    document = relationship("SignatureDocument")
    user = relationship("User")