import subprocess # Pour exécuter la commande lp
import os
from config import ConfigDict
from typing import cast
from logging import getLogger

logger = getLogger(__name__)

def get_config() -> ConfigDict:
    """Import tardif pour éviter l'import circulaire"""
    from application import peraudiere
    return cast(ConfigDict, peraudiere.config)

def get_watched_dir() -> str:
    return get_config().get("PRINT_PATH", '/prints')

def get_cups_server() -> str:
    """Retourne l'IP du serveur CUPS sur l'hôte Docker"""
    try:
        # Récupérer l'IP de la passerelle Docker (hôte)
        result = subprocess.run(['ip', 'route', 'show', 'default'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            # Extraire l'IP de la passerelle de la sortie
            gateway_ip = result.stdout.split()[2]
            logger.info(f"CUPS server IP detected: {gateway_ip}")
            return gateway_ip
        else:
            # Fallback vers l'IP Docker bridge standard
            logger.warning("Could not determine gateway IP, using default")
            return '172.17.0.1'
    except Exception as e:
        logger.error(f"Error determining gateway IP: {e}, using fallback")
        return '172.17.0.1'

def get_printer_name() -> str:
    return get_config().get("PRINTER_NAME", 'Imprimerie_Sharp')

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
        
        logger.info(f"Printing file {file_path} to printer {printer_name} via CUPS server {cups_server}")
        logger.info(f"Command: {' '.join(cmd)}")
        
        # Exécuter la commande d'impression
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Extraire l'ID du travail d'impression de la sortie
            output = result.stdout.strip()
            logger.info(f"Print job submitted successfully: {output}")
            print(f"✅ Impression envoyée avec succès: {output}")
        else:
            error_msg = result.stderr.strip() if result.stderr else "Erreur inconnue"
            logger.error(f"Print command failed: {error_msg}")
            raise Exception(f"Erreur d'impression: {error_msg}")
            
    except subprocess.TimeoutExpired:
        logger.error("Print command timed out")
        raise Exception("Timeout lors de l'impression")
    except FileNotFoundError:
        logger.error("lp command not found - cups-client not installed?")
        raise Exception("Commande lp non trouvée. Installer cups-client.")
    except Exception as e:
        logger.error(f"Print error: {e}")
        raise Exception(f"Erreur lors de l'impression: {e}")
