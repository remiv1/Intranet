import cups # Importation de la bibliothèque cups pour la gestion des impressions, impossible sur Windows
from config import ConfigDict
from typing import cast

def get_config() -> ConfigDict:
    """Import tardif pour éviter l'import circulaire"""
    from application import peraudiere
    return cast(ConfigDict, peraudiere.config)

def get_watched_dir() -> str:
    return get_config().get("PRINT_PATH", '/prints')

def get_connection():
    return cups.Connection(host='host.docker.internal')

def get_printer_name() -> str:
    return get_config().get("PRINTER_NAME", 'Default_Printer')

def print_file(file_path: str, user_name: str = 'Default', site_name: str = 'Default',
               copies: str = '1', sides: str = 'one-sided', media: str = 'A4',
               orientation: str = '3', color: str = 'monochrome') -> None:
    options = {
        'copies': copies,
        'sides': sides, # 'two-sided-long-edge', 'two-sided-short-edge', 'one-sided'
        'media': media,
        'orientation-requested': orientation, # '3' = landscape, '4' = reverse landscape
        'print-color-mode': color, # 'color', 'monochrome'
        'job-hold-until': 'no-hold',
        'job-sheets': 'none,none',
        'job-priority': '1',
        'job-name': 'Impression Intranet',
        'job-originating-user-name': user_name + site_name,
        'job-originating-host-name': 'Intranet',
        'job-originating-host': 'Intranet',
        'job-originating-host-ip': '192.168.1.135'
    }
    conn = get_connection()
    printer_name = get_printer_name()
    conn.printFile(printer_name, file_path, "Print Job", options)
