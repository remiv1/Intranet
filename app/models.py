from sqlalchemy import Integer, String, Date, Boolean, ForeignKey, Numeric, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.sql import func
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from typing import Optional, Dict, Any
from datetime import datetime
from os.path import splitext

Base = declarative_base()
PK_CONTRACT = '01_contrats.id'
PK_DOC_TO_SIGNE = '20_documents_a_signer.id'

class User(Base):
    """
    Modèle représentant un utilisateur dans la base de données.
    Attributs :
        id (int): Identifiant unique de l'utilisateur.
        prenom (str): Prénom de l'utilisateur.
        nom (str): Nom de l'utilisateur.
        mail (str): Adresse e-mail de l'utilisateur.
        identifiant (str): Identifiant de connexion de l'utilisateur.
        sha_mdp (str): Mot de passe hashé de l'utilisateur.
        habilitation (int): Niveau d'habilitation de l'utilisateur.
        debut (date): Date de début de validité de l'utilisateur.
        fin (date): Date de fin de validité de l'utilisateur.
        false_test (int): Nombre d'essais de connexion échoués.
        locked (bool): Indique si le compte est verrouillé.
    Relations :
        documents (List[DocToSigne]): Liste des documents créés pour signature par l'utilisateur.
    Méthodes :
        to_dict(with_mdp: bool = False) -> Dict[str, Optional[Any]]:
            Retourne un dictionnaire représentant l'utilisateur.
            Si with_mdp est True, inclut le mot de passe hashé dans le dictionnaire.
        __repr__() -> str:
            Retourne une représentation textuelle de l'objet User.
    """
    __tablename__ = '99_users'

    # Données principales
    id = mapped_column(Integer, primary_key=True)
    prenom = mapped_column(String(255), nullable=False)
    nom = mapped_column(String(255), nullable=False)

    # Authentification
    identifiant = mapped_column(String(25), nullable=True)
    sha_mdp = mapped_column(String(255), nullable=False)
    habilitation = mapped_column(Integer, nullable=True)

    # Coordonnées
    mail = mapped_column(String(255), nullable=False)

    # Statut
    debut = mapped_column(Date, nullable=True, default=func.current_date())
    fin = mapped_column(Date, nullable=True)
    false_test = mapped_column(Integer, nullable=True, default=0)   # nombre d'essais de connexion échoués
    locked = mapped_column(Boolean, nullable=True, default=False)

    # Relations
    documents = relationship("DocToSigne", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self, with_mdp: bool = False) -> Dict[str, Optional[Any]]:
        user_dict: Dict[str, Optional[Any]] = {
            "id": self.id,
            "prenom": self.prenom,
            "nom": self.nom,
            "mail": self.mail,
            "identifiant": self.identifiant,
            "habilitation": self.habilitation,
            "debut": self.debut.isoformat() if self.debut else None,
            "fin": self.fin.isoformat() if self.fin else None,
            "locked": self.locked
        }
        if with_mdp:
            user_dict["sha_mdp"] = self.sha_mdp
        return user_dict

    def __repr__(self) -> str:
        return (f"<User(id={self.id}, prenom='{self.prenom}', nom='{self.nom}', "
            f"mail='{self.mail}', identifiant='{self.identifiant}', "
            f"habilitation={self.habilitation}, "
            f"début={self.debut}, fin={self.fin}, bloqué={self.locked})>")
    
class Contract(Base):
    """
    Représente un contrat dans le système.
    Attributs :
        id (int): Identifiant unique du contrat.
        type_contrat (str): Type du contrat (Immobilier, Services, ...).
        sous_type_contrat (str): Sous-type du contrat (Suivant dictionnaire des types et sous_type).
        entreprise (str): Nom de l'entreprise associée au contrat.
        id_externe_contrat (str): Identifiant externe du contrat (numéro de contrat).
        intitule (str): Intitulé du contrat.
        date_debut (date): Date de début de validité du contrat.
        date_fin_preavis (date): Date de fin de préavis du contrat.
        date_fin (date): Date de fin de validité du contrat (optionnelle).
    Relations :
        contacts (List[Contacts]): Liste des contacts associés au contrat.
    Méthodes :
        __repr__() -> str:
            Retourne une représentation textuelle de l'objet Contract.
    """
    
    __tablename__ = '01_contrats'

    # Données principales
    id = mapped_column(Integer, primary_key=True)
    type_contrat = mapped_column(String(50), nullable=False)
    sous_type_contrat = mapped_column(String(50), nullable=False)
    entreprise = mapped_column(String(255), nullable=False)
    id_externe_contrat = mapped_column(String(50), nullable=False)
    intitule = mapped_column(String(255), nullable=False)

    # Dates
    date_debut = mapped_column(Date, nullable=False)
    date_fin_preavis = mapped_column(Date, nullable=False)
    date_fin = mapped_column(Date, nullable=True)

    # Relations
    contacts = relationship("Contacts", back_populates="contrat", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (f"<Contract(id={self.id}, type_contrat='{self.type_contrat}', sous_type_contrat='{self.sous_type_contrat}', "
            f"entreprise='{self.entreprise}', id_externe_contrat='{self.id_externe_contrat}', "
            f"intitule='{self.intitule}', date_debut={self.date_debut}, date_fin_preavis={self.date_fin_preavis}, "
            f"date_fin={self.date_fin})>")

class Contacts(Base):
    """
    Représente un contact associé à un contrat.
    Attributs :
        id (int): Identifiant unique du contact.
        id_contrat (int): Identifiant du contrat associé.
        nom (str): Nom du contact.
        fonction (str): Fonction du contact.
        mail (str): Adresse e-mail du contact.
        tel_fixe (str): Numéro de téléphone fixe du contact.
        tel_portable (str): Numéro de téléphone portable du contact.
        adresse (str): Adresse postale du contact.
        code_postal (str): Code postal du contact.
        ville (str): Ville du contact.
    
    """
    __tablename__ = '02_contacts'
    id = mapped_column(Integer, primary_key=True)
    id_contrat = mapped_column(Integer, ForeignKey(PK_CONTRACT), nullable=False)
    contrat = relationship("Contract", back_populates="contacts")
    nom = mapped_column(String(255), nullable=False)
    fonction = mapped_column(String(100), nullable=True)
    mail = mapped_column(String(255), nullable=False)
    tel_fixe = mapped_column(String(20), nullable=True)
    tel_portable = mapped_column(String(20), nullable=True)
    adresse = mapped_column(String(255), nullable=True)
    code_postal = mapped_column(String(10), nullable=True)
    ville = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (f"<Contacts(id={self.id}, id_contrat={self.id_contrat}, nom='{self.nom}', prenom='{self.prenom}', "
            f"fonction='{self.fonction}', mail='{self.mail}', tel_fixe='{self.tel_fixe}', "
            f"tel_portable='{self.tel_portable}', adresse='{self.adresse}', code_postal='{self.code_postal}', "
            f"ville='{self.ville}', pays='{self.pays}')>")

class Document(Base):
    __tablename__ = '11_documents'
    id = mapped_column(Integer, primary_key=True)
    id_contrat = mapped_column(Integer, ForeignKey(PK_CONTRACT), nullable=False)
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
    
    def _get_extension(self, *, binary_file: Optional[FileStorage]=None) -> str:
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
        self.str_lien = self.name + extention
        return self

    def upload(self, *, file_to_upload: FileStorage) -> bool:
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
    id_contrat = mapped_column(Integer, ForeignKey(PK_CONTRACT), nullable=False)
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
    id_contrat = mapped_column(Integer, ForeignKey(PK_CONTRACT), nullable=False)
    date_facture = mapped_column(Date, nullable=False)
    titre_facture = mapped_column(String(255), nullable=False)
    montant = mapped_column(Numeric(10, 2), nullable=False)
    str_lien = mapped_column(String(255), nullable=True)
    name = mapped_column(String(30), nullable=True)

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet Facture."""
        return (f"<Bill(id={self.id}, id_contrat={self.id_contrat}, date_facture={self.date_facture}, "
            f"titre_facture='{self.titre_facture}', montant={self.montant}, lien='{self.str_lien}')>")
    
    def _get_extension(self, *, binary_file: Optional[FileStorage]=None) -> str:
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
        # Récupération de l'extension du fichier
        extention = self._get_extension(binary_file=binary_file)

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

    def upload(self, *, file_to_upload: FileStorage) -> bool:
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

class DocToSigne(Base):
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
    id_user = mapped_column(Integer, ForeignKey('99_users.id'), nullable=True) # identifiant créateur
    cree_at = mapped_column(DateTime, default=func.now())
    
    # Statuts et dates
    status = mapped_column(Integer, nullable=False, default=0)                      # -2: annulé, -1: expiré, 0: en attente, 1: signé
    limite_signature = mapped_column(DateTime, nullable=False, computed="DATE_ADD(cree_at, INTERVAL echeance DAY)")
    complete_at = mapped_column(DateTime, nullable=True)
    
    # Relations
    user = relationship("User", back_populates="documents")
    points = relationship("Points", back_populates="document", cascade="all, delete-orphan")
    signatures = relationship("Signature", back_populates="document", cascade="all, delete-orphan")

