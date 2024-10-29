import os
import sys
import pandas as pd
import datetime as dt

# Añadir el directorio raíz del proyecto al sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

#from modules.data_processing import calcular_cmg, ordenar_dataframe_con_primera_fila, 
from modules.file_utils import guardar_csv
from modules.graph_utils import generar_grafico_cmg
from informe_utils import parches_rio, ordenar_dataframe_con_primera_fila

def main(fecha=None):
    if not fecha:
        hoy = dt.datetime.now() - dt.timedelta(hours=4)
        fecha = hoy.strftime("%y%m%d")

    # Rutas basadas en el directorio del script
    datos_dir = os.path.join(project_root, 'datos')
    ruta_rio = os.path.join(datos_dir, 'rio', f'RIO{fecha}.xlsx')
    ruta_des = os.path.join(datos_dir, 'des', f'{fecha}.csv')
    ruta_cmg = os.path.join(datos_dir, 'cmg', f'{fecha}.csv')
    ruta_plot_cmg = os.path.join(datos_dir, 'plot_cmg', f'{fecha}.jpg')
    ruta_po = os.path.join(datos_dir, 'po', f'PO{fecha}.xlsx')


    
    # Leer y procesar el archivo descargado
    df_rio = pd.read_excel(ruta_rio, sheet_name="MOV-CMG", engine='calamine').replace("ERNC","PAM_COGEN")
    df_rio = parches_rio(df_rio)
    df_rio = ordenar_dataframe_con_primera_fila(df_rio)
    
    #Leer políticas
    df_po = pd.read_excel(ruta_po, sheet_name="TCO", engine='calamine')
    df_fp = pd.read_excel(ruta_po, sheet_name="FP diario",engine = 'calamine')

    
    df_cmg, df_fp = calcular_cmg(df_rio,fecha,datos_dir)

    # Guardar el archivo CSV de `df_cmg`
    guardar_csv(df_cmg, ruta_cmg)

    # Generar el gráfico de CMG y guardarlo
    generar_grafico_cmg(fecha, ruta_cmg, ruta_plot)

if __name__ == "__main__":
    main()