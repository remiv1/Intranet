from typing import List, Dict, Any, Optional, overload, Literal, Union
from os.path import dirname, join as join_os
import json

# Création des variables et constantes
NOT_ALLOWED = 'Accès non autorisé'
RESERVED_SPACE = 'Espace réservé'
JSON_MENUS = 'menus.json'
TYPINGS = 'types et sous-types'
ACCUEIL_CONTRAT = 'contracts_bp.contrats'
DETAIL_CONTRAT = 'contracts_bp.contrats_by_num'

@overload
def get_jsoned_datas(file: str, level_one: str, *, dumped: Literal[True]) -> str: ...
@overload  
def get_jsoned_datas(file: str, level_one: str, level_two: str, *, dumped: Literal[True]) -> str: ...
@overload
def get_jsoned_datas(file: str, level_one: str, *, dumped: Literal[False] = False) -> List[Dict[str, Any]]: ...
@overload
def get_jsoned_datas(file: str, level_one: str, level_two: str, *, dumped: Literal[False] = False) -> Union[Dict[str, Any], List[Dict[str, Any]]]: ...

def get_jsoned_datas(file: str, level_one: str, level_two: Optional[str] = None, dumped: bool = False
                     ) -> Union[str, Dict[str, Any], list[Any]]:
    """
    Récupère les menus depuis le fichier JSON et les convertit en chaîne JSON.
    Args:
        file (str): Le nom du fichier JSON.
        level_one (str): Le niveau un à récupérer dans le JSON.
        level_two (Optional[str]): Le niveau deux à récupérer dans le JSON (optionnel).
        dumped (Optional[bool]): Si True, retourne une chaîne JSON, sinon retourne un dictionnaire ou une liste.
    Returns:
        str ou Dict[str, Any] ou List[Any]: Les menus au format JSON ou en tant que structure de données Python.
    """
    with open(join_os(dirname(__file__), 'json', file), 'r', encoding='utf-8') as f:
        data = json.load(f)
        if level_two is None:
            menus_json = data[1][level_one]
        else:
            menus_json = data[1][level_one][0][level_two]
    if dumped:
        return json.dumps(menus_json, ensure_ascii=False)
    return menus_json
