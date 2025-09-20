"""
Configuration et fixtures pour les tests du projet Intranet.

Ce fichier contient toutes les fixtures nécessaires pour les tests,
incluant des mocks pour simuler la base de données en CI/CD.
"""

import pytest
import os
import sys
from datetime import date, timedelta
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch
from flask import Flask
from flask.testing import FlaskClient

# Ajouter le répertoire racine au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models import User, Contract, Document, Event
from app.config import Config

# Import des fixtures supplémentaires
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from fixtures import (
    create_test_user, create_admin_user, create_test_contract,              # type: ignore
    create_expiring_contract, create_test_document, create_test_event,     # type: ignore
    create_multiple_users, create_multiple_contracts,           # type: ignore
    create_contract_with_documents_and_events, mock_authenticated_session,   # type: ignore
    mock_flask_session  # type: ignore
)


class MockQuery:
    """Classe pour simuler les requêtes SQLAlchemy."""
    
    def __init__(self, data_list: List[Any]):
        self.data_list = data_list
    
    def all(self) -> List[Any]:
        """Retourne tous les éléments."""
        return self.data_list
    
    def first(self) -> Any:
        """Retourne le premier élément ou None."""
        return self.data_list[0] if self.data_list else None
    
    def count(self) -> int:
        """Retourne le nombre d'éléments."""
        return len(self.data_list)
    
    def get(self, obj_id: int) -> Any:
        """Récupère un objet par son ID."""
        for item in self.data_list:
            if hasattr(item, 'id') and item.id == obj_id:
                return item
        return None
    
    def filter_by(self, **kwargs: Any) -> 'MockQuery':
        """Filtre les éléments par attributs."""
        filtered_list: List[Any] = []
        for item in self.data_list:
            match = True
            for key, value in kwargs.items():
                if not hasattr(item, key) or getattr(item, key) != value:
                    match = False
                    break
            if match:
                filtered_list.append(item)
        return MockQuery(filtered_list)
    
    def filter(self, condition: Any) -> 'MockQuery':
        """Filtre simple (retourne tous les éléments pour simplicité)."""
        return MockQuery(self.data_list)
    
    def delete(self) -> None:
        """Supprime tous les éléments de la liste."""
        self.data_list.clear()


class MockSession:
    """Session de base de données mockée pour les tests."""
    
    def __init__(self):
        self._users: List[User] = []
        self._contracts: List[Contract] = []
        self._documents: List[Document] = []
        self._events: List[Event] = []
        self._next_id = 1
    
    def add(self, obj: Any) -> None:
        """Ajoute un objet à la session."""
        # Assigner un ID si l'objet n'en a pas
        if not hasattr(obj, 'id') or obj.id is None:
            obj.id = self._next_id
            self._next_id += 1
        
        # Ajouter à la liste appropriée
        if isinstance(obj, User):
            self._users.append(obj)
        elif isinstance(obj, Contract):
            self._contracts.append(obj)
        elif isinstance(obj, Document):
            self._documents.append(obj)
        elif isinstance(obj, Event):
            self._events.append(obj)
    
    def query(self, model_class: Any) -> MockQuery:
        """Crée une requête pour un modèle donné."""
        data_list = self._get_data_for_model(model_class)
        return MockQuery(data_list)
    
    def commit(self) -> None:
        """Simule le commit de la transaction."""
        pass
    
    def rollback(self) -> None:
        """Simule le rollback de la transaction."""
        pass
    
    def refresh(self, obj: Any) -> None:
        """Simule le refresh d'un objet."""
        pass
    
    def close(self) -> None:
        """Simule la fermeture de la session."""
        pass
    
    def clear(self) -> None:
        """Nettoie toutes les données de la session."""
        self._users.clear()
        self._contracts.clear()
        self._documents.clear()
        self._events.clear()
        self._next_id = 1
    
    def _get_data_for_model(self, model_class: Any) -> List[Any]:
        """Retourne la liste de données pour un modèle donné."""
        if model_class == User:
            return self._users
        elif model_class == Contract:
            return self._contracts
        elif model_class == Document:
            return self._documents
        elif model_class == Event:
            return self._events
        else:
            return []
    
    # Propriétés publiques pour l'accès aux données (pour les tests)
    @property
    def users(self) -> List[User]:
        """Accès public à la liste des utilisateurs."""
        return self._users
    
    @property
    def contracts(self) -> List[Contract]:
        """Accès public à la liste des contrats."""
        return self._contracts
    
    @property
    def documents(self) -> List[Document]:
        """Accès public à la liste des documents."""
        return self._documents
    
    @property
    def events(self) -> List[Event]:
        """Accès public à la liste des événements."""
        return self._events
    
    @property
    def next_id(self) -> int:
        """Accès public au prochain ID."""
        return self._next_id


class TestConfig(Config):
    """Configuration spécifique aux tests."""
    
    # Configuration pour les tests sans base de données réelle
    TESTING = True
    
    # Désactiver les emails et impressions en test
    EMAIL_USER = ''
    EMAIL_PASSWORD = ''
    PRINTER_NAME = ''
    
    # Chemins temporaires pour les tests
    UPLOAD_FOLDER = '/tmp/test_uploads'
    PRINT_PATH = '/tmp/test_prints'
    
    # Configuration de sécurité pour les tests
    SECRET_KEY = 'test-secret-key-not-for-production'


@pytest.fixture(scope="function")
def mock_db_session() -> MagicMock:
    """
    Fixture pour créer une session de base de données mockée.
    
    Utilise la classe MockSession pour une gestion plus claire,
    mais retourne un MagicMock pour la compatibilité avec les tests existants.
    """
    # Créer l'instance de MockSession
    mock_session = MockSession()
    
    # Créer un MagicMock qui wrape notre MockSession
    session_mock = MagicMock(spec=MockSession)
    
    # Déléguer les appels vers notre MockSession
    session_mock.add.side_effect = mock_session.add
    session_mock.query.side_effect = mock_session.query
    session_mock.commit.side_effect = mock_session.commit
    session_mock.rollback.side_effect = mock_session.rollback
    session_mock.refresh.side_effect = mock_session.refresh
    session_mock.close.side_effect = mock_session.close
    
    # Exposer les données pour les tests qui en ont besoin
    session_mock._users = mock_session.users
    session_mock._contracts = mock_session.contracts
    session_mock._documents = mock_session.documents
    session_mock._events = mock_session.events
    session_mock._next_id = mock_session.next_id
    session_mock.clear = mock_session.clear
    
    return session_mock


@pytest.fixture(scope="function")
def clean_mock_db(mock_db_session: MagicMock):
    """
    Fixture pour nettoyer la base de données mockée avant chaque test.
    """
    mock_db_session.clear()



@pytest.fixture
def app() -> Flask:
    """
    Fixture pour créer une instance de l'application Flask de test.
    """
    # Mock des modules SQLAlchemy avant tout import
    with patch('sqlalchemy.create_engine') as mock_create_engine, \
         patch('sqlalchemy.orm.sessionmaker') as mock_sessionmaker:
        
        # Configurer les mocks
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session_class = MagicMock()
        mock_sessionmaker.return_value = mock_session_class
        
        # Ajouter le chemin de l'app pour l'import direct
        import sys
        import os
        app_path = os.path.join(os.path.dirname(__file__), '..', 'app')
        if app_path not in sys.path:
            sys.path.insert(0, app_path)
        
        # Import de l'application maintenant que tout est mocké
        import application              # type: ignore
        app = application.peraudiere    # type: ignore
        
        # Configuration de test
        app.config.from_object(TestConfig)      # type: ignore
        app.config['TESTING'] = True            # type: ignore
        
        return app      # type: ignore


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """
    Fixture pour créer un client de test Flask.
    """
    return app.test_client()


@pytest.fixture
def mock_session_context(mock_db_session: MagicMock):
    """
    Fixture pour patcher la session de base de données dans l'application.
    
    Utilise cette fixture dans les tests qui ont besoin d'accéder aux données.
    """
    with patch('application.Session') as mock_session_class:
        mock_session_class.return_value = mock_db_session
        yield mock_db_session


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """
    Fixture fournissant des données d'utilisateur de test.
    """
    return {
        'prenom': 'Jean',
        'nom': 'Dupont',
        'mail': 'jean.dupont@test.com',
        'identifiant': 'jdupont',
        'sha_mdp': 'hashed_password_here',
        'habilitation': 1,
        'debut': date.today(),
        'fin': None,
        'false_test': 0,
        'locked': False
    }


@pytest.fixture
def sample_contract_data() -> Dict[str, Any]:
    """
    Fixture fournissant des données de contrat de test.
    """
    return {
        'type_contrat': 'Maintenance',
        'sous_type_contrat': 'Informatique',
        'entreprise': 'TechCorp',
        'id_externe_contrat': 'TC001',
        'intitule': 'Maintenance des serveurs',
        'date_debut': date.today(),
        'date_fin_preavis': date.today() + timedelta(days=365),
        'date_fin': None
    }


@pytest.fixture
def sample_document_data() -> Dict[str, Any]:
    """
    Fixture fournissant des données de document de test.
    """
    return {
        'type_document': 'Contrat',
        'sous_type_document': 'Initial',
        'descriptif': 'Contrat initial de maintenance',
        'str_lien': '/documents/contrat_001.pdf',
        'date_document': date.today(),
        'name': 'contrat_001.pdf'
    }


@pytest.fixture
def sample_event_data() -> Dict[str, Any]:
    """
    Fixture fournissant des données d'événement de test.
    """
    return {
        'type_evenement': 'Renouvellement',
        'sous_type_evenement': 'Automatique',
        'date_evenement': date.today() + timedelta(days=30),
        'descriptif': 'Renouvellement automatique du contrat'
    }


@pytest.fixture
def mock_file_operations():
    """
    Fixture pour mocker les opérations sur les fichiers.
    """
    with patch('os.path.exists') as mock_exists, \
         patch('os.makedirs') as mock_makedirs, \
         patch('builtins.open', create=True) as mock_open:
        
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "contenu fichier test"
        
        yield {
            'exists': mock_exists,
            'makedirs': mock_makedirs,
            'open': mock_open
        }


@pytest.fixture
def mock_ssh_operations():
    """
    Fixture pour mocker les opérations SSH.
    """
    with patch('paramiko.SSHClient') as mock_ssh_client:
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        
        # Mock des méthodes SSH
        mock_client.connect.return_value = None
        mock_client.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_client.close.return_value = None
        
        yield mock_client


@pytest.fixture
def mock_email_operations():
    """
    Fixture pour mocker les opérations d'envoi d'email.
    """
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Mock des méthodes SMTP
        mock_server.starttls.return_value = None
        mock_server.login.return_value = None
        mock_server.send_message.return_value = {}
        mock_server.quit.return_value = None
        
        yield mock_server


@pytest.fixture
def mock_print_operations():
    """
    Fixture pour mocker les opérations d'impression.
    """
    with patch('subprocess.run') as mock_subprocess:
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Impression réussie"
        mock_subprocess.return_value.stderr = ""
        
        yield mock_subprocess