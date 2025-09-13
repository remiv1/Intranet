import os
import subprocess
from sqlalchemy import create_engine, text
from waitress import serve
from application import peraudiere

# Récupère l'URL de la base depuis l'environnement
DB_URL = os.environ.get('DB_URL')
ALEMBIC_VERSION_TABLE = 'alembic_version'
alembic_head = None

# Récupère la version head attendue depuis Alembic
try:
    result = subprocess.run(['alembic', 'heads'], capture_output=True, text=True)
    alembic_head = result.stdout.split()[0] if result.returncode == 0 else None
except Exception:
    alembic_head = None

# Vérifie la version actuelle de la base
if DB_URL and alembic_head:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        try:
            current_version = conn.execute(text(f"SELECT version_num FROM {ALEMBIC_VERSION_TABLE}")).scalar()
        except Exception:
            current_version = None
        if current_version != alembic_head:
            print(f"Migration nécessaire : {current_version} -> {alembic_head}")
            subprocess.run(['alembic', 'upgrade', 'head'])
        else:
            print("La base est à jour.")

if __name__ == '__main__':
    serve(peraudiere, host="0.0.0.0", port=5000)
