"""Module pour la création et la gestion des documents PDF signés.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

import json
import hashlib
import shutil
from typing import Any
from pathlib import Path
from io import BytesIO
from datetime import datetime
from smtplib import SMTPException

from flask import session, g, render_template
from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfgen import canvas
from PIL import Image as PILImage
import cairosvg

from .utils import send_email_signed_files

from . import SecureCertificateManager
from ..models import DocToSigne, Points, Signatures, User, Invitation, ViewPoints
from ..config.logger import api_logger

class SignedDocumentCreator:
    """Classe pour gérer la création du document PDF final signé. Cette classe s'occupe de :

    - Charger le document à signer et vérifier les droits d'accès.
    - Vérifier l'intégrité du document via son hash.
    - Récupérer les points et signatures associées au document.
    - Vérifier si toutes les signatures requises ont été effectuées.
    - Appliquer les signatures SVG sur le document PDF.
    - Incorporer les certificats de signature dans le PDF.
    - Sauvegarder le document signé final.
    - Envoyer le document signé par email à tous les participants.

    :param id_document: L'ID du document à traiter.
    :type id_document: int
    
    .. methods::
        - `load_and_verify_document(hash_document: str) -> 'SignedDocumentCreator'`: Charge le
        document, vérifie les droits d'accès ET l'intégrité du fichier via son hash.
        - `load_signatures_and_points() -> 'SignedDocumentCreator'`: Récupère les points et
        signatures associées au document.
        - `verify_all_signatures_completed() -> 'SignedDocumentCreator'`: Vérifie si toutes les
        signatures requises ont été effectuées.
        - `apply_signatures_to_pdf() -> 'SignedDocumentCreator'`: Applique les signatures SVG sur
        le document PDF.
        - `_prepare_signed_document() -> None`: Prépare le document signé en incorporant les
        certificats.
        - `_process_all_pages() -> None`: Traite toutes les pages du document pour y ajouter les
        signatures.
        - `_write_signed_pdf() -> None`: Écrit le document PDF signé dans le fichier de sortie.
        - `_create_fallback_copy() -> None`: Crée une copie de secours du document signé.
        - `_update_document_hash() -> None`: Met à jour le hash du document signé dans la base de
        données.
        - `_create_signature_overlay(
        page: Any, signatures_data: List[Dict[str, Any]], page_num: int) -> bytes | None`: Crée
        une superposition PDF avec les signatures pour une page donnée.
        - `_add_single_signature_to_canvas(can: Canvas, data: Dict[str, Any], page_width: float,
        page_height: float) -> bool`: Ajoute une seule signature SVG au canevas PDF.
        - `_process_signature_image(svg_graph: str, largeur: int, hauteur: int) -> PILImage.Image
        | None`: Traite l'image SVG de la signature et la convertit en image PIL.
        - `_calculate_signature_position(self, point: Dict[str, Any], svg_image: PILImage.Image,
        page_width: float, page_height: float) -> tuple[float, float]`: Calcule la position de la
        signature sur la page.
        - `_draw_signature_on_canvas(self, can: Canvas, svg_image: PILImage.Image, x_pos: float,
        y_pos: float, point: Dict[str, Any]) -> None`: Dessine la signature sur le canevas PDF.
        - `_add_signature_metadata_text(self, can: Canvas, nom_complet: str, signature:
        Dict[str, Any], x_pos: float, y_pos: float, img_w: int, img_h: int, page_width: float)
        -> None`: Ajoute les métadonnées de la signature au canevas PDF.
        - `_convert_svg_to_image(self, *, svg_content: str, width: int, height: int) ->
        PILImage.Image | None`: Convertit le contenu SVG en une image PIL.
        - `add_signature_certificates() -> 'SignedDocumentCreator'`: Ajoute les certificats de
        signature dans le PDF.
        - `save_final_document() -> 'SignedDocumentCreator'`: Sauvegarde le document signé final.
        - `send_signed_document_by_email() -> 'SignedDocumentCreator'`: Envoie le document signé par
        email à tous les participants.
    """

    def __init__(self, *, id_document: int) -> None:
        """Initialise le créateur de document signé.
        
        :param id_document (int): L'ID du document à traiter.
        :type id_document: int
        """
        self.id_document = id_document
        self.current_user_id = session.get('id', 0)

        # Attributs qui seront initialisés par les méthodes
        self.document: DocToSigne | None = None
        self.document_path: Path | None = None
        self.points: list[Points] = []
        self.signatures: list[Signatures] = []
        self.signatories: list[User] = []
        self.creator: User | None = None
        self.signed_document_path: Path | None = None
        self.expeditor_user: User | None = None
        self.document_data: dict[str, Any] | None = None
        self.view_points: list[dict[str, Any]] = []
        self.reader: PdfReader
        self.writer: PdfWriter
        self.data_by_page: dict[int, list[dict[str, Any]]] = {}

    def load_and_verify_document(self, *, hash_document: str) -> 'SignedDocumentCreator':
        """Récupère le document en base, vérifie les droits d'accès et l'intégrité du fichier. Cette
        méthode combine la récupération du document, la vérification des permissions et la
        validation de l'intégrité du fichier via son hash SHA-256.

        :param hash_document: Le hash du document pour vérification.
        :type hash_document: str

        :returns: self: SignedDocumentCreator avec document et document_path initialisés.
        :rtype: SignedDocumentCreator

        :raises ValueError: Si le document n'existe pas, hash invalide, accès non autorisé, ou si le
        fichier a été modifié.
        :raises FileNotFoundError: Si le fichier PDF n'est pas trouvé sur le disque.
        """
        # Récupérer le document en base
        self.document = g.db_session.query(DocToSigne).filter_by(
            id=self.id_document,
            hash_fichier=hash_document
        ).first()

        # Vérifier que le document avec ce hash existe et lève une erreur si non
        if not self.document:
            raise ValueError("Document non trouvé ou hash invalide.")

        # Vérifier que l'utilisateur a le droit d'accéder à ce document
        # Soit il est le créateur, soit il a une invitation pour ce document
        is_creator = self.document.id_user == self.current_user_id
        has_invitation = g.db_session.query(Invitation).filter_by(
            id_document=self.id_document,
            id_user=self.current_user_id
        ).first() is not None

        # Si ça n'est pas le cas, lever une erreur d'accès non autorisé
        if not (is_creator or has_invitation):
            raise ValueError("Accès non autorisé à ce document.")

        # Récupérer le créateur du document et l'utilisateur expéditeur
        self.creator = g.db_session.query(User).filter_by(id=self.document.id_user).first()
        self.expeditor_user = g.db_session.query(User).filter_by(
            id=self.current_user_id
        ).first()

        # Préparer les données du document pour les logs et emails
        self.document_data = {
            'document': self.document,
            'expeditor': self.expeditor_user,
            'expeditor_mail': self.expeditor_user.mail if self.expeditor_user else None
        }

        # Vérifier l'existence du fichier PDF sur le disque
        self.document_path = Path(self.document.chemin_fichier)

        # Lever une erreur si le fichier n'existe pas
        if not self.document_path.exists():
            raise FileNotFoundError(f"Fichier PDF non trouvé : {self.document_path}")

        # Vérifier le hash du fichier
        with open(self.document_path, "rb") as f:
            file_content = f.read()
            calculated_hash = hashlib.sha256(file_content).hexdigest()

        # Lève une erreur si le hash ne correspond pas
        if calculated_hash != self.document.hash_fichier:
            raise ValueError("Le fichier a été modifié depuis sa création (hash invalide).")

        return self

    def load_signatures_and_points(self) -> 'SignedDocumentCreator':
        """Récupère les points et signatures associées au document et les utilisateurs associés
        et crée une structure consolidée.

        :return: self
        :rtype: SignedDocumentCreator

        :raises ValueError: si aucun point n'est trouvé
        """
        if not self.document:
            raise ValueError("Document non chargé. Appelez load_and_verify_document() d'abord.")

        # Récupérer tous les points de signature des utilisateurs et leurs signatures
        points = g.db_session.query(Points).filter_by(
            id_document=self.id_document
        ).all()
        self.view_points = ViewPoints(points).to_dict()

        # Levée d'erreur en cas de manque de données et de correspondance
        if not self.view_points:
            raise ValueError("Aucun point de signature ou utilisateur trouvé pour ce document.")

        # Extraire les signatures et signataires uniques depuis view_points
        seen_signature_ids: set[Any] = set()
        seen_user_ids: set[Any] = set()

        for data in self.view_points:
            signature_data = data.get('signature')
            user_data = data.get('user')

            if signature_data and signature_data.get('id') not in seen_signature_ids:
                seen_signature_ids.add(signature_data['id'])
                # Récupérer l'objet Signature complet depuis la base
                sig_obj = g.db_session.query(Signatures).filter_by(id=signature_data['id']).first()
                if sig_obj:
                    self.signatures.append(sig_obj)

            if user_data and user_data.get('id') not in seen_user_ids:
                seen_user_ids.add(user_data['id'])
                # Récupérer l'objet User complet depuis la base
                user_obj = g.db_session.query(User).filter_by(id=user_data['id']).first()
                if user_obj:
                    self.signatories.append(user_obj)

        return self

    def verify_all_signatures_completed(self) -> 'SignedDocumentCreator':
        """Vérifie que toutes les signatures requises ont été effectuées.

        :return: self
        :rtype: SignedDocumentCreator

        :raises ValueError: Si toutes les signatures ne sont pas complétées.
        """
        # Vérifier que des points de signature existent
        if not self.view_points:
            raise ValueError("Aucun point de signature trouvé pour ce document.")

        # Vérifier que tous les points ont été signés (status = 1)
        unsigned_users: bool = False
        for data in self.view_points:
            point = data['point']
            # point est un dictionnaire, accéder avec ['status']
            if point['status'] != 1:
                unsigned_users = True
                break

        # Si des utilisateurs n'ont pas signé, lever une erreur
        if unsigned_users:
            raise ValueError("Signatures manquantes sur le document.")

        return self

    def apply_signatures_to_pdf(self) -> 'SignedDocumentCreator':
        """Applique les signatures SVG sur le document PDF en utilisant pypdf.

        :return: self
        :rtype: SignedDocumentCreator
        :raises Exception: Si une erreur survient lors de l'application des signatures.
        """
        # Vérifier que le document et les points de signature sont chargés
        if not self.document_path or not self.view_points:
            raise ValueError("Document ou données de signature manquants.")

        # Appliquer les signatures sur le PDF : préparation, traitement des pages, écriture
        try:
            self._prepare_signed_document()
            self._process_all_pages()
            self._write_signed_pdf()
            self._update_document_hash()

            return self

        # En cas d'erreur, créer une copie simple du fichier
        except Exception as e:
            self._create_fallback_copy()
            raise ValueError(f"Erreur lors de l'application des signatures : {e}") from e

    def _prepare_signed_document(self) -> None:
        """Prépare le document signé : chemin, lecteur et regroupement des signatures.
        
        :return: None
        :rtype: None

        :raises ValueError: Si le chemin du document est manquant.
        """
        # Vérifier que le chemin du document est défini
        if not self.document_path:
            raise ValueError("Chemin du document manquant")

        # Créer le chemin pour le document signé
        signed_filename = f"signed_{self.document_path.name}"
        self.signed_document_path = self.document_path.parent / signed_filename

        # Lire le PDF original
        self.reader = PdfReader(str(self.document_path))
        self.writer = PdfWriter()

        # Grouper les données de signature par page
        self.data_by_page: dict[int, list[dict[str, Any]]] = {}
        for data in self.view_points:
            page_num = data['point']['page_num']
            if page_num not in self.data_by_page:
                self.data_by_page[page_num] = []
            self.data_by_page[page_num].append(data)

    def _process_all_pages(self) -> None:
        """Traite toutes les pages du PDF en ajoutant les signatures.
        
        :return: None
        :rtype: None
        """
        # Parcourir chaque page du PDF
        for page_num in range(1, len(self.reader.pages) + 1):
            page = self.reader.pages[page_num - 1]

            # S'il y a des signatures sur cette page, créer un overlay
            if page_num in self.data_by_page:
                overlay_pdf = self._create_signature_overlay(
                    page=page,
                    signatures_data=self.data_by_page[page_num]
                )

                # Ajouter l'overlay à la page si créé
                if overlay_pdf:
                    overlay_reader = PdfReader(BytesIO(overlay_pdf))
                    page.merge_page(overlay_reader.pages[0])

            self.writer.add_page(page)

    def _write_signed_pdf(self) -> None:
        """Écrit le PDF signé sur le disque et vérifie son intégrité.
        
        :return: None
        :rtype: None

        :raises ValueError: Si le chemin du document signé est manquant ou si le fichier n'a pas été
        créé correctement.
        """
        # Vérifier que le chemin du document signé est défini
        if not self.signed_document_path:
            raise ValueError("Chemin du document signé manquant")

        # Écrire le PDF signé dans le fichier de sortie
        with open(self.signed_document_path, 'wb') as output_file:
            self.writer.write(output_file)

        # Vérifier que le fichier a bien été créé et n'est pas vide
        file_size = self.signed_document_path.stat().st_size
        if not self.signed_document_path.exists() or file_size == 0:
            raise ValueError(f"Le fichier signé n'a pas été créé : {self.signed_document_path}")

    def _create_fallback_copy(self) -> None:
        """Crée une copie simple du fichier en cas d'erreur.
        
        :return: None
        :rtype: None
        """
        # Si présence du document original, faire une copie simple
        if self.document_path:
            signed_filename = f"signed_{self.document_path.name}"
            self.signed_document_path = self.document_path.parent / signed_filename
            shutil.copy2(self.document_path, self.signed_document_path)

    def _update_document_hash(self) -> None:
        """Met à jour le hash du document signé.
        
        :return: None
        :rtype: None

        :raises ValueError: Si le chemin du document signé ou l'objet document est manquant.
        """
        # Si absence du document sur le disque ou objet document, lever une erreur
        if not self.signed_document_path or not self.document:
            raise ValueError("Chemin du document signé ou objet document manquant")

        # Calculer le hash SHA-256 du fichier signé et mettre à jour en base
        with open(self.signed_document_path, "rb") as f:
            file_content = f.read()
            new_hash = hashlib.sha256(file_content).hexdigest()
        self.document.hash_signed_file = new_hash

    def _create_signature_overlay(
            self, page: Any, signatures_data: list[dict[str, Any]]
        ) -> bytes | None:
        """
        Crée un overlay PDF avec les signatures pour une page donnée.
        
        :param page: La page PDF (pypdf)
        :type page: Any
        :param signatures_data: Liste des données de signature pour cette page
        :type signatures_data: list[dict[str, Any]]
        :param page_num: Numéro de la page
        :type page_num: int
            
        :return: Le PDF overlay en bytes, ou None si aucune signature
        :rtype: bytes | None

        :raise ValueError: Si aucune signature valide n'a pu être ajoutée sur la page ou que
        l'overlay du PDF n'a pas pu être créé.
        """
        try:
            # Récupérer les dimensions de la page
            page_box = page.mediabox
            page_width = float(page_box.width)
            page_height = float(page_box.height)

            # Créer un buffer pour le PDF overlay
            packet = BytesIO()
            can: Canvas = canvas.Canvas(packet, pagesize=(page_width, page_height))
            signatures_added = 0

            # Ajouter chaque signature sur l'overlay
            for data in signatures_data:
                if self._add_single_signature_to_canvas(can, data, page_width, page_height):
                    signatures_added += 1

            # Finaliser le canvas seulement si des signatures ont été ajoutées
            if signatures_added == 0:
                raise ValueError("Aucune signature valide à ajouter sur cette page.")

            # Finaliser le PDF overlay
            can.save()
            packet.seek(0)

            return packet.getvalue()

        except Exception as e:
            raise ValueError(f"Impossible de créer l'overlay de signature: {e}") from e

    def _add_single_signature_to_canvas(
            self,
            can: Canvas,
            data: dict[str, Any],
            page_width: float,
            page_height: float,
        ) -> bool:
        """Ajoute une signature unique sur le canvas.
        
        :param can: Le canvas reportlab
        :type can: Canvas
        :param data: Les données de la signature (signature, point, user)
        :type data: dict[str, Any]
        :param page_width: Largeur de la page
        :type page_width: float
        :param page_height: Hauteur de la page
        :type page_height: float
            
        :return: True si la signature a été ajoutée avec succès
        :rtype: bool
        """
        # Extraire les données nécessaires
        signature = data['signature']
        point = data['point']
        nom_complet = data['user_complete_name']

        # Vérifier si on a un SVG valide
        svg_graph = signature.get('svg_graph')
        if not svg_graph or len(str(svg_graph).strip()) == 0:
            raise ValueError(f"Pas de SVG valide pour le point {point.get('id')}")

        # Traiter l'image de signature
        largeur = signature.get('largeur_graph', 600)
        hauteur = signature.get('hauteur_graph', 200)
        svg_image = self._process_signature_image(svg_graph, largeur, hauteur)

        if not svg_image:
            raise ValueError(
                f"Impossible de convertir le SVG en image pour le point {point.get('id')}"
            )

        # Calculer la position de la signature
        x_pos, y_pos = self._calculate_signature_position(
            point, svg_image, page_width, page_height
        )

        # Dessiner la signature sur le canvas
        self._draw_signature_on_canvas(can, svg_image, x_pos, y_pos)

        # Ajouter les métadonnées textuelles
        self._add_signature_metadata_text(
            can, nom_complet, signature, x_pos, y_pos,
            svg_image.width, svg_image.height, page_width
        )

        return True

    def _process_signature_image(
            self,
            svg_graph: str,
            largeur: int,
            hauteur: int,
        ) -> PILImage.Image | None:
        """Traite l'image de signature : conversion SVG et redimensionnement.
        
        :param svg_graph: Le contenu SVG de la signature
        :type svg_graph: str
        :param largeur: Largeur originale
        :type largeur: int
        :param hauteur: Hauteur originale
        :type hauteur: int

        :return: Image PIL redimensionnée ou None si échec
        :rtype: PILImage.Image | None
        """
        # Convertir le SVG en image
        svg_image = self._convert_svg_to_image(
            svg_content=svg_graph,
            width=largeur,
            height=hauteur
        )

        # Si échec de la conversion, retourner None
        if not svg_image:
            return None

        # Réduire la taille à 33% (un tiers de la taille originale)
        img_width, img_height = svg_image.size
        reduction_factor = 1/3

        new_width = int(img_width * reduction_factor)
        new_height = int(img_height * reduction_factor)
        svg_image = svg_image.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
        api_logger.info(
            "Image réduite à 33%% : (%s x %s) → (%s x %s)",
            img_width,
            img_height,
            new_width,
            new_height,
        )

        # Redimensionner encore si trop grande
        max_width = 450
        max_height = 150
        final_width, final_height = svg_image.size
        scale_ratio = 1.0

        # Vérifier si on dépasse les dimensions max de la page
        if final_width > max_width:
            scale_ratio = max_width / final_width
        if final_height * scale_ratio > max_height:
            scale_ratio = max_height / final_height

        # Gestion du redimensionnement si nécessaire
        if scale_ratio < 1.0:
            final_width = int(final_width * scale_ratio)
            final_height = int(final_height * scale_ratio)
            svg_image = svg_image.resize((final_width, final_height), PILImage.Resampling.LANCZOS)

        return svg_image

    def _calculate_signature_position(
            self,
            point: dict[str, Any],
            svg_image: PILImage.Image,
            page_width: float,
            page_height: float,
        ) -> tuple[float, float]:
        """Calcule la position de la signature sur la page PDF.
        
        :param point: Le point de signature avec coordonnées x, y
        :type point: dict[str, Any]
        :param svg_image: L'image PIL de la signature
        :type svg_image: PILImage.Image
        :param page_width: Largeur de la page
        :type page_width: float
        :param page_height: Hauteur de la page
        :type page_height: float
            
        :return: (x_pos, y_pos) position finale sur la page
        :rtype: tuple[float, float]
        """
        # Récupérer les coordonnées du point en pixels
        point_x_pixels = float(point.get('x', 100))
        point_y_pixels = float(point.get('y', 100))

        # CONVERSION PIXELS → POINTS PDF
        pdf_scale = 1.5  # Correspond à pdfScale dans le JavaScript
        point_x = point_x_pixels / pdf_scale
        point_y = point_y_pixels / pdf_scale

        # Calculer la position pour centrer l'image sur le point
        img_w = svg_image.width
        img_h = svg_image.height

        # VALIDATION DES COORDONNÉES
        if point_y > page_height:
            point_x = page_width / 2
            point_y = page_height / 2

        if point_x > page_width:
            point_x = page_width / 2

        # S'assurer que la signature ne déborde pas de la page
        x_pos = point_x - (img_w / 2)
        y_pos = page_height - point_y - (img_h / 2)

        # Ajuster si la signature déborde
        if x_pos < 0:
            x_pos = 10
        if x_pos + img_w > page_width:
            x_pos = page_width - img_w - 10
        if y_pos < 0:
            y_pos = 10
        if y_pos + img_h > page_height:
            y_pos = page_height - img_h - 10

        return x_pos, y_pos

    def _draw_signature_on_canvas(
            self,
            can: Canvas,
            svg_image: PILImage.Image,
            x_pos: float, y_pos: float,
        ) -> None:
        """Dessine l'image de signature sur le canvas.
        
        :param can: Le canvas reportlab
        :type can: Canvas
        :param svg_image: L'image PIL à dessiner
        :type svg_image: PILImage.Image
        :param x_pos: Position X sur la page
        :type x_pos: float
        :param y_pos: Position Y sur la page
        :type y_pos: float
        :param point: Le point de signature (pour logging)
        :type point: dict[str, Any]
        """
        # Convertir l'image PIL en ImageReader pour reportlab
        img_reader: ImageReader = ImageReader(svg_image)
        can.drawImage(  # type: ignore[call-arg]
            img_reader,
            x_pos,
            y_pos,
            width=svg_image.width,
            height=svg_image.height,
            mask='auto',
            preserveAspectRatio=True,
        )

    def _add_signature_metadata_text(
            self,
            can: Canvas,
            nom_complet: str,
            signature: dict[str, Any],
            x_pos: float, y_pos: float, img_w: int, img_h: int,
            page_width: float,
        ) -> None:
        """Ajoute le texte de métadonnées sous la signature.
        
        :param can: Le canvas reportlab
        :type can: Canvas
        :param nom_complet: Nom complet du signataire
        :type nom_complet: str
        :param signature: Dict contenant les données de signature
        :type signature: dict[str, Any]
        :param x_pos: Position X de l'image
        :type x_pos: float
        :param y_pos: Position Y de l'image
        :type y_pos: float
        :param img_w: Largeur de l'image
        :type img_w: int
        :param img_h: Hauteur de l'image
        :type img_h: int
        :param page_width: Largeur de la page
        :type page_width: float
        """
        can.setFont("Helvetica", 8)

        # Préparer les textes
        text_line1 = f"Signé par: {nom_complet}"
        text_line2 = f"Le: {signature.get('signe_at', 'Date inconnue')}"

        # Calculer la largeur des textes pour les centrer
        text_width1 = can.stringWidth(text_line1, "Helvetica", 8)
        text_width2 = can.stringWidth(text_line2, "Helvetica", 8)

        # Position Y en dessous de l'image
        text_y_line1 = y_pos - 12
        text_y_line2 = text_y_line1 - 10

        # Vérifier que le texte ne dépasse pas le bas de la page
        min_margin = 5
        if text_y_line2 < min_margin:
            # Placer au-dessus de la signature
            text_y_line1 = y_pos + img_h + 12
            text_y_line2 = text_y_line1 + 10

        # Centrer horizontalement les textes
        text_x1 = x_pos + (img_w - text_width1) / 2
        text_x2 = x_pos + (img_w - text_width2) / 2

        # Ajuster si débordement
        if text_x1 < 0:
            text_x1 = min_margin
        if text_x2 < 0:
            text_x2 = min_margin
        if text_x1 + text_width1 > page_width:
            text_x1 = page_width - text_width1 - min_margin
        if text_x2 + text_width2 > page_width:
            text_x2 = page_width - text_width2 - min_margin

        # Dessiner les textes
        can.drawString(text_x1, text_y_line1, text_line1)
        can.drawString(text_x2, text_y_line2, text_line2)

    def _convert_svg_to_image(self, *, svg_content: str, width: int, height: int):
        """Convertit un contenu SVG en image utilisable par borb.
        
        :param svg_content: Le contenu SVG
        :type svg_content: str
        :param width: Largeur souhaitée
        :type width: int
        :param height: Hauteur souhaitée
        :type height: int
            
        :returns: Image PIL ou None si échec
        :rtype: PIL.Image.Image or None

        :raise ValueError: Si la conversion échoue ou si le contenu SVG est invalide
        :raise ImportError: Si cairosvg ou PIL ne sont pas disponibles
        """
        try:
            # Valider le contenu SVG
            if not svg_content or len(svg_content.strip()) == 0:
                raise ValueError("Contenu SVG manquant")

            # Vérifier que le contenu ressemble à du SVG
            if '<svg' not in svg_content.lower():
                raise ValueError("Le contenu fourni n'est pas un SVG valide")

            # Convertir SVG en PNG avec cairosvg
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=width if width > 0 else 100,
                output_height=height if height > 0 else 50
            )

            # Vérifier que png_data n'est pas None et est de type bytes avant de l'utiliser
            if png_data is not None:
                # Créer une image PIL depuis les données PNG
                image = PILImage.open(BytesIO(png_data))
                return image
            raise ValueError("Conversion SVG en PNG a échoué, données invalides.")

        except ImportError as eie:
            raise ImportError("cairosvg ou PIL non disponible pour la conversion SVG") from eie
        except Exception as e:
            raise ValueError(f"Erreur lors de la conversion SVG : {e}") from e

    def add_signature_certificates(self) -> 'SignedDocumentCreator':
        """Incorpore les certificats de signature sécurisés dans le PDF.
        
        :return: self
        :rtype: SignedDocumentCreator

        :raises ValueError: Si le certificat sécurisé ne peut pas être créé ou est invalide.
            
        .. note:
            Cette méthode crée un certificat cryptographiquement sécurisé avec signature numérique
            pour garantir l'intégrité.
        """
        try:
            if not self.signed_document_path or not self.signatures:
                raise ValueError("Document ou signatures manquants.")

            # Créer le certificat sécurisé avec signature cryptographique
            document_hash = self.document.hash_fichier if self.document else "unknown"
            secure_cert = SecureCertificateManager.create_secure_certificate(
                signatures=self.signatures,
                signatories=self.signatories,
                document=self.document,
                view_points=self.view_points,
            )

            # Vérifier immédiatement le certificat créé
            is_valid = SecureCertificateManager.verify_certificate(secure_cert)
            if not is_valid:
                raise ValueError("Certificat invalide généré")

            # Sauvegarder le certificat sécurisé dans un fichier JSON
            if self.signed_document_path:
                cert_file_path = self.signed_document_path.with_suffix('.secure.cert')
                with open(cert_file_path, 'w', encoding='utf-8') as cert_file:
                    json.dump(secure_cert, cert_file, indent=2, ensure_ascii=False)

                # Créer également un fichier de vérification rapide
                verification_info: dict[str, Any] = {
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

            return self

        except Exception as e:
            raise ValueError(f"Erreur lors de l'ajout des certificats : {e}") from e

    def save_final_document(self) -> 'SignedDocumentCreator':
        """Sauvegarde le document signé final en remplacement de l'original.
        
        :returns: self
        :rtype: SignedDocumentCreator

        :raises ValueError: Si le document signé n'a pas été généré ou est invalide.
        """
        if not self.signed_document_path or not self.document_path:
            raise ValueError("Document signé non généré.")

        # Vérifier que le fichier signé existe et n'est pas vide
        file_size = self.signed_document_path.stat().st_size
        if not self.signed_document_path.exists() or file_size == 0:
            raise ValueError(
                f"Le fichier signé n'existe pas ou est vide : {self.signed_document_path}"
            )

        # Sauvegarder l'original avec un suffixe _original et déplace le doc signé à la place.
        original_backup = self.document_path.parent / f"original_{self.document_path.name}"
        if self.document_path.exists():
            shutil.move(self.document_path, original_backup)
        shutil.move(self.signed_document_path, self.document_path)

        # Mettre à jour le document en base (marquer comme finalisé)
        if self.document:
            self.document.status = 1
            self.document.complete_at = datetime.now()

        if self.signatures:
            for signature in self.signatures:
                signature.status = 1

        return self

    def send_signed_document_by_email(self) -> 'SignedDocumentCreator':
        """Envoie le document signé par email à tous les participants.
        
        :returns: self
        :rtype: SignedDocumentCreator

        :raises ValueError: Si le document n'est pas chargé ou le chemin est invalide.
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
        except (SMTPException, FileNotFoundError, IOError) as e:
            api_logger.exception("Erreur lors de l'envoi du document signé par email : %s", str(e))
            # Ne pas lever d'exception pour ne pas bloquer le processus

        return self
