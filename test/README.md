# Tests pour l'Intranet API'Raudière

Ce dossier contient tous les tests pour l'application Intranet, conçus pour fonctionner dans un environnement CI/CD sans base de données réelle.

## Structure des tests

```
test/
├── conftest.py              # Configuration globale et fixtures principales
├── fixtures.py              # Fixtures spécialisées pour les données de test
├── test_example.py          # Exemples de tests pour démonstration
├── pytest.ini              # Configuration pytest
├── docker-compose.test.yaml # Configuration Docker pour tests locaux (optionnel)
└── README.md               # Cette documentation
```

## Fixtures disponibles

### Fixtures de base de données mockée

- `mock_db_session` : Session de base de données simulée
- `clean_mock_db` : Nettoie la base mockée avant chaque test

### Fixtures de données de test

- `sample_user_data` : Données d'utilisateur de test
- `sample_contract_data` : Données de contrat de test
- `sample_document_data` : Données de document de test
- `sample_event_data` : Données d'événement de test

### Fixtures d'objets créés

- `create_test_user` : Crée un utilisateur de test
- `create_admin_user` : Crée un utilisateur administrateur
- `create_test_contract` : Crée un contrat de test
- `create_multiple_users` : Crée plusieurs utilisateurs avec différents niveaux d'habilitation
- `create_multiple_contracts` : Crée plusieurs contrats avec des échéances différentes

### Fixtures d'application Flask

- `app` : Instance de l'application Flask configurée pour les tests
- `client` : Client de test Flask
- `mock_session_context` : Contexte de session mockée pour l'application

### Fixtures d'opérations externes

- `mock_file_operations` : Mock des opérations sur les fichiers
- `mock_ssh_operations` : Mock des opérations SSH
- `mock_email_operations` : Mock des envois d'emails
- `mock_print_operations` : Mock des opérations d'impression

## Utilisation des fixtures

### Test simple avec utilisateur

```python
def test_user_creation(mock_db_session, clean_mock_db, sample_user_data):
    user = User(**sample_user_data)
    mock_db_session.add(user)
    mock_db_session.commit()
    
    assert user.id is not None
    assert user.prenom == "Jean"
```

### Test avec fixture d'objet créé

```python
def test_user_authentication(create_admin_user):
    admin = create_admin_user
    assert admin.habilitation == 1
    assert admin.identifiant == "admin"
```

### Test de route Flask

```python
def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200
```

### Test avec authentification mockée

```python
def test_authenticated_route(client, mock_authenticated_session):
    with patch('flask.session', mock_authenticated_session):
        response = client.get('/dashboard')
        assert response.status_code == 200
```

## Lancement des tests

### En local

```bash
# Installer les dépendances de test
pip install pytest pytest-flask pytest-cov pytest-mock

# Lancer tous les tests
cd test/
python -m pytest

# Lancer avec couverture de code
python -m pytest --cov=../app --cov-report=html

# Lancer des tests spécifiques
python -m pytest test_example.py::TestUserOperations::test_create_user

# Lancer avec marqueurs
python -m pytest -m "unit and not slow"
```

### Dans GitHub Actions

Les tests sont automatiquement lancés lors des push/pull requests vers les branches `main` et `develop`.

Le workflow GitHub Actions :
- Teste sur Python 3.9, 3.10, et 3.11
- Lance les tests avec couverture de code
- Effectue un scan de sécurité avec bandit
- Vérifie les dépendances avec safety

## Marqueurs de tests

Utilisez les marqueurs pour organiser vos tests :

```python
@pytest.mark.unit
def test_simple_function():
    pass

@pytest.mark.integration  
def test_complex_workflow():
    pass

@pytest.mark.slow
def test_heavy_operation():
    pass

@pytest.mark.auth
def test_authentication():
    pass
```

## Bonnes pratiques

### Isolation des tests

Chaque test doit être indépendant :
- Utilisez `clean_mock_db` pour avoir une base vide
- Ne partagez pas d'état entre les tests
- Utilisez des fixtures pour les données communes

### Nommage

- Tests : `test_what_it_does`
- Classes de test : `TestFeatureName`
- Fichiers de test : `test_feature.py`

### Mocks

Les mocks simulent les dépendances externes :
- Base de données : automatiquement mockée
- Fichiers : utilisez `mock_file_operations`
- SSH : utilisez `mock_ssh_operations`
- Emails : utilisez `mock_email_operations`
- Impression : utilisez `mock_print_operations`

### Structure d'un test

```python
def test_feature_name(fixtures):
    # Arrange (préparer les données)
    user = User(name="Test")
    
    # Act (exécuter l'action)
    result = some_function(user)
    
    # Assert (vérifier le résultat)
    assert result.success is True
```

## Ajout de nouveaux tests

1. Créez un fichier `test_*.py` dans le dossier `test/`
2. Importez les fixtures nécessaires depuis `conftest.py`
3. Utilisez les marqueurs appropriés
4. Documentez les tests complexes
5. Vérifiez que les tests passent localement avant de commit

## Dépendances de test

Les dépendances suivantes sont requises pour les tests :

```
pytest>=7.0.0
pytest-flask>=1.2.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
```

Ces dépendances sont automatiquement installées dans GitHub Actions.

## Exemple complet

Voir `test_example.py` pour des exemples concrets d'utilisation de toutes les fixtures disponibles.