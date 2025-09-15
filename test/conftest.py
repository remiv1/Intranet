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

# Ajouter le répertoire app au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.models import User, Contract, Document, Event
from app.config import Config


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
def mock_db_session():
    """
    Fixture pour créer une session de base de données mockée.
    
    Simule les méthodes de SQLAlchemy Session sans vraie base de données.
    """
    session_mock = MagicMock()
    
    # Mock des données en mémoire pour simuler la base
    session_mock._users = []
    session_mock._contracts = []
    session_mock._documents = []
    session_mock._events = []
    session_mock._next_id = 1
    
    def mock_add(obj: Any):
        """Simule l'ajout d'un objet en session."""
        if not hasattr(obj, 'id') or obj.id is None:
            obj.id = session_mock._next_id
            session_mock._next_id += 1
        
        if isinstance(obj, User):
            session_mock._users.append(obj)
        elif isinstance(obj, Contract):
            session_mock._contracts.append(obj)
        elif isinstance(obj, Document):
            session_mock._documents.append(obj)
        elif isinstance(obj, Event):
            session_mock._events.append(obj)

    def mock_query(model_class: Any):
        """Simule une requête sur un modèle."""
        query_mock = MagicMock()
        
        if model_class == User:
            data_list = session_mock._users
        elif model_class == Contract:
            data_list = session_mock._contracts
        elif model_class == Document:
            data_list = session_mock._documents
        elif model_class == Event:
            data_list = session_mock._events
        else:
            data_list: List[Any] = []
        
        # Mock des méthodes de query
        query_mock.all.return_value = data_list
        query_mock.first.return_value = data_list[0] if data_list else None
        query_mock.count.return_value = len(data_list)

        def mock_filter(condition: Any):
            # Simulation simple de filtrage
            filtered_query = MagicMock()
            filtered_query.all.return_value = data_list
            filtered_query.first.return_value = data_list[0] if data_list else None
            filtered_query.count.return_value = len(data_list)
            return filtered_query

        def mock_filter_by(**kwargs: Any):
            # Simulation simple de filtrage par attributs
            filtered_list: List[Any] = []
            for item in data_list:
                match = True
                for key, value in kwargs.items():
                    if not hasattr(item, key) or getattr(item, key) != value:
                        match = False
                        break
                if match:
                    filtered_list.append(item)
            
            filtered_query = MagicMock()
            filtered_query.all.return_value = filtered_list
            filtered_query.first.return_value = filtered_list[0] if filtered_list else None
            filtered_query.count.return_value = len(filtered_list)
            return filtered_query

        def mock_get(obj_id: int):
            """Simule la récupération par ID."""
            for item in data_list:
                if hasattr(item, 'id') and item.id == obj_id:
                    return item
            return None
        
        def mock_delete():
            """Simule la suppression de tous les objets."""
            data_list.clear()
        
        query_mock.filter = mock_filter
        query_mock.filter_by = mock_filter_by
        query_mock.get = mock_get
        query_mock.delete = mock_delete
        
        return query_mock
    
    def mock_commit():
        """Simule le commit de la transaction."""
        pass
    
    def mock_rollback():
        """Simule le rollback de la transaction."""
        pass
    
    def mock_refresh(obj: Any):
        """Simule le refresh d'un objet."""
        pass
    
    def mock_close():
        """Simule la fermeture de la session."""
        pass
    
    # Configurer les mocks
    session_mock.add = mock_add
    session_mock.query = mock_query
    session_mock.commit = mock_commit
    session_mock.rollback = mock_rollback
    session_mock.refresh = mock_refresh
    session_mock.close = mock_close
    
    return session_mock


@pytest.fixture(scope="function")
def clean_mock_db(mock_db_session: MagicMock):
    """
    Fixture pour nettoyer la base de données mockée avant chaque test.
    """
    mock_db_session._users.clear()
    mock_db_session._contracts.clear()
    mock_db_session._documents.clear()
    mock_db_session._events.clear()
    mock_db_session._next_id = 1



@pytest.fixture
def app() -> Flask:
    """
    Fixture pour créer une instance de l'application Flask de test.
    """
    # Mock de l'engine et de la session avant l'import de l'application
    with patch('app.application.engine'), \
         patch('app.application.Session') as mock_session_class:
        mock_session_class.return_value = mock_db_session
        # Import de l'application (après configuration du path)
        from app.application import peraudiere as app
        
        # Configuration de test
        app.config.from_object(TestConfig)
        app.config['TESTING'] = True
        
        # Mock de la session de base de données
        mock_session_instance = MagicMock()
        mock_session_class.return_value = mock_session_instance
        
        return app


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