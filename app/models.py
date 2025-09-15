from sqlalchemy import Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func

Base = declarative_base()

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
    id_contrat = mapped_column(Integer, ForeignKey('01_contrats.id'), nullable=False)
    type_document = mapped_column(String(50), nullable=False)
    sous_type_document = mapped_column(String(50), nullable=True)
    descriptif = mapped_column(String(255), nullable=False)
    str_lien = mapped_column(String(255), nullable=True)
    date_document = mapped_column(Date, nullable=False)
    name = mapped_column(String(30), nullable=True)

    def __repr__(self) -> str:
        return (f"<Document(id={self.id}, id_contrat={self.id_contrat}, type_document='{self.type_document}', sous_type_document='{self.sous_type_document}', "
            f"descriptif='{self.descriptif}', date_document={self.date_document}, str_lien='{self.str_lien}', name='{self.name}')>")

class Event(Base): 
    __tablename__ = '12_evenements'
    id = mapped_column(Integer, primary_key=True)
    id_contrat = mapped_column(Integer, ForeignKey('01_contrats.id'), nullable=False)
    type_evenement = mapped_column(String(50), nullable=False)
    sous_type_evenement = mapped_column(String(50), nullable=False)
    date_evenement = mapped_column(Date, nullable=False)
    descriptif = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str: 
        return (f"<Event(id={self.id}, id_contrat={self.id_contrat}, date_evenement={self.date_evenement}, "
        f"type_evenement='{self.type_evenement}', sous_type_evenement='{self.sous_type_evenement}', descriptif='{self.descriptif}')>")
    
