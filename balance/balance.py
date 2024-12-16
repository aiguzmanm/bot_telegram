import os
import sys
import datetime as dt
import pandas as pd

from balance_utils import ajustar_formato_opreal, ajustar_formato_programa, guardar_archivo_gen, obtener_balance

# Asegurar que el directorio raíz del proyecto está en sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

from modules.telegram_utils import cargar_config, enviar_foto_telegram
from modules.graph_utils import generar_graficos_balance

def main(fecha=None):
    # Configuración inicial
    config = cargar_config()

    # Manejo de fecha
    if fecha is None and len(sys.argv) > 1:
        fecha = sys.argv[1]
    if not fecha:
        deltatime = int(config['timezone']['adjustment_hours'])
        fecha = (dt.datetime.now() - dt.timedelta(hours=deltatime)).strftime("%y%m%d")

    df_opreal = pd.read_parquet(os.path.join(project_root,'datos','opreal', f"{fecha}.parquet"))

    # Ajustar formato de datos
    df_opreal = ajustar_formato_opreal(df_opreal)
    df_programa = ajustar_formato_programa(fecha)

    # Guardar archivo gen
    max_hora = guardar_archivo_gen(fecha,df_opreal, df_programa)
    obtener_balance(fecha)
    generar_graficos_balance(fecha,max_hora)
    enviar_foto_telegram(os.path.join(project_root,'datos','plot_balance', f"{fecha}.png"))
    
if __name__ == "__main__":
    main()
