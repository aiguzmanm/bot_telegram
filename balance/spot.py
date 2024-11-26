def SQL(fecha):
    import pandas as pd
    from sqlalchemy import create_engine

    #Conectarse a la base
    
    #en1 = create_engine("mysql+pymysql://{user}:{pw}@db-mysql-instance-1.cbvatw6u4qcm.us-east-2.rds.amazonaws.com/{db}"
    #                    .format(user="operaciones_w",
    #                            pw="ClaveOperaciones2021!",
    #                            db="operaciones"))


    #Leer base sql
    #df_opreal = pd.read_sql_query("SELECT * FROM operaciones.gen_opreal_h where `Id Fecha`= 20"+str(fecha)  , en1)
    df_opreal = pd.read_parquet("/home/ubuntu/Gendia_v2/Gendia_Gen_Opreal/g_o_gen_"+"20"+str(fecha)[:4]+".parquet")

    df_opreal=df_opreal[["Id Central","Id Fecha","Hora","Energia Bruta [MWh]"]]
    df_opreal=df_opreal[df_opreal["Id Fecha"]==int("20"+str(fecha))]
    df_opreal["origen"]="opreal"
    
    #df_programa = pd.read_sql_query("SELECT * FROM operaciones.gen_programa_h where `Id Fecha`= 20"+str(fecha)  , en1)
    df_programa = pd.read_parquet("/home/ubuntu/Gendia_v2/Gendia_Gen_Programa/g_p_gen_"+"20"+str(fecha)[:4]+".parquet")
    df_programa=df_programa[["Id Central","Id Fecha","Hora","Energia Bruta [MWh]"]]
    df_programa=df_programa[df_programa["Id Fecha"]==int("20"+str(fecha))]
    df_programa=df_programa.groupby(["Id Central","Id Fecha","Hora"]).sum().reset_index()
    df_programa["origen"]="programa"

    #leer parámetros
    df_idCent=pd.read_excel('./Param/parametros.xlsx',sheet_name='IdCentral-Central')


    df_programa=pd.merge(df_programa,df_idCent,how='left',left_on='Id Central',right_on='Id Central')
    df_programa=df_programa[df_programa['Central Reporte'].notna()]

    df_opreal=pd.merge(df_opreal,df_idCent,how='left',left_on='Id Central',right_on='Id Central')
    df_opreal=df_opreal[df_opreal['Central Reporte'].notna()]


    #completar datos de df_opreal con df_programa para horas que no hay datos en df_opreal
    if df_programa.shape[0]==0:
        df_cent=df_opreal
        max_hora=24
    else:
            df_opreal2=df_opreal.groupby(["Hora"]).sum().reset_index()
            max_hora= df_opreal2[df_opreal2["Energia Bruta [MWh]"]>2100]["Hora"].max()
            df_cent=df_opreal[df_opreal["Hora"]<=max_hora]
            df_cent=df_cent.append(df_programa[df_programa["Hora"]>max_hora])
            df_cent=df_cent.sort_values(by=["Hora"])
            print(max_hora)

    df_Iny=df_cent[["Central Reporte","Energia Bruta [MWh]","origen","Tecnologia"]]
    df_Iny=df_Iny.rename(columns={"Energia Bruta [MWh]": "Energía Bruta [MWh]"})
    df_Iny["Año"]="20"+str(fecha)[0:2]
    df_Iny["Mes"]=str(fecha)[2:4]
    df_Iny["Día"]=str(fecha)[4:6]
    df_Iny["Hora"]=df_cent["Hora"]
    print(df_Iny)
    df_Iny.to_csv("./Iny/"+str(fecha)+".csv",index=False, encoding="latin-1")
    graf_gen(fecha,max_hora)
    return(max_hora)

def Consulta(fecha):
    
    import pandas as pd

    idfecha="20"+str(fecha)

    #leer archivos
    df_retiros=pd.read_csv('./Param/RetirosBDG.csv',encoding='latin-1')
    df_inyecciones=pd.read_csv('./Iny/'+fecha+'.csv',encoding='latin-1')
    df_cmg=pd.read_csv('../real_time/CMG/'+fecha+'.csv')
    df_CenZona=pd.read_excel('./Param/parametros.xlsx',sheet_name='Central-Zona')
    df_ZonaBarr=pd.read_excel('./Param/parametros.xlsx',sheet_name='Zona-Barra')

    #rescatar Retiros por Zona del día
    df_retiros['Id_Fecha']=df_retiros['Id Fecha']*100+df_retiros['Hora']
    df_retiros=df_retiros[df_retiros['Id_Fecha'].astype(str).str[:8]==idfecha]
    df_retiros.rename(columns={'Fisico [MWh]':'Retiros[MWh]'},inplace=True)
    df_retiros=df_retiros[['Id_Fecha','Zona','Retiros[MWh]']]
    df_retiros=df_retiros.groupby(['Id_Fecha','Zona']).sum().reset_index()

    #rescatar Inyecciones por Zona del día
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
    df_balance.to_csv('./Bal/'+fecha+'.csv',index=False)

def Graf(fecha,hora):
    import pandas as pd
    import datetime as dt
    import numpy as np
    import matplotlib.pyplot as plt

    idfecha="20"+str(fecha)
    horalim = hora
    max_hora = hora
    fecha2=str(fecha)[4:6]+"/"+str(fecha)[2:4]+"/"+str(fecha)[0:2]
    #Leer Parámetros
    df_graf=pd.read_excel('./Param/parametros.xlsx',sheet_name='Graficos')

    #leer balance
    df_bal = pd.read_csv('./Bal/'+fecha+'.csv')
    #si la hora es menor que horalim rellenar con nan
    #df_bal['SPOT[MWh]'] = np.where(df_bal['Hora']<=horalim,df_bal['SPOT[MWh]'],np.nan)
    #df_bal['SPOT[USD]'] = np.where(df_bal['Hora']<=horalim,df_bal['SPOT[USD]'],np.nan)

    #Crear Zonas
    zonas =["00_SING","01_DAlmagro","02_Card_Maite_PAz","03_LosVilos","04_Nog_Quillota","05_Polpaico","06_Enel Distribución","07_Rapel","08_AJahuel_Ancoa","09_Charrua","10_Concepcion","11_Temuco","12_Valdivia_Pmontt"]
    horaZ = np.arange(1,25,1)
    fisicoZ=[[0] * 24 for i in range(13)]
    monetarioZ=[[0] * 24 for i in range(13)]

    for i in range(0,13):
        for j in range(0,24):
            fisicoZ[i][j]=df_bal[(df_bal['Zona']==zonas[i]) & (df_bal['Hora']==j+1)]['SPOT[MWh]'].sum()
            monetarioZ[i][j]=df_bal[(df_bal['Zona']==zonas[i]) & (df_bal['Hora']==j+1)]['SPOT[USD]'].sum()

    #Número de Gráficos
    n=df_graf.shape[0]
    fisico=[[0] * 24 for i in range(n)]
    monetario=[[0] * 24 for i in range(n)]

    def str2arange(string,sep):
        string=string.split(sep)
        string=[int(i) for i in string]
        return string

    for i in range(0,n):
        zon= str2arange(str(df_graf['Zonas'][i]),"+")
        for j in range(0,len(zon)):
            for k in range(0,24):
                fisico[i][k]=fisico[i][k]+fisicoZ[zon[j]][k]
                monetario[i][k]=monetario[i][k]+monetarioZ[zon[j]][k]

    for i in range(0,n):
        for j in range(0,24):
            monetario[i][j]=monetario[i][j]/1000

    df_cmg=pd.read_csv('../real_time/CMG/'+fecha+'.csv')

    #df_cmg['CRUCERO__220'] número de valores no nulos
    hora_cmg = df_cmg['CRUCERO__220'].count()

    fig, axes = plt.subplots(n)
    fig.set_size_inches(10, 4*n)

    for i in range(n):
        axes[i].bar(horaZ[:max_hora], fisico[i][:max_hora], color='b')
        axes[i].bar(horaZ[max_hora:], fisico[i][max_hora:], color='g')
        #axes[i].bar(horaZ, fisico[i], color='b')
        #axes[i].set_xlabel('Hora')
        axes[i].set_ylabel('SPOT [MWh]', color='b')
        axes[i].set_title(df_graf['Gráficos'][i], fontsize=15)
        twin_axes_1 = axes[i].twinx() 
        twin_axes_1.plot(horaZ[:hora_cmg], monetario[i][:hora_cmg], 'r')
        twin_axes_1.set_ylabel('SPOT [mUSD]', color='r')
        axes[i].grid()
        axes[i].set_xticks(range(1, 25, 1))
        twin_axes_1.set_xticks(range(1, 25, 1))
        yabs_max1 = abs(max(axes[i].get_ylim(), key=abs))
        axes[i].set_ylim(ymin=-yabs_max1, ymax=yabs_max1)
        yabs_max2 = abs(max(twin_axes_1.get_ylim(), key=abs))
        twin_axes_1.set_ylim(ymin=-yabs_max2, ymax=yabs_max2)

    axes[n-1].legend(['Real','Programa'], loc='upper right')
    axes[n-1].set_xlabel('Hora')
    fig.suptitle('Balance Enel \n'+fecha2, fontsize=20)
    plt.savefig("./Graf/"+fecha+".png")
    #plt.show()

def Telegram(fecha):
    import requests as rq
    import datetime as dt
    import os

    files = {'photo': open('./Graf/'+fecha+'.png', 'rb')}
    Chat = '-1001437637888'
    token = '1702011759:AAET9BGHMjrTZr3mcs3nOVmDPMPK9xT4jMc'

    txt = 'https://api.telegram.org/bot' + token + '/sendPhoto?chat_id=' + Chat

    prueba = rq.post(txt,files=files)

def Gen(fecha):

    import requests as rq
    import datetime as dt
    import os

    files1 = {'photo': open('./graf_gen/'+fecha+'.png', 'rb')}
    files2 = {'photo': open('./tab_gen/'+fecha+'.png', 'rb')}
    files3 = {'document': open('./Iny/'+fecha+'.csv', 'rb')}

    Chat = '-1001437637888'
    token = '1702011759:AAET9BGHMjrTZr3mcs3nOVmDPMPK9xT4jMc'

    txt1 = 'https://api.telegram.org/bot' + token + '/sendPhoto?chat_id=' + Chat
    txt2 = 'https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + Chat

    prueba1 = rq.post(txt1,files=files1)
    prueba2 = rq.post(txt1,files=files2)
    prueba3 = rq.post(txt2,files=files3)

def graf_gen(fecha,hora):
    
    import pandas as pd
    import matplotlib.pyplot as plt

    def graf_gen(fecha, hora):
        fecha = str(fecha)
        data = pd.read_csv('./Iny/'+fecha+'.csv', encoding='latin1')

        # Agrupa y suma las energías por hora y tecnología
        energias_por_hora_tecnologia = data.groupby(['Hora', 'Tecnologia'])['Energía Bruta [MWh]'].sum()
        df_energias = energias_por_hora_tecnologia.unstack()
        horas = df_energias.index
        tecnologias = df_energias.columns.get_level_values('Tecnologia')

        # Define los colores para cada tecnología
        colores = {
            '0.OTRA': 'violet',
            '1.HP': 'lightblue',
            '2.EO': 'purple',
            '3.FV': 'yellow',
            '5.CAR': 'gray',
            '6.CC_GN': 'lightgreen',
            '7.HE': 'blue',
            '8.0.TG_GN': 'darkgreen',
            '8.1.CC_DI': 'orange',
            '9.TG': 'red'
        }

        # Crea el gráfico de barras apiladas
        ax = df_energias.plot(kind='bar', stacked=True, color=[colores.get(tecnologia, 'gray') for tecnologia in tecnologias], width=0.9)

        # Personaliza el gráfico
        plt.xlabel('Hora')
        plt.ylabel('Energía Bruta [MWh]')
        plt.title('Generación bruta Enel  '+fecha[4:6]+'/'+fecha[2:4]+'/20'+fecha[0:2])
        plt.legend(title='Tecnología')
        #ubicar la caja de la leyenda fuera del gráfico
        plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
        #agregar grilla de líneas horizontales
        plt.grid(axis='y', alpha=0.5)

        # Encuentra el índice correspondiente a la hora específica
        indice_hora = hora
        # Aplica la diferencia a partir de la hora específica
        if indice_hora >= 0:
            for container in ax.containers:
                for i, bar in enumerate(container):
                    if i >= indice_hora:
                        bar.set_alpha(0.4)  # Aumenta la transparencia de las barras
                        #bar.set_hatch('x')  # Cambia la textura de las barras (opcional)
        #guardar el gráfico como graf.png
        plt.savefig('./graf_gen/'+fecha+'.png', bbox_inches='tight')
        # Muestra el gráfico
        #plt.show()

    def tab_gen(fecha, hora):
        fecha = str(fecha)
        data = pd.read_csv('./Iny/'+fecha+'.csv', encoding='latin1')

        energias_por_hora_tecnologia = data.groupby(['Hora', 'Tecnologia'])['Energía Bruta [MWh]'].sum()
        df_energias = energias_por_hora_tecnologia.unstack().transpose()
        df_energias.loc['Total'] = df_energias.sum()
        df_energias['Total'] = df_energias.sum(axis=1)
        # Crea una figura con el alto ajustado

        fig, ax = plt.subplots(figsize=(18, 2.5)) #Ajustar a mano

        # Elimina los ejes
        ax.axis('off')
        tabla = ax.table(cellText=df_energias.values.astype(int),
                        colLabels=df_energias.columns,
                        rowLabels=df_energias.index,
                        loc='center',
                        cellLoc='center')
                    
        # Establecer el tamaño de fuente de la tabla
        tabla.auto_set_font_size(False)
        tabla.set_fontsize(9)    
        plt.title('Generación bruta Enel  '+fecha[4:6]+'/'+fecha[2:4]+'/20'+fecha[0:2])
        # Obtener el índice de la columna correspondiente a la hora específica
        hora_especifica_index = df_energias.columns.get_loc(hora)

        # Recorrer cada celda en la tabla y establecer el color según la hora específica
        for i, cell in enumerate(tabla.get_celld().values()):
            if i % len(df_energias.columns) <= hora_especifica_index:
                cell.set_text_props(weight='bold', color='blue')
            elif i % len(df_energias.columns) > hora_especifica_index:
                cell.set_text_props(weight='bold', color='darkgreen')

        # Guardar la tabla como una imagen
        plt.savefig('./tab_gen/'+fecha+'.png', bbox_inches='tight', pad_inches=0)
        #plt.show()

        # Cierra la figura
        plt.close(fig)
    graf_gen(fecha, hora)
    tab_gen(fecha, hora)