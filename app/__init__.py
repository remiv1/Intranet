from flask import Flask
from config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
from app.models import Base

app = Flask(__name__)

#Charger la configuration depuis config.py
app.config.from_object(Config)

#Création des différents dictionnaires de configuration
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif', '.jpeg', '.tif', '.tiff', '.pdf']

#Construction de l'URL de la base de données
db_url = URL.create(
    drivername="mysql+mysqlconnector",
    username=app.config["DB_USER"],
    password=app.config["DB_PASSWORD"],
    host=app.config["DB_HOST"],
    port=3306,
    database=app.config["DB_NAME"],
    query={"charset": "utf8mb4"}
)

#Créer l'engin SQLAlchemy
engine = create_engine(db_url, echo=True)

#Créer les tables de la base de données
Base.metadata.create_all(engine)

#Créer une session de base de données
Session = sessionmaker(bind=engine)
db_session = Session()

from app import routes