import os
import time
import cups
from app import app

WATCHED_DIR = app.config["PRINT_PATH"]
conn = cups.Connection()
printer_name = app.config["PRINTER_NAME"]

def print_file(file_path):
    conn.printFile(printer_name, file_path, "Print Job", {})

def main():
    while True:
        for filename in os.listdir(WATCHED_DIR):
            file_path = os.path.join(WATCHED_DIR, filename)
            if os.path.isfile(file_path):
                print_file(file_path)
                os.remove(file_path)
        time.sleep(600)
