import os
import pandas as pd
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
temp_path = os.path.abspath(os.path.join(project_root,'datos','tmp'))

def hacer_solicitud_curl(url, token, output_path):
    """
    Realiza una solicitud GET usando curl y guarda la respuesta en un archivo.
    
    :param url: URL del endpoint.
    :param token: Token de autenticación.
    :param output_path: Ruta donde guardar la respuesta.
    """
    command = f'curl -s -H "Authorization: Token {token}" "{url}" > {output_path}'
    os.system(command)

def get_endpoint(url, token, temp_file="out.json"):
    """
    Obtiene datos de un endpoint iterando sobre las páginas usando curl.
    
    :param url: URL inicial del endpoint.
    :param token: Token de autenticación.
    :param temp_file: Nombre del archivo temporal donde guardar las respuestas.
    :return: DataFrame con todos los resultados.
    """
    df = pd.DataFrame()
    while url:
        print(f"Consultando: {url}")
        hacer_solicitud_curl(url, token, temp_file)
        with open(temp_file, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                print("Error al decodificar JSON. Revisa el archivo temporal.")
                break

        # Si la respuesta es una lista, no hay paginación
        if isinstance(data, list):
            df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)
            break

        # Si la respuesta es un diccionario, verifica paginación
        if 'results' in data:
            df = pd.concat([df, pd.DataFrame(data['results'])], ignore_index=True)
        
        # Obtener el enlace a la siguiente página
        url = data.get('next', None)
    
    # Eliminar archivo temporal
    if os.path.exists(temp_file):
        os.remove(temp_file)

    return df

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


def guardar_parquet(dataframe, output_dir, filename):
    """
    Guarda un DataFrame en formato parquet.
    
    :param dataframe: DataFrame a guardar.
    :param output_dir: Directorio de salida.
    :param filename: Nombre del archivo.
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    dataframe.to_parquet(filepath, index=False)
    #dataframe.to_csv(filepath+'.csv', index=False)  
    print(f"Archivo guardado: {filepath}")