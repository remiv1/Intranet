"""Module contenant la modélisation des documents dans l'application.

.. classes::
    - `Document`: Représente un document dans la base de données.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from os.path import splitext

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from sqlalchemy import Integer, String, Date, ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped

from ._common import Base, PK_CONTRACT

class Document(Base):
    """Représente un document associé à un contrat.

    :param id: Identifiant unique du document.
    :type id: int
    :param id_contrat: Identifiant du contrat associé.
    :type id_contrat: int
    :param date_document: Date du document.
    :type date_document: date
    :param type_document: Type du document (Contrat, Avenant, etc.).
    :type type_document: str
    :param sous_type_document: Sous-type du document.
    :type sous_type_document: str
    :param descriptif: Descriptif du document.
    :type descriptif: str
    :param str_lien: Chemin du fichier stocké.
    :type str_lien: str
    :param name: Nom du fichier stocké.
    :type name: str

    .. relations :
        - `contrat` (Contract): Contrat associé au document.

    .. table: `11_documents`

    .. methods :
        - `__repr__()` -> str: Retourne une représentation textuelle de l'objet Document.
        - `_get_extension(binary_file: Optional[FileStorage]=None) -> str`: Retourne
        l'extension du fichier lié au document.
        - `create_name(binary_file: Optional[FileStorage]=None) -> 'Document'`: Crée le
        nom du document en fonction de ses attributs.
        - `upload(file_to_upload: FileStorage) -> bool`: Télécharge le fichier associé au document.
        - `rename_file() -> bool`: Change le nom du fichier associé au document.
        - `download() -> Optional[io.BytesIO]`: Télécharge le fichier associé au document.
        - `switch(file_to_switch: FileStorage, old_file_name: str) -> bool`: Remplace le fichier du
        document par un nouveau fichier.

    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    __tablename__ = '11_documents'

    # Données principales
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Identifiant du document.",
    )
    id_contrat: Mapped[int] = mapped_column(
        Integer, ForeignKey(PK_CONTRACT),
        nullable=False,
        comment="Identifiant du contrat associé.",
    )
    date_document: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date du document.",
    )
    type_document: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type du document (Contrat, Avenant, etc.).",
    )
    sous_type_document: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Sous-type du document (ex: Contrat de service).",
    )
    descriptif: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Descriptif du document.",
    )

    # Données du fichier binaire
    str_lien: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Chemin du fichier stocké.",
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        comment="Nom du fichier stocké.",
    )

    # Relations
    contrat = relationship(
        "Contract",
        back_populates="documents",
    )

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet Document.

        .. example::
            .. code-block:: python
                print(document)

            .. code-block:: console
                <Document(id=1, name='25092024_001_0001_Contr', date_document=2024-09-25,
                id_contrat=1, type_document='Contrat', sous_type_document='Contrat de service',
                descriptif='Contrat de service annuel')>
        """
        return (f"<Document(id={self.id}, name='{self.name}', date_document={self.date_document}, "
            f"id_contrat={self.id_contrat}, type_document='{self.type_document}', "
            f"sous_type_document='{self.sous_type_document}', descriptif='{self.descriptif}')>")

    def _get_extension(self, *, binary_file: Optional[FileStorage]=None) -> str:
        """
        Retourne l'extension du fichier lié au document. Si le lien est vide ou n'a pas d'extension,
        retourne '.any'.

        :param binary_file: Fichier binaire pour extraire l'extension. Defaults to None.
        :type binary_file: Optional[FileStorage]

        :returns: Extension du fichier (ex: .pdf, .docx) ou '.any' si non disponible.
        :rtype: str
        """
        if binary_file:
            return splitext(str(binary_file.filename))[1]
        return splitext(self.str_lien)[1] if self.str_lien else '.any'

    def create_name(self, *, binary_file: Optional[FileStorage]=None) -> 'Document':
        """
        Crée le nom du document en fonction de ses attributs.
        Format : JJMMYYYY_IDCONTRAT_IDDOCUMENT_SOUSTYPEDOCUMENT
        :param binary_file: Fichier binaire pour extraire l'extension. Defaults to None.
        :type binary_file: Optional[FileStorage]

        :returns: self
        :rtype: Document

        .. example::
            .. code-block:: python
                document.create_name(binary_file=binary_file)
        """
        # Récupération de l'extension du fichier
        extention = self._get_extension(binary_file=binary_file)

        # Création de la partie date au format JJMMYYYY
        date_date = datetime.strptime(str(self.date_document), '%Y-%m-%d')
        str_date = date_date.strftime('%d%m%Y')

        # Création des autres parties du nom
        id_contrat = str(self.id_contrat).zfill(3)
        id_document = str(self.id).zfill(4)
        sous_type_document = self.sous_type_document[:5] if self.sous_type_document else 'Docum'

        # Assemblage du nom complet et mise à jour des attributs
        self.name = secure_filename(f'{str_date}_{id_contrat}_{id_document}_{sous_type_document}')
        self.str_lien = (self.name or "") + extention
        return self

    def upload(self, *, file_to_upload: FileStorage) -> bool:
        """Fonction pour uploader le fichier du document. Utilise la fonction `upload_file`
        du module docs.py.
        
        :param file_to_upload: Fichier binaire à uploader
        :type file_to_upload: FileStorage
        :returns: True si l'upload a réussi, False sinon.
        :rtype: bool

        .. example::
            .. code-block:: python
                document.upload(file_to_upload=binary_file)
        """
        from ..docs import upload_file  # pylint: disable=C0415
        if not self.str_lien:
            raise OSError("Le document ne possède pas de nom de fichier.")
        upload_file(file_to_upload, file_name=self.str_lien)
        return True

    def rename_file(self) -> bool:
        """Fonction pour changer le nom du fichier du document. Utilise la fonction `rename_file`
        du module docs.py.
        
        :returns: True si le renommage a réussi, False sinon.
        :rtype: bool

        .. example::
            .. code-block:: python
                document.create_name().rename_file()
        """
        from ..docs import rename_file  # pylint: disable=C0415
        if not self.str_lien:
            raise OSError("Le document ne possède pas de fichier à renommer.")
        old_name = self.str_lien
        self.create_name()
        return rename_file(old_file_name=old_name, new_file_name=self.str_lien)

    def download(self):
        """
        Fonction pour télécharger le fichier du document.
        Utilise la fonction download_file du module docs.py.
        Arguments :
            None
        Returns :
            io.BytesIO: Fichier binaire téléchargé, ou None si échec.
        .. example::
            .. code-block:: python
                file = document.download()
                # or
                document.download()
        """
        try:
            if self.str_lien:
                from ..docs import download_file    # pylint: disable=C0415
                return download_file(self.str_lien)
        except OSError:
            return None

    def switch(self, *, file_to_switch: FileStorage, old_file_name: str) -> bool:
        """
        Fonction pour remplacer le fichier du document par un nouveau fichier.
        Arguments :
            file_to_switch (FileStorage): Nouveau fichier binaire
            old_file_name (str): Nom du fichier à remplacer
        Returns :
            bool: True si le remplacement a réussi, False sinon.
        Exemple d'utilisation :
            ```python
            document.switch(file_to_switch=binary_file, old_file_name='ancien_nom.pdf')
            ```
        """
        from ..docs import exchange_files, upload_file   # pylint: disable=C0415
        self.create_name(binary_file=file_to_switch)
        if not old_file_name:
            upload_file(file_to_switch, file_name=self.str_lien or "")
            return True
        return exchange_files(
            old_file_name=old_file_name,
            new_file=file_to_switch,
            new_file_name=self.str_lien or "",
        )
