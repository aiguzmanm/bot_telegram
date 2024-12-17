import os
import pandas as pd
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
temp_path = os.path.abspath(os.path.join(project_root,'datos','tmp'))


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

def guardar_archivo_gen(fecha, df_opreal, df_programa):
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
        max_hora = df_opreal2[df_opreal2["Energia Bruta [MWh]"] > 8000]["Hora"].max()
    
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


def obtener_balance(fecha):
    
    idfecha="20"+str(fecha)
    datos_root = os.path.abspath(os.path.join(project_root, 'datos'))
    gen_root = os.path.join(datos_root, 'gen')
    cmg_root = os.path.join(datos_root, 'cmg')
    balance_root = os.path.join(datos_root, 'balance')

    #leer archivos
    df_retiros=pd.read_csv(datos_root+'/RetirosBDG.csv',encoding='latin-1')
    df_inyecciones=pd.read_parquet(gen_root+f'/{fecha}.parquet')
    df_cmg=pd.read_csv(cmg_root+f'/{fecha}.csv')
    df_CenZona=pd.read_excel(datos_root+'/parametros.xlsx',sheet_name='Central-Zona',engine='calamine')
    df_ZonaBarr=pd.read_excel(datos_root+'/parametros.xlsx',sheet_name='Zona-Barra',engine='calamine')

    #rescatar Retiros por Zona del día
    df_retiros['Id_Fecha']=df_retiros['Id Fecha']*100+df_retiros['Hora']
    df_retiros=df_retiros[df_retiros['Id_Fecha'].astype(str).str[:8]==idfecha]
    df_retiros.rename(columns={'Fisico [MWh]':'Retiros[MWh]'},inplace=True)
    df_retiros=df_retiros[['Id_Fecha','Zona','Retiros[MWh]']]
    df_retiros=df_retiros.groupby(['Id_Fecha','Zona']).sum().reset_index()

    #rescatar Inyecciones por Zona del día

    # finltrar inyecciones donde Grupo = ENEL, después borrar Grupo
    df_inyecciones=df_inyecciones[df_inyecciones['Grupo']=='ENEL']
    df_inyecciones.drop('Grupo', axis=1, inplace=True)
    #convertir año mes dia en int
    df_inyecciones['Año']=df_inyecciones['Año'].astype(int)
    df_inyecciones['Mes']=df_inyecciones['Mes'].astype(int)
    df_inyecciones['Día']=df_inyecciones['Día'].astype(int)
    df_inyecciones['Id_Fecha']=df_inyecciones['Año']*1000000+df_inyecciones['Mes']*10000+df_inyecciones['Día']*100+df_inyecciones['Hora']
    df_inyecciones=pd.merge(df_inyecciones,df_CenZona,how='left',left_on='Central Reporte',right_on='Central Reporte')
    df_inyecciones.rename(columns={'Energía Bruta [MWh]':'Inyecciones[MWh]'},inplace=True)
    df_inyecciones=df_inyecciones[['Id_Fecha','Zona','Inyecciones[MWh]']]
    df_inyecciones=df_inyecciones.groupby(['Id_Fecha','Zona']).sum().reset_index()

    #rescatar Cmg por Zona del día
    df_cmg.drop(df_cmg.columns[0], axis=1, inplace=True)
    df_cmg=df_cmg.unstack().reset_index()
    df_cmg.rename(columns={'level_0':'Barra',0:'Cmg[MWh]','level_1':'Hora'},inplace=True)
    df_cmg['Id_Fecha']=int(idfecha)*100 + df_cmg['Hora']+1

    #crear df Balance
    df_balance=pd.merge(df_retiros,df_inyecciones,how='outer',on=['Id_Fecha','Zona'])
    df_balance=pd.merge(df_balance,df_ZonaBarr,how='left',on='Zona')
    df_balance=pd.merge(df_balance,df_cmg[['Id_Fecha','Barra','Cmg[MWh]']],how='left',on=['Id_Fecha','Barra'])
    df_balance['Inyecciones[MWh]'].fillna(0,inplace=True)
    df_balance['Retiros[MWh]'].fillna(0,inplace=True)
    df_balance['Retiros[USD]']=df_balance['Retiros[MWh]']*df_balance['Cmg[MWh]']
    df_balance['Inyecciones[USD]']=df_balance['Inyecciones[MWh]']*df_balance['Cmg[MWh]']
    df_balance['SPOT[MWh]']=df_balance['Inyecciones[MWh]']+df_balance['Retiros[MWh]']
    df_balance['SPOT[USD]']=df_balance['Inyecciones[USD]']+df_balance['Retiros[USD]']
    df_balance['Hora']=df_balance['Id_Fecha']-int(idfecha)*100
    df_balance['SPOT[MWh]'].fillna(0,inplace=True)
    df_balance['SPOT[USD]'].fillna(0,inplace=True)

    #Guardar Balance
    df_balance.to_csv(balance_root+f'/{fecha}.csv',index=False)