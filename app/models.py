from typing import Dict, Any, List

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.sql import func
from flask import g


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
    action = mapped_column(Integer, nullable=False)  # -2: annuler, -1: expirer, 0: créer, 1: consulter, 2: signer, 3: expédier
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

class ViewPoints:
    """
    Classe de vue 
    Attributs :
        point: Points: Instance du point de signature.
        user: User: Instance de l'utilisateur signataire.
        signature: Signatures: Instance de la signature apposée (si signée).
        user_mail: str: Adresse e-mail de l'utilisateur (pour affichage).
        user_complete_name: str: Nom complet de l'utilisateur (pour affichage).
    Méthodes :
        __init__(self, points: List[Points]) -> None:
            Initialise les attributs de la classe.
    """

    def __init__(self, points: List[Points]) -> None:
        """
        Récupère les informations liées aux points de signature et les utilisateurs et signatures associées.
        Arguments :
            points (List[Points]): Liste des points de signature.
        Exemple d'utilisation :
            ```python
            view_points = ViewPoints(points)
            ```
        """
        self.points: List[Any] = []
        for p in points:
            user = g.db_session.query(User).filter(User.id == p.id_user).first()
            signature = g.db_session.query(Signatures).filter(Signatures.id == p.id_signature).first()
            point_list: List[Any] = [p, user, signature]
            self.points.append(point_list)

    def __repr__(self) -> str:
        """
        Représentation textuelle de l'objet ViewPoints.
        Exemple :
            ```python
            print(view_points)
            ```
            ```console
            <ViewPoints(nombre de points=3)>
            ```
        """
        return f"<ViewPoints(nombre de points={len(self.points)})>"
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """
        Convertit la liste des points en une liste de dictionnaires.
        Utile pour la sérialisation JSON.
        Returns:
            list: Liste de dictionnaires représentant les points.
        Exemple d'utilisation :
            ```python
            points_dict = view_points.to_dict()
            ```
        """
        points_list: List[Dict[str, Any]] = []
        for p, u, s in self.points:
            point: Dict[str, Any] = {
                "user": u.to_dict() if u else None,
                "user_mail": u.mail if u else None,
                "user_complete_name": f'{u.prenom} {u.nom}' if u else None,
                "point": p.to_dict(),
                "signature": s.to_dict() if s else None
            }
            points_list.append(point)
        return points_list
