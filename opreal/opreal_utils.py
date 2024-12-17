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
    print(f"Archivo guardado: {filepath}")


def ajustar_formato_opreal(df):
    """
    Ajusta el formato del DataFrame descargado y realiza la homologación de centrales.

    :param df: DataFrame con los datos descargados.
    :param path_homologaciones: Ruta al archivo de homologaciones.
    :return: DataFrame ajustado.
    """
    # Leer el archivo de homologaciones
    homologaciones_path = os.path.join(project_root,'datos','homologa', 'Homologaciones bd v1.xlsx')
    hoja_central = "Central Origen Opreal"
    df_central_origen = pd.read_excel(homologaciones_path, sheet_name=hoja_central, engine='calamine')

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

def ajustar_formato_programa(fecha):

    """
    Ajusta el formato del programa descargado desde el archivo PRG y realiza la homologación de centrales.

    :param fecha: Fecha en formato yymmdd para identificar el archivo PRG correspondiente.
    :return: DataFrame con los datos ajustados y homologados.
    """ 
    # Leer el archivo de homologaciones
    homologaciones_path = os.path.join(project_root,'datos','homologa', 'Homologaciones bd v1.xlsx')
    hoja_central = "Central Origen Programa"
    df_central_origen = pd.read_excel(homologaciones_path, sheet_name=hoja_central, engine='calamine')

    # Ruta del archivo PRG
    prg_path = os.path.join(project_root, 'datos', 'prg', f'PRG{fecha}.xlsx')
    hoja_programa = 'PROGRAMA'

    # Validar existencia de archivo
    if not os.path.exists(prg_path):
        raise FileNotFoundError(f"Archivo no encontrado: {prg_path}")

    # Leer el archivo y rescatar solo columnas C, E-AB
    df_programa = pd.read_excel(prg_path, sheet_name=hoja_programa, header=None, engine='calamine')
    df_programa = df_programa.iloc[:, [2] + list(range(4, 28))]  # Columna C y columnas E-AB

    # Secciones relevantes
    secciones_relevantes = [
        'Hidroeléctricas de Pasada', 'Eólicas', 'Solares',
        'Centrales de concentración solar', 'Térmicas',
        'Embalses y Reguladas', 'Sistemas de Almacenamiento'
    ]

    # Procesar cada sección
    dfs = []
    for i, value in enumerate(df_programa.iloc[:, 0]):  # Revisar la columna C (índice 0 del nuevo DataFrame)
        if isinstance(value, str) and value.strip() in secciones_relevantes:
            # Identificar el inicio de la sección (fila con el nombre de la sección)
            start_row = i + 2  # Saltar la fila inmediatamente debajo (Totales)
            
            # Determinar el final de la sección
            end_row = next((j for j in range(start_row, len(df_programa)) 
                            if pd.isna(df_programa.iloc[j, 0])), len(df_programa))

            # Extraer datos de la sección
            df_seccion = df_programa.iloc[start_row:end_row].copy()

            # Asignar nombres de columnas
            df_seccion.columns = ['Nombre'] + list(range(1, 25))  # Nombre y horas (1-24)

            # Reorganizar formato base de datos
            df_seccion = df_seccion.melt(id_vars=['Nombre'], var_name='Hora', value_name='Energia Bruta [MWh]')
            df_seccion['Hora'] = df_seccion['Hora'].astype(int)
            df_seccion.dropna(subset=['Energia Bruta [MWh]'], inplace=True)
            df_seccion['Nombre'] = df_seccion['Nombre'].str.upper()

            dfs.append(df_seccion)

    # Unir todas las secciones
    df_final = pd.concat(dfs, ignore_index=True)

    # Agregar la fecha
    df_final['Id Fecha'] = int(fecha)

    # Seleccionar las columnas finales
    columnas_finales = ['Nombre', 'Id Fecha', 'Hora', 'Energia Bruta [MWh]']
    df_final = df_final[columnas_finales]

    # Cruzar los DataFrames usando "Nombre" con "Central Origen"
    df_final = df_final.merge(df_central_origen[['Central Origen', 'Id Central']], 
                  left_on='Nombre', right_on='Central Origen', how='left')
    
    # Seleccionar las columnas finales
    columnas_finales =  ['Id Fecha', 'Hora', 'Energia Bruta [MWh]', 'Id Central']
    df_final = df_final[columnas_finales]

    return df_final

def guardar_archivo_gen(fecha, df_opreal, df_programa,umbral=8000):
    """Guarda los archivos generados en el directorio de salida.

    Args:
        fecha (str): Fecha en formato YYYYMMDD.
        df_opreal (DataFrame): DataFrame con los datos de ORPEAL.
        df_programa (DataFrame): DataFrame con los datos del programa.
    """
    # Guardar los archivos generados
    output_dir = os.path.join(project_root, 'datos', 'gen')

    df_opreal["origen"]="opreal"    
    df_programa=df_programa.groupby(["Id Central","Id Fecha","Hora"]).sum().reset_index()
    df_programa["origen"]="programa"

    #completar datos de df_opreal con df_programa para horas que no hay datos en df_opreal
    if df_programa.shape[0] == 0:
        # Si no hay datos en df_programa, usa todo df_opreal
        df_cent = df_opreal.copy()
        max_hora = 24
    else:
        # Determinar la última hora válida en df_opreal
        df_opreal2 = df_opreal.groupby(["Hora"]).sum().reset_index()
        max_hora = df_opreal2[df_opreal2["Energia Bruta [MWh]"] > umbral]["Hora"].max()
    
    df_programa_filtered = df_programa[df_programa['Hora'] > max_hora]
    df_opreal_filtered = df_opreal[df_opreal['Hora'] <= max_hora]

    # Combinar ambos dataframes en df_Cent
    df_cent = pd.concat([df_opreal_filtered, df_programa_filtered], ignore_index=True)

    # leer homologado
    homologaciones_path = os.path.join(project_root,'datos','homologa', 'Homologado_v3.xlsx')
    hoja_central = "ID CENTRAL"
    hoja_propietario = "ID PROPIETARIO"
    df_idCent = pd.read_excel(homologaciones_path, sheet_name=hoja_central, engine='calamine')
    df_idProp = pd.read_excel(homologaciones_path, sheet_name=hoja_propietario, engine='calamine')

    df_cent= pd.merge(df_cent,df_idCent,how='left',left_on='Id Central',right_on='Id Central')
    df_cent =df_cent[df_cent['Central Reporte'].notna()]

    df_cent= pd.merge(df_cent,df_idProp,how='left',left_on='Id Propietario',right_on='Id Propietario')
    df_cent =df_cent[df_cent['Propietario'].notna()]

    df_Iny=df_cent[["Central Reporte","Energia Bruta [MWh]","origen","Tecnologia","Grupo"]]
    df_Iny=df_Iny.rename(columns={"Energia Bruta [MWh]": "Energía Bruta [MWh]"})
    df_Iny["Año"]="20"+str(fecha)[0:2]
    df_Iny["Mes"]=str(fecha)[2:4]
    df_Iny["Día"]=str(fecha)[4:6]
    df_Iny["Hora"]=df_cent["Hora"]

    df_Iny.to_csv(output_dir+f'/{fecha}.csv',index=False, encoding="latin-1")
    return(max_hora)