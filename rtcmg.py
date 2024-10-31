import requests as rq
import wget
import pandas as pd
import datetime as dt
import os
import zipfile as zp
import ssl

pd.options.mode.chained_assignment = None


def Desacoples(dfCMG):
    dfCMG["desacople"]=""
    for i in dfCMG.index:
        
        if(dfCMG["CRUCERO__220"][i]>dfCMG["D.ALMAGRO__220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"CRUCERO"+"<--"+"D.ALMAGRO"+"   "
        if(dfCMG["CRUCERO__220"][i]<dfCMG["D.ALMAGRO__220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"CRUCERO"+"-->"+"D.ALMAGRO"+"   "
            
        if(dfCMG["D.ALMAGRO__220"][i]>dfCMG["CARDONES_220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"D.ALMAGRO"+"<--"+"CARDONES"+"   "
        if(dfCMG["D.ALMAGRO__220"][i]<dfCMG["CARDONES_220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"D.ALMAGRO"+"-->"+"CARDONES"+"   "
            
        if(dfCMG["CARDONES_220"][i]>dfCMG["P.AZUCAR__220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"CARDONES"+"<--"+"P.AZUCAR"+"   "
        if(dfCMG["CARDONES_220"][i]<dfCMG["P.AZUCAR__220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"CARDONES"+"-->"+"P.AZUCAR"+"   "
        
        if(dfCMG["P.AZUCAR__220"][i]>dfCMG["L.PALMAS___220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"P.AZUCAR"+"<--"+"L.PALMAS"+"   "
        if(dfCMG["P.AZUCAR__220"][i]<dfCMG["L.PALMAS___220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"P.AZUCAR"+"-->"+"L.PALMAS"+"   "
            
        if(dfCMG["L.PALMAS___220"][i]>dfCMG["QUILLOTA__220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"L.PALMAS"+"<--"+"QUILLOTA"+"   "
        if(dfCMG["L.PALMAS___220"][i]<dfCMG["QUILLOTA__220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"L.PALMAS"+"-->"+"QUILLOTA"+"   "

        if(dfCMG["QUILLOTA__220"][i]>dfCMG["A.JAHUEL__220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"QUILLOTA"+"<--"+"A.JAHUEL"+"   "
        if(dfCMG["QUILLOTA__220"][i]<dfCMG["A.JAHUEL__220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"QUILLOTA"+"-->"+"A.JAHUEL"+"   "
            
        if(dfCMG["A.JAHUEL__220"][i]>dfCMG["CHARRUA__220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"A.JAHUEL"+"<--"+"CHARRUA"+"   "
        if(dfCMG["A.JAHUEL__220"][i]<dfCMG["CHARRUA__220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"A.JAHUEL"+"-->"+"CHARRUA"+"   "
            
        if(dfCMG["CHARRUA__220"][i]>dfCMG["P.MONTT___220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"CHARRUA"+"<--"+"P.MONTT"+"   "
        if(dfCMG["CHARRUA__220"][i]<dfCMG["P.MONTT___220"][i]):
            dfCMG["desacople"][i]=dfCMG["desacople"][i]+"CHARRUA"+"-->"+"P.MONTT"+"   "
        if(dfCMG["desacople"][i]==""):
            dfCMG["desacople"][i]="Sitema Acoplado"
            
    dfCMG["desacople_s1"]=dfCMG["desacople"].shift(1)
    dfCMG=dfCMG[dfCMG["desacople_s1"]!=dfCMG["desacople"]]
    dfCMG=dfCMG[['Hora Movi.', 'desacople']]
    dfCMG.to_csv("./DES/"+fecha+".csv",index=False)


hoy_F = dt.datetime.now() - dt.timedelta(hours=4) #- dt.timedelta(days=16)
fecha= str(hoy_F.year)[2:4]+ str(hoy_F.month).zfill(2)+ str(hoy_F.day).zfill(2)


dfRIO = pd.read_excel("./RIO/RIO"+fecha+".xls", sheet_name="MOV-CMG").replace("ERNC","PAM_COGEN")
dfRIO.loc[0, 'Unnamed: 23'] = "QUILLOTA__220" #PaRCHE rio
dfRIO.loc[0, 'Unnamed: 22'] = "P.AZUCAR__220" #PaRCHE rio
dfRIO.columns.values[3] = "aux"
dfRIO.loc[0, 'aux'] = "Central-Unidad" #PaRCHE rio
dfRIO.columns.values[1] = "aux2"
dfRIO.loc[0, 'aux2'] = "Hora Movi." #PaRCHE rio
def ordenar_dataframe_con_primera_fila(dataframe):
    # Obtén el índice de la primera fila
    primer_fila_idx = dataframe.index[0]

    # Separa la primera fila del DataFrame
    primer_fila = dataframe.iloc[primer_fila_idx]

    # Elimina la primera fila del DataFrame original
    dataframe = dataframe.drop(primer_fila_idx)

    # Ordena el DataFrame por la columna de ordenación
    dataframe = dataframe.sort_values(by=[dataframe.columns[2]], ascending=True)

    # Restablece el índice del DataFrame resultante
    dataframe = dataframe.reset_index(drop=True)

    # Inserta la primera fila al principio del DataFrame resultante
    dataframe = pd.concat([primer_fila.to_frame().T, dataframe])

    return dataframe
dfRIO=ordenar_dataframe_con_primera_fila(dfRIO)
#print(dfRIO)


dfPO = pd.read_excel("./PO/PO"+fecha+".xlsx", sheet_name="TCO")
dfFP = pd.read_excel("./PO/PO"+fecha+".xlsx", sheet_name="FP diario")#.iloc[1:,1:].set_index(["Unnamed: 1"])

#Tabla con central por barra por bloque
dfBAR=dfRIO.iloc[:, [1,19,20,21,22,23,24,25,26,27]]
dfBAR.columns = dfBAR.iloc[0,:]
dfBAR=dfBAR.drop([0,1])
dfBAR=dfBAR.dropna()
dfBAR['hora']=dfBAR['Hora Movi.'].astype(str).str[0:2].astype(int)
dfBAR1 = dfBAR[dfBAR['hora'] < 8]
dfBAR2 = dfBAR[(dfBAR['hora'] >= 8)&(dfBAR['hora'] < 18)]
dfBAR3 = dfBAR[dfBAR['hora'] >= 18]

#Tablas de costos variables por bloque
Col=['Bar','CV']
dfCV1=dfPO.iloc[6:,[2,3]]
dfCV1.columns =Col
dfCV2=dfPO.iloc[6:,[6,7]]
dfCV2.columns =Col
dfCV3=dfPO.iloc[6:,[10,11]]
dfCV3.columns =Col

#Rescatar factores de Penalización
dfFP=dfFP.iloc[:,1:]
dfFP.iloc[0,0]="BarNom"
dfFP.columns = dfFP.iloc[0,:]
dfFP = dfFP.drop(0).set_index("BarNom")
dfFP = dfFP.loc[["Crucero220","DAlmagro220","Cardones220","PAzucar220","Quillota220","AJahuel220","Charrua220","PMontt220","LPalmas220"],:]
dfFP=pd.DataFrame(dfFP.to_numpy(), index=["CRUCERO__220","D.ALMAGRO__220","CARDONES_220","P.AZUCAR__220","QUILLOTA__220","A.JAHUEL__220","CHARRUA__220","P.MONTT___220","L.PALMAS___220"])
dfFP = dfFP.T.iloc[0:24,:]

dfCV1 = dfCV1.drop_duplicates(subset="Bar", keep="first")
dfCV2 = dfCV2.drop_duplicates(subset="Bar", keep="first")
dfCV3 = dfCV3.drop_duplicates(subset="Bar", keep="first")

#Armar Costos Marginales
for col in dfBAR1.columns[1:10]:
    dfBAR1[col]=dfBAR1[col].map(dfCV1.set_index("Bar")["CV"])
for col in dfBAR2.columns[1:10]:
    dfBAR2[col]=dfBAR2[col].map(dfCV2.set_index('Bar')['CV'])
for col in dfBAR3.columns[1:10]:
    dfBAR3[col]=dfBAR3[col].map(dfCV3.set_index('Bar')['CV'])
dfCMG = pd.concat([dfBAR1,dfBAR2,dfBAR3])
for col in dfCMG.columns[1:10]:
    dfCMG[col]=dfCMG[col].astype(float)

Desacoples(dfCMG)

#Calcular Promedio Ponderado
# crea indice Datetime
dfCMG['Datetime']=pd.to_datetime(fecha + " " + dfCMG["Hora Movi."].astype(str))
# elimina campo Hora Movi (innecesario ahora)
dfCMG.drop(["Hora Movi."],inplace=True, axis=1)
# índice de la tabla ahora es Datetime
dfCMG=dfCMG.set_index('Datetime')
# elimina duplicados
dfCMG = dfCMG[~dfCMG.index.duplicated(keep='first')]
# resample con pad (rellena valores nuevos con el valor del registro anterior)
dfCMG=dfCMG.resample('60s').pad()
# recalcula campo "hora"
dfCMG["hora"]=dfCMG.index.hour  
dfCMG =dfCMG.groupby('hora').mean()
dfCMG=dfCMG.mul(dfFP)
dfCMG.reindex(range(1,24))
dfCMG.index = dfCMG.index +1
dfCMG.to_csv("./CMG/"+fecha+".csv",index=True)


dfBAR_cmg = dfBAR[['Hora Movi.', 'CRUCERO__220', 'QUILLOTA__220', 'P.MONTT___220',]]
dfBAR_cmg = dfBAR_cmg.drop_duplicates(subset=['CRUCERO__220', 'QUILLOTA__220', 'P.MONTT___220'], keep='first').replace("PAM_COGEN","ERNC")
dfBAR_cmg.to_csv("./bar-cen/"+fecha+".csv",index=False)