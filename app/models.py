from sqlalchemy import Column, Integer, String, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = '99_users'
    id = Column(Integer, primary_key=True)
    prenom = Column(String(255), nullable=False)
    nom = Column(String(255), nullable=False)
    mail = Column(String(255), nullable=False)
    identifiant = Column(String(25), nullable=True)
    shaMdp = Column(String(255), nullable=False)
    habilitation = Column(Integer, nullable=True)
    debut = Column(Date, nullable=True, default=func.current_date())
    fin = Column(Date, nullable=True)
    falseTest = Column(Integer, nullable=True, default=0)
    locked = Column(Boolean, nullable=True, default=False)

    def __repr__(self):
        return (f"<User(id={self.id}, prenom='{self.prenom}', nom='{self.nom}', "
            f"mail='{self.mail}', identifiant='{self.identifiant}', "
            f"shaMdp='{self.shaMdp}', habilitation={self.habilitation}, "
            f"debut={self.debut}, fin={self.fin}, locked={self.locked})>")
    
class Contract(Base):
    __tablename__ = '01_contrats'
    id = Column(Integer, primary_key=True)
    Type = Column(String(50), nullable=False)
    SType = Column(String(50), nullable=False)
    entreprise = Column(String(255), nullable=False)
    numContratExterne = Column(String(50), nullable=False)
    intitule = Column(String(255), nullable=False)
    dateDebut = Column(Date, nullable=False)
    dateFinPreavis = Column(Date, nullable=False)
    dateFin = Column(Date, nullable=True)

    def __repr__(self):
        return (f"<Contract(id={self.id}, Type='{self.Type}', SType='{self.SType}', "
            f"entreprise='{self.entreprise}', numContratExterne='{self.numContratExterne}', "
            f"intitule='{self.intitule}', dateDebut={self.dateDebut}, dateFinPreavis={self.dateFinPreavis}, "
            f"dateFin={self.dateFin})>")
    
class Document(Base):
    __tablename__ = '11_documents'
    id = Column(Integer, primary_key=True)
    idContrat = Column(Integer, nullable=False)
    Type = Column(String(50), nullable=False)
    SType = Column(String(50), nullable=True)
    descriptif = Column(String(255), nullable=False)
    strLien = Column(String(255), nullable=True)
    dateDocument = Column(Date, nullable=False)
    name = Column(String(30), nullable=True)

    def __repr__(self):
        return (f"<Document(id={self.id}, idContrat={self.idContrat}, Type='{self.Type}', SType='{self.SType}', "
            f"descriptif='{self.descriptif}', dateDocument={self.dateDocument}, strLien='{self.strLien}', name='{self.str_Name}')>")

class Event(Base): 
    __tablename__ = '12_evenements'
    id = Column(Integer, primary_key=True)
    idContrat = Column(Integer, nullable=False)
    dateEvenement = Column(Date, nullable=False)
    Type = Column(String(50), nullable=False)
    SType = Column(String(50), nullable=False)
    descriptif = Column(String(255), nullable=False)

    def __repr__(self): 
        return (f"<Event(id={self.id}, idContrat={self.idContrat}, dateEvenement={self.dateEvenement}, "
        f"Type='{self.Type}', SType='{self.SType}', descriptif='{self.descriptif}')>")