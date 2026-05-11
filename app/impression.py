"""
Module de gestion de l'impression via CUPS sur l'hôte Docker.
Ce module fournit des fonctions pour configurer l'impression, détecter le serveur CUPS
et envoyer des fichiers à imprimer en utilisant la commande lp.
Il gère les options d'impression telles que le nombre de copies, le format de page,
le recto/verso, l'orientation et la couleur, tout en assurant une compatibilité maximale
avec les pilotes d'impression courants.
"""

import subprocess
import os
from logging import getLogger
from .config.config import ConfigApp

logger = getLogger(__name__)

DEFAULT_PRINTER_NAME = 'Imprimerie_Sharp'
DEFAULT_PRINTER_IP = '172.17.0.1'  # IP Docker bridge par défaut

def get_watched_dir() -> str:
    """Retourne le chemin du dossier surveillé pour les fichiers à imprimer."""
    return ConfigApp.PRINT_PATH

def get_cups_server() -> str:
    """Retourne l'IP du serveur CUPS sur l'hôte Docker"""
    try:
        # Récupérer l'IP de la passerelle Docker (hôte)
        result = subprocess.run(['ip', 'route', 'show', 'default'],
                              capture_output=True, text=True, check=True)
        if result.returncode == 0:
            # Extraire l'IP de la passerelle de la sortie
            gateway_ip = result.stdout.split()[2]
            logger.info("CUPS server IP detected: %s", gateway_ip)
            return gateway_ip
        else:
            # Fallback vers l'IP Docker bridge standard
            logger.warning("Could not determine gateway IP, using default")
            return DEFAULT_PRINTER_IP
    except Exception as e:
        logger.exception("Error determining gateway IP: %s, using fallback", e)
        return DEFAULT_PRINTER_IP

def get_printer_name() -> str:
    """Retourne le nom de l'imprimante configurée."""
    return ConfigApp.PRINTER_NAME

def print_file(file_path: str, user_name: str = 'Default', site_name: str = 'Default',
               copies: str = '1', sides: str = 'one-sided', media: str = 'A4',
               orientation: str = '3', color: str = 'monochrome') -> None:
    """
    Imprimer un fichier via la commande lp en utilisant CUPS sur l'hôte Docker
    """
    try:
        # Configuration du serveur CUPS
        cups_server = get_cups_server()
        printer_name = get_printer_name()

        # Préparation de la commande lp avec options
        cmd = ['lp', '-d', printer_name]

        # Ajouter les options d'impression supportées
        cmd.extend(['-n', copies])  # Nombre de copies

        # Format de page (utiliser PageSize au lieu de media)
        if media.upper() in ['A4', 'A3', 'A5', 'LETTER', 'LEGAL']:
            cmd.extend(['-o', f'PageSize={media.upper()}'])
        else:
            cmd.extend(['-o', 'PageSize=A4'])  # Par défaut A4

        # Gestion du recto/verso
        duplex_mapping = {
            'one-sided': 'None',
            'two-sided-long-edge': 'DuplexNoTumble',
            'two-sided-short-edge': 'DuplexTumble'
        }
        duplex_value = duplex_mapping.get(sides, 'None')
        cmd.extend(['-o', f'Duplex={duplex_value}'])

        # Orientation (si supportée par le pilote)
        if orientation == '4':  # Paysage
            cmd.extend(['-o', 'landscape'])
        elif orientation == '3':  # Portrait (par défaut)
            cmd.extend(['-o', 'portrait'])

        # Pour les options de couleur non supportées par les pilotes génériques,
        # on peut essayer d'utiliser des options PostScript/PCL directes
        if color == 'monochrome':
            # Option pour forcer le noir et blanc (peut ne pas fonctionner avec tous les pilotes)
            cmd.extend(['-o', 'ColorModel=Gray'])
        elif color == 'color':
            cmd.extend(['-o', 'ColorModel=RGB'])

        # Titre du travail
        cmd.extend(['-t', f'Intranet-{user_name}-{site_name}'])

        # Options supplémentaires pour améliorer la qualité
        cmd.extend(['-o', 'fit-to-page'])  # Ajuster à la page
        cmd.extend(['-o', 'number-up=1'])  # Une page par feuille

        # Ajouter le fichier à imprimer
        cmd.append(file_path)

        # Configuration de l'environnement pour pointer vers le serveur CUPS de l'hôte
        env = os.environ.copy()
        env['CUPS_SERVER'] = cups_server

        logger.info(
            "Printing file %s to printer %s via CUPS server %s",
            file_path, printer_name, cups_server
        )
        logger.info("Command: %s", ' '.join(cmd))

        # Exécuter la commande d'impression
        result = subprocess.run(
            cmd, env=env, capture_output=True, text=True, timeout=30, check=True
        )

        if result.returncode == 0:
            # Extraire l'ID du travail d'impression de la sortie
            output = result.stdout.strip()
            logger.info("Print job submitted successfully: %s", output)
            print(f"✅ Impression envoyée avec succès: {output}")
        else:
            error_msg = result.stderr.strip() if result.stderr else "Erreur inconnue"
            logger.error("Print command failed: %s", error_msg)
            raise RuntimeError(f"Erreur d'impression: {error_msg}")

    except subprocess.TimeoutExpired as e:
        logger.error("Print command timed out")
        raise RuntimeError("Timeout lors de l'impression") from e
    except FileNotFoundError as e:
        logger.error("lp command not found - cups-client not installed?")
        raise RuntimeError("Commande lp non trouvée. Installer cups-client.") from e
    except Exception as e:
        logger.exception("Erreur lors de l'impression")
        raise RuntimeError(f"Erreur lors de l'impression: {e}") from e
