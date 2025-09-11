from sqlalchemy import Integer, String, Date, Boolean
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
    shaMdp = mapped_column(String(255), nullable=False)
    habilitation = mapped_column(Integer, nullable=True)
    debut = mapped_column(Date, nullable=True, default=func.current_date())
    fin = mapped_column(Date, nullable=True)
    falseTest = mapped_column(Integer, nullable=True, default=0)
    locked = mapped_column(Boolean, nullable=True, default=False)

    def __repr__(self):
        return (f"<User(id={self.id}, prenom='{self.prenom}', nom='{self.nom}', "
            f"mail='{self.mail}', identifiant='{self.identifiant}', "
            f"shaMdp='{self.shaMdp}', habilitation={self.habilitation}, "
            f"debut={self.debut}, fin={self.fin}, locked={self.locked})>")
    
class Contract(Base):
    __tablename__ = '01_contrats'
    id = mapped_column(Integer, primary_key=True)
    Type = mapped_column(String(50), nullable=False)
    SType = mapped_column(String(50), nullable=False)
    entreprise = mapped_column(String(255), nullable=False)
    numContratExterne = mapped_column(String(50), nullable=False)
    intitule = mapped_column(String(255), nullable=False)
    dateDebut = mapped_column(Date, nullable=False)
    dateFinPreavis = mapped_column(Date, nullable=False)
    dateFin = mapped_column(Date, nullable=True)

    def __repr__(self):
        return (f"<Contract(id={self.id}, Type='{self.Type}', SType='{self.SType}', "
            f"entreprise='{self.entreprise}', numContratExterne='{self.numContratExterne}', "
            f"intitule='{self.intitule}', dateDebut={self.dateDebut}, dateFinPreavis={self.dateFinPreavis}, "
            f"dateFin={self.dateFin})>")
    
class Document(Base):
    __tablename__ = '11_documents'
    id = mapped_column(Integer, primary_key=True)
    idContrat = mapped_column(Integer, nullable=False)
    Type = mapped_column(String(50), nullable=False)
    SType = mapped_column(String(50), nullable=True)
    descriptif = mapped_column(String(255), nullable=False)
    strLien = mapped_column(String(255), nullable=True)
    dateDocument = mapped_column(Date, nullable=False)
    name = mapped_column(String(30), nullable=True)

    def __repr__(self):
        return (f"<Document(id={self.id}, idContrat={self.idContrat}, Type='{self.Type}', SType='{self.SType}', "
            f"descriptif='{self.descriptif}', dateDocument={self.dateDocument}, strLien='{self.strLien}', name='{self.str_Name}')>")

class Event(Base): 
    __tablename__ = '12_evenements'
    id = mapped_column(Integer, primary_key=True)
    idContrat = mapped_column(Integer, nullable=False)
    dateEvenement = mapped_column(Date, nullable=False)
    Type = mapped_column(String(50), nullable=False)
    SType = mapped_column(String(50), nullable=False)
    descriptif = mapped_column(String(255), nullable=False)

    def __repr__(self): 
        return (f"<Event(id={self.id}, idContrat={self.idContrat}, dateEvenement={self.dateEvenement}, "
        f"Type='{self.Type}', SType='{self.SType}', descriptif='{self.descriptif}')>")
    
