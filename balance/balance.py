import os
import sys
import datetime as dt
import pandas as pd

from balance_utils import obtener_balance

# Asegurar que el directorio raíz del proyecto está en sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

from modules.telegram_utils import cargar_config, enviar_foto_telegram, enviar_archivo_telegram
from modules.graph_utils import generar_grafico_balance

def main(fecha=None):
    # Configuración inicial
    config = cargar_config()

    # Manejo de fecha
    if fecha is None and len(sys.argv) > 1:
        fecha = sys.argv[1]
    if not fecha:
        deltatime = int(config['timezone']['adjustment_hours'])
        fecha = (dt.datetime.now() - dt.timedelta(hours=deltatime)).strftime("%y%m%d")

    data = pd.read_csv(project_root+f'/datos/gen/{fecha}.csv',encoding='latin-1')
    max_hora = data[data['origen'] == 'opreal']['Hora'].max()

    obtener_balance(fecha)
    generar_grafico_balance(fecha,max_hora)
    enviar_foto_telegram(os.path.join(project_root,'datos','plot_balance', f"{fecha}.png"))
    enviar_archivo_telegram(os.path.join(project_root,'datos','balance', f"{fecha}.csv"))
    
if __name__ == "__main__":
    main()
