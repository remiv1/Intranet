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

-- Note: Le mot de passe par défaut est 'admin' (SHA-256)
-- Il est fortement recommandé de changer ce mot de passe après la première connexion.

-- Création d'un schéduleur de tâches pour rendre expirés les signatures dépassées et non signées
-- Ce script doit être placé dans un fichier séparé et sera exécuté par MariaDB au démarrage
-- Assurez-vous que l'option event_scheduler est activée dans la configuration de MariaDB
USE intranet_db;

DELIMITER $$

CREATE EVENT IF NOT EXISTS expire_signatures
ON SCHEDULE EVERY 1 HOUR
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    UPDATE 20_documents_a_signer
    JOIN 21_points ON 21points.id_document = 20_documents_a_signer.id
    SET 21_points.status = -1,
        20_documents_a_signer.status = -1
    WHERE 20_documents_a_signer.limite_signature < CURRENT_DATE()
      AND 20_documents_a_signer.status = 0;
END$$

DELIMITER ;