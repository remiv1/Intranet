# Architecture Globale du Projet Intranet

Ce diagramme présente l'architecture complète du système Intranet, incluant les composants frontend, backend, bases de données et infrastructure Docker.

```mermaid
graph TB
    subgraph Clients
        USER[Utilisateurs Web]
        ADMIN[Administrateurs]
    end

    subgraph Network
        NGINX[Nginx Reverse Proxy<br/>HTTPS/HTTP - Ports 80/443]
    end

    subgraph Docker_Infra[Infrastructure Docker]
        FLASK[Flask 3.1.0<br/>Python 3.12 - Waitress WSGI]
        BP_MAIN[Routes Principales<br/>application.py]
        BP_CONTRACTS[Contrats<br/>bp_contracts.py]
        BP_SIGNATURE[Signatures<br/>bp_signature.py]
        AUTH[Authentification<br/>habilitations.py]
        DOCS[Documents<br/>docs.py]
        PRINT[Impression<br/>impression.py]
        SIGS[Signatures Électroniques<br/>signatures.py]
        REPORTS[Rapports<br/>rapport_echeances.py]
        MODELS[Modèles SQLAlchemy<br/>models.py]
        ALEMBIC[Migrations Alembic]
        
        FASTAPI[FastAPI Dashboard<br/>dashboard_logs/]
        FASTAPI_ROUTERS[Routers Login/Logout<br/>PageView/Security]
    end
    
    subgraph Databases[Bases de Données]
        MARIADB[(MariaDB 12.0.2<br/>Base Principale<br/>Port 3306)]
        MONGODB[(MongoDB<br/>Logs & Monitoring<br/>Port 27017)]
    end
    
    subgraph Volumes[Volumes Persistants]
        VOL_DB[Volume DB]
        VOL_DOCS[Documents/Contrats]
        VOL_PRINT[Fichiers Impression]
        VOL_SIG[Fichiers Signatures]
        VOL_MONGO[Données MongoDB]
    end

    subgraph Networks[Réseaux Docker]
        NET_INTRANET[intranet_net<br/>172.20.0.0/16]
        NET_CUPS[cups_network<br/>192.168.100.0/24]
    end

    subgraph External[Services Externes]
        CUPS[CUPS Print Server<br/>host.docker.internal]
    end

    USER -->|HTTPS/HTTP| NGINX
    ADMIN -->|HTTPS/HTTP| NGINX
    
    NGINX -->|Proxy Pass| FLASK
    NGINX -->|Proxy Pass| FASTAPI
    
    FLASK --> BP_MAIN
    FLASK --> BP_CONTRACTS
    FLASK --> BP_SIGNATURE
    
    BP_MAIN --> AUTH
    BP_MAIN --> DOCS
    BP_MAIN --> PRINT
    BP_MAIN --> REPORTS
    BP_CONTRACTS --> MODELS
    BP_SIGNATURE --> SIGS
    
    MODELS -->|SQLAlchemy| MARIADB
    ALEMBIC -->|Migrations| MARIADB
    
    FASTAPI --> FASTAPI_ROUTERS
    FASTAPI_ROUTERS -->|Logs| MONGODB
    
    MARIADB -.->|Persistance| VOL_DB
    FLASK -.->|Stockage| VOL_DOCS
    FLASK -.->|Stockage| VOL_PRINT
    FLASK -.->|Stockage| VOL_SIG
    MONGODB -.->|Persistance| VOL_MONGO
    
    PRINT -->|Network CUPS| CUPS
    
    FLASK -.->|Member| NET_INTRANET
    FLASK -.->|IP 192.168.100.10| NET_CUPS
    MARIADB -.->|Member| NET_INTRANET
    NGINX -.->|Member| NET_INTRANET

    classDef flaskClass fill:#3fb950,stroke:#2ea043,color:#000
    classDef dbClass fill:#1f6feb,stroke:#1158c7,color:#fff
    classDef nginxClass fill:#f85149,stroke:#da3633,color:#fff
    classDef volumeClass fill:#f778ba,stroke:#d54ba5,color:#000
    classDef networkClass fill:#9e6a03,stroke:#845306,color:#fff
    
    class FLASK,BP_MAIN,BP_CONTRACTS,BP_SIGNATURE,AUTH,DOCS,PRINT,SIGS,REPORTS,MODELS,ALEMBIC flaskClass
    class MARIADB,MONGODB dbClass
    class NGINX nginxClass
    class VOL_DB,VOL_DOCS,VOL_PRINT,VOL_SIG,VOL_MONGO volumeClass
    class NET_INTRANET,NET_CUPS networkClass
```

## Composants Principaux

### Frontend

- Interface web responsive (HTML/CSS/JS)
- Bibliothèques : Bootstrap 5.3.3, jQuery 3.7.1, SignaturePad 4.1.7, PDF.js 3.11.174

### Backend Flask (Python 3.12)

- **Routes principales** : Gestion utilisateurs, authentification, accueil
- **Module Contrats** : CRUD complet des contrats avec contacts et factures
- **Module Signatures** : Placement de points, capture graphique, génération de PDF signés
- **Impression** : Impression à distance via CUPS
- **Rapports** : Génération de rapports d'échéances

### Dashboard Logs (FastAPI)

- API de monitoring et analyse des logs
- Routers : Login, Logout, PageView, Security

### Bases de Données

- **MariaDB 12.0.2** : Données métier (utilisateurs, contrats, signatures, factures)
- **MongoDB** : Logs d'activité et monitoring

### Infrastructure Docker

- **4 conteneurs** : nginx (proxy), web (Flask), db (MariaDB), mongodb
- **Volumes persistants** : Base de données, documents, impressions, signatures
- **Réseaux isolés** : intranet_net (172.20.0.0/16), cups_network (192.168.100.0/24)

## Flux de Données

1. Les utilisateurs accèdent à l'application via HTTPS (Nginx)
2. Nginx route les requêtes vers Flask ou FastAPI
3. Flask interagit avec MariaDB via SQLAlchemy
4. Les logs sont envoyés vers MongoDB via FastAPI
5. Les fichiers sont stockés dans des volumes Docker persistants
6. L'impression se fait via le réseau CUPS
