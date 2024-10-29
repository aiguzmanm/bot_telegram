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

from modules.download_utils import descarga_rio_api, descarga_rio_web, descarga_rio_recdec  # Asegúrate de que la ruta sea correcta


warnings.filterwarnings('ignore')
pd.options.mode.chained_assignment = None

def descargar_rio(fecha, base_dir="./datos"):
    rio_dir = os.path.join(base_dir, 'rio')
    dest_csv = os.path.join(rio_dir, f"RIO{fecha}.csv")
    dest_xlsx = os.path.join(rio_dir, f"RIO{fecha}.xlsx")
    
    descarga_rio_api(fecha, dest_csv, dest_xlsx)
    formato_rio(dest_csv, dest_xlsx)



def formato_rio(dest_csv, dest_xlsx):
    #print(f"Formateando RIO desde {dest_csv} a {dest_xlsx}")
    df = pd.read_csv(dest_csv, encoding='utf-8', skiprows=4, sep=';')
    df = df.dropna(subset=['HORA'])
    df = df.sort_values(by=['HORA'], ascending=True)
    df = df.drop(df.columns[len(df.columns)-1], axis=1)
    
    # Mapear nombres de columnas incorrectos a correctos
    mapeo_columnas = {
        'FECHA': 'fecha',
        'HORA': 'Hora Movi.',
        'NOMBRE CONFIGURACIÓN': 'Central-Unidad',
        'UNIDAD GENERADORA': 'Configuración',
        'POTENCIA MAXIMA': 'POTENCIA MÁXIMA',
        'POTENCIA MANIMA': 'POTENCIA MÍNIMA',
        'POTENCIA INSTRUIDA': 'Despacho',
        'ESTADO OPERACIONAL': 'Estado',
        'ESTADO OPERACIONAL COMBUSTIBLE': 'EO',
        'CONSIGNAS': 'Consigna/Cmg',
        'CONSIGNA LIMITACIAN': 'Consigna/Limitación',
        'MOTIVO': 'Motivo',
        'COMENTARIO': 'Instrucción Cmg',
        'ZONA DESACOPLE': 'Zona Desacople',
        'SENTIDO FLUJO': 'SENTIDO FLUJO',
        'ESTADO DE EMBALSE': 'ESTADO DE EMBALSE',
        'Nº DOCUMENTO': 'Nº DOCUMENTO',
        'CENTRO DE CONTROL': 'CENTRO DE CONTROL',
        'BCMG CRUCERO_22O': 'CRUCERO__220',
        'BCMG D.ALMAGRO_22O': 'D.ALMAGRO__220',
        'BCMG CARDONES_22O': 'CARDONES_220',
        'BCMG P.AZUCAR_22O': 'P.AZUCAR__220',
        'BCMG L.PALMAS_22O': 'L.PALMAS___220',
        'BCMG QUILLOTA_22O': 'QUILLOTA__220',
        'BCMG A.JAHUEL_22O': 'A.JAHUEL__220',
        'BCMG CHARRUA_22O': 'CHARRUA__220',
        'BCMG P.MONTT_22O': 'P.MONTT___220'
    }
    
    # Normalizar los nombres de las columnas
    df.columns = df.columns.str.strip().str.upper()
    # Renombrar las columnas
    df.rename(columns=mapeo_columnas, inplace=True)
    
    #print("Columnas después de renombrar:")
    #print(df.columns)
    
    # Crear la primera fila con los nombres de las columnas
    df_columns = df.columns.tolist()
    nuevo_df = pd.DataFrame([df_columns], columns=df.columns)
    df = pd.concat([nuevo_df, df], ignore_index=True)
    
    # Insertar columna vacía después de 'Hora Movi.'
    df.insert(2, 'VACIO', '')
    
    # Mover las columnas 'POTENCIA MÁXIMA' y 'POTENCIA MÍNIMA' después de la columna 17
    for col in ['POTENCIA MÁXIMA', 'POTENCIA MÍNIMA']:
        if col in df.columns:
            df.insert(17, col, df.pop(col))
        else:
            print(f"Advertencia: La columna '{col}' no se encontró y no se pudo mover.")
    
    # Guardar el DataFrame en un archivo Excel con extensión .xlsx
    df.to_excel(dest_xlsx, sheet_name='MOV-CMG', index=False, engine='openpyxl')
    print(f"Archivo RIO formateado y guardado en {dest_xlsx}")

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

