"""Module contenant la modélisation des factures dans l'application.

.. classes::
    - `Bill`: Représente une facture dans la base de données.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""

from __future__ import annotations

from typing import Optional
from os.path import splitext
from datetime import datetime

from sqlalchemy import Integer, String, Date, ForeignKey, Numeric
from sqlalchemy.orm import mapped_column, relationship, Mapped
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from ._common import Base, PK_CONTRACT

class Bill(Base):
    """Représente une facture associée à un contrat.

    :param id: Identifiant unique de la facture.
    :type id: int
    :param id_contrat: Identifiant du contrat associé.
    :type id_contrat: int
    :param date_facture: Date de la facture.
    :type date_facture: date
    :param titre_facture: Titre de la facture.
    :type titre_facture: str
    :param montant: Montant de la facture.
    :type montant: Decimal
    :param str_lien: Chemin du fichier de la facture.
    :type str_lien: str
    :param name: Nom du fichier de la facture.
    :type name: str

    .. table:: `13_factures`

    .. relations::
        - `contrat` (Contract): Contrat associé à la facture.

    .. methods ::
        - `__repr__() -> str`: Retourne une représentation textuelle de l'objet Bill.
        - `_get_extension(binary_file: Optional[FileStorage]=None) -> str`: Retourne l'extension
        du fichier lié à la facture.
        - `create_name(binary_file: Optional[FileStorage]=None) -> 'Bill'`: Crée le nom de la
        facture en fonction de ses attributs.
        - `upload(file_to_upload: FileStorage) -> bool`: Uploade le fichier de la facture.
        - `rename_file() -> bool`: Change le nom du fichier de la facture.
        - `download() -> Optional[io.BytesIO]`: Télécharge le fichier de la facture.
        - `switch(file_to_switch: FileStorage, old_file_name: str) -> bool`: Remplace le fichier
        de la facture par un nouveau fichier.
    
    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    __tablename__ = '13_factures'

    # Données principales
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Identifiant unique de la facture.",
    )
    id_contrat: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(PK_CONTRACT),
        nullable=False,
        comment="Identifiant du contrat associé.",
    )
    date_facture: Mapped[datetime] = mapped_column(
        Date,
        nullable=False,
        comment="Date de la facture.",
    )
    titre_facture: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Titre de la facture.",
    )
    montant: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Montant de la facture.",
    )

    # Données du fichier binaire
    str_lien: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Chemin du fichier de la facture.",
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        comment="Nom du fichier de la facture.",
    )

    # Relations
    contrat = relationship(
        "Contract",
        back_populates="factures",
    )

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet Facture.

        .. example::
            .. code-block:: python
                print(bill)
                >>> <Bill(id=1, id_contrat=1, date_facture=2024-09-25, titre_facture='Consulting',
                montant=1500.00, lien='25092024_001_0001_Consu.pdf')>
        """
        return (
            f"<Bill(id={self.id}, id_contrat={self.id_contrat}, "
            f"date_facture={self.date_facture}, titre_facture='{self.titre_facture}', "
            f"montant={self.montant}, lien='{self.str_lien}')>"
        )

    def _get_extension(self, *, binary_file: Optional[FileStorage]=None) -> str:
        """
        Retourne l'extension du fichier lié à la facture. Si le lien est vide ou n'a pas
        d'extension, retourne '.any'.

        :param binary_file: Fichier binaire pour extraire l'extension. Defaults to None.
        :type binary_file: FileStorage, optional

        :returns: Extension du fichier (ex: .pdf, .docx) ou '.any' si non disponible.
        :rtype: str
        """
        if binary_file:
            return splitext(str(binary_file.filename))[1]
        else:
            return splitext(self.str_lien)[1] if self.str_lien else '.any'

    def create_name(self, *, binary_file: Optional[FileStorage]=None) -> 'Bill':
        """Crée le nom de la facture en fonction de ses attributs.

        :param binary_file: Fichier binaire pour extraire l'extension. Defaults to None.
        :type binary_file: FileStorage, optional

        :returns: self
        :rtype: Bill

        .. example::
            .. code-block:: python
            bill.create_name(binary_file=binary_file)

        .. note::
            Format : JJMMYYYY_IDCONTRAT_IDFACTURE_TITREFACTURE
        """
        # Récupération de l'extension du fichier
        extention = self._get_extension(binary_file=binary_file)

        # Création de la partie date au format JJMMYYYY
        date_facture = self.date_facture
        if isinstance(date_facture, str):
            date_facture = datetime.strptime(date_facture, '%Y-%m-%d')
        str_date = date_facture.strftime('%d%m%Y')

        # Création des autres parties du nom
        id_contrat = str(self.id_contrat).zfill(3)
        id_bill = str(self.id).zfill(4)
        titre_facture = self.titre_facture[:5] if self.titre_facture else 'Factu'

        # Assemblage du nom complet et mise à jour des attributs
        self.name = secure_filename(f'F{str_date}_{id_contrat}_{id_bill}_{titre_facture}')
        self.str_lien = (self.name or "") + extention
        return self

    def upload(self, *, file_to_upload: FileStorage) -> bool:
        """Fonction pour uploader le fichier de la facture. Utilise la fonction `upload_file`
        du module docs.py.

        :param file_to_upload: Fichier binaire à uploader (io.BytesIO)
        :type file_to_upload: FileStorage
        :param extension: Extension du fichier (ex: .pdf, .docx)
        :type extension: str, optional

        :returns: True si l'upload a réussi, False sinon.
        :rtype: bool

        .. example::
            .. code-block:: python
            bill.upload(file_to_upload=binary_file)
        """
        from ..docs import upload_file  # pylint: disable=C0415
        if not self.str_lien:
            raise OSError("La facture ne possède pas de nom de fichier.")
        upload_file(file_to_upload, file_name=self.str_lien)
        return True

    def rename_file(self) -> bool:
        """Fonction pour changer le nom du fichier du document. Utilise la fonction
        `rename_file` du module docs.py.

        :param new_name: Nouveau nom sans extension
        :type new_name: str
        :param extension: Extension du fichier (ex: .pdf, .docx)
        :type extension: str

        :returns: True si le renommage a réussi, False sinon.
        :rtype: bool

        .. example::
            .. code-block:: python
                bill.create_name().rename_file()
        """
        from ..docs import rename_file    # pylint: disable=C0415
        if not self.str_lien:
            raise OSError("La facture ne possède pas de fichier à renommer.")
        old_name = self.str_lien
        self.create_name()
        return rename_file(old_file_name=old_name, new_file_name=self.str_lien)

    def download(self):
        """Fonction pour télécharger le fichier de la facture. Utilise la fonction `download_file`
        du module docs.py.

        :returns: Fichier binaire téléchargé, ou None si échec.
        :rtype: io.BytesIO or None

        .. example::
            .. code-block:: python
                file = bill.download()
                # or
                bill.download()
        """
        try:
            if self.str_lien:
                from ..docs import download_file    # pylint: disable=C0415
                return download_file(self.str_lien)
        except OSError:
            return None

    def switch(self, *, file_to_switch: FileStorage, old_file_name: str) -> bool:
        """Fonction pour remplacer le fichier de la facture par un nouveau fichier.

        :param file_to_switch: Nouveau fichier binaire (FileStorage)
        :type file_to_switch: FileStorage
        :param old_file_name: Nom du fichier à remplacer
        :type old_file_name: str

        :returns: True si le remplacement a réussi, False sinon.
        :rtype: bool

        :raises OSError: Si le remplacement échoue en raison d'une erreur système.

        .. example::
            .. code-block:: python
                bill.switch(file_to_switch=new_file, old_file_name=old_file_name)
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
