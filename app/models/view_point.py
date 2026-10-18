"""Module représentant la vue des points de signature.

.. classes::
    - `ViewPoints`: Classe représentant la vue des points de signature.

    
.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

from typing import Dict, Any, List
from flask import g

from .points import Points
from .user import User
from .signature import Signatures

class ViewPoints:
    """Classe de vue des points de signature.

    :param points: Instance du point de signature.
    :type points: List[Points]

    .. methodes::
        - `__init__(self, points: List[Points]) -> None`: Initialise les attributs de la classe.
    """

    def __init__(self, points: List[Points]) -> None:
        """Récupère les informations liées aux points de signature ainsi que les utilisateurs
        et signatures associées.

        :param points: Liste des points de signature.
        :type points: List[Points]

        .. exemple::
            .. code-block:: python
            view_points = ViewPoints(points)
        """
        self.points: List[Any] = []
        for p in points:
            user = g.db_session.query(User).filter(User.id == p.id_user).first()
            signature = g.db_session.query(Signatures) \
                .filter(Signatures.id == p.id_signature) \
                .first()
            point_list: List[Any] = [p, user, signature]
            self.points.append(point_list)

    def __repr__(self) -> str:
        """ Représentation textuelle de l'objet ViewPoints.
        .. exemple::
            .. code-block:: python
                print(view_points)
                >>> <ViewPoints(nombre de points=3)>
        """
        return f"<ViewPoints(nombre de points={len(self.points)})>"

    def to_dict(self) -> List[Dict[str, Any]]:
        """ Convertit la liste des points en une liste de dictionnaires.

        :return: Liste de dictionnaires représentant les points.
        :rtype: list[Dict[str, Any]]
        
        .. exemple::
            .. code-block:: python
                points_dict = view_points.to_dict()
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
