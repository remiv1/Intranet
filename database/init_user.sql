-- Création de la table 99_users
CREATE TABLE IF NOT EXISTS 99_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prenom VARCHAR(255) NOT NULL,
    nom VARCHAR(255) NOT NULL,
    mail VARCHAR(255) NOT NULL,
    identifiant VARCHAR(25),
    sha_mdp VARCHAR(255) NOT NULL,
    habilitation INT,
    debut DATE DEFAULT CURRENT_DATE(),
    fin DATE,
    false_test INT DEFAULT 0,
    locked BOOLEAN DEFAULT FALSE
);

-- Insertion d'un utilisateur par défaut
INSERT INTO 99_users (prenom, nom, mail, identifiant, sha_mdp, habilitation, debut, locked)
VALUES ('Admin', 'Initial', 'admin@localhost', 'admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', '1', CURRENT_DATE(), FALSE);
