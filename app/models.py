from sqlalchemy import Integer, String, Date, Boolean, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from typing import Optional
from datetime import datetime
from os.path import splitext

Base = declarative_base()
CONTRACT_KEY = '01_contrats.id'

class User(Base):
    __tablename__ = '99_users'
    id = mapped_column(Integer, primary_key=True)
    prenom = mapped_column(String(255), nullable=False)
    nom = mapped_column(String(255), nullable=False)
    mail = mapped_column(String(255), nullable=False)
    identifiant = mapped_column(String(25), nullable=True)
    sha_mdp = mapped_column(String(255), nullable=False)
    habilitation = mapped_column(Integer, nullable=True)
    debut = mapped_column(Date, nullable=True, default=func.current_date())
    fin = mapped_column(Date, nullable=True)
    false_test = mapped_column(Integer, nullable=True, default=0)
    locked = mapped_column(Boolean, nullable=True, default=False)

    def __repr__(self) -> str:
        return (f"<User(id={self.id}, prenom='{self.prenom}', nom='{self.nom}', "
            f"mail='{self.mail}', identifiant='{self.identifiant}', "
            f"sha_mdp='{self.sha_mdp}', habilitation={self.habilitation}, "
            f"debut={self.debut}, fin={self.fin}, locked={self.locked})>")
    
class Contract(Base):
    __tablename__ = '01_contrats'
    id = mapped_column(Integer, primary_key=True)
    type_contrat = mapped_column(String(50), nullable=False)
    sous_type_contrat = mapped_column(String(50), nullable=False)
    entreprise = mapped_column(String(255), nullable=False)
    id_externe_contrat = mapped_column(String(50), nullable=False)
    intitule = mapped_column(String(255), nullable=False)
    date_debut = mapped_column(Date, nullable=False)
    date_fin_preavis = mapped_column(Date, nullable=False)
    date_fin = mapped_column(Date, nullable=True)

    def __repr__(self) -> str:
        return (f"<Contract(id={self.id}, type_contrat='{self.type_contrat}', sous_type_contrat='{self.sous_type_contrat}', "
            f"entreprise='{self.entreprise}', id_externe_contrat='{self.id_externe_contrat}', "
            f"intitule='{self.intitule}', date_debut={self.date_debut}, date_fin_preavis={self.date_fin_preavis}, "
            f"date_fin={self.date_fin})>")
    
class Document(Base):
    __tablename__ = '11_documents'
    id = mapped_column(Integer, primary_key=True)
    id_contrat = mapped_column(Integer, ForeignKey(CONTRACT_KEY), nullable=False)
    date_document = mapped_column(Date, nullable=False)
    type_document = mapped_column(String(50), nullable=False)
    sous_type_document = mapped_column(String(50), nullable=True)
    descriptif = mapped_column(String(255), nullable=False)
    str_lien = mapped_column(String(255), nullable=True)
    name = mapped_column(String(30), nullable=True)

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet Document."""
        return (f"<Document(id={self.id}, name='{self.name}', date_document={self.date_document}, "
            f"id_contrat={self.id_contrat}, type_document='{self.type_document}', "
            f"sous_type_document='{self.sous_type_document}', descriptif='{self.descriptif}')>")
    
    def _get_extension(self, binary_file: Optional[FileStorage]) -> str:
        """
        Retourne l'extension du fichier lié au document.
        Si le lien est vide ou n'a pas d'extension, retourne '.any'.
        """
        if binary_file:
            return splitext(str(binary_file.filename))[1]
        else:
            return splitext(self.str_lien)[1] if self.str_lien else '.any'

    def create_name(self, *, binary_file: Optional[FileStorage]=None) -> 'Document':
        """
        Crée le nom du document en fonction de ses attributs.
        Format : JJMMYYYY_IDCONTRAT_IDDOCUMENT_SOUSTYPEDOCUMENT
        Exemple : 25092024_001_0001_Contr
        Arguments : None
        Returns: self
        """
        # Récupération de l'extension du fichier
        extention = self._get_extension(binary_file)

        # Création de la partie date au format JJMMYYYY
        date_date = datetime.strptime(str(self.date_document), '%Y-%m-%d')
        str_date = date_date.strftime('%d%m%Y')

        # Création des autres parties du nom
        id_contrat = str(self.id_contrat).zfill(3)
        id_document = str(self.id).zfill(4)
        sous_type_document = self.sous_type_document[:5] if self.sous_type_document else 'Docum'
        
        # Assemblage du nom complet et mise à jour des attributs
        self.name = secure_filename(f'{str_date}_{id_contrat}_{id_document}_{sous_type_document}')
        self.str_lien = self.name + extention
        return self

    def upload(self, file_to_upload: FileStorage) -> bool:
        """
        Fonction pour uploader le fichier du document.
        Utilise la fonction upload_file du module docs.py.
        Arguments :
            file (io.BytesIO): Fichier binaire à uploader
            extension (str): Extension du fichier (ex: .pdf, .docx)
        Returns :
            bool: True si l'upload a réussi, False sinon.
        """
        try:
            from docs import upload_file
            if self.str_lien:
                upload_file(file_to_upload, file_name=self.str_lien)
                return True
            else:
                return False
        except Exception:
            return False

    def rename_file(self) -> bool:
        """
        Fonction pour changer le nom du fichier du document.
        Utilise la fonction rename_file du module docs.py.
        Arguments :
            new_name (str): Nouveau nom sans extension
            extension (str): Extension du fichier (ex: .pdf, .docx)
        Returns :
            bool: True si le renommage a réussi, False sinon.
        """
        try:
            if self.str_lien:
                from docs import rename_file
                old_name = self.str_lien
                self.create_name()
                rename_file(old_file_name=old_name, new_file_name=self.str_lien)
                return True
            else:
                return False
        except Exception:
            return False
        
    def download(self):
        """
        Fonction pour télécharger le fichier du document.
        Utilise la fonction download_file du module docs.py.
        Arguments : None
        Returns :
            io.BytesIO: Fichier binaire téléchargé, ou None si échec.
        exemple :
            file = document.download()
            # or
            document.download()
        """
        try:
            if self.str_lien:
                from docs import download_file
                return download_file(self.str_lien)
        except Exception:
            return None
        
    def switch(self, *, file_to_switch: FileStorage, old_file_name: str)-> bool:
        """
        Fonction pour remplacer le fichier du document par un nouveau fichier.
        Arguments :
            file (FileStorage): Nouveau fichier binaire
        Returns :
            bool: True si le remplacement a réussi, False sinon.
        """
        try:
            if self.str_lien:
                from docs import exchange_files
                self.create_name(binary_file=file_to_switch)
                return exchange_files(old_file_name=old_file_name, new_file=file_to_switch,
                                      new_file_name=self.str_lien)
            else:
                return False
        except Exception:
            return False

class Event(Base): 
    __tablename__ = '12_evenements'
    id = mapped_column(Integer, primary_key=True)
    id_contrat = mapped_column(Integer, ForeignKey(CONTRACT_KEY), nullable=False)
    type_evenement = mapped_column(String(50), nullable=False)
    sous_type_evenement = mapped_column(String(50), nullable=False)
    date_evenement = mapped_column(Date, nullable=False)
    descriptif = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str: 
        return (f"<Event(id={self.id}, id_contrat={self.id_contrat}, date_evenement={self.date_evenement}, "
        f"type_evenement='{self.type_evenement}', sous_type_evenement='{self.sous_type_evenement}', descriptif='{self.descriptif}')>")
    
class Bill(Base):
    __tablename__ = '13_factures'
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_contrat = mapped_column(Integer, ForeignKey(CONTRACT_KEY), nullable=False)
    date_facture = mapped_column(Date, nullable=False)
    titre_facture = mapped_column(String(255), nullable=False)
    montant = mapped_column(Numeric(10, 2), nullable=False)
    str_lien = mapped_column(String(255), nullable=True)
    name = mapped_column(String(30), nullable=True)

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet Facture."""
        return (f"<Bill(id={self.id}, id_contrat={self.id_contrat}, date_facture={self.date_facture}, "
            f"titre_facture='{self.titre_facture}', montant={self.montant}, lien='{self.lien}')>")
    
    def _get_extension(self, binary_file: Optional[FileStorage]) -> str:
        """
        Retourne l'extension du fichier lié à la facture.
        Si le lien est vide ou n'a pas d'extension, retourne '.any'.
        """
        if binary_file:
            return splitext(str(binary_file.filename))[1]
        else:
            return splitext(self.str_lien)[1] if self.str_lien else '.any'
    
    def create_name(self, *, binary_file: Optional[FileStorage]=None) -> 'Bill':
        """
        Crée le nom de la facture en fonction de ses attributs.
        Format : JJMMYYYY_IDCONTRAT_IDFACTURE_TITREFACTURE
        Exemple : F10062024_005_0001_Factu
        Arguments : None
        Returns: self
        """
        # Réupération de l'extension du fichier
        extention = self._get_extension(binary_file)

        # Création de la partie date au format JJMMYYYY
        date_date = datetime.strptime(str(self.date_facture), '%Y-%m-%d')
        str_date = date_date.strftime('%d%m%Y')

        # Création des autres parties du nom
        id_contrat = str(self.id_contrat).zfill(3)
        id_bill = str(self.id).zfill(4)
        titre_facture = self.titre_facture[:5] if self.titre_facture else 'Factu'

        # Assemblage du nom complet et mise à jour des attributs
        self.name = secure_filename(f'F{str_date}_{id_contrat}_{id_bill}_{titre_facture}')
        self.str_lien = self.name + extention
        return self

    def upload(self, file_to_upload: FileStorage) -> bool:
        """
        Fonction pour uploader le fichier de la facture.
        Utilise la fonction upload_file du module docs.py.
        Arguments :
            file : Fichier binaire à uploader (io.BytesIO)
            extension : Extension du fichier (ex: .pdf, .docx)
        Returns :
            bool: True si l'upload a réussi, False sinon.
        """
        try:
            from docs import upload_file
            if self.str_lien:
                upload_file(file_to_upload, file_name=self.str_lien)
                return True
            else:
                return False
        except Exception:
            return False

    def rename_file(self) -> bool:
        """
        Fonction pour changer le nom du fichier du document.
        Utilise la fonction rename_file du module docs.py.
        Arguments :
            new_name (str): Nouveau nom sans extension
            extension (str): Extension du fichier (ex: .pdf, .docx)
        Returns :
            bool: True si le renommage a réussi, False sinon.
        """
        try:
            if self.str_lien:
                from docs import rename_file
                old_name = self.str_lien
                self.create_name()
                rename_file(old_file_name=old_name, new_file_name=self.str_lien)
                return True
            else:
                return False
        except Exception:
            return False

    def download(self):
        """
        Fonction pour télécharger le fichier de la facture.
        Utilise la fonction download_file du module docs.py.
        Arguments : None
        Returns :
            io.BytesIO: Fichier binaire téléchargé, ou None si échec.
        exemple :
            file = bill.download()
            # or
            bill.download()
        """
        try:
            if self.str_lien:
                from docs import download_file
                return download_file(self.str_lien)
        except Exception:
            return None
        
    def switch(self, *, file_to_switch: FileStorage, old_file_name: str) -> bool:
        """
        Fonction pour remplacer le fichier de la facture par un nouveau fichier.
        Arguments :
            file : Nouveau fichier binaire (FileStorage)
        Returns :
            bool: True si le remplacement a réussi, False sinon.
        """
        try:
            if self.str_lien:
                from docs import exchange_files
                self.create_name(binary_file=file_to_switch)
                return exchange_files(old_file_name=old_file_name, new_file=file_to_switch,
                                      new_file_name=self.str_lien)
            else:
                return False
        except Exception:
            return False
