import pandas as pd
import os

def desacoples(df_cmg, archivo_destino):
    df_cmg["desacople"] = ""
    # ... (lógica de los if y los cálculos)
    df_cmg["desacople_s1"] = df_cmg["desacople"].shift(1)
    df_cmg = df_cmg[df_cmg["desacople_s1"] != df_cmg["desacople"]]
    df_cmg = df_cmg[['Hora Movi.', 'desacople']]
    df_cmg.to_csv(archivo_destino, index=False)

def ordenar_dataframe_con_primera_fila(dataframe):
    # Obtén el índice de la primera fila
    primer_fila_idx = dataframe.index[0]

    # Separa la primera fila del DataFrame
    #primer_fila = dataframe.iloc[primer_fila_idx]

    # Elimina la primera fila del DataFrame original
    #dataframe = dataframe.drop(primer_fila_idx)

    # Ordena el DataFrame por la columna de ordenación
    dataframe = dataframe.sort_values(by=[dataframe.columns[1]], ascending=True)

    # Restablece el índice del DataFrame resultante
    dataframe = dataframe.reset_index(drop=True)

    # Inserta la primera fila al principio del DataFrame resultante
    #dataframe = pd.concat([primer_fila.to_frame().T, dataframe])

    return dataframe

def calcular_cmg(df_rio, fecha, datos_dir="./datos"):
    ruta_po = os.path.join(datos_dir, 'po', f'PO{fecha}.xlsx')

    # Cargar datos desde las hojas TCO y FP diario
    df_po = pd.read_excel(ruta_po, sheet_name="TCO")
    df_fp = pd.read_excel(ruta_po, sheet_name="FP diario")

    # Crear `df_cmg` a partir de una selección de columnas de `df_rio`
    columnas_cmg = [
        "Hora Movi.", "CRUCERO__220", "D.ALMAGRO__220", "CARDONES_220",
        "P.AZUCAR__220", "L.PALMAS___220", "QUILLOTA__220",
        "A.JAHUEL__220", "CHARRUA__220", "P.MONTT___220"
    ]
    df_cmg = df_rio[columnas_cmg].copy()

    # Procesar columnas horarias en `df_cmg`
    df_cmg['hora'] = df_cmg['Hora Movi.'].astype(str).str[0:2].astype(int)
    df_cmg1 = df_cmg[df_cmg['hora'] < 8]
    df_cmg2 = df_cmg[(df_cmg['hora'] >= 8) & (df_cmg['hora'] < 18)]
    df_cmg3 = df_cmg[df_cmg['hora'] >= 18]

    # Tablas de costos variables por bloque
    col = ['Bar', 'CV']
    df_cv1 = df_po.iloc[6:, [2, 3]]
    df_cv1.columns = col
    df_cv2 = df_po.iloc[6:, [6, 7]]
    df_cv2.columns = col
    df_cv3 = df_po.iloc[6:, [10, 11]]
    df_cv3.columns = col

    # Rescatar factores de penalización
    df_fp = df_fp.iloc[:, 1:]
    df_fp.iloc[0, 0] = "BarNom"
    df_fp.columns = df_fp.iloc[0, :]
    df_fp = df_fp.drop(0).set_index("BarNom")
    df_fp = df_fp.loc[
        ["Crucero220", "DAlmagro220", "Cardones220", "PAzucar220",
         "Quillota220", "AJahuel220", "Charrua220", "PMontt220", "LPalmas220"], :
    ]
    df_fp = pd.DataFrame(df_fp.to_numpy(), index=[
        "CRUCERO__220", "D.ALMAGRO__220", "CARDONES_220", "P.AZUCAR__220",
        "QUILLOTA__220", "A.JAHUEL__220", "CHARRUA__220", "P.MONTT___220", "L.PALMAS___220"
    ])
    df_fp = df_fp.T.iloc[0:24, :]

    # Eliminar duplicados en cada bloque de CV
    df_cv1 = df_cv1.drop_duplicates(subset="Bar", keep="first")
    df_cv2 = df_cv2.drop_duplicates(subset="Bar", keep="first")
    df_cv3 = df_cv3.drop_duplicates(subset="Bar", keep="first")

    # Asignar costos variables por bloque a las columnas correspondientes en `df_cmg`
    for col in df_cmg1.columns[1:]:
        df_cmg1[col] = df_cmg1[col].map(df_cv1.set_index("Bar")["CV"])
    for col in df_cmg2.columns[1:]:
        df_cmg2[col] = df_cmg2[col].map(df_cv2.set_index('Bar')['CV'])
    for col in df_cmg3.columns[1:]:
        df_cmg3[col] = df_cmg3[col].map(df_cv3.set_index('Bar')['CV'])

    # Concatenar bloques horarios en `df_cmg`
    df_cmg = pd.concat([df_cmg1, df_cmg2, df_cmg3])
    df_cmg['hora'] = df_cmg['Hora Movi.'].astype(str).str[0:2].astype(int)
    
    desacoples_barras(fecha,df_cmg,datos_dir)
    df_cmg = df_cmg.drop(columns=['desacople', 'desacople_s1'], errors='ignore')

    
    #Calcular Promedio Ponderado
    # crea indice Datetime
    df_cmg['Datetime']=pd.to_datetime(fecha + " " + df_cmg["Hora Movi."].astype(str))
    # elimina campo Hora Movi (innecesario ahora)
    df_cmg.drop(["Hora Movi."],inplace=True, axis=1)
    # índice de la tabla ahora es Datetime
    df_cmg=df_cmg.set_index('Datetime')
    # elimina duplicados
    df_cmg = df_cmg[~df_cmg.index.duplicated(keep='first')]
    # resample con pad (rellena valores nuevos con el valor del registro anterior)
    df_cmg=df_cmg.resample('60s').ffill()
    # recalcula campo "hora"
    df_cmg["hora"]=df_cmg.index.hour  
    df_cmg =df_cmg.groupby('hora').mean()
    df_cmg=df_cmg.mul(df_fp)
    df_cmg.reindex(range(1,24))
    df_cmg.index = df_cmg.index +1

    return df_cmg, df_fp

def desacoples_barras(fecha,df_cmg,datos_dir):
    df_cmg["desacople"]=""
    for i in df_cmg.index:
        
        if(df_cmg["CRUCERO__220"][i]>df_cmg["D.ALMAGRO__220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"CRUCERO"+"<--"+"D.ALMAGRO"+"   "
        if(df_cmg["CRUCERO__220"][i]<df_cmg["D.ALMAGRO__220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"CRUCERO"+"-->"+"D.ALMAGRO"+"   "
            
        if(df_cmg["D.ALMAGRO__220"][i]>df_cmg["CARDONES_220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"D.ALMAGRO"+"<--"+"CARDONES"+"   "
        if(df_cmg["D.ALMAGRO__220"][i]<df_cmg["CARDONES_220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"D.ALMAGRO"+"-->"+"CARDONES"+"   "
            
        if(df_cmg["CARDONES_220"][i]>df_cmg["P.AZUCAR__220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"CARDONES"+"<--"+"P.AZUCAR"+"   "
        if(df_cmg["CARDONES_220"][i]<df_cmg["P.AZUCAR__220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"CARDONES"+"-->"+"P.AZUCAR"+"   "
        
        if(df_cmg["P.AZUCAR__220"][i]>df_cmg["L.PALMAS___220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"P.AZUCAR"+"<--"+"L.PALMAS"+"   "
        if(df_cmg["P.AZUCAR__220"][i]<df_cmg["L.PALMAS___220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"P.AZUCAR"+"-->"+"L.PALMAS"+"   "
            
        if(df_cmg["L.PALMAS___220"][i]>df_cmg["QUILLOTA__220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"L.PALMAS"+"<--"+"QUILLOTA"+"   "
        if(df_cmg["L.PALMAS___220"][i]<df_cmg["QUILLOTA__220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"L.PALMAS"+"-->"+"QUILLOTA"+"   "

        if(df_cmg["QUILLOTA__220"][i]>df_cmg["A.JAHUEL__220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"QUILLOTA"+"<--"+"A.JAHUEL"+"   "
        if(df_cmg["QUILLOTA__220"][i]<df_cmg["A.JAHUEL__220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"QUILLOTA"+"-->"+"A.JAHUEL"+"   "
            
        if(df_cmg["A.JAHUEL__220"][i]>df_cmg["CHARRUA__220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"A.JAHUEL"+"<--"+"CHARRUA"+"   "
        if(df_cmg["A.JAHUEL__220"][i]<df_cmg["CHARRUA__220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"A.JAHUEL"+"-->"+"CHARRUA"+"   "
            
        if(df_cmg["CHARRUA__220"][i]>df_cmg["P.MONTT___220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"CHARRUA"+"<--"+"P.MONTT"+"   "
        if(df_cmg["CHARRUA__220"][i]<df_cmg["P.MONTT___220"][i]):
            df_cmg["desacople"][i]=df_cmg["desacople"][i]+"CHARRUA"+"-->"+"P.MONTT"+"   "
        if(df_cmg["desacople"][i]==""):
            df_cmg["desacople"][i]="Sitema Acoplado"
          
    df_cmg["desacople_s1"]=df_cmg["desacople"].shift(1)
    df_cmg=df_cmg[df_cmg["desacople_s1"]!=df_cmg["desacople"]]
    df_cmg=df_cmg[['Hora Movi.', 'desacople']]
    df_cmg.to_csv(datos_dir+"/des/"+fecha+".csv",index=False)
