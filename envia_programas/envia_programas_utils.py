import os
import sys
import pandas as pd
import warnings
import wget
import zipfile as zp
import shutil
import cloudscraper


warnings.filterwarnings('ignore')

# Añadir el directorio raíz del proyecto al sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

from modules.telegram_utils import enviar_mensaje_telegram, enviar_archivo_telegram, enviar_foto_telegram
from modules.graph_utils import generar_grafico_prg
from modules.download_utils import wget_cloudflare
from modules.email_utils import send_mail

def enviar_programas(fecha, base_dir="./datos"):
    ...
    
def reporte_prg(zip,file):

    tmp_dir=os.path.join(project_root,'datos','tmp')
    file_dir=os.path.join(tmp_dir,file)

    df_PRG = pd.read_excel(file_dir, sheet_name='PROGRAMA')
    #eliminar las 2 primeras columnas
    df_PRG = df_PRG.iloc[:,2:]
    #buscar el valor "Hidroeléctricas de Pasada" en la primera columna y ocupar esa fila como nombres de columna
    df_PRG.columns = df_PRG.iloc[df_PRG[df_PRG.iloc[:,0]=='Hidroeléctricas de Pasada'].index[0]]
    #buscar el valor "Generación Total [MWh]" en la primera columna y guardar el valor de la columna Total en una variable llamda "demanda" como int
    demanda = int(df_PRG.iloc[df_PRG[df_PRG.iloc[:,0]=='Generación Total [MWh]'].index[0],-1])
    #buscarv el valor "Solares" en la primera columna, para la fila siguiente a la encontrada guardar el valor de la columna Total en una variable llamda "solar" como int
    fv = int(df_PRG.iloc[df_PRG[df_PRG.iloc[:,0]=='Solares'].index[0]+1,-1])
    hp = int(df_PRG.iloc[df_PRG[df_PRG.iloc[:,0]=='Hidroeléctricas de Pasada'].index[0]+1,-1])
    eo = int(df_PRG.iloc[df_PRG[df_PRG.iloc[:,0]=='Eólicas'].index[0]+1,-1])
    ter = int(df_PRG.iloc[df_PRG[df_PRG.iloc[:,0]=='Térmicas'].index[0]+1,-1])
    he = int(df_PRG.iloc[df_PRG[df_PRG.iloc[:,0]=='Embalses y Reguladas'].index[0]+1,-1]) 
    car =int(df_PRG[df_PRG.iloc[:,0].str.contains('_CAR',na=False,regex=True)].iloc[:,-1].sum())
    gas =int(df_PRG[df_PRG.iloc[:,0].str.contains('_GN',na=False,regex=True)].iloc[:,-1].sum())
    diesel =int(df_PRG[df_PRG.iloc[:,0].str.contains('_DIE',na=False,regex=True)].iloc[:,-1].sum())
    hidro = hp + he
    #demanda como string con puntuación de miles
    demanda = "{:,}".format(demanda)
    fv = "{:,}".format(fv)
    hp = "{:,}".format(hp)
    eo = "{:,}".format(eo)
    ter = "{:,}".format(ter)
    he = "{:,}".format(he)
    car = "{:,}".format(car)
    gas = "{:,}".format(gas)
    diesel = "{:,}".format(diesel)
    hidro = "{:,}".format(hidro)
    #crear un string con el resumen del programa
    resu = (
        f"**Nuevo programa publicado:** {zip}\n\n"
        f"**Resumen del programa:**\n\n"
        f"Demanda Total: {demanda} MWh\n"
        f"Generación Solar FV: {fv} MWh\n"
        f"Generación Hidroeléctrica de Pasada: {hp} MWh\n"
        f"Generación Eólica: {eo} MWh\n"
        f"Generación Térmica: {ter} MWh\n"
        f"Generación Embalses y Reguladas: {he} MWh\n"
        f"Generación Hidroeléctrica Total: {hidro} MWh\n"
        f"Generación a Carbón: {car} MWh\n"
        f"Generación a Gas Natural: {gas} MWh\n"
        f"Generación a Diesel: {diesel} MWh\n"
    )

    return resu

def limpiar_dir(dir):
    # Listar todos los archivos y carpetas en el directorio
    for nombre in os.listdir(dir):
        # Crear la ruta completa
        ruta = os.path.join(dir, nombre)
        
        # Verificar si es un archivo o una carpeta
        if os.path.isfile(ruta):
            os.remove(ruta)  # Eliminar el archivo
        elif os.path.isdir(ruta):
            shutil.rmtree(ruta)  # Eliminar la carpeta y su contenido

def links(contenido,year,month,tipo):

    links_dir=os.path.abspath(os.path.join(project_root,'datos','links','links_'+tipo+'.csv'))

    inicio = 'https://www.coordinador.cl/wp-content/uploads/'+str(year)+'/'+str(month).zfill(2)+'/'+tipo
    final = '.zip'

    # Cargar el DataFrame existente o crear uno vacío si no existe
    try:
        df_link = pd.read_csv(links_dir)
        enlaces_existentes = set(df_link['Texto'])
    except FileNotFoundError:
        df_link = pd.DataFrame(columns=['Texto'])
        enlaces_existentes = set()
    
    textos = []
    nuevos_links = []
    inicio_len = len(inicio)
    final_len = len(final)
    pos_inicio = 0
    
    while True:
        pos_inicio = contenido.find(inicio, pos_inicio)
        if pos_inicio == -1:
            break
        pos_fin = contenido.find(final, pos_inicio + inicio_len)
        if pos_fin == -1:
            break
        texto = contenido[pos_inicio:pos_fin + final_len]
        textos.append(texto)
        pos_inicio = pos_fin + final_len
        if texto not in enlaces_existentes:
            nuevos_links.append(texto)
            print(f'¡Nuevo enlace encontrado! Enlace: {texto}')

    # Agregar nuevos enlaces al DataFrame y guardar en el archivo CSV
    if nuevos_links:
        nuevos_df = pd.DataFrame({'Texto': nuevos_links})
        df_link = pd.concat([df_link, nuevos_df], ignore_index=True)
        df_link.to_csv(links_dir, index=False)

    return df_link, nuevos_links

def descargar_PRO(txt,year,month,tipo):
    fecha_fin=""
    zip_fin=""

    tmp_dir=os.path.join(project_root,'datos','tmp')
    tipo_dir=os.path.join(project_root,'datos',tipo)

    limpiar_dir(tmp_dir)

    df_link, nuevos_links = links(txt,year,month,tipo)

    if len(nuevos_links) > 0:
        for link in nuevos_links:
            print(link)
            wget_cloudflare(link,tmp_dir)
            #obtener la última parte del string link luego del último "/"
            zip = link.split('/')[-1]
            zip_dir=os.path.join(tmp_dir,zip)
            #descomprimir el archivo zip en la carpeta TMP
            with zp.ZipFile(zip_dir,"r") as POzip:
                POzip.extractall(path=tmp_dir)
            #buscar en la carpeta TMP el nombre del archivo que termina con .xlsx
            for file in os.listdir(tmp_dir):
                if file.endswith('.xlsx'):
                    if file.startswith('PRG'):
                        #electrogas.gas(tmp_dir+file)
                        msj=reporte_prg(zip,file)
                        enviar_mensaje_telegram(msj)
                        file_dir=os.path.join(tmp_dir,file)
                        prg_dir=os.path.join(project_root,'datos','prg',file)
                        plot_dir=os.path.join(project_root,'datos','plot_prg',file+".jpg")
                        enviar_archivo_telegram(file_dir)
                        generar_grafico_prg(file_dir,plot_dir)
                        enviar_foto_telegram(plot_dir)
                        shutil.move(file_dir,prg_dir)
                        send_mail("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/PID","eliminar",prg_dir)
                        #mail.send("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/gas","eliminar","/home/ubuntu/real_time/gas/"+file[3:])
                    elif file.startswith('PO'):
                        #obtener los 6 caracteres después de "PO" en file
                        fecha_fin = file[2:8]
                        zip_fin = zip
                        file_dir=os.path.join(tmp_dir,file)
                        po_dir=os.path.join(project_root,'datos','po',file)
                        enviar_archivo_telegram(file_dir)
                        shutil.move(file_dir,po_dir)
                        send_mail("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/PID","eliminar",po_dir)
            #eliminar todos los archivos de la carpeta TMP
            limpiar_dir(tmp_dir)

    else:
        print('No hay programas nuevos')
    return fecha_fin,zip_fin

def descargar_PID(txt,year,month,tipo):
    fecha_fin=""
    zip_fin=""

    tmp_dir=os.path.join(project_root,'datos','tmp')
    tipo_dir=os.path.join(project_root,'datos',tipo)

    #eliminar todos los archivos de la carpeta TMP
    limpiar_dir(tmp_dir)

    df_link, nuevos_links = links(txt,year,month,tipo)
    if len(nuevos_links) > 0:
        for link in nuevos_links:
            wget_cloudflare(link,tmp_dir)
            #obtener la última parte del string link luego del último "/"
            zip = link.split('/')[-1]
            dir=zip[:-4]
            print(zip)
            zip_dir=os.path.join(tmp_dir,zip)
            #descomprimir el archivo zip en la carpeta TMP
            with zp.ZipFile(zip_dir,"r") as POzip:
                POzip.extractall(path=tmp_dir)
            #buscar en la carpeta TMP el nombre del archivo que termina con .xlsx
            sub_dir = os.path.join(tmp_dir, dir)
            # Mover archivos de sub_dir a tmp_dir
            for file_name in os.listdir(sub_dir):
                file_path = os.path.join(sub_dir, file_name)
                if os.path.isfile(file_path):
                    shutil.move(file_path, tmp_dir)  # Mueve el archivo a tmp_dir
            for file in os.listdir(tmp_dir):
                if file.endswith('.xlsx'):
                    if file.startswith('PRG'):
                        print(file)
                        #electrogas.gas2("./TMP/"+dir+"/"+file)
                        enviar_mensaje_telegram("Se ha publicado una nueva programación intradiaria")
                        file_dir=os.path.join(tmp_dir,file)
                        pid_dir=os.path.join(project_root,'datos','pid',file)
                        plot_dir=os.path.join(project_root,'datos','plot_prg',file+".jpg")
                        enviar_archivo_telegram(file_dir)
                        generar_grafico_prg(file_dir,plot_dir)
                        enviar_foto_telegram(plot_dir)
                        shutil.move(file_dir,pid_dir)
                        send_mail("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/PID","eliminar",pid_dir)
                        #send_mail("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/gas_PID","eliminar","/home/ubuntu/real_time/gas_PID/"+file[3:])
            #eliminar todos los archivos de la carpeta TMP
            limpiar_dir(tmp_dir)
    else:
        print('No hay programas intradiarios nuevos')