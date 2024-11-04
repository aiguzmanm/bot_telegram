import os
import sys
import pandas as pd
import datetime as dt

pd.options.mode.chained_assignment = None

# Añadir el directorio raíz del proyecto al sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)


from modules.telegram_utils import enviar_reporte_telegram, enviar_foto_telegram, cargar_config
#from modules.data_processing import calcular_cmg, ordenar_dataframe_con_primera_fila, 
from modules.graph_utils import generar_grafico_cmg
from informe_utils import parches_rio, ordenar_dataframe_con_primera_fila, calcular_cmg

def main(fecha=None):

    config = cargar_config()
    #cargar deltatime como int
    deltatime = int(config['timezone']['adjustment_hours'])

    # Si se proporciona un argumento de fecha, úsalo
    if fecha is None and len(sys.argv) > 1:
        fecha = sys.argv[1]

    # Si la fecha sigue siendo None, usa la fecha de hoy
    if not fecha:
        hoy = dt.datetime.now() - dt.timedelta(hours=deltatime)
        fecha = hoy.strftime("%y%m%d")

    # Rutas basadas en el directorio del script
    datos_dir = os.path.join(project_root, 'datos')
    ruta_rio = os.path.join(datos_dir, 'rio', f'RIO{fecha}.xls')
    ruta_des = os.path.join(datos_dir, 'des', f'{fecha}.csv')
    ruta_cmg = os.path.join(datos_dir, 'cmg', f'{fecha}.csv')
    ruta_plot_cmg = os.path.join(datos_dir, 'plot_cmg', f'{fecha}.jpg')
    ruta_po = os.path.join(datos_dir, 'po', f'PO{fecha}.xlsx')


    
    # Leer y procesar el archivo descargado
    df_rio = pd.read_excel(ruta_rio, sheet_name="MOV-CMG", engine='calamine').replace("ERNC","PAM_COGEN")
    #df_rio = parches_rio(df_rio)
    df_rio = ordenar_dataframe_con_primera_fila(df_rio)
    
    #Leer políticas
    df_po = pd.read_excel(ruta_po, sheet_name="TCO", engine='calamine')
    df_fp = pd.read_excel(ruta_po, sheet_name="FP diario",engine = 'calamine')

    
    df_cmg, df_fp = calcular_cmg(df_rio,fecha,datos_dir)

    # Guardar el archivo CSV de `df_cmg`
    df_cmg.to_csv(ruta_cmg, index=True)

    # Generar el gráfico de CMG y guardarlo
    generar_grafico_cmg(fecha, ruta_cmg, ruta_plot_cmg)
    enviar_reporte_telegram(fecha)
    enviar_foto_telegram(ruta_plot_cmg)

if __name__ == "__main__":
    main()