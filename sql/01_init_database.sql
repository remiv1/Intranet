-- Script d'initialisation de la base de données pour le développement
-- Ce script crée les tables nécessaires si elles n'existent pas

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS 99_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prenom VARCHAR(255) NOT NULL,
    nom VARCHAR(255) NOT NULL,
    mail VARCHAR(255) NOT NULL,
    identifiant VARCHAR(25),
    shaMdp VARCHAR(255) NOT NULL,
    habilitation INT,
    debut DATE DEFAULT (CURRENT_DATE),
    fin DATE,
    falseTest INT DEFAULT 0,
    locked BOOLEAN DEFAULT FALSE
);

-- Table des contrats
CREATE TABLE IF NOT EXISTS 01_contrats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Type VARCHAR(50) NOT NULL,
    SType VARCHAR(50) NOT NULL,
    entreprise VARCHAR(255) NOT NULL,
    numContratExterne VARCHAR(50) NOT NULL,
    intitule VARCHAR(255) NOT NULL,
    dateDebut DATE NOT NULL,
    dateFinPreavis DATE NOT NULL,
    dateFin DATE
);

-- Table des documents
CREATE TABLE IF NOT EXISTS 11_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idContrat INT NOT NULL,
    dateDocument DATE,
    Type VARCHAR(50),
    SType VARCHAR(50),
    descriptif TEXT,
    strLien VARCHAR(500),
    FOREIGN KEY (idContrat) REFERENCES 01_contrats(id)
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_user_identifiant ON 99_users(identifiant);
CREATE INDEX IF NOT EXISTS idx_contrat_entreprise ON 01_contrats(entreprise);
CREATE INDEX IF NOT EXISTS idx_document_contrat ON 11_documents(idContrat);
