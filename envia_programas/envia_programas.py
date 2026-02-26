# envia_programas.py
import os
import sys
import datetime as dt

from envia_programas_utils import descargar_PRO_API, descargar_PID_API

# Añadir el directorio raíz del proyecto al sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

def main():
    fechas = [
        dt.datetime.now() - dt.timedelta(days=1),  # ayer
        dt.datetime.now(),                         # hoy
        dt.datetime.now() + dt.timedelta(days=1),  # mañana
    ]

    for ref_date in fechas:
        descargar_PRO_API(ref_date=ref_date)
        descargar_PID_API(ref_date=ref_date)

if __name__ == "__main__":
    main()