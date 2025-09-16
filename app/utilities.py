from typing import List, Dict, Any, Optional, overload, Literal, Union
from os.path import dirname, join as join_os, splitext
from models import Document, Bill
from docs import create_name, exchange_files, rename_file
from flask import g
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

def check_changements(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> bool:
    """
    Compare deux dictionnaires et vérifie s'il y a des changements entre eux.
    Args:
        old_data (Dict[str, Any]): Le dictionnaire original.
        new_data (Dict[str, Any]): Le dictionnaire à comparer.
    Returns:
        bool: True s'il y a des changements, False sinon.
    """
    for key in new_data:
        if key in old_data and old_data[key] != new_data[key]:
            return True
    return False

def _update_document_file(document_model: Document, new_binary_document: Any, new_values: Dict[str, Any],
                          id_contrat: int, id_document: Optional[int], context_changes: bool, binary_changes: bool):
    if not context_changes and binary_changes:
        name = splitext(document_model.str_lien)[0]
        extention = splitext(str(new_binary_document.filename))[1]
        exchange_files(old_file_name=document_model.str_lien, new_file=new_binary_document,
                       new_file_name=name, extension=extention)
        document_model.str_lien = name + extention
        document_model.name = name
    else:
        document_model.date_document = new_values['date_document']
        document_model.type_document = new_values['type_document']
        document_model.sous_type_document = new_values['sous_type_document']
        name = create_name(new_values['date_document'], str(id_contrat), str(id_document), new_values['sous_type_document'])
        if binary_changes:
            extention = splitext(str(new_binary_document.filename))[1]
            exchange_files(old_file_name=document_model.str_lien, new_file=new_binary_document,
                           new_file_name=name, extension=extention)
        else:
            extention = splitext(str(document_model.str_lien))[1]
            rename_file(old_file_name=document_model.str_lien, new_file_name=name, extension=extention)

def _update_bill_file(bill_model: Bill, new_binary_document: Any, new_values: Dict[str, Any],
                      id_contrat: int, id_bill: Optional[int], context_changes: bool, binary_changes: bool):
    if not context_changes and binary_changes:
        name = splitext(bill_model.str_lien)[0]
        extention = splitext(str(new_binary_document.filename))[1]
        exchange_files(old_file_name=bill_model.str_lien, new_file=new_binary_document,
                       new_file_name=name, extension=extention)
        bill_model.str_lien = name + extention
        bill_model.name = name
    else:
        bill_model.date_facture = new_values['date_facture']
        bill_model.titre_facture = new_values['titre_facture']
        bill_model.montant = new_values['montant']
        name = create_name(new_values['date_facture'], str(id_contrat), str(id_bill), new_values['titre_facture'])
        if binary_changes:
            extention = splitext(str(new_binary_document.filename))[1]
            exchange_files(old_file_name=bill_model.str_lien, new_file=new_binary_document,
                           new_file_name=name, extension=extention)
        else:
            extention = splitext(str(bill_model.str_lien))[1]
            rename_file(old_file_name=bill_model.str_lien, new_file_name=name, extension=extention)

def update_files(context_changes: bool, binary_changes: bool,
                 id_contrat: int, new_values: Dict[str, Any], new_binary_document: Any,
                 id_document: Optional[int]=None, document_model: Optional[Document]=None,
                 id_bill: Optional[int]=None, bill_model: Optional[Bill]=None) -> None:
    """Fonction interne pour mettre à jour les fichiers associés au document."""
    if document_model:
        _update_document_file(document_model, new_binary_document, new_values, id_contrat, id_document, context_changes, binary_changes)
    elif bill_model:
        _update_bill_file(bill_model, new_binary_document, new_values, id_contrat, id_bill, context_changes, binary_changes)
    g.db_session.commit()