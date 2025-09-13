import os
import subprocess
from sqlalchemy import create_engine, text
from waitress import serve
from application import peraudiere
from datetime import datetime
from typing import Any, List


DB_URL = os.environ.get('DB_URL')
ALEMBIC_VERSION_TABLE = 'alembic_version'
alembic_head = None

# Récupère la version head attendue depuis Alembic
try:
    result = subprocess.run(['alembic', 'heads'], capture_output=True, text=True)
    alembic_head = result.stdout.split()[0] if result.returncode == 0 else None
except Exception:
    alembic_head = None

def get_db_creation_date(conn: Any) -> Any | None:
    """
    Récupère la date de création de la base de données. (Pour MySQL/MariaDB)
    Arguments:
        conn: Connexion SQLAlchemy à la base de données.
    Returns:
        datetime | None: Date de création de la base, ou None si non trouvée ou erreur.
    """
    result = conn.execute(text(
        "SELECT CREATE_TIME FROM information_schema.tables WHERE table_schema = DATABASE() ORDER BY CREATE_TIME ASC LIMIT 1"
    ))
    row = result.fetchone()
    return row[0] if row and row[0] else None

def get_alembic_migrations_since(date_min: Any | None) -> list[str]:
    """
    Récupère les migrations Alembic depuis une date donnée.
    Arguments:
        date_min (datetime | None): Date minimale pour filtrer les migrations. Si None, toutes les migrations sont retournées.
    Returns:
        List[str]: Liste des identifiants de migration (noms de fichiers sans extension) à appliquer.
    """
    # Récupération des fichiers de migration
    versions_dir = os.path.join(os.path.dirname(__file__), '..', 'alembic', 'versions')

    # Parcours des fichiers pour extraire les dates de création
    migrations: List[str] = []
    for fname in os.listdir(versions_dir):
        if fname.endswith('.py'):
            # Lecture du fichier pour extraire la date de création
            fpath = os.path.join(versions_dir, fname)

            mig_date = extract_migration_date(fpath)
            if mig_date and (not date_min or mig_date >= date_min):
                migrations.append(fname[:-3])

    return migrations

def extract_migration_date(filepath: str) -> datetime | None:
    """
    Extrait la date de création d'une migration à partir de son fichier.
    Arguments:
        filepath (str): Chemin du fichier de migration.
    Returns:
        datetime | None: Date de création de la migration, ou None si non trouvée ou erreur.
    """
    try:
        with open(filepath, encoding='utf-8') as f:
            for line in f:
                if line.startswith('Create Date:'):
                    date_str = line.split('Create Date:')[1].strip()
                    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
    except Exception:
        return None

# Vérifie la version actuelle de la base et applique les migrations récentes
if DB_URL and alembic_head:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        db_creation_date = get_db_creation_date(conn)
        try:
            current_version = conn.execute(text(f"SELECT version_num FROM {ALEMBIC_VERSION_TABLE}")).scalar()
        except Exception:
            current_version = None

        if db_creation_date:
            print(f"Date de création de la base : {db_creation_date}")
            migrations_to_apply = get_alembic_migrations_since(db_creation_date)
            for mig in migrations_to_apply:
                print(f"Application de la migration {mig}")
                subprocess.run(['alembic', 'upgrade', mig])
        elif current_version != alembic_head:
            print(f"Migration nécessaire : {current_version} -> {alembic_head}")
            subprocess.run(['alembic', 'upgrade', 'head'])
        else:
            print("La base est à jour.")

if __name__ == '__main__':
    serve(peraudiere, host="0.0.0.0", port=5000)
