import os
import sys
import datetime as dt
from opreal_utils import get_endpoint, guardar_parquet

# Asegurar que el directorio raíz del proyecto está en sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

from modules.telegram_utils import cargar_config

def main(fecha=None):
    # Configuración inicial
    config = cargar_config()
    token = config['opreal']['token']
    base_url = "https://opreal.coordinador.cl/api/v3/datapoints/measurement/"
    output_dir = os.path.abspath(os.path.join(project_root, 'datos', 'opreal'))

    # Manejo de fecha
    if fecha is None and len(sys.argv) > 1:
        fecha = sys.argv[1]
    if not fecha:
        deltatime = int(config['timezone']['adjustment_hours'])
        fecha = (dt.datetime.now() - dt.timedelta(hours=deltatime)).strftime("%y%m%d")
    fechaurl = dt.datetime.strptime(fecha, "%y%m%d").strftime("%Y-%m-%d")
    print(f"Consultando generación para la fecha: {fechaurl}")

    # Parámetros de la API
    url = f"{base_url}?date={fechaurl}&key_type=energi"

    # Obtener datos usando curl
    datos_df = get_endpoint(url, token)

    # Guardar resultados en formato parquet
    guardar_parquet(datos_df, output_dir, f"{fecha}.parquet")

if __name__ == "__main__":
    main()
