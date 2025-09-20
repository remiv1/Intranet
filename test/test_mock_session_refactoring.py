"""
Test de validation de la refactorisation MockSession.

Ce fichier valide que notre nouvelle classe MockSession fonctionne correctement.
"""
from datetime import date
from typing import Dict, Any
from unittest.mock import MagicMock
from app.models import User


class TestMockSessionRefactoring:
    """Tests pour valider la refactorisation de MockSession."""

    def test_mock_session_is_magicmock(self, mock_db_session: MagicMock):
        """Vérifie que mock_db_session est bien un MagicMock pour la compatibilité."""
        assert isinstance(mock_db_session, MagicMock)
        assert hasattr(mock_db_session, 'add')
        assert hasattr(mock_db_session, 'query')
        assert hasattr(mock_db_session, 'commit')

    def test_mock_session_has_assert_methods(self, mock_db_session: MagicMock, sample_user_data: Dict[str, Any]):
        """Vérifie que les méthodes assert_called_with fonctionnent."""
        user = User(**sample_user_data)
        mock_db_session.add(user)
        mock_db_session.commit()
        
        # Vérifier que les assertions MagicMock fonctionnent
        mock_db_session.add.assert_called_with(user)
        mock_db_session.commit.assert_called()

    def test_mock_session_stores_data_correctly(self, mock_db_session: MagicMock, clean_mock_db: MagicMock, sample_user_data: Dict[str, Any]):
        """Vérifie que les données sont correctement stockées."""
        user = User(**sample_user_data)
        mock_db_session.add(user)
        
        # Vérifier que l'utilisateur a un ID
        assert user.id is not None
        assert user.id == 1
        
        # Vérifier que les données sont dans les listes
        assert len(mock_db_session._users) == 1
        assert mock_db_session._users[0] == user

    def test_mock_session_query_functionality(self, mock_db_session: MagicMock, clean_mock_db: MagicMock, sample_user_data: Dict[str, Any]):
        """Vérifie que les requêtes fonctionnent correctement."""
        # Ajouter un utilisateur
        user = User(**sample_user_data)
        mock_db_session.add(user)
        
        # Tester les requêtes
        all_users = mock_db_session.query(User).all()
        assert len(all_users) == 1
        assert all_users[0] == user
        
        # Tester get par ID
        found_user = mock_db_session.query(User).get(1)
        assert found_user == user
        
        # Tester filter_by
        filtered_users = mock_db_session.query(User).filter_by(prenom="Jean").all()
        assert len(filtered_users) == 1
        assert filtered_users[0] == user

    def test_mock_session_clear_functionality(self, mock_db_session: MagicMock, sample_user_data: Dict[str, Any]):
        """Vérifie que le nettoyage fonctionne."""
        # Ajouter des données
        user = User(**sample_user_data)
        mock_db_session.add(user)
        assert len(mock_db_session._users) == 1
        
        # Nettoyer
        mock_db_session.clear()
        assert len(mock_db_session._users) == 0
        assert mock_db_session._next_id == 1

    def test_mock_session_incremental_ids(self, mock_db_session: MagicMock, clean_mock_db: MagicMock):
        """Vérifie que les IDs sont bien incrémentaux."""
        # Créer plusieurs utilisateurs
        for i in range(3):
            user_data: Dict[str, Any] = {
                'prenom': f'User{i}',
                'nom': 'Test',
                'mail': f'user{i}@test.com',
                'identifiant': f'user{i}',
                'sha_mdp': 'password',
                'habilitation': 1,
                'debut': date.today(),
                'fin': None,
                'false_test': 0,
                'locked': False
            }
            user = User(**user_data)
            mock_db_session.add(user)
            assert user.id == i + 1

    def test_mock_session_multiple_models(self, mock_db_session: MagicMock, clean_mock_db: MagicMock, sample_user_data: Dict[str, Any], sample_contract_data: Dict[str, Any]):
        """Vérifie que plusieurs types de modèles peuvent être gérés."""
        from app.models import Contract
        
        # Ajouter un utilisateur et un contrat
        user = User(**sample_user_data)
        contract = Contract(**sample_contract_data)
        
        mock_db_session.add(user)
        mock_db_session.add(contract)
        
        # Vérifier que chaque modèle est dans sa liste respective
        assert len(mock_db_session._users) == 1
        assert len(mock_db_session._contracts) == 1
        
        # Vérifier les requêtes par modèle
        users = mock_db_session.query(User).all()
        contracts = mock_db_session.query(Contract).all()
        
        assert len(users) == 1
        assert len(contracts) == 1
        assert users[0] == user
        assert contracts[0] == contract