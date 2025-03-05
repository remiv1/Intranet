import cups
from app import app

WATCHED_DIR = app.config["PRINT_PATH"]
conn = cups.Connection()
printer_name = app.config["PRINTER_NAME"]

def print_file(file_path, user_name='Default', site_name='Default', copies='1', sides='one-sided', media='A4', orientation='3', color='monochrome'):
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
    conn.printFile(printer_name, file_path, "Print Job", options)
