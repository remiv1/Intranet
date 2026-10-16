from typing import Optional, Dict, Any, List
import io

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    ForeignKey,
    Numeric,
    DateTime,
    Text,
    Computed,
)
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.sql import func
from flask import g

class DocToSigne(Base):
    """
    Représente un document à signer électroniquement.
    Attributs :
        id (int): Identifiant unique du document.
        doc_nom (str): Nom définitif du document.
        doc_type (str): Type de document (contrat, convention, etc.).
        doc_sous_type (str): Sous-type de document.
        priorite (int): Priorité du document (-1 : basse, 0 : normale, 1 : haute, 2 : urgente).
        echeance (int): Délai en jours pour la signature (1-15 jours).
        duree_archivage (int): Durée d'archivage du document en jours.
        description (str): Description du document.
        chemin_fichier (str): Chemin du fichier stocké.
        hash_fichier (str): Hash du fichier pour vérifier l'intégrité.
        id_user (int): Identifiant de l'utilisateur créateur du document.
        cree_at (datetime): Date et heure de création du document.
        status (int): Statut du document (-2: annulé, -1: expiré, 0: en attente, 1: signé).
        limite_signature (datetime): Date limite pour la signature (calculée).
        complete_at (datetime): Date et heure de la complétion (signature finale).
    Relations :
        user (User): Utilisateur créateur du document.
        points (List[Points]): Liste des points de signature associés au document.
        signatures (List[Signatures]): Liste des signatures apposées sur le document.
    Méthodes :
        __repr__() -> str:
    """
    __tablename__ = '20_documents_a_signer'
    
    id = mapped_column(Integer, primary_key=True)
    doc_nom = mapped_column(String(255), nullable=False)            # nom_définitif du document
    doc_type = mapped_column(String(50), nullable=False)            # contrat, convention, etc.
    doc_sous_type = mapped_column(String(100), nullable=True)
    priorite = mapped_column(Integer, default=0)                    # -1 : basse, 0 : normale, 1 : haute, 2 : urgente
    echeance = mapped_column(Integer, nullable=False)               # 1-15 jours
    duree_archivage = mapped_column(Integer, nullable=True)         # durée d'archivage
    description = mapped_column(Text, nullable=True)
    
    # Métadonnées techniques
    chemin_fichier = mapped_column(String(500), nullable=False)     # chemin du fichier
    hash_fichier = mapped_column(String(64), nullable=False)        # hash du fichier pour intégrité
    id_user = mapped_column(Integer, ForeignKey(PK_USER), nullable=True) # identifiant créateur
    cree_at = mapped_column(DateTime, default=func.now())
    
    # Statuts et dates
    status = mapped_column(Integer, nullable=False, default=0)      # -2: annulé, -1: expiré, 0: en attente, 1: signé
    limite_signature = mapped_column(DateTime, Computed("DATE_ADD(cree_at, INTERVAL echeance DAY)"), nullable=True)
    complete_at = mapped_column(DateTime, nullable=True)
    
    # Relations
    user = relationship("User", back_populates="documents")
    points = relationship("Points", back_populates="document", cascade=CASCADE)
    invitation = relationship("Invitation", back_populates="document", cascade=CASCADE)

    def __repr__(self) -> str:
        """
        Représentation textuelle de l'objet DocToSigne.
        Exemple :
            ```python
            print(doc)
            ```
            ```console
            <DocToSigne(id=1, doc_nom='25092024_001_0001_Contr', status=0)>
            ```
        """
        return f"<DocToSigne(id={self.id}, doc_nom={self.doc_nom}, status={self.status})>"
    
    def download(self) -> Optional[io.BytesIO]:
        """
        Fonction pour télécharger le fichier du document à signer.
        Utilise la fonction download_file du module docs.py.
        Arguments : None
        Returns :
            io.BytesIO: Fichier binaire téléchargé, ou None si échec.
        Exemple :
            ```python
            file = doc.download()
            # or
            doc.download()
            ```
        """
        try:
            if self.chemin_fichier:
                with open(self.chemin_fichier, 'rb') as f:
                    file_data = f.read()
                    return io.BytesIO(file_data)
        except Exception:
            return None

class Points(Base):
    """
    Représente un point de signature sur un document PDF.
    Attributs :
        id (int): Identifiant unique du point de signature.
        id_document (int): Identifiant du document associé.
        x (Decimal): Position X en pixels (1/72 inch).
        y (Decimal): Position Y en pixels (1/72 inch).
        page_num (int): Numéro de page (1-indexed).
        id_user (int): Identifiant de l'utilisateur signataire.
        status (int): Statut du point de signature (-2: annulé, -1: expiré, 0: en attente, 1: signé).
        signe_at (datetime): Date et heure de la signature (si signée).
    Relations :
        document (DocToSigne): Document associé au point de signature.
        user (User): Utilisateur signataire.
        signature (Signatures): Signature apposée sur ce point (si signée).
    Méthodes :
        __repr__() -> str: Représentation textuelle de l'objet Points.
    """
    __tablename__ = '21_points'
    
    id = mapped_column(Integer, primary_key=True)
    id_document = mapped_column(Integer, ForeignKey(PK_DOC_TO_SIGNE), nullable=False)
    
    # Position sur le PDF
    x = mapped_column(Numeric(10, 2), nullable=False)           # position X en pixels (1/72 inch)
    y = mapped_column(Numeric(10, 2), nullable=False)           # position Y en pixels (1/72 inch)
    page_num = mapped_column(Integer, nullable=False)           # numéro de page (1-indexed)
    
    # Signataire assigné
    id_user = mapped_column(Integer, ForeignKey(PK_USER), nullable=False)
    
    # Statut
    status = mapped_column(Integer, default=0)                  # -2: annulé, -1: expiré, 0: en attente, 1: signé
    id_signature = mapped_column(Integer, ForeignKey('22_signatures.id'), nullable=True)
    signe_at = mapped_column(DateTime, nullable=True)
    
    # Relations
    document = relationship("DocToSigne", back_populates="points")
    user = relationship("User", back_populates="points")
    signature = relationship("Signatures", back_populates="points", uselist=False)

    def __repr__(self) -> str:
        """
        Représentation textuelle de l'objet Points.
        Exemple :
            ```python
            print(point)
            ```
            ```console
            <Points(id=1, id_document=5, page_num=2, coordonnées=(150.00, 300.00), id_user=3, status=0)>
            ```
        """
        return (f"<Points(id={self.id}, id_document={self.id_document}, page_num={self.page_num}, "
            f"coordonnées=({self.x}, {self.y}), id_user={self.id_user}, status={self.status})>")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'objet Points en dictionnaire.
        Utile pour la sérialisation JSON.
        Returns:
            dict: Dictionnaire représentant l'objet Points.
        Exemple d'utilisation :
            ```python
            point_dict = point.to_dict()
            ```
        """
        point: Dict[str, Any] = {
            "id": self.id,
            "id_document": self.id_document,
            "x": float(self.x),
            "y": float(self.y),
            "page_num": self.page_num,
            "id_user": self.id_user,
            "status": self.status,
            "signe_at": self.signe_at.isoformat() if self.signe_at else None
        }
        return point

class Signatures(Base):
    """
    Représente une signature apposée sur un document.
    Attributs :
        id (int): Identifiant unique de la signature.
        signe_at (datetime): Date et heure de la signature.
        signature_hash (str): Hash de la signature pour vérification.
        ip_addresse (str): Adresse IP de l'utilisateur au moment de la signature.
        user_agent (str): User-Agent du navigateur au moment de la signature.
        status (int): Statut de la signature (0: en attente, 1: signé, -1: annulé, -2: expiré).
        svg_graph (str): Données SVG de la signature graphique (optionnel).
        data_graph (str): Données JSON des coordonnées de la signature graphique (optionnel).
        largeur_graph (int): Largeur de la zone de signature graphique (optionnel).
        hauteur_graph (int): Hauteur de la zone de signature graphique (optionnel).
        timestamp_graph (datetime): Horodatage de la signature graphique (optionnel).
    Relations :
        document (DocToSigne): Document associé à la signature.
        points (List[Points]): Liste des points de signature associés à cette signature.
        user (User): Utilisateur ayant signé.
    Méthodes :
        __repr__() -> str: Représentation textuelle de l'objet Signatures.
    """
    __tablename__ = '22_signatures'
    
    # Données principales
    id = mapped_column(Integer, primary_key=True)
    
    # Données de signature
    signe_at = mapped_column(DateTime, default=func.now())
    signature_hash = mapped_column(String(128), nullable=False)     # hash de la signature
    ip_addresse = mapped_column(String(45), nullable=True)
    user_agent = mapped_column(String(1024), nullable=True)
    status = mapped_column(Integer, default=0)                      # 0: en attente, 1: signé, -1: annulé, -2: expiré
    
    # Signature graphique - AJOUT
    svg_graph = mapped_column(Text, nullable=True)                  # Format SVG de la signature tracée
    data_graph = mapped_column(Text, nullable=True)                 # JSON coordinates (alternatif/backup)
    largeur_graph = mapped_column(Integer, nullable=True)           # Largeur de la zone de signature
    hauteur_graph = mapped_column(Integer, nullable=True)           # Hauteur de la zone de signature
    timestamp_graph = mapped_column(DateTime, default=func.now())   # Horodatage de la signature graphique

    # Relations
    points = relationship("Points", back_populates="signature")

    def __repr__(self) -> str:
        """
        Représentation textuelle de l'objet Signatures.
        Exemple :
            ```python
            print(signature)
            ```
            ```console
            <Signatures(id=1, id_user=3, signe_at=2024-09-25 14:30:00, statut=1)>
            ```
        """
        return (f"<Signatures(id={self.id}, id_user={self.id_user}, signe_at={self.signe_at}, "
            f"status={self.status})>")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'objet Signatures en dictionnaire.
        Utile pour la sérialisation JSON.
        Returns:
            dict: Dictionnaire représentant l'objet Signatures.
        Exemple d'utilisation :
            ```python
            signature_dict = signature.to_dict()
            ```
        """
        signature: Dict[str, Any] = {
            "id": self.id,
            "signe_at": self.signe_at.isoformat() if self.signe_at else None,
            "signature_hash": self.signature_hash,
            "ip_addresse": self.ip_addresse,
            "user_agent": self.user_agent,
            "status": self.status,
            "svg_graph": self.svg_graph,
            "data_graph": self.data_graph,
            "largeur_graph": self.largeur_graph,
            "hauteur_graph": self.hauteur_graph,
            "timestamp_graph": self.timestamp_graph.isoformat() if self.timestamp_graph else None
        }
        return signature
    
class Invitation(Base):
    """
    Représente une invitation à signer un document.
    Attributs :
        id (int): Identifiant unique de l'invitation.
        id_document (int): Identifiant du document à signer.
        id_user (int): Identifiant de l'utilisateur invité.
        token (str): Token sécurisé pour le lien d'invitation.
        envoye_at (datetime): Date et heure d'envoi de l'invitation.
        expire_at (datetime): Date et heure d'expiration de l'invitation.
        accede_at (datetime): Date et heure de la première consultation (nullable).
        signe_at (datetime): Date et heure de la signature (nullable).
        mail_envoye (bool): Indique si l'e-mail a été envoyé.
        mail_compte (int): Nombre de tentatives d'envoi d'e-mail.
    Relations :
        document (DocToSigne): Document associé à l'invitation.
        user (User): Utilisateur invité.
    Méthodes :
        __repr__() -> str: Représentation textuelle de l'objet Invitation.
    """
    __tablename__ = '23_invitations'
    
    # Données principales
    id = mapped_column(Integer, primary_key=True)
    id_document = mapped_column(Integer, ForeignKey(PK_DOC_TO_SIGNE), nullable=False)
    id_user = mapped_column(Integer, ForeignKey(PK_USER), nullable=False)

    # Token sécurisé pour le lien
    token = mapped_column(String(128), unique=True, nullable=False)
    
    # Statuts et dates
    envoye_at = mapped_column(DateTime, default=func.now())
    expire_at = mapped_column(DateTime, nullable=False)
    accede_at = mapped_column(DateTime, nullable=True)          # première consultation
    signe_at = mapped_column(DateTime, nullable=True)
    
    # Méta-données et OTP de validation
    mail_envoye = mapped_column(Boolean, default=False)
    mail_compte = mapped_column(Integer, default=0)
    code_otp = mapped_column(String(6), nullable=True)        # OTP pour validation finale
    
    # Relations
    document = relationship("DocToSigne", back_populates="invitation")
    user = relationship("User")

    def __repr__(self) -> str:
        """
        Représentation de l'invitation.
        Exemple :
            ```python
            print(invitation)
            ```
            ```console
            <Invitation(id=1, document_id=5, user_id=3, envoye_at=2024-09-25 14:30:00, expire_at=2024-10-02 14:30:00)>
            ```
        """
        return f"<Invitation(id={self.id}, document_id={self.id_document}, user_id={self.id_user}, envoye_at={self.envoye_at}, expire_at={self.expire_at})>"

class AuditLog(Base):
    """
    Représentation de l'historique des actions sur les documents à signer.
    Attributs :
        id (int): Identifiant unique de l'entrée de log.
        id_document (int): Identifiant du document concerné.
        id_user (int): Identifiant de l'utilisateur ayant effectué l'action (nullable).
        action (int): Type d'action effectuée (-2: annulé, -1: expiré, 0: créé, 1: consulté, 2: signé, 3: expédié).
        details (str): Détails supplémentaires sur l'action (nullable).
        ip_addresse (str): Adresse IP de l'utilisateur au moment de l'action (nullable).
        user_agent (str): User-Agent du navigateur au moment de l'action (nullable).
        timestamp (datetime): Date et heure de l'action.
    Relations :
        document (DocToSigne): Document concerné par l'action.
        user (User): Utilisateur ayant effectué l'action (nullable).
    Méthodes :
        __repr__() -> str: Représentation textuelle de l'objet AuditLog.
    """
    __tablename__ = '24_audit_logs'
    
    # Données principales
    id = mapped_column(Integer, primary_key=True)
    id_document = mapped_column(Integer, ForeignKey(PK_DOC_TO_SIGNE), nullable=False)
    id_user = mapped_column(Integer, ForeignKey(PK_USER), nullable=True)

    # Événement
    action = mapped_column(Integer, nullable=False)  # -2: annuler, -1: expirer, 0: créer, 1: consulter, 2: signer, 3: expédier
    details = mapped_column(String(255), nullable=True)
    
    # Contexte technique
    ip_addresse = mapped_column(String(45), nullable=True)
    user_agent = mapped_column(String(1024), nullable=True)
    timestamp = mapped_column(DateTime, default=func.now())
    
    # Relations
    document = relationship("DocToSigne")
    user = relationship("User")

    def __repr__(self) -> str:
        """
        Représentation textuelle de l'objet AuditLog.
        Exemple :
            ```python
            print(audit_log)
            ```
            ```console
            <AuditLog(id=1, consultation le 2024-09-25 14:30:00)>
            ```
        """
        action = {
            -2: "annulation",
            -1: "expiré",
             0: "création",
             1: "consultation",
             2: "signature",
             3: "expédition"
        }.get(self.action, "inconnu")
        return f"<AuditLog(id={self.id}, {action} le {self.timestamp})>"

class ViewPoints:
    """
    Classe de vue 
    Attributs :
        point: Points: Instance du point de signature.
        user: User: Instance de l'utilisateur signataire.
        signature: Signatures: Instance de la signature apposée (si signée).
        user_mail: str: Adresse e-mail de l'utilisateur (pour affichage).
        user_complete_name: str: Nom complet de l'utilisateur (pour affichage).
    Méthodes :
        __init__(self, points: List[Points]) -> None:
            Initialise les attributs de la classe.
    """

    def __init__(self, points: List[Points]) -> None:
        """
        Récupère les informations liées aux points de signature et les utilisateurs et signatures associées.
        Arguments :
            points (List[Points]): Liste des points de signature.
        Exemple d'utilisation :
            ```python
            view_points = ViewPoints(points)
            ```
        """
        self.points: List[Any] = []
        for p in points:
            user = g.db_session.query(User).filter(User.id == p.id_user).first()
            signature = g.db_session.query(Signatures).filter(Signatures.id == p.id_signature).first()
            point_list: List[Any] = [p, user, signature]
            self.points.append(point_list)

    def __repr__(self) -> str:
        """
        Représentation textuelle de l'objet ViewPoints.
        Exemple :
            ```python
            print(view_points)
            ```
            ```console
            <ViewPoints(nombre de points=3)>
            ```
        """
        return f"<ViewPoints(nombre de points={len(self.points)})>"
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """
        Convertit la liste des points en une liste de dictionnaires.
        Utile pour la sérialisation JSON.
        Returns:
            list: Liste de dictionnaires représentant les points.
        Exemple d'utilisation :
            ```python
            points_dict = view_points.to_dict()
            ```
        """
        points_list: List[Dict[str, Any]] = []
        for p, u, s in self.points:
            point: Dict[str, Any] = {
                "user": u.to_dict() if u else None,
                "user_mail": u.mail if u else None,
                "user_complete_name": f'{u.prenom} {u.nom}' if u else None,
                "point": p.to_dict(),
                "signature": s.to_dict() if s else None
            }
            points_list.append(point)
        return points_list
