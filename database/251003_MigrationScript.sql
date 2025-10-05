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