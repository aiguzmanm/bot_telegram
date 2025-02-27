import os
import sys
import pandas as pd
import datetime as dt
import requests as rq
import cloudscraper

from descarga_enso_utils import descargar_archivo_enso, data_ONI

# Añadir el directorio raíz del proyecto al sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

def main():
    descargar_archivo_enso()
    #data_ONI()
if __name__ == "__main__":
    main()