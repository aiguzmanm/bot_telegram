import os
import sys
import datetime as dt
import pandas as pd


# Asegurar que el directorio raíz del proyecto está en sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

from modules.graph_utils import generar_grafico_gen, generar_tabla_gen
from modules.telegram_utils import cargar_config

def main(fecha=None, grupo=None):
    # Configuración inicial
    config = cargar_config()
    #cargar deltatime como int
    deltatime = int(config['timezone']['adjustment_hours'])

    # Manejo de fecha
    if fecha is None and len(sys.argv) > 1:
        fecha = sys.argv[1]
    if not fecha:
        deltatime = int(config['timezone']['adjustment_hours'])
        fecha = (dt.datetime.now() - dt.timedelta(hours=deltatime)).strftime("%y%m%d")


    data = pd.read_parquet(project_root+f'/datos/gen/{fecha}.parquet')
    destino_root_gen = os.path.abspath(os.path.join(project_root,'datos','plot_gen'))
    destino_root_tab = os.path.abspath(os.path.join(project_root,'datos','tab_gen'))


    if grupo is None and len(sys.argv) > 2:
        grupo = sys.argv[2]
        data = data[data['Grupo'] == grupo.upper()]
        #pasar el string grupo a mayúsculas
        destino_root_gen = os.path.abspath(os.path.join(project_root,'datos','plot_gen_'+grupo))
        destino_root_tab = os.path.abspath(os.path.join(project_root,'datos','tab_gen_'+grupo))

    if not grupo:
        grupo = 'SEN'


    # max_hora corresponde al máximo valor de hora en data donde origen es igual a opreal
    max_hora = data[data['origen'] == 'opreal']['Hora'].max()

    generar_grafico_gen(fecha,data,max_hora,destino_root_gen,grupo)
    generar_tabla_gen(fecha,data,max_hora,destino_root_tab,grupo)
    
if __name__ == "__main__":
    main()