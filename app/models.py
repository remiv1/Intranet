from sqlalchemy import Integer, String, Date, Boolean, ForeignKey, Numeric, DateTime, Text, Computed
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
PK_USER = '99_users.id'
PK_POINTS = '23_points.id'
CASCADE = "all, delete-orphan"

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
    documents = relationship("DocToSigne", back_populates="user", cascade=CASCADE)
    points = relationship("Points", back_populates="user", cascade=CASCADE)

    def to_dict(self, with_mdp: bool = False) -> Dict[str, Optional[Any]]:
        """
        Retourne un dictionnaire représentant l'utilisateur.
        Si with_mdp est True, inclut le mot de passe hashé dans le dictionnaire.
        Arguments :
            with_mdp (bool): Indique si le mot de passe hashé doit être inclus. Defaults to False.
        Returns :
            Dict[str, Optional[Any]]: Dictionnaire des attributs de l'utilisateur.
        Exemple d'utilisation :
            ```python
            user_dict = user.to_dict(with_mdp=True)
            ```
        """
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
        """
        Retourne une représentation textuelle de l'objet User.
        Exemple :
            ```python
            print(user)
            ```
            ```console
            <User(id=1, prenom='John', nom='Doe', mail='john.doe@example.com', identifiant='jdoe', habilitation=1, début=2024-01-01, fin=2024-12-31, bloqué=False)>
            ```
        """
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
    contacts = relationship("Contacts", back_populates="contrat", cascade=CASCADE)
    evenements = relationship("Event", back_populates="contrat", cascade=CASCADE)
    factures = relationship("Bill", back_populates="contrat", cascade=CASCADE)
    documents = relationship("Document", back_populates="contrat", cascade=CASCADE)

    def __repr__(self) -> str:
        """
        Représentation textuelle de l'objet Contract.
        Exemple :
            ```python
            print(contract)
            ```
            ```console
            <Contract(id=1, type_contrat='Immobilier', sous_type_contrat='Bail commercial', entreprise='Entreprise XYZ', id_externe_contrat='C12345', intitule='Contrat de location bureau', date_debut=2024-01-01, date_fin_preavis=2024-12-31, date_fin=2025-12-31)>
            ```
        """
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

    # Données principales
    id = mapped_column(Integer, primary_key=True)
    id_contrat = mapped_column(Integer, ForeignKey(PK_CONTRACT), nullable=False)

    # Coordonnées
    nom = mapped_column(String(255), nullable=False)
    fonction = mapped_column(String(100), nullable=True)
    mail = mapped_column(String(255), nullable=False)
    tel_fixe = mapped_column(String(20), nullable=True)
    tel_portable = mapped_column(String(20), nullable=True)
    adresse = mapped_column(String(255), nullable=True)
    code_postal = mapped_column(String(10), nullable=True)
    ville = mapped_column(String(100), nullable=True)

    # Relations
    contrat = relationship("Contract", back_populates="contacts")

    def __repr__(self) -> str:
        """
        Représentation textuelle de l'objet Contacts.
        Exemple :
            ```python
            print(contact)
            ```
            ```console
            <Contacts(id=1, id_contrat=1, nom='Doe', prenom='John', fonction='Manager', mail='john.doe@example.com', tel_fixe='0123456789', tel_portable='0612345678', adresse='123 Rue de Paris', code_postal='75001', ville='Paris', pays='France')>
            ```
        """
        return (f"<Contacts(id={self.id}, id_contrat={self.id_contrat}, nom='{self.nom}', prenom='{self.prenom}', "
            f"fonction='{self.fonction}', mail='{self.mail}', tel_fixe='{self.tel_fixe}', "
            f"tel_portable='{self.tel_portable}', adresse='{self.adresse}', code_postal='{self.code_postal}', "
            f"ville='{self.ville}', pays='{self.pays}')>")

class Document(Base):
    """
    Représente un document associé à un contrat.
    Attributs :
        id (int): Identifiant unique du document.
        id_contrat (int): Identifiant du contrat associé.
        date_document (date): Date du document.
        type_document (str): Type du document (Contrat, Avenant, etc.).
        sous_type_document (str): Sous-type du document.
        descriptif (str): Descriptif du document.
        str_lien (str): Chemin du fichier stocké.
        name (str): Nom du fichier stocké.
    Relations :
        contrat (Contract): Contrat associé au document.
    Méthodes :
        __repr__() -> str:
            Retourne une représentation textuelle de l'objet Document.
        _get_extension(binary_file: Optional[FileStorage]=None) -> str:
            Retourne l'extension du fichier lié au document.
        create_name(binary_file: Optional[FileStorage]=None) -> 'Document':
            Crée le nom du document en fonction de ses attributs.
        upload(file_to_upload: FileStorage) -> bool:
            Télécharge le fichier associé au document.
        rename_file() -> bool:
            Change le nom du fichier associé au document.
        download() -> Optional[io.BytesIO]:
            Télécharge le fichier associé au document.
        switch(file_to_switch: FileStorage, old_file_name: str) -> bool:
            Remplace le fichier du document par un nouveau fichier.
    """
    __tablename__ = '11_documents'

    # Données principales
    id = mapped_column(Integer, primary_key=True)
    id_contrat = mapped_column(Integer, ForeignKey(PK_CONTRACT), nullable=False)
    date_document = mapped_column(Date, nullable=False)
    type_document = mapped_column(String(50), nullable=False)
    sous_type_document = mapped_column(String(50), nullable=True)
    descriptif = mapped_column(String(255), nullable=False)

    # Données du fichier binaire
    str_lien = mapped_column(String(255), nullable=True)
    name = mapped_column(String(30), nullable=True)

    # Relations
    contrat = relationship("Contract", back_populates="documents")

    def __repr__(self) -> str:
        """
        Représentation textuelle de l'objet Document.
        Exemple :
            ```python
            print(document)
            ```
            ```console
            <Document(id=1, name='25092024_001_0001_Contr', date_document=2024-09-25, id_contrat=1, type_document='Contrat', sous_type_document='Contrat de service', descriptif='Contrat de service annuel')>
            ```
        """
        return (f"<Document(id={self.id}, name='{self.name}', date_document={self.date_document}, "
            f"id_contrat={self.id_contrat}, type_document='{self.type_document}', "
            f"sous_type_document='{self.sous_type_document}', descriptif='{self.descriptif}')>")
    
    def _get_extension(self, *, binary_file: Optional[FileStorage]=None) -> str:
        """
        Retourne l'extension du fichier lié au document.
        Si le lien est vide ou n'a pas d'extension, retourne '.any'.
        Arguments :
            binary_file (FileStorage, optional): Fichier binaire pour extraire l'extension. Defaults to None.
        Returns:
            str: Extension du fichier (ex: .pdf, .docx) ou '.any' si non disponible.
        Fonction protégée utilisée en interne de la classe.
        """
        if binary_file:
            return splitext(str(binary_file.filename))[1]
        else:
            return splitext(self.str_lien)[1] if self.str_lien else '.any'

    def create_name(self, *, binary_file: Optional[FileStorage]=None) -> 'Document':
        """
        Crée le nom du document en fonction de ses attributs.
        Format : JJMMYYYY_IDCONTRAT_IDDOCUMENT_SOUSTYPEDOCUMENT
        Arguments :
            binary_file (FileStorage, optional): Fichier binaire pour extraire l'extension. Defaults to None.
        Returns:
            self
        Exemple d'utilisation :
            ```python
            document.create_name(binary_file=binary_file)
            ```
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
        Exemple d'utilisation :
            ```python
            document.upload(file_to_upload=binary_file)
            ```
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
        Exemple d'utilisation :
            ```python
            document.create_name().rename_file()
            ```
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
        Arguments :
            None
        Returns :
            io.BytesIO: Fichier binaire téléchargé, ou None si échec.
        exemple :
            ```python
            file = document.download()
            # or
            document.download()
            ```
        """
        try:
            if self.str_lien:
                from docs import download_file
                return download_file(self.str_lien)
        except Exception:
            return None

    def switch(self, *, file_to_switch: FileStorage, old_file_name: str) -> bool:
        """
        Fonction pour remplacer le fichier du document par un nouveau fichier.
        Arguments :
            file (FileStorage): Nouveau fichier binaire
        Returns :
            bool: True si le remplacement a réussi, False sinon.
        Exemple d'utilisation :
            ```python
            document.switch(file_to_switch=binary_file, old_file_name='ancien_nom.pdf')
            ```
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
    """
    Représente un événement associé à un contrat.
    Attributs :
        id (int): Identifiant unique de l'événement.
        id_contrat (int): Identifiant du contrat associé.
        type_evenement (str): Type de l'événement (Renouvellement, Résiliation, etc.).
        sous_type_evenement (str): Sous-type de l'événement.
        date_evenement (date): Date de l'événement.
        descriptif (str): Descriptif de l'événement.
    Relations :
        contrat (Contract): Contrat associé à l'événement.
    Méthodes :
        __repr__() -> str:
            Retourne une représentation textuelle de l'objet Event.
    """
    __tablename__ = '12_evenements'

    # Données principales
    id = mapped_column(Integer, primary_key=True)
    id_contrat = mapped_column(Integer, ForeignKey(PK_CONTRACT), nullable=False)
    type_evenement = mapped_column(String(50), nullable=False)
    sous_type_evenement = mapped_column(String(50), nullable=False)
    date_evenement = mapped_column(Date, nullable=False)
    descriptif = mapped_column(String(255), nullable=False)

    # Relations
    contrat = relationship("Contract", back_populates="evenements")

    def __repr__(self) -> str:
        """
        Représentation textuelle de l'objet Event.
        Exemple :
            ```python
            print(event)
            ```
            ```console
            <Event(id=1, id_contrat=1, date_evenement=2024-09-25, type_evenement='Renouvellement', sous_type_evenement='Annuel', descriptif='Renouvellement du contrat annuel')>
            ```
        """
        return (f"<Event(id={self.id}, id_contrat={self.id_contrat}, date_evenement={self.date_evenement}, "
        f"type_evenement='{self.type_evenement}', sous_type_evenement='{self.sous_type_evenement}', descriptif='{self.descriptif}')>")
    
class Bill(Base):
    """
    Représente une facture associée à un contrat.
    Attributs :
        id (int): Identifiant unique de la facture.
        id_contrat (int): Identifiant du contrat associé.
        date_facture (date): Date de la facture.
        titre_facture (str): Titre de la facture.
        montant (Decimal): Montant de la facture.
        str_lien (str): Chemin du fichier de la facture.
        name (str): Nom du fichier de la facture.
    Relations :
        contrat (Contract): Contrat associé à la facture.
    Méthodes :
        __repr__() -> str:
            Retourne une représentation textuelle de l'objet Bill.
        _get_extension(binary_file: Optional[FileStorage]=None) -> str:
            Retourne l'extension du fichier lié à la facture.
        create_name(binary_file: Optional[FileStorage]=None) -> 'Bill':
            Crée le nom de la facture en fonction de ses attributs.
        upload(file_to_upload: FileStorage) -> bool:
            Uploade le fichier de la facture.
        rename_file() -> bool:
            Change le nom du fichier de la facture.
        download() -> Optional[io.BytesIO]:
            Télécharge le fichier de la facture.
        switch(file_to_switch: FileStorage, old_file_name: str) -> bool:
            Remplace le fichier de la facture par un nouveau fichier.
    """
    __tablename__ = '13_factures'

    # Données principales
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_contrat = mapped_column(Integer, ForeignKey(PK_CONTRACT), nullable=False)
    date_facture = mapped_column(Date, nullable=False)
    titre_facture = mapped_column(String(255), nullable=False)
    montant = mapped_column(Numeric(10, 2), nullable=False)

    # Données du fichier binaire
    str_lien = mapped_column(String(255), nullable=True)
    name = mapped_column(String(30), nullable=True)

    # Relations
    contrat = relationship("Contract", back_populates="factures")

    def __repr__(self) -> str:
        """
        Représentation textuelle de l'objet Facture.
        Exemple :
            ```python
            print(bill)
            ```
            ```console
            <Bill(id=1, id_contrat=1, date_facture=2024-09-25, titre_facture='Consulting', montant=1500.00, lien='25092024_001_0001_Consu.pdf')>
            ```
        """
        return (f"<Bill(id={self.id}, id_contrat={self.id_contrat}, date_facture={self.date_facture}, "
            f"titre_facture='{self.titre_facture}', montant={self.montant}, lien='{self.str_lien}')>")
    
    def _get_extension(self, *, binary_file: Optional[FileStorage]=None) -> str:
        """
        Retourne l'extension du fichier lié à la facture.
        Si le lien est vide ou n'a pas d'extension, retourne '.any'.
        Arguments :
            binary_file (FileStorage, optional): Fichier binaire pour extraire l'extension. Defaults to None.
        Returns:
            str: Extension du fichier (ex: .pdf, .docx) ou '.any' si non disponible.
        Fonction protégée utilisée en interne de la classe.
        """
        if binary_file:
            return splitext(str(binary_file.filename))[1]
        else:
            return splitext(self.str_lien)[1] if self.str_lien else '.any'
    
    def create_name(self, *, binary_file: Optional[FileStorage]=None) -> 'Bill':
        """
        Crée le nom de la facture en fonction de ses attributs.
        Format : JJMMYYYY_IDCONTRAT_IDFACTURE_TITREFACTURE
        Arguments : 
            binary_file (FileStorage, optional): Fichier binaire pour extraire l'extension. Defaults to None.
        Returns:
            self
        Exemple d'utilisation :
            ```python
            bill.create_name(binary_file=binary_file)
            ```
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
        Exemple d'utilisation :
            ```python
            bill.upload(file_to_upload=binary_file)
            ```
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
        Exemple d'utilisation :
            ```python
            bill.create_name().rename_file()
            ```
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
        Exemple :
            ```python
            file = bill.download()
            # or
            bill.download()
            ```
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
        Exemple d'utilisation :
            ```python
            bill.switch(file_to_switch=new_file, old_file_name=old_file_name)
            ```
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
    #TODO: prévoir un soft_delete des utilisateurs pour conservation pendant la durée de validité des documents
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
    
class Signatures(Base):
    """
    Représente une signature apposée sur un document.
    Attributs :
        id (int): Identifiant unique de la signature.
        signe_at (datetime): Date et heure de la signature.
        signature_hash (str): Hash de la signature pour vérification.
        ip_addresse (str): Adresse IP de l'utilisateur au moment de la signature.
        user_agent (str): User-Agent du navigateur au moment de la signature.
        statut (int): Statut de la signature (0: en attente, 1: signé, -1: annulé, -2: expiré).
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
    statut = mapped_column(Integer, default=0)                      # 0: en attente, 1: signé, -1: annulé, -2: expiré
    
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
            f"statut={self.statut})>")
    
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
    
    # Méta-données
    mail_envoye = mapped_column(Boolean, default=False)
    mail_compte = mapped_column(Integer, default=0)
    
    # Relations
    document = relationship("DocToSigne")
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
    action = mapped_column(Integer, nullable=False)  # -2: annulé, -1: expiré, 0: créé, 1: consulté, 2: signé, 3: expédié
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
