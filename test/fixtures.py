"""
Fixtures spécialisées pour créer des instances d'objets de test avec mocks.

Ce module contient des fixtures qui créent des objets mockés
sans utiliser de vraie base de données.
"""
import pytest
from typing import List, Dict, Any, Generator
from datetime import date, timedelta
from unittest.mock import MagicMock
from app.models import User, Contract, Document, Event


@pytest.fixture
def create_test_user(mock_db_session: MagicMock, sample_user_data: Dict[str, Any]) -> User:
    """
    Fixture pour créer un utilisateur de test dans la session mockée.
    
    Returns:
        User: L'utilisateur créé avec un ID généré
    """
    user = User(**sample_user_data)
    mock_db_session.add(user)
    mock_db_session.commit()
    return user


@pytest.fixture
def create_admin_user(mock_db_session: MagicMock) -> User:
    """
    Fixture pour créer un utilisateur administrateur de test.
    
    Returns:
        User: L'utilisateur administrateur créé
    """
    admin_data: Dict[str, Any] = {
        'prenom': 'Admin',
        'nom': 'Système',
        'mail': 'admin@test.com',
        'identifiant': 'admin',
        'sha_mdp': 'admin_hashed_password',
        'habilitation': 1,  # Administrateur
        'debut': date.today(),
        'fin': None,
        'false_test': 0,
        'locked': False
    }
    
    user = User(**admin_data)
    mock_db_session.add(user)
    mock_db_session.commit()
    return user


@pytest.fixture
def create_test_contract(mock_db_session: MagicMock, sample_contract_data: Dict[str, Any]) -> Contract:
    """
    Fixture pour créer un contrat de test dans la session mockée.
    
    Returns:
        Contract: Le contrat créé avec un ID généré
    """
    contract = Contract(**sample_contract_data)
    mock_db_session.add(contract)
    mock_db_session.commit()
    return contract


@pytest.fixture
def create_expiring_contract(mock_db_session: MagicMock) -> Contract:
    """
    Fixture pour créer un contrat arrivant à échéance.
    
    Returns:
        Contract: Un contrat qui arrive à échéance dans 30 jours
    """
    contract_data: Dict[str, Any] = {
        'type_contrat': 'Service',
        'sous_type_contrat': 'Nettoyage',
        'entreprise': 'CleanCorp',
        'id_externe_contrat': 'CC001',
        'intitule': 'Service de nettoyage',
        'date_debut': date.today() - timedelta(days=335),  # Commencé il y a ~11 mois
        'date_fin_preavis': date.today() + timedelta(days=30),  # Échéance dans 30 jours
        'date_fin': None
    }
    
    contract = Contract(**contract_data)
    mock_db_session.add(contract)
    mock_db_session.commit()
    return contract


@pytest.fixture
def create_test_document(mock_db_session: MagicMock, create_test_contract: Contract, sample_document_data: Dict[str, Any]) -> Document:
    """
    Fixture pour créer un document de test lié à un contrat.
    
    Args:
        create_test_contract: Le contrat auquel lier le document
        
    Returns:
        Document: Le document créé avec un ID généré
    """
    document_data = sample_document_data.copy()
    document_data['id_contrat'] = create_test_contract.id
    
    document = Document(**document_data)
    mock_db_session.add(document)
    mock_db_session.commit()
    return document


@pytest.fixture
def create_test_event(mock_db_session: MagicMock, create_test_contract: Contract, sample_event_data: Dict[str, Any]) -> Event:
    """
    Fixture pour créer un événement de test lié à un contrat.
    
    Args:
        create_test_contract: Le contrat auquel lier l'événement
        
    Returns:
        Event: L'événement créé avec un ID généré
    """
    event_data = sample_event_data.copy()
    event_data['id_contrat'] = create_test_contract.id
    
    event = Event(**event_data)
    mock_db_session.add(event)
    mock_db_session.commit()
    return event


@pytest.fixture
def create_multiple_users(mock_db_session: MagicMock) -> List[User]:
    """
    Fixture pour créer plusieurs utilisateurs avec différents niveaux d'habilitation.
    
    Returns:
        List[User]: Liste des utilisateurs créés
    """
    users_data: List[Dict[str, Any]] = [
        {
            'prenom': 'Jean', 'nom': 'Administrateur', 'mail': 'jean.admin@test.com',
            'identifiant': 'jadmin', 'sha_mdp': 'hash1', 'habilitation': 1,
            'debut': date.today(), 'fin': None, 'false_test': 0, 'locked': False
        },
        {
            'prenom': 'Marie', 'nom': 'Gestionnaire', 'mail': 'marie.gestionnaire@test.com',
            'identifiant': 'mgest', 'sha_mdp': 'hash2', 'habilitation': 2,
            'debut': date.today(), 'fin': None, 'false_test': 0, 'locked': False
        },
        {
            'prenom': 'Pierre', 'nom': 'Professeur', 'mail': 'pierre.prof@test.com',
            'identifiant': 'pprof', 'sha_mdp': 'hash3', 'habilitation': 4,
            'debut': date.today(), 'fin': None, 'false_test': 0, 'locked': False
        },
        {
            'prenom': 'Sophie', 'nom': 'Élève', 'mail': 'sophie.eleve@test.com',
            'identifiant': 'seleve', 'sha_mdp': 'hash4', 'habilitation': 8,
            'debut': date.today(), 'fin': None, 'false_test': 0, 'locked': False
        }
    ]

    users: List[User] = []
    for user_data in users_data:
        user = User(**user_data)
        mock_db_session.add(user)
        users.append(user)
    
    mock_db_session.commit()
    return users


@pytest.fixture
def create_multiple_contracts(mock_db_session: MagicMock) -> List[Contract]:
    """
    Fixture pour créer plusieurs contrats avec des échéances différentes.
    
    Returns:
        List[Contract]: Liste des contrats créés
    """
    today = date.today()

    contracts_data: List[Dict[str, Any]] = [
        {
            'type_contrat': 'Maintenance', 'sous_type_contrat': 'Informatique',
            'entreprise': 'TechCorp', 'id_externe_contrat': 'TC001',
            'intitule': 'Maintenance serveurs', 'date_debut': today - timedelta(days=300),
            'date_fin_preavis': today + timedelta(days=65), 'date_fin': None
        },
        {
            'type_contrat': 'Service', 'sous_type_contrat': 'Nettoyage',
            'entreprise': 'CleanCorp', 'id_externe_contrat': 'CC001',
            'intitule': 'Nettoyage locaux', 'date_debut': today - timedelta(days=200),
            'date_fin_preavis': today + timedelta(days=120), 'date_fin': None
        },
        {
            'type_contrat': 'Formation', 'sous_type_contrat': 'Informatique',
            'entreprise': 'FormaCorp', 'id_externe_contrat': 'FC001',
            'intitule': 'Formation développement', 'date_debut': today - timedelta(days=100),
            'date_fin_preavis': today + timedelta(days=200), 'date_fin': None
        },
        {
            'type_contrat': 'Maintenance', 'sous_type_contrat': 'Chauffage',
            'entreprise': 'HeatCorp', 'id_externe_contrat': 'HC001',
            'intitule': 'Maintenance chauffage', 'date_debut': today - timedelta(days=400),
            'date_fin_preavis': today - timedelta(days=30), 'date_fin': today - timedelta(days=30)  # Contrat expiré
        }
    ]

    contracts: List[Contract] = []
    for contract_data in contracts_data:
        contract = Contract(**contract_data)
        mock_db_session.add(contract)
        contracts.append(contract)
    
    mock_db_session.commit()
    return contracts


@pytest.fixture
def create_contract_with_documents_and_events(
    mock_db_session: MagicMock, 
    create_test_contract: Contract
) -> Contract:
    """
    Fixture pour créer un contrat complet avec des documents et événements associés.
    
    Args:
        create_test_contract: Le contrat de base
        
    Returns:
        Contract: Le contrat avec documents et événements créés
    """
    contract = create_test_contract
    
    # Créer plusieurs documents
    documents_data: List[Dict[str, Any]] = [
        {
            'id_contrat': contract.id, 'type_document': 'Contrat', 'sous_type_document': 'Initial',
            'descriptif': 'Contrat initial', 'str_lien': '/docs/contrat_initial.pdf',
            'date_document': date.today() - timedelta(days=300), 'name': 'contrat_initial.pdf'
        },
        {
            'id_contrat': contract.id, 'type_document': 'Avenant', 'sous_type_document': 'Modification',
            'descriptif': 'Avenant tarifaire', 'str_lien': '/docs/avenant_001.pdf',
            'date_document': date.today() - timedelta(days=100), 'name': 'avenant_001.pdf'
        }
    ]
    
    # Créer plusieurs événements
    events_data: List[Dict[str, Any]] = [
        {
            'id_contrat': contract.id, 'type_evenement': 'Signature', 'sous_type_evenement': 'Initial',
            'date_evenement': date.today() - timedelta(days=300),
            'descriptif': 'Signature du contrat initial'
        },
        {
            'id_contrat': contract.id, 'type_evenement': 'Renouvellement', 'sous_type_evenement': 'Automatique',
            'date_evenement': date.today() + timedelta(days=30),
            'descriptif': 'Renouvellement automatique prévu'
        }
    ]
    
    # Persister les documents
    for doc_data in documents_data:
        document = Document(**doc_data)
        mock_db_session.add(document)
    
    # Persister les événements
    for event_data in events_data:
        event = Event(**event_data)
        mock_db_session.add(event)
    
    mock_db_session.commit()
    return contract


@pytest.fixture
def mock_authenticated_session() -> Dict[str, Any]:
    """
    Fixture pour simuler une session utilisateur authentifiée.
    
    Returns:
        dict: Données de session simulées
    """
    dict_return: Dict[str, Any] = {
        'user_id': 1,
        'user_prenom': 'Test',
        'user_nom': 'User',
        'user_habilitation': 1,  # Administrateur
        'authenticated': True
    }
    return dict_return

@pytest.fixture
def mock_flask_session(mock_authenticated_session: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """
    Fixture pour mocker la session Flask.
    
    Returns:
        MagicMock: Session Flask mockée avec des données d'authentification
    """
    from unittest.mock import patch
    
    with patch('flask.session', mock_authenticated_session) as mock_session:
        yield mock_session