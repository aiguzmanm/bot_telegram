import os
import sys
import datetime as dt
import pandas as pd


from balance_utils import ajustar_formato

# Asegurar que el directorio raíz del proyecto está en sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)


from modules.telegram_utils import cargar_config

def main(fecha=None):
    # Configuración inicial
    config = cargar_config()
    path_homologaciones = os.path.abspath(os.path.join(project_root,'datos','homologa'))

    # Manejo de fecha
    if fecha is None and len(sys.argv) > 1:
        fecha = sys.argv[1]
    if not fecha:
        deltatime = int(config['timezone']['adjustment_hours'])
        fecha = (dt.datetime.now() - dt.timedelta(hours=deltatime)).strftime("%Y-%m-%d")

    df_opreal = pd.read_parquet(os.path.join(project_root,'datos','opreal' f"{fecha}.parquet"))

    # Ajustar formato de datos
    df_opreal = ajustar_formato(df_opreal, path_homologaciones)
if __name__ == "__main__":
    main()
