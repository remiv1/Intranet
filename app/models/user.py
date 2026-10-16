"""Module contenant la modélisation de l'utilisateur dans l'application.

.. classes::
    - `User`: Représente un utilisateur dans la base de données.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.3.0
"""
from datetime import date
from typing import Optional, Dict, Any

from sqlalchemy import Integer, String, Date, Boolean
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy.sql import func

from ._common import Base, CASCADE

class User(Base):
    """
    Modèle représentant un utilisateur dans la base de données.

    :param id: Identifiant unique de l'utilisateur.
    :type id: int
    :param prenom: Prénom de l'utilisateur.
    :type prenom: str
    :param nom: Nom de l'utilisateur.
    :type nom: str
    :param mail: Adresse e-mail de l'utilisateur.
    :type mail: str
    :param identifiant: Identifiant de connexion de l'utilisateur.
    :type identifiant: str
    :param sha_mdp: Mot de passe hashé de l'utilisateur.
    :type sha_mdp: str
    :param habilitation: Niveau d'habilitation de l'utilisateur.
    :type habilitation: int
    :param debut: Date de début de validité de l'utilisateur.
    :type debut: date
    :param fin: Date de fin de validité de l'utilisateur.
    :type fin: date
    :param false_test: Nombre d'essais de connexion échoués.
    :type false_test: int
    :param locked: Indique si le compte est verrouillé.
    :type locked: bool

    .. table_name:: `99_users`
    
    .. relations::
        - documents (List[DocToSigne]): Liste des documents créés pour signature par l'utilisateur.
        - points (List[Points]): Liste des points associés à l'utilisateur.

    .. methods::
        - to_dict(with_mdp: bool = False) -> Dict[str, Optional[Any]]: Retourne un dictionnaire
        représentant l'utilisateur. Si with_mdp est True, inclut le mot de passe hashé dans
        le dictionnaire.
        - __repr__() -> str: Retourne une représentation textuelle de l'objet User.

    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    __tablename__ = '99_users'

    # Données principales
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Identifiant unique de l'utilisateur"
    )
    prenom: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Prénom de l'utilisateur"
    )
    nom: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nom de l'utilisateur"
    )

    # Authentification
    identifiant: Mapped[Optional[str]] = mapped_column(
        String(25),
        nullable=True,
        comment="Identifiant de connexion de l'utilisateur"
    )
    sha_mdp: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Mot de passe hashé de l'utilisateur"
    )
    habilitation: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Niveau d'habilitation de l'utilisateur"
    )

    # Coordonnées
    mail: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Adresse mail de l'utilisateur"
    )

    # Statut
    debut: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        default=func.current_date(),
        comment="Date de début de validité de l'utilisateur"
    )
    fin: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date de fin de validité de l'utilisateur"
    )
    false_test: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="Nombre d'essais de connexion échoués"
    )
    locked: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
        comment="Indique si le compte est verrouillé"
    )

    # Relations
    documents = relationship(
        "DocToSigne",
        back_populates="user",
        cascade=CASCADE,
    )
    points = relationship(
        "Points",
        back_populates="user",
        cascade=CASCADE,
    )

    def to_dict(self, with_mdp: bool = False) -> Dict[str, Optional[Any]]:
        """Retourne un dictionnaire représentant l'utilisateur. Si with_mdp est True, inclut
        le mot de passe hashé dans le dictionnaire.

        :param with_mdp: Indique si le mot de passe hashé doit être inclus. Defaults to False.
        :type with_mdp: bool

        :returns: Dictionnaire des attributs de l'utilisateur.
        :rtype: Dict[str, Optional[Any]]

        .. Exemple::
            Pour inclure le mot de passe hashé, utilisez :
            .. code-block:: python
                user_dict = user.to_dict(with_mdp=True)
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

        .. example::
            Le code suivant illustre l'utilisation de la méthode __repr__ :
            .. code-block:: python
                print(user)

            La sortie en console donne ceci :
            .. code-block:: console
                >>> <User(id=1, prenom='John', nom='Doe', mail='john.doe@example.com',
                identifiant='jdoe', habilitation=1, début=2024-01-01, fin=2024-12-31,
                bloqué=False)>
        """
        return (f"<User(id={self.id}, prenom='{self.prenom}', nom='{self.nom}', "
            f"mail='{self.mail}', identifiant='{self.identifiant}', "
            f"habilitation={self.habilitation}, "
            f"début={self.debut}, fin={self.fin}, bloqué={self.locked})>")
