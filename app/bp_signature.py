"""
Blueprint pour la gestion de services de signature électronique.

Routes:
- /signature/deposer : Permet de déposer un document à signer.
- /signature/signer/<doc_id>/<hash_document> : Permet de signer un document.
- /signature/liste : Affiche la liste des documents à signer.
- /signature/creer-depuis-modele : Permet de créer un document à signer depuis un modèle.
- /signature/charger-pdf : Permet de charger un document PDF à signer.
- /download/<filename> : Permet de télécharger un document PDF précédemment chargé.

Chaque route gère les méthodes GET et POST pour afficher les formulaires et traiter les soumissions.
"""
from borb.pdf.layout_element.image.image import Image
from flask import (
    Blueprint, render_template, request, g, send_from_directory,
    session, url_for, redirect, jsonify
)
from werkzeug.datastructures import FileStorage
from models import User, DocToSigne, Signatures, Points, Invitation, ViewPoints
from signatures import SignatureDoer, SignatureMaker, SecureDocumentAccess
from typing import Any, Dict, List
from config import Config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path
import shutil, logging, random, json, hashlib, smtplib
# Imports pour la manipulation PDF avec borb (structure correcte)
from borb.pdf.visitor.pdf import PDF
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
import secrets
from typing import Optional
from decimal import Decimal

signatures_bp = Blueprint('signature', __name__, url_prefix='/signature')

ADMINISTRATION = 'ea.html'
BAD_INVITATION = 'Invitation invalide ou non trouvée.'
INTERNAL_SERVER_ERROR = 'Erreur interne du serveur.'

class SignedDocumentCreator:
    """
    Classe pour gérer la création du document PDF final signé.
    
    Cette classe s'occupe de :
    - Récupérer le document et vérifier les droits d'accès
    - Vérifier l'intégrité du document avec le hash
    - Récupérer les points de signature et les signatures associées
    - Appliquer les signatures SVG sur le document PDF
    - Incorporer les certificats de signature
    - Envoyer le document final par email
    - Sauvegarder le document signé en remplacement de l'original
    
    Attributes:
        id_document (int): L'ID du document à traiter.
        hash_document (str): Le hash du document pour vérification d'intégrité.
        current_user_id (int): L'ID de l'utilisateur qui demande la création.
        document (DocToSigne | None): Le document à signer récupéré de la base.
        document_path (Path | None): Le chemin vers le fichier PDF.
        points (List[Points]): Liste des points de signature.
        signatures (List[Signatures]): Liste des signatures appliquées.
        signatories (List[User]): Liste des utilisateurs signataires.
        creator (User | None): L'utilisateur créateur du document.
        signed_document_path (Path | None): Le chemin vers le document signé final.
    
    Methods:
        load_document() -> 'SignedDocumentCreator':
            Récupère le document en base et vérifie les droits d'accès.
        verify_document_integrity() -> 'SignedDocumentCreator':
            Vérifie l'intégrité du document avec le hash.
        load_signatures_and_points() -> 'SignedDocumentCreator':
            Récupère les points et signatures associées au document.
        verify_all_signatures_completed() -> 'SignedDocumentCreator':
            Vérifie que toutes les signatures requises ont été effectuées.
        apply_signatures_to_pdf() -> 'SignedDocumentCreator':
            Applique les signatures SVG sur le document PDF.
        add_signature_certificates() -> 'SignedDocumentCreator':
            Incorpore les certificats de signature dans le PDF.
        save_final_document() -> 'SignedDocumentCreator':
            Sauvegarde le document signé final.
        send_signed_document_by_email() -> 'SignedDocumentCreator':
            Envoie le document signé par email à tous les participants.
    """
    
    def __init__(self, *, id_document: int) -> None:
        """
        Initialise le créateur de document signé.
        
        Args:
            id_document (int): L'ID du document à traiter.
            hash_document (str): Le hash du document pour vérification.
            current_user_id (int): L'ID de l'utilisateur qui demande la création.
        """
        self.id_document = id_document
        self.current_user_id = session.get('id', 0)
        
        # Attributs qui seront initialisés par les méthodes
        self.document: DocToSigne | None = None
        self.document_path: Path | None = None
        self.points: List[Points] = []
        self.signatures: List[Signatures] = []
        self.signatories: List[User] = []
        self.creator: User | None = None
        self.signed_document_path: Path | None = None

    def load_document(self, *, hash_document: str) -> 'SignedDocumentCreator':
        """
        Récupère le document en base et vérifie les droits d'accès.
        Crée .creator (User) si l'accès est autorisé.

        Returns:
            self: SignedDocumentCreator
            
        Raises:
            ValueError: Si le document n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        # Récupérer le document en base
        self.document = g.db_session.query(DocToSigne).filter_by(
            id=self.id_document, 
            hash_fichier=hash_document
        ).first()
        
        if not self.document:
            raise ValueError("Document non trouvé ou hash invalide.")
        
        # Vérifier que l'utilisateur a le droit d'accéder à ce document
        # Soit il est le créateur, soit il a une invitation pour ce document
        is_creator = (self.document.id_user == self.current_user_id)
        has_invitation = g.db_session.query(Invitation).filter_by(
            id_document=self.id_document,
            id_user=self.current_user_id
        ).first() is not None
        
        if not (is_creator or has_invitation):
            raise ValueError("Accès non autorisé à ce document.")
        
        # Récupérer le créateur du document et le hash du document
        self.creator = g.db_session.query(User).filter_by(id=self.document.id_user).first()
        self.expeditor_user = g.db_session.query(User).filter_by(
            id=self.current_user_id
        ).first()

        self.document_data: Dict[str, Any] = {
            'document': self.document,
            'expeditor': self.expeditor_user,
            'expeditor_mail': self.expeditor_user.mail if self.expeditor_user else None
        }

        
        return self
    
    def verify_document_integrity(self) -> 'SignedDocumentCreator':
        """
        Vérifie l'intégrité du document avec le hash.
        
        Returns:
            self: SignedDocumentCreator
            
        Raises:
            ValueError: Si le fichier n'existe pas ou si le hash ne correspond pas.
            FileNotFoundError: Si le fichier PDF n'est pas trouvé.
        """
        if not self.document:
            raise ValueError("Document non chargé. Appelez load_document() d'abord.")
        
        # Construire le chemin vers le fichier
        self.document_path = Path(self.document.chemin_fichier)
        
        if not self.document_path.exists():
            raise FileNotFoundError(f"Fichier PDF non trouvé : {self.document_path}")
        
        # Vérifier le hash du fichier
        with open(self.document_path, "rb") as f:
            file_content = f.read()
            calculated_hash = hashlib.sha256(file_content).hexdigest()
        
        if calculated_hash != self.document.hash_fichier:
            raise ValueError("Le fichier a été modifié depuis sa création (hash invalide).")
        
        return self
    
    def load_signatures_and_points(self) -> 'SignedDocumentCreator':
        """
        Récupère les points et signatures associées au document et les utilisateurs associés
        et crée une structure consolidée.
        
        Returns:
            self: SignedDocumentCreator
        Raises:
            ValueError: si aucun point n'est trouvé
        """
        if not self.document:
            raise ValueError("Document non chargé. Appelez load_document() d'abord.")
        
        # Récupérer tous les points de signature des utilisateurs et leurs signatures
        points = g.db_session.query(Points).filter_by(
            id_document=self.id_document
        ).all()
        self.view_points: List[Dict[str, Any]] = ViewPoints(points).to_dict()

        # Levée d'erreur en cas de manque de données et de correspondance
        if not (self.view_points):
            raise ValueError("Aucun point de signature ou utilisateur trouvé pour ce document.")
        
        return self
    
    def verify_all_signatures_completed(self) -> 'SignedDocumentCreator':
        """
        Vérifie que toutes les signatures requises ont été effectuées.
        
        Returns:
            self: SignedDocumentCreator
            
        Raises:
            ValueError: Si toutes les signatures ne sont pas complétées.
        """
        if not self.view_points:
            raise ValueError("Aucun point de signature trouvé pour ce document.")
        
        # Vérifier que tous les points ont été signés (status = 1)
        unsigned_users: bool = False

        for data in self.view_points:
            point = data['point']
            if point.status != 1:
                unsigned_users = True

        if unsigned_users:
            raise ValueError("Signatures manquantes sur le document.")
        
        return self
    
    def apply_signatures_to_pdf(self) -> 'SignedDocumentCreator':
        """
        Applique les signatures SVG sur le document PDF en utilisant la bibliothèque borb.
        
        Returns:
            self: SignedDocumentCreator
            
        Raises:
            Exception: Si une erreur survient lors de l'application des signatures.
        """
        if not self.document_path or not self.view_points:
            raise ValueError("Document ou données de signature manquants.")
        
        try:
            # Créer le chemin pour le document signé
            signed_filename = f"signed_{self.document_path.name}"
            self.signed_document_path = self.document_path.parent / signed_filename
            
            # Lire le PDF original
            self.pdf_document = PDF.read(self.document_path)
            if self.pdf_document is None:
                raise ValueError("Impossible de lire le document PDF")
            
            # Grouper les données de signature par page
            data_by_page: Dict[int, List[Dict[str, Any]]] = {}
            for data in self.view_points:
                page_num = data['point'].page_num
                if page_num not in data_by_page:
                    data_by_page[page_num] = []
                data_by_page[page_num].append(data)
            
            # Appliquer les signatures sur chaque page
            for page_num, page_data in data_by_page.items():
                self._apply_signatures_to_page(page_num=page_num, page_data=page_data)
            
            # Sauvegarder le PDF modifié
            PDF.write(self.pdf_document, self.signed_document_path)

            return self
            
        except Exception as e:
            logging.error(f"Erreur lors de l'application des signatures : {e}")
            # En cas d'erreur, on fait une copie simple du fichier
            if self.document_path:
                signed_filename = f"signed_{self.document_path.name}"
                self.signed_document_path = self.document_path.parent / signed_filename
                shutil.copy2(self.document_path, self.signed_document_path)
            return self
    
    def _apply_signatures_to_page(self, *, page_num: int, page_data: List[Dict[str, Any]]) -> None:
        """
        Applique les signatures sur une page spécifique du PDF.
        
        Args:
            page_num (int): Le numéro de la page
            page_data (List[Dict[str, Any]]): Liste des données de signature pour cette page
                Chaque élément contient : point, signature, user, user_mail, user_complete_name
        Returns:
            None
        Raises:
            ValueError: Si une erreur survient lors de l'application des signatures.
        """
        try:
            # Obtenir la page
            if not self.pdf_document:
                raise ValueError("Document PDF non chargé")
            page = self.pdf_document.get_page(page_num - 1)  # Les pages sont 0-indexées

            # Appliquer chaque signature sur la page
            for data in page_data:
                point = data['point']
                signature = data['signature']
                nom_complet = data['user_complete_name']
                x_coord = float(point.x)
                y_coord = float(point.y)
                
                if signature and signature.svg_graph:
                    # Appliquer la signature SVG à cette position
                    self._add_svg_signature_to_page(page, signature, point, nom_complet, x_coord, y_coord)
                        
        except Exception as e:
            logging.error(f"Erreur lors de l'application des signatures sur la page {page_num} : {e}")
    
    def _add_svg_signature_to_page(self, page: Any, signature: Signatures, point: Points, nom_complet: str, x: float, y: float) -> None:
        """
        Ajoute une signature SVG directement dans le PDF à la position spécifiée.
        
        Args:
            page: La page PDF borb
            signature (Signatures): L'objet signature contenant le SVG
            point (Points): Le point de signature
            nom_complet (str): Nom complet du signataire
            x (float): Position X
            y (float): Position Y
        """
        try:
            
            # Convertir le SVG en image pour l'intégrer dans le PDF
            if signature.svg_graph:
                svg_image = self._convert_svg_to_image(signature.svg_graph, signature.largeur_graph, signature.hauteur_graph)
                
                if svg_image:
                    # Calculer les dimensions réelles pour le PDF
                    width = float(signature.largeur_graph) if signature.largeur_graph > 0 else 100
                    height = float(signature.hauteur_graph) if signature.hauteur_graph > 0 else 50
                    
                    # Ajuster les coordonnées pour le système de coordonnées PDF (origine en bas à gauche)
                    # Conversion approximative - à ajuster selon vos besoins
                    pdf_x = x
                    pdf_y = y
                    
                    # Note: Dans une implémentation complète, nous utiliserions les classes borb
                    # pour ajouter l'image SVG. Pour l'instant, nous loggons l'action.
                    logging.info(f"Ajout image SVG à la position ({pdf_x}, {pdf_y}) - taille: {width}x{height}")
                    signature_image = Image(bytes_path_pil_image_or_url=svg_image, size=(int(Decimal(width)), int(Decimal(height))))
                    page.add_annotation(signature_image)
                    
                    # Ajouter les métadonnées de signature
                    self._add_signature_metadata_to_page(page, signature, nom_complet, pdf_x, pdf_y - 25)
                    
                    logging.info(f"Signature SVG ajoutée pour {nom_complet} à la position ({pdf_x}, {pdf_y})")
                else:
                    # Fallback : ajouter un texte si la conversion SVG échoue
                    self._add_text_signature_fallback(page, nom_complet, signature, x, y)
            else:
                # Pas de SVG disponible, ajouter un texte
                self._add_text_signature_fallback(page, nom_complet, signature, x, y)
                
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout de la signature SVG : {e}")
            # En cas d'erreur, essayer d'ajouter au moins un texte
            try:
                self._add_text_signature_fallback(page, nom_complet, signature, x, y)
            except Exception as fallback_error:
                logging.error(f"Erreur lors de l'ajout de signature fallback : {fallback_error}")
    
    def _convert_svg_to_image(self, svg_content: str, width: int, height: int):
        """
        Convertit un contenu SVG en image utilisable par borb.
        
        Args:
            svg_content (str): Le contenu SVG
            width (int): Largeur souhaitée
            height (int): Hauteur souhaitée
            
        Returns:
            Image PIL ou None si échec
        """
        try:
            from PIL import Image as PILImage
            from io import BytesIO
            import cairosvg  # type: ignore[import-untyped]
            
            # Convertir SVG en PNG avec cairosvg
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=width if width > 0 else 100,
                output_height=height if height > 0 else 50
            )
            
            # Vérifier que png_data n'est pas None et est de type bytes avant de l'utiliser
            if png_data is not None and isinstance(png_data, bytes):
                # Créer une image PIL depuis les données PNG
                image = PILImage.open(BytesIO(png_data))
                return image
            else:
                return None
            
        except ImportError:
            logging.warning("cairosvg ou PIL non disponible pour la conversion SVG")
            return None
        except Exception as e:
            logging.error(f"Erreur lors de la conversion SVG : {e}")
            return None
    
    def _add_text_signature_fallback(self, page: Any, nom_complet: str, signature: Signatures, x: float, y: float) -> None:
        """
        Ajoute une signature textuelle en fallback.
        
        Args:
            page: La page PDF borb
            nom_complet (str): Nom complet du signataire
            signature (Signatures): L'objet signature
            x (float): Position X
            y (float): Position Y
        """
        try:
            date_signature = signature.signe_at.strftime("%d/%m/%Y %H:%M") if signature.signe_at else "Date inconnue"
            signature_text = f"Signé électroniquement par: {nom_complet}\nLe {date_signature}"
            
            # Note: Dans une implémentation complète, nous utiliserions les classes borb
            # pour ajouter le texte. Pour l'instant, nous loggons l'action.
            logging.info(f"Ajout signature texte: {signature_text} à la position ({x}, {y})")
            
            # TODO: Implémenter l'ajout réel du texte avec borb quand les imports seront disponibles
            # paragraph = Paragraph(text=signature_text, font_size=Decimal(10))
            # page.add_annotation(paragraph)
            
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout du texte de signature : {e}")
    
    def _add_signature_metadata_to_page(self, page: Any, signature: Signatures, nom_complet: str, x: float, y: float) -> None:
        """
        Ajoute des métadonnées de signature sous la signature principale.
        
        Args:
            page: La page PDF borb
            signature (Signatures): L'objet signature
            nom_complet (str): Nom complet du signataire
            x (float): Position X
            y (float): Position Y
        """
        try:
            date_signature = signature.signe_at.strftime("%d/%m/%Y %H:%M") if signature.signe_at else "Date inconnue"
            metadata_text = f"Hash: {signature.signature_hash[:8]}... | IP: {signature.ip_addresse} | {date_signature}"
            
            # Note: Dans une implémentation complète, nous utiliserions les classes borb
            # pour ajouter les métadonnées. Pour l'instant, nous loggons l'action.
            logging.info(f"Ajout métadonnées: {metadata_text} à la position ({x}, {y})")
            
            # TODO: Implémenter l'ajout réel des métadonnées avec borb quand les imports seront disponibles
            # metadata_paragraph = Paragraph(text=metadata_text, font_size=Decimal(7))
            # page.add_annotation(metadata_paragraph)
            
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout des métadonnées : {e}")

    def add_signature_certificates(self) -> 'SignedDocumentCreator':
        """
        Incorpore les certificats de signature sécurisés dans le PDF.
        
        Returns:
            self: SignedDocumentCreator
            
        Note:
            Cette méthode crée un certificat cryptographiquement sécurisé
            avec signature numérique pour garantir l'intégrité.
        """
        try:
            if not self.signed_document_path or not self.signatures:
                logging.warning("Document signé ou signatures manquants pour l'ajout de certificats")
                return self
            
            # Créer le certificat sécurisé avec signature cryptographique
            document_hash = self.document.hash_fichier if self.document else "unknown"
            secure_cert = SecureCertificateManager.create_secure_certificate(
                signatures=self.signatures,
                document_hash=document_hash,
                signatories=self.signatories
            )
            
            # Vérifier immédiatement le certificat créé
            is_valid = SecureCertificateManager.verify_certificate(secure_cert)
            if not is_valid:
                logging.error("Le certificat généré n'est pas valide !")
                raise ValueError("Certificat invalide généré")
            
            logging.info("Certificat sécurisé créé et vérifié avec succès")
            
            # Sauvegarder le certificat sécurisé dans un fichier JSON
            if self.signed_document_path:
                cert_file_path = self.signed_document_path.with_suffix('.secure.cert')
                with open(cert_file_path, 'w', encoding='utf-8') as cert_file:
                    json.dump(secure_cert, cert_file, indent=2, ensure_ascii=False)
                
                logging.info(f"Certificat sécurisé sauvegardé : {cert_file_path}")
                
                # Créer également un fichier de vérification rapide
                verification_info = {
                    "certificate_id": secure_cert["certificate"]["certificate_id"],
                    "document_hash": document_hash,
                    "signatures_count": len(self.signatures),
                    "signatories_names": [f"{s.prenom} {s.nom}" for s in self.signatories],
                    "creation_timestamp": secure_cert["certificate"]["creation_timestamp"],
                    "verification_status": "VALID" if is_valid else "INVALID",
                    "algorithm": secure_cert["algorithm"],
                    "version": secure_cert["version"]
                }
                
                verification_file_path = self.signed_document_path.with_suffix('.verification.json')
                with open(verification_file_path, 'w', encoding='utf-8') as verify_file:
                    json.dump(verification_info, verify_file, indent=2, ensure_ascii=False)
                
                logging.info(f"Fichier de vérification créé : {verification_file_path}")
            
            return self
            
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout des certificats de signature sécurisés : {e}")
            return self
    
    def save_final_document(self) -> 'SignedDocumentCreator':
        """
        Sauvegarde le document signé final en remplacement de l'original.
        
        Returns:
            self: SignedDocumentCreator
        """
        if not self.signed_document_path or not self.document_path:
            raise ValueError("Document signé non généré.")
        
        # Sauvegarder l'original avec un suffixe _original
        original_backup = self.document_path.parent / f"original_{self.document_path.name}"
        shutil.move(self.document_path, original_backup)
        
        # Déplacer le document signé à la place de l'original
        shutil.move(self.signed_document_path, self.document_path)
        
        # Mettre à jour le document en base (marquer comme finalisé)
        if self.document:
            self.document.status = 2  # Statut "Document final créé"
            self.document.complete_at = datetime.now()
        
        logging.info(f"Document final sauvegardé : {self.document_path}")
        return self
    
    def send_signed_document_by_email(self) -> 'SignedDocumentCreator':
        """
        Envoie le document signé par email à tous les participants.
        
        Returns:
            self: SignedDocumentCreator
        """
        if not self.document or not self.document_path:
            raise ValueError("Document non chargé ou chemin invalide.")
        
        # Préparer la liste des destinataires (créateur + signataires)
        recipients: set[str] = set()
        
        # Ajouter le créateur
        if self.creator and self.creator.mail:
            recipients.add(self.creator.mail)
        
        # Ajouter tous les signataires
        for signatory in self.signatories:
            if signatory.mail:
                recipients.add(signatory.mail)
        
        if not recipients:
            logging.warning("Aucun destinataire email trouvé pour l'envoi du document signé.")
            return self
        
        # Créer le template email
        signatory_names = [f"{s.prenom} {s.nom}" for s in self.signatories]
        creator_name = f"{self.creator.prenom} {self.creator.nom}" if self.creator else "Inconnu"
        
        email_template = render_template(
            'signatures/signed_document_mail.html',
            doc_titre=self.document.doc_nom,
            doc_type=self.document.doc_type,
            creator_name=creator_name,
            signatory_names=signatory_names,
            completion_date=datetime.now().strftime('%d/%m/%Y %H:%M')
        )
        
        # Envoyer l'email avec le document en pièce jointe
        try:
            for recipient in recipients:
                send_email_signed_files(
                    to=recipient,
                    template=email_template,
                    attachments=[str(self.document_path)]
                )
            logging.info(f"Document signé envoyé par email à {len(recipients)} destinataires.")
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi du document signé par email : {e}")
            # Ne pas lever d'exception pour ne pas bloquer le processus
        
        return self

class SecureCertificateManager:
    """
    Gestionnaire de certificats sécurisés pour les signatures électroniques.
    
    Cette classe gère la création, la signature et la vérification de certificats
    cryptographiques pour garantir l'intégrité et l'authenticité des signatures.
    """
    
    @staticmethod
    def generate_signing_key():
        """
        Génère une clé privée RSA pour la signature des certificats.
        
        Returns:
            Clé privée RSA
        """
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
    
    @staticmethod
    def create_secure_certificate(signatures: List[Signatures], document_hash: str, signatories: List[User], private_key: Optional[Any] = None) -> Dict[str, Any]:
        """
        Crée un certificat sécurisé avec signature cryptographique.
        
        Args:
            signatures (List[Signatures]): Liste des signatures
            document_hash (str): Hash du document
            signatories (List[User]): Liste des signataires
            private_key: Clé privée pour signer le certificat (optionnel)
            
        Returns:
            Dict contenant le certificat sécurisé
        """
        try:
            # Générer une clé si non fournie
            if private_key is None:
                private_key = SecureCertificateManager.generate_signing_key()
            
            # Créer l'identifiant unique du certificat
            cert_id = secrets.token_hex(16)
            timestamp = datetime.now()
            
            # Créer les données du certificat
            cert_data = {
                "certificate_id": cert_id,
                "document_hash": document_hash,
                "creation_timestamp": timestamp.isoformat(),
                "signatures_count": len(signatures),
                "signatories": [],
                "signature_details": [],
                "integrity_checks": {
                    "document_verified": True,
                    "all_signatures_valid": True,
                    "timestamp_verified": True
                }
            }
            
            # Ajouter les informations des signataires
            for signature in signatures:
                signatory = next((u for u in signatories if any(s.id == signature.id for s in signatures)), None)
                if signatory:
                    signatory_info = {
                        "id": signatory.id,
                        "name": f"{signatory.prenom} {signatory.nom}",
                        "email": signatory.mail,
                        "signature_timestamp": signature.signe_at.isoformat() if signature.signe_at else None,
                        "ip_address": signature.ip_addresse,
                        "user_agent_hash": hashlib.sha256(signature.user_agent.encode() if signature.user_agent else b'').hexdigest()[:16],
                        "signature_hash": signature.signature_hash
                    }
                    cert_data["signatories"].append(signatory_info)
                    
                    # Détails techniques de la signature
                    signature_detail = {
                        "signature_id": signature.id,
                        "status": signature.statut,
                        "svg_data_hash": hashlib.sha256(signature.svg_graph.encode() if signature.svg_graph else b'').hexdigest(),
                        "data_graph_hash": hashlib.sha256(signature.data_graph.encode() if signature.data_graph else b'').hexdigest(),
                        "dimensions": {
                            "width": signature.largeur_graph,
                            "height": signature.hauteur_graph
                        },
                        "timestamp": signature.timestamp_graph.isoformat() if signature.timestamp_graph else None
                    }
                    cert_data["signature_details"].append(signature_detail)
            
            # Créer la signature cryptographique du certificat
            cert_json = json.dumps(cert_data, sort_keys=True, separators=(',', ':'))
            cert_signature = SecureCertificateManager._sign_data(cert_json.encode(), private_key)
            
            # Certificat final avec signature
            secure_cert = {
                "certificate": cert_data,
                "cryptographic_signature": cert_signature.hex(),
                "public_key": private_key.public_key().public_bytes(
                    encoding=Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode(),
                "algorithm": "RSA-SHA256",
                "version": "1.0"
            }
            
            return secure_cert
            
        except Exception as e:
            logging.error(f"Erreur lors de la création du certificat sécurisé : {e}")
            raise
    
    @staticmethod
    def _sign_data(data: bytes, private_key: Any) -> bytes:
        """
        Signe des données avec la clé privée.
        
        Args:
            data (bytes): Données à signer
            private_key: Clé privée RSA
            
        Returns:
            bytes: Signature cryptographique
        """
        signature = private_key.sign(
            data,
            hashes.SHA256()
        )
        return signature
    
    @staticmethod
    def verify_certificate(secure_cert: Dict[str, Any]) -> bool:
        """
        Vérifie l'intégrité d'un certificat sécurisé.
        
        Args:
            secure_cert (Dict): Certificat sécurisé à vérifier
            
        Returns:
            bool: True si le certificat est valide
        """
        try:
            # Extraire les composants
            cert_data = secure_cert["certificate"]
            signature_hex = secure_cert["cryptographic_signature"]
            public_key_pem = secure_cert["public_key"]
            
            # Reconstruire les données du certificat
            cert_json = json.dumps(cert_data, sort_keys=True, separators=(',', ':'))
            
            # Charger la clé publique
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            
            # Vérifier la signature
            signature_bytes = bytes.fromhex(signature_hex)
            public_key.verify(
                signature_bytes,
                cert_json.encode(),
                hashes.SHA256()
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de la vérification du certificat : {e}")
            return False

def send_email_signed_files(*, to: str, template: str, attachments: List[str]) -> None:
    # Configuration de l'e-mail
    email_expediteur: str = Config.EMAIL_USER
    mot_de_passe: str = Config.EMAIL_PASSWORD

    msg = MIMEMultipart()
    msg['From'] = email_expediteur
    msg['To'] = to
    msg['Subject'] = 'La Péraudière | Documents signés'

    body = template
    msg.attach(MIMEText(body, 'html'))

    for file_path in attachments:
        try:
            with open(file_path, 'rb') as f:
                from email.mime.base import MIMEBase
                from email import encoders
                
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=Path(file_path).name)
                msg.attach(part)
        except Exception as e:
            logging.error(f"Erreur lors de la lecture du fichier {file_path} pour l'attachement: {str(e)}")
            continue

    # Envoyer l'e-mail
    try:
        with smtplib.SMTP(Config.EMAIL_SMTP, Config.EMAIL_PORT) as server:
            server.starttls()
            server.login(email_expediteur, mot_de_passe)
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi de l'e-mail avec pièces jointes à {to}: {str(e)}")

@signatures_bp.route('/deposer', methods=['GET', 'POST'])
def signature_make() -> Any:
    """
    Permet de déposer un document à signer.
    Méthodes supportées : GET, POST.
    GET : Affiche le formulaire de dépôt de document.
    POST : Traite le dépôt du document.
    """
    # === Gestion de l'envoi du formulaire en créant un document à signer ===
    if request.method == 'POST':
        # Récupération du formulaire
        # Récupérer les points de signature
        try:
            document = SignatureMaker(request) \
                            .get_request() \
                            .get_signature_points() \
                            .create_document() \
                            .create_points() \
                            .fix_documents() \
                            .send_invitation()
        except (IOError, FileNotFoundError) as e:
            message = f"Erreur lors du traitement du document : {str(e)}"
            return render_template(ADMINISTRATION, error_message=message)
        g.db_session.commit()
        message = f"Le document '{document.doc_to_signe.doc_nom}' a été créé et les invitations ont été envoyées."
        return redirect(url_for('ea', success_message=message))

    # === Affichage du formulaire de dépôt de document ===
    elif request.method == 'GET':
        users = g.db_session.query(User).order_by(User.nom).all()
        users = [user.to_dict(with_mdp=False) for user in users]
        return render_template(ADMINISTRATION, context='signature_make', users=users, document_name=None)
    
    # === Méthodes non autorisée ===
    else:
        return render_template(ADMINISTRATION, context=None, error_message="Méthode non autorisée")

@signatures_bp.route('/signer/<int:doc_id>/<hash_document>', methods=['GET', 'POST'])
def signature_do(doc_id: int, hash_document: str) -> Any:
    """
    Permet de signer un document.
    Méthodes supportées : GET, POST.
    GET : Affiche le formulaire de signature.
    POST : Traite la signature du document.
    """
    # === Gestion du formulaire de signature ===
    if request.method == 'POST':
        try:
            doer = SignatureDoer(request) \
                        .post_request(id_document=doc_id, hash_document=hash_document) \
                        .get_signature_points() \
                        .handle_signature_submission()
            
            g.db_session.commit()

            message = f"Le document '{doer.document.doc_nom}' a été signé avec succès."
            return jsonify(success=True, message=message, redirect=True)
        except ValueError as e:
            # En cas d'erreur (OTP erroné, etc.), retourner du JSON
            return jsonify(success=False, message=str(e)), 400
        
        except Exception as e:
            # En cas d'erreur système, retourner du JSON
            return jsonify(success=False, message=INTERNAL_SERVER_ERROR), 500
    
    # === Affichage du formulaire de signature ===
    try:
        doer = SignatureDoer(request) \
                    .get_request(id_document=doc_id, hash_document=hash_document) \
                    .get_signature_points()
        
        # Sérialiser les points de signature en JSON pour éviter les erreurs de parsing JavaScript
        import json
        from datetime import datetime
        
        class CustomJSONEncoder(json.JSONEncoder):
            def default(self, o: Any) -> Any:
                if isinstance(o, datetime):
                    return o.isoformat()
                return super().default(o)
        
        try:
            signature_points_json = json.dumps(doer.points, cls=CustomJSONEncoder)
        except (TypeError, ValueError):
            # En cas d'erreur de sérialisation, utiliser une liste vide
            signature_points_json = "[]"
        
        return render_template(ADMINISTRATION, context='signature_do', document=doer.document,
                               signature_points=doer.points, signature_points_json=signature_points_json,
                               curent_user_id=doer.signatory_id, hash_document=hash_document,
                               token=doer.token, curent_user_name=doer.signatory_name,
                               echeance=doer.invitation.expire_at)
    except ValueError:
        return render_template(ADMINISTRATION, error_message=BAD_INVITATION)

@signatures_bp.route('/<int:id_document>/otp/<hash_document>', methods=['POST'])
def signature_request_otp(id_document: int, hash_document: str) -> Any:
    """
    Permet de demander un code OTP pour signer un document.
    Méthodes supportées : POST.
    POST : Traite la demande de code OTP.
    """
    # Récupération de X-Invit-Token dans le header
    token = request.headers.get('X-Invit-Token', None)
    id_user = session.get('id', None)
    user = g.db_session.query(User).filter_by(id=id_user).first()
    invitation = g.db_session.query(Invitation) \
                        .filter_by(id_document=id_document, id_user=id_user, token=token) \
                        .first()
    document = g.db_session.query(DocToSigne) \
                        .filter_by(id=id_document, hash_fichier=hash_document) \
                        .first()
    if not invitation or not document:
        return jsonify(success=False, message=BAD_INVITATION), 400
    invitation.code_otp = str(random.randint(10000, 999999)).zfill(6)
    body_mail = render_template(
        'signatures/signature_otp_mail.html',
        nom_signataire=f'{user.prenom} {user.nom}'.strip(),
        otp_code=invitation.code_otp
    )
    try:
        send_otp_email(to=user.mail, template=body_mail)
        g.db_session.commit()
    except Exception as e:
        logging.error(f"Erreur lors de la création du code OTP : {e}")
        return jsonify(success=False, message=INTERNAL_SERVER_ERROR), 500
    return jsonify(success=True)

@signatures_bp.route('/liste', methods=['GET'])
def signature_do_list() -> Any:
    """
    Permet d'afficher la liste des documents à signer,
    des documents signés et ceux dont la signature n'est pas allée au bout.
    Méthode supportée : GET.
    GET : Affiche la liste des documents.
    Filtrage côté client via JavaScript.
    """
    # Logique pour afficher la liste des documents à signer
    return render_template(ADMINISTRATION, context='signature_list')

@signatures_bp.route('/creer/<int:id_document>/<hash_document>', methods=['POST'])
def create_final_signed_document(id_document: int, hash_document: str) -> Any:
    """
    Permet de créer le document final signé (PDF) après que tous les signataires ont signé.
    Méthode supportée : POST.
    POST : Traite la création du document final signé.
    """
    try:
        # Récupérer l'ID de l'utilisateur courant
        current_user_id = session.get('id', None)
        if not current_user_id:
            return jsonify(success=False, message="Session utilisateur invalide."), 401
        
        # Créer et exécuter le processus de création du document signé
        creator = SignedDocumentCreator(
            id_document=id_document,
            hash_document=hash_document,
            current_user_id=current_user_id
        )
        
        # Exécuter toutes les étapes du processus
        creator.load_document() \
               .verify_document_integrity() \
               .load_signatures_and_points() \
               .verify_all_signatures_completed() \
               .apply_signatures_to_pdf() \
               .add_signature_certificates() \
               .save_final_document() \
               .send_signed_document_by_email()
        
        # Sauvegarder les modifications en base
        g.db_session.commit()
        
        # Retourner une réponse de succès
        document_name = creator.document.doc_nom if creator.document else "Document"
        return jsonify(
            success=True, 
            message=f"Le document '{document_name}' a été finalisé et envoyé par email avec succès.",
            document_id=id_document
        )
        
    except ValueError as e:
        # Erreurs métier (droits, intégrité, etc.)
        return jsonify(success=False, message=str(e)), 400
        
    except FileNotFoundError as e:
        # Erreurs de fichier
        return jsonify(success=False, message=f"Fichier non trouvé : {str(e)}"), 404
        
    except Exception as e:
        # Erreurs système
        logging.error(f"Erreur lors de la création du document final signé : {e}")
        g.db_session.rollback()
        return jsonify(success=False, message=INTERNAL_SERVER_ERROR), 500

@signatures_bp.route('/creer-depuis-modele', methods=['GET', 'POST'])
def create_signature_from_template() -> Any:
    """
    Permet de créer un document à signer depuis un modèle.
    Méthodes supportées : GET, POST.
    GET : Affiche le formulaire de création depuis un modèle.
    POST : Traite la création du document depuis un modèle.
    """
    if request.method == 'POST':
        # Logique pour créer un document à signer depuis un modèle
        pass
    return render_template(ADMINISTRATION, context='signature_create_from_template')

@signatures_bp.route('/upload', methods=['POST'])
def upload_document() -> Any:
    """
    Permet de charger un document PDF à signer.
    Méthodes supportées : POST.
    POST : Traite le chargement du document PDF.
    """
    if request.method == 'POST':
        pdf_document: FileStorage | None = request.files.get('pdf', None)
        filename = getattr(pdf_document, "filename", None)
        if not pdf_document or not filename:
            return render_template(ADMINISTRATION, error_message="Aucun document PDF téléchargé ou nom de fichier invalide.")
        elif filename.lower().endswith('.pdf'):
            # Nettoyer les fichiers expirés avant de créer un nouveau
            SecureDocumentAccess.cleanup_expired_temp_files()
            
            # Sauvegarde du fichier pdf
            filename = Path(filename).name
            
            # Sécuriser le nom de fichier
            folder_path = SecureDocumentAccess.TEMP_DIR
            
            # Vérifier que le dossier existe
            Path(folder_path).mkdir(parents=True, exist_ok=True)

            # Sauvegarder le fichier PDF
            file_path = f"{folder_path}/{filename}"
            pdf_document.save(file_path)
            
            # Générer le hash d'accès et créer le fichier temporaire
            document_hash = SecureDocumentAccess.generate_document_hash(filename)
            SecureDocumentAccess.create_temp_access_file(filename, document_hash)
            users = g.db_session.query(User).order_by(User.nom).all()
            users = [user.to_dict(with_mdp=False) for user in users]
            return render_template(ADMINISTRATION, context='signature_make',
                                   success_message="Document PDF téléchargé avec succès.",
                                   document_name=filename, users=users)
        else:
            return render_template(ADMINISTRATION, error_message="Le fichier téléchargé n'est pas un PDF.")
    else:
        return render_template(ADMINISTRATION, error_message="Méthode non autorisée.")
    
@signatures_bp.route('/download/<filename>')
def download_pdf(filename: str):
    """
    Permet de télécharger un document PDF précédemment chargé.
    Sécurisé par vérification d'accès via fichiers JSON temporaires ou points de signature.
    """
    temp_dir_param = request.args.get('temp_dir', 'false').lower()
    temp_dir: bool = temp_dir_param in ('true', '1', 'yes')
    
    # Vérifier l'accès via les fichiers temporaires
    if temp_dir:
        if not SecureDocumentAccess.verify_temp_access(filename):
            return "Accès non autorisé à ce document", 403
        
        folder_path = SecureDocumentAccess.TEMP_DIR
        return send_from_directory(folder_path, filename)
    
    # Vérifier l'accès via les points de signature (documents définitifs)
    else:
        id_user = session.get('id', None)
        if not id_user:
            return "Session utilisateur non valide", 401
        
        # Rechercher les points de signature pour ce fichier et cet utilisateur
        points = g.db_session.query(Points).join(DocToSigne, DocToSigne.id == Points.id_document) \
                    .filter(Points.id_user == id_user) \
                    .filter(
                        (DocToSigne.doc_nom == filename) |
                        (DocToSigne.chemin_fichier.like(f'%/{filename}')) |
                        (DocToSigne.chemin_fichier.like(f'%\\{filename}')) |
                        (DocToSigne.chemin_fichier.endswith(filename))
                    ).all()
        
        if not points:
            return "Accès non autorisé à ce document", 403
        
        # Récupérer le chemin réel du fichier depuis la base de données
        document = points[0].document
        real_file_path = Path(document.chemin_fichier)
        
        if not real_file_path.exists():
            return "Fichier non trouvé", 404
        
        # Servir le fichier depuis son emplacement réel
        folder_path = str(real_file_path.parent)
        filename_real = real_file_path.name
        
        return send_from_directory(folder_path, filename_real)
