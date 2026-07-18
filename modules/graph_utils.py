import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime as dt
import numpy as np

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))

def generar_grafico_cmg(fecha, ruta_csv, ruta_guardado):
    # Convertir 'fecha' de formato 'yymmdd' a 'dd/mm/yy' para el título
    fecha_formateada = f"{fecha[4:6]}/{fecha[2:4]}/{fecha[0:2]}"
    # Cargar datos del CSV
    df = pd.read_csv(ruta_csv, index_col=0)
    # Generar el gráfico
    columnas_a_graficar = ["CRUCERO__220", "P.AZUCAR__220", "QUILLOTA__220",
                           "A.JAHUEL__220", "CHARRUA__220", "P.MONTT___220"]
    df[columnas_a_graficar].plot(
        figsize=(10, 4), xlabel="Horas", ylabel="CMG [USD/MWh]"
    )
    plt.xticks(range(1, 25, 1))
    plt.legend(loc='lower left', prop={'size': 8})
    plt.grid()
    plt.title(f"Costos Marginales {fecha_formateada}")

    # Asegurarse de que el directorio de guardado exista
    os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
    
    # Guardar el gráfico
    plt.savefig(ruta_guardado)
    plt.close()

def generar_grafico_prg(ruta_prg, ruta_guardado):
    programa_df = pd.read_excel(ruta_prg, sheet_name='PROGRAMA')
        # Extraer la fecha del programa
    program_date = programa_df.iloc[2, 2]
    formatted_date = pd.to_datetime(program_date).strftime('%d-%b-%y')
    
    # Extraer tecnologías y valores de generación
    column_c = programa_df['Unnamed: 2']
    technologies = []
    generation_values = []
    empty_count = 0

    # Recorrer la columna C para encontrar las tecnologías y valores
    for i, value in enumerate(column_c):
        if pd.isna(value):
            empty_count += 1
        else:
            empty_count = 0
        if empty_count == 3:
            break
        if value == 'Total':
            current_technology = column_c[i - 1]
            current_generation = programa_df.iloc[i, 4:4 + 24].tolist()
            # Transformar los valores de generación a mayores o iguales a 0
            generation_values.append([max(0, val) for val in current_generation])
            technologies.append(current_technology)

    # Buscar "Sistemas de Almacenamiento" y transformar los valores
    for i, value in enumerate(column_c):
        if value == 'Sistemas de Almacenamiento':
            if column_c[i + 1] == 'Total':
                storage_generation = programa_df.iloc[i + 1, 4:4 + 24].tolist()
                generation_values.insert(0, [max(0, val) for val in storage_generation])
                technologies.insert(0, 'Sistemas de Almacenamiento')
            break

    # Colores y abreviaciones
    final_with_storage_colors = ['orange', 'lightblue', 'mediumpurple', 'yellow', 'orange', 'lightgray', 'blue']
    updated_technologies = ['Baterías' if tech == 'Sistemas de Almacenamiento' else
                            'H. Pasada' if tech == 'Hidroeléctricas de Pasada' else
                            'CSP' if tech == 'Centrales de concentración solar' else
                            'Embalses' if tech == 'Embalses y Reguladas' else
                            tech for tech in technologies]

    # Extraer "Costos Marginales" y transformar los valores
    costs_technology = []
    costs_data = []
    found_costs_marginales = False
    for i, value in enumerate(column_c):
        if value == "Costos Marginales":
            found_costs_marginales = True
            continue
        if found_costs_marginales:
            if pd.isna(value):
                break
            costs_technology.append(value)
            costs_data.append([max(0, val) for val in programa_df.iloc[i, 4:4 + 24].tolist()])  # Transformar costos
    costs_dict = dict(zip(costs_technology, costs_data))
    selected_bars = ['Crucero220', 'Quillota220', 'Charrua220', 'PMontt220']
    selected_costs = {bar: costs_dict[bar] for bar in selected_bars if bar in costs_dict}

    # Graficar el programa de generación y costos marginales
    fig, ax1 = plt.subplots(figsize=(12, 6))
    bottom = [0] * 24
    hours = list(range(1, 25))  # Horas de 1 a 24
    bar_width = 0.85
    for tech, gen, color in zip(updated_technologies, generation_values, final_with_storage_colors):
        ax1.bar(hours, gen, bar_width, bottom=bottom, label=tech, color=color)
        bottom = [sum(x) for x in zip(bottom, gen)]
    ax1.set_xlabel('Hour of the Day')
    ax1.set_ylabel('Generation (MW)', color='black')
    ax2 = ax1.twinx()
    for bar, costs in selected_costs.items():
        ax2.plot(hours, costs, label=bar, linestyle='-', linewidth=2)
    ax2.set_ylabel('Marginal Costs (USD/MWh)', color='black')
    ax1.legend(loc='upper left', bbox_to_anchor=(1.1, 1), title="Generation")
    ax2.legend(loc='lower left', bbox_to_anchor=(1.1, 0.3), title="Marginal Costs")
    plt.title(f'Programa de generación horaria día {formatted_date}')
    plt.tight_layout()
        # Asegurarse de que el directorio de guardado exista
    os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
    
    # Guardar el gráfico
    plt.savefig(ruta_guardado)
    plt.close()

def generar_graficos_sscc(fecha, datos_dir, plot_dir):
    # Leer los archivos procesados
    archivos = ["dfPRGCPFS.xlsx", "dfPRGCSFS.xlsx", "dfPRGCTFS.xlsx", 
                "dfPRGCPFB.xlsx", "dfPRGCSFB.xlsx", "dfPRGCTFB.xlsx"]
    dataframes = [pd.read_excel(os.path.join(datos_dir, archivo)) for archivo in archivos]
    
    # Generar gráficos para CPF, CSF, y CTF
    nombres = ["CPF", "CSF", "CTF"]
    for i, nombre in enumerate(nombres):
        df_subida = dataframes[i * 2].transpose()
        df_bajada = dataframes[i * 2 + 1].transpose()
        df_subida.columns = df_subida.iloc[0]
        df_bajada.columns = df_bajada.iloc[0]
        df_subida = df_subida[1:]
        df_bajada = df_bajada[1:]
        
        # Crear los gráficos
        fig, axes = plt.subplots(2, 1, figsize=(14, 7))
        plt.subplots_adjust(hspace=0.3)
        df_subida.plot(kind='bar', stacked=True, ax=axes[0], title=f"{nombre} Subida {fecha}")
        df_bajada.plot(kind='bar', stacked=True, ax=axes[1], title=f"{nombre} Bajada {fecha}")
        plt.savefig(os.path.join(plot_dir, f"{nombre}.jpg"))
        plt.close()



def generar_grafico_balance(fecha,hora):

    datos_root = os.path.abspath(os.path.join(project_root, 'datos'))
    cmg_root = os.path.join(datos_root, 'cmg')
    plot_root = os.path.join(datos_root, 'plot_balance')


    max_hora = hora
    fecha2=str(fecha)[4:6]+"/"+str(fecha)[2:4]+"/"+str(fecha)[0:2]
    #Leer Parámetros
    df_graf=pd.read_excel(datos_root+'/parametros.xlsx',sheet_name='Graficos')

    #leer balance
    df_bal = pd.read_csv(datos_root+f'/balance/{fecha}.csv')


    #Crear Zonas
    zonas =["00_SING","01_DAlmagro","02_Card_Maite_PAz","03_LosVilos","04_Nog_Quillota","05_Polpaico","06_Enel Distribucion","07_Rapel","08_AJahuel_Ancoa","09_Charrua","10_Concepcion","11_Temuco","12_Valdivia_Pmontt"]
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

    df_cmg=pd.read_csv(cmg_root+f'/{fecha}.csv')

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
    plt.savefig(plot_root+f'/{fecha}.png')
    #plt.show()

def generar_grafico_gen(fecha,data,hora, destino_root,grupo):
    fecha = str(fecha)

    # Agrupa y suma las energías por hora y tecnologíapython
    energias_por_hora_tecnologia = data.groupby(['Hora', 'Tecnologia'])['Energía Bruta [MWh]'].sum()
    df_energias = energias_por_hora_tecnologia.unstack()
    horas = df_energias.index
    tecnologias = df_energias.columns.get_level_values('Tecnologia')

    # Define los colores para cada tecnología
    colores = {
        '0.1.BAT': '#00FFFF',
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
    plt.title(f'Generación bruta {grupo.upper()}  '+fecha[4:6]+'/'+fecha[2:4]+'/20'+fecha[0:2])
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
    plt.savefig(destino_root+f'/{fecha}.png', bbox_inches='tight')
    # Muestra el gráfico
    #plt.show()

def generar_tabla_gen(fecha,data,hora, destino_root,grupo):

    fecha = str(fecha)

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
    plt.title(f'Generación bruta {grupo.upper()}  '+fecha[4:6]+'/'+fecha[2:4]+'/20'+fecha[0:2])
    # Obtener el índice de la columna correspondiente a la hora específica
    hora_especifica_index = df_energias.columns.get_loc(hora)

    # Recorrer cada celda en la tabla y establecer el color según la hora específica
    for i, cell in enumerate(tabla.get_celld().values()):
        if i % len(df_energias.columns) <= hora_especifica_index:
            cell.set_text_props(weight='bold', color='blue')
        elif i % len(df_energias.columns) > hora_especifica_index:
            cell.set_text_props(weight='bold', color='darkgreen')

    # Guardar la tabla como una imagen
    plt.savefig(destino_root+f'/{fecha}.png', bbox_inches='tight', pad_inches=0)
    plt.show()

    # Cierra la figura
    plt.close(fig)