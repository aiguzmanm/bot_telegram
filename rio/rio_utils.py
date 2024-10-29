import os
import pandas as pd
import requests as rq
import ssl
import wget
import warnings
import sys

# Añadir el directorio raíz del proyecto al sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

from modules.download_utils import descarga_rio_api  # Asegúrate de que la ruta sea correcta


warnings.filterwarnings('ignore')
pd.options.mode.chained_assignment = None

def descargar_rio(fecha, base_dir="./datos"):
    rio_dir = os.path.join(base_dir, 'rio')
    dest_csv = os.path.join(rio_dir, f"RIO{fecha}.csv")
    dest_xlsx = os.path.join(rio_dir, f"RIO{fecha}.xlsx")
    
    descarga_rio_api(fecha, dest_csv, dest_xlsx)
    formato_rio(dest_csv, dest_xlsx)
def formato_rio(destcsv, destxls):
    # Leer el archivo CSV, omitiendo las primeras cuatro filas y configurando el delimitador correcto
    df = pd.read_csv(destcsv, encoding='utf-8', skiprows=4, sep=';')
    
    # Eliminar todas las filas donde la columna "HORA" es NaN
    df = df.dropna(subset=['HORA'])
    
    # Ordenar el DataFrame por la columna 'HORA'
    df = df.sort_values(by=['HORA'], ascending=True)
    
    # Eliminar la última columna (columna de FECHA)
    df = df.drop(df.columns[len(df.columns)-1], axis=1)
    
    # Lista de valores para la segunda fila
    datos_primera_fila = [
        'fecha', 'Hora Movi.', 'Central-Unidad', 'Configuración', 'POTENCIA MÁXIMA', 'POTENCIA MÍNIMA', 
        'Despacho', 'Estado', 'EO', 'Consigna/Cmg', 'Consigna/Limitación', 'Instrucción Cmg', 'Motivo', 
        'Zona Desacople', 'SENTIDO FLUJO', 'ESTADO DE EMBALSE', 'Nº DOCUMENTO', 'CENTRO DE CONTROL', 
        'CRUCERO__220', 'D.ALMAGRO__220', 'CARDONES_220', 'P.AZUCAR__220', 'L.PALMAS___220', 'QUILLOTA__220', 
        'A.JAHUEL__220', 'CHARRUA__220', 'P.MONTT___220'
    ]
    
    # Crear un DataFrame para la segunda fila
    nuevo_df = pd.DataFrame([datos_primera_fila])
    nuevo_df.columns = df.columns  # Asegurar que los nombres de las columnas coinciden
    
    # Concatenar la fila adicional al DataFrame original
    df = pd.concat([nuevo_df, df], ignore_index=True)
    
    # Insertar una columna vacía después de 'Hora Movi.'
    df.insert(2, 'VACIO', '')
    
    # Trasladar las columnas "POTENCIA MÁXIMA" y "POTENCIA MÍNIMA" después de la columna "Nº DOCUMENTO"
    df.insert(17, 'POTENCIA MÁXIMA', df.pop('POTENCIA MÁXIMA'))
    df.insert(18, 'POTENCIA MÍNIMA', df.pop('POTENCIA MÍNIMA'))
    
    # Eliminar filas donde 'BCMG QUILLOTA_22O' es NaN (si esta columna existe)
    if 'BCMG QUILLOTA_22O' in df.columns:
        df = df.dropna(subset=['BCMG QUILLOTA_22O'])
    
    # Guardar el DataFrame en un archivo Excel con el formato deseado
    df.to_excel(destxls, sheet_name='MOV-CMG', index=False)
    print(f"Archivo RIO formateado y guardado en {destxls}")

def detectar_fallas(fecha, base_dir="../datos"):
    rio_dir = os.path.join(base_dir, 'rio')
    fallas_dir = os.path.join(base_dir, 'fallas')

    ruta_rio = os.path.join(rio_dir, f"RIO{fecha}.xlsx")
    ruta_fallas = os.path.join(fallas_dir, f"{fecha}.csv")

    df_rio = pd.read_excel(ruta_rio, sheet_name="MOV-CMG")
    dffalla = df_rio.iloc[2:, [1, 3, 6]]
    dffalla.columns = ['Hora', 'Planta', 'Estado']
    dffalla = dffalla[dffalla['Estado'] == 'DF']

    if dffalla.empty:
        return None

    if os.path.exists(ruta_fallas):
        dffalla_anterior = pd.read_csv(ruta_fallas)
    else:
        dffalla.to_csv(ruta_fallas, index=False)
        return dffalla

    # Comparar con fallas anteriores
    nuevas_fallas = pd.concat([dffalla, dffalla_anterior]).drop_duplicates(keep=False)

    # Guardar las fallas actuales
    dffalla.to_csv(ruta_fallas, index=False)

    return nuevas_fallas if not nuevas_fallas.empty else None

