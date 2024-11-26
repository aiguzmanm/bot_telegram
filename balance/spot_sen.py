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
    df_idCent=pd.read_excel('./Param/parametros.xlsx',sheet_name='SEN')


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
            max_hora= df_opreal2[df_opreal2["Energia Bruta [MWh]"]>8000]["Hora"].max()
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
    df_Iny.to_csv("./Iny_sen/"+str(fecha)+".csv",index=False, encoding="latin-1")
    graf_gen(fecha,max_hora)
    return(max_hora)

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

    files1 = {'photo': open('./graf_gen_sen/'+fecha+'.png', 'rb')}
    files2 = {'photo': open('./tab_gen_sen/'+fecha+'.png', 'rb')}
    files3 = {'document': open('./Iny_sen/'+fecha+'.csv', 'rb')}

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
        data = pd.read_csv('./Iny_sen/'+fecha+'.csv', encoding='latin1')

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
        plt.title('Generación bruta SEN  '+fecha[4:6]+'/'+fecha[2:4]+'/20'+fecha[0:2])
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
        plt.savefig('./graf_gen_sen/'+fecha+'.png', bbox_inches='tight')
        # Muestra el gráfico
        #plt.show()

    def tab_gen(fecha, hora):
        fecha = str(fecha)
        data = pd.read_csv('./Iny_sen/'+fecha+'.csv', encoding='latin1')

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
        plt.title('Generación bruta SEN  '+fecha[4:6]+'/'+fecha[2:4]+'/20'+fecha[0:2])
        # Obtener el índice de la columna correspondiente a la hora específica
        hora_especifica_index = df_energias.columns.get_loc(hora)

        # Recorrer cada celda en la tabla y establecer el color según la hora específica
        for i, cell in enumerate(tabla.get_celld().values()):
            if i % len(df_energias.columns) <= hora_especifica_index:
                cell.set_text_props(weight='bold', color='blue')
            elif i % len(df_energias.columns) > hora_especifica_index:
                cell.set_text_props(weight='bold', color='darkgreen')

        # Guardar la tabla como una imagen
        plt.savefig('./tab_gen_sen/'+fecha+'.png', bbox_inches='tight', pad_inches=0)
        #plt.show()

        # Cierra la figura
        plt.close(fig)
    graf_gen(fecha, hora)
    tab_gen(fecha, hora)