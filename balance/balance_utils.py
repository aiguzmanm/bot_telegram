import os
import pandas as pd
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
temp_path = os.path.abspath(os.path.join(project_root,'datos','tmp'))


def ajustar_formato(df, path_homologaciones):
    """
    Ajusta el formato del DataFrame descargado y realiza la homologación de centrales.

    :param df: DataFrame con los datos descargados.
    :param path_homologaciones: Ruta al archivo de homologaciones.
    :return: DataFrame ajustado.
    """
    # Leer el archivo de homologaciones
    homologaciones_path = os.path.join(path_homologaciones, 'Homologaciones bd v1.xlsx')
    hoja_central = "Central Origen Opreal"
    df_central_origen = pd.read_excel(homologaciones_path, sheet_name=hoja_central, engine='openpyxl')

    # Asegurar que las claves estén en mayúsculas
    df['natural_key'] = df['natural_key'].str.upper()
    df_central_origen['Central Origen'] = df_central_origen['Central Origen'].str.upper()

    # Cruzar los DataFrames usando "natural_key" con "Central Origen"
    df = df.merge(df_central_origen[['Central Origen', 'Id Central']], 
                  left_on='natural_key', right_on='Central Origen', how='left')

    # Validar si hay valores de "natural_key" que no se pudieron homologar
    no_homologados = df[df['Id Central'].isna()]
    if not no_homologados.empty:
        print(f"Advertencia: {len(no_homologados)} valores de 'natural_key' no se pudieron homologar:")
        print(no_homologados['natural_key'].unique())

    # Renombrar columnas según lo especificado
    df.rename(columns={
        'hour': 'Hora',
        'value': 'Energia Bruta [MWh]',
        'date': 'Id Fecha'
    }, inplace=True)

    # Convertir "Id Fecha" al formato yymmdd
    df['Id Fecha'] = pd.to_datetime(df['Id Fecha'], format='%Y-%m-%d').dt.strftime('%y%m%d').astype(int)

    # Reorganizar el DataFrame dejando solo las columnas requeridas
    columnas_finales = ['Id Fecha', 'Hora', 'Energia Bruta [MWh]', 'Id Central']
    df = df[columnas_finales]

    return df