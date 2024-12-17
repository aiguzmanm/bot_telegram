import os
import pandas as pd
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
temp_path = os.path.abspath(os.path.join(project_root,'datos','tmp'))

def obtener_balance(fecha):
    
    idfecha="20"+str(fecha)
    datos_root = os.path.abspath(os.path.join(project_root, 'datos'))
    gen_root = os.path.join(datos_root, 'gen')
    cmg_root = os.path.join(datos_root, 'cmg')
    balance_root = os.path.join(datos_root, 'balance')

    #leer archivos
    df_retiros=pd.read_csv(datos_root+'/RetirosBDG.csv',encoding='latin-1')
    df_inyecciones=pd.read_csv(gen_root+f'/{fecha}.csv',encoding='latin-1')
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