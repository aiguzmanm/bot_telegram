import requests as rq
import wget
import pandas as pd
import datetime as dt
import os
import zipfile as zp
import shutil
import reporte
import electrogas
import mail
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

token = '1702011759:AAET9BGHMjrTZr3mcs3nOVmDPMPK9xT4jMc'
Chat = '-1001437637888'
#Chat = '-873976078'

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

def enviar_file(Chat,token,ruta):
    Chat=str(Chat)
    token=str(token)
    ruta=str(ruta)
    files = {'document': open(ruta, 'rb')}
    txt = 'https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + Chat
    prueba=rq.post(txt,files=files)

def enviar_msj(Chat,token,msj):
    Chat=str(Chat)
    token=str(token)
    txt = 'https://api.telegram.org/bot' + token + '/sendMessage?chat_id=' + Chat + '&parse_mode=Markdown&text=' + msj
    res = rq.get(txt)

    return res.json()

def reporte_prg(zip,file):
    df_PRG = pd.read_excel('./TMP/'+file, sheet_name='PROGRAMA')
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
    resu = "Nuevo programa publicado:  "+zip+":\n"+"*****Resumen del programa:*****\n"+"\nDemanda: "+demanda+ "\nGeneración FV: "+fv+"\nGeneración Pasada: "+hp+"\nGeneración Eólica: "+eo+"\nGeneración Térmica: "+ter+"\nGeneración Embalses: "+he+"\nGeneración Hidro Total: "+hidro+"\nGeneración Carbón: "+car+"\nGeneración Gas: "+gas+"\nGeneración Diesel: "+diesel+"\n\n" "\n**********\n\n"
    #print(resu)
    return resu

def links(contenido,year,month,tipo):

    inicio = 'https://www.coordinador.cl/wp-content/uploads/'+str(year)+'/'+str(month).zfill(2)+'/'+tipo
    final = '.zip'

    # Cargar el DataFrame existente o crear uno vacío si no existe
    try:
        df_link = pd.read_csv('links_'+tipo+'.csv')
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
        df_link.to_csv('links_'+tipo+'.csv', index=False)

    return df_link, nuevos_links


def descargar_PRO(txt,year,month,tipo):
    fecha_fin=""
    zip_fin=""
    limpiar_dir('./TMP')

    df_link, nuevos_links = links(txt,year,month,tipo)
    if len(nuevos_links) > 0:
        for link in nuevos_links:
            wget.download(link, './'+tipo+'/')
            wget.download(link, './TMP/')
            #obtener la última parte del string link luego del último "/"
            zip = link.split('/')[-1]
            #descomprimir el archivo zip en la carpeta TMP
            with zp.ZipFile('./TMP/'+zip,"r") as POzip:
                POzip.extractall(path="./TMP/")
            #buscar en la carpeta TMP el nombre del archivo que termina con .xlsx
            for file in os.listdir('./TMP/'):
                if file.endswith('.xlsx'):
                    if file.startswith('PRG'):
                        electrogas.gas("./TMP/"+file)
                        msj=reporte_prg(zip,file)
                        enviar_msj(Chat,token,msj)
                        enviar_file(Chat,token,"./TMP/"+file)
                        shutil.move("./TMP/"+file,"../real_time/PRG/"+file)
                        mail.send("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/gas","eliminar","/home/ubuntu/real_time/gas/"+file[3:])
                    elif file.startswith('PO'):
                        #obtener los 6 caracteres después de "PO" en file
                        fecha_fin = file[2:8]
                        zip_fin = zip
                        enviar_file(Chat,token,"./TMP/"+file)
                        shutil.move("./TMP/"+file,"../real_time/PO/"+file)
            #eliminar todos los archivos de la carpeta TMP
            limpiar_dir('./TMP')

    else:
        print('No hay programas nuevos')
    return fecha_fin,zip_fin

def descargar_PID(txt,year,month,tipo):
    fecha_fin=""
    zip_fin=""
    #eliminar todos los archivos de la carpeta TMP
    limpiar_dir('./TMP')

    df_link, nuevos_links = links(txt,year,month,tipo)
    if len(nuevos_links) > 0:
        for link in nuevos_links:
            wget.download(link, './'+tipo+'/')
            wget.download(link, './TMP/')
            #obtener la última parte del string link luego del último "/"
            zip = link.split('/')[-1]
            dir=zip[:-4]
            #descomprimir el archivo zip en la carpeta TMP
            with zp.ZipFile('./TMP/'+zip,"r") as POzip:
                POzip.extractall(path="./TMP/")
            #buscar en la carpeta TMP el nombre del archivo que termina con .xlsx
            for file in os.listdir(f'./TMP/{dir}/'):
                if file.endswith('.xlsx'):
                    if file.startswith('PRG'):
                        electrogas.gas2("./TMP/"+dir+"/"+file)
                        enviar_msj(Chat,token,"Se ha publicado una nueva programación intradiaria")
                        enviar_file(Chat,token,f"./TMP/{dir}/"+file)
                        shutil.move("./TMP/"+dir+"/"+file,"../real_time/PID/"+file)
                        mail.send("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/PID","eliminar","/home/ubuntu/real_time/PID/"+file)
                        mail.send("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/gas_PID","eliminar","/home/ubuntu/real_time/gas_PID/"+file[3:])
            #eliminar todos los archivos de la carpeta TMP
            limpiar_dir('./TMP')

    else:
        print('No hay programas intradiarios nuevos')





def descargar(txt,year,month,tipo):
    df_link, nuevos_links = links(txt,year,month,tipo)
    if len(nuevos_links) > 0:
        for link in nuevos_links:
            wget.download(link, './'+tipo+'/')
    else:
        print('No hay nuevos'+tipo)

fecha = ""
zip = ""

url='https://www.coordinador.cl/operacion/documentos/programas-de-operacion-2021/'
datos = rq.get(url, verify=False)
txt = datos.text
url2='https://www.coordinador.cl/operacion/documentos/programacion-intradiaria/'
datos2 = rq.get(url2)
txt2 = datos2.text
now = dt.datetime.now()
year = now.year
month = now.month
fecha,zip=descargar_PRO(txt,year,month,"PRO")
descargar_PID(txt2,year,month,"PID")
descargar(txt,year,month,"TCO")
descargar(txt,year,month,"PLP")
descargar(txt2,year,month,"PLE")
#descargar(txt,year,month,"PID")
if fecha != "":
    print(fecha)
    reporte.cotas(fecha,zip)
    reporte.informe(fecha,zip)
    reporte.pdf(fecha)
    enviar_file(Chat,token,'./INF/informe.pdf')

now = dt.datetime.now() - dt.timedelta(days=1)
year = now.year
month = now.month
fecha,zip=descargar_PRO(txt,year,month,"PRO")
descargar_PID(txt2,year,month,"PID")
descargar(txt,year,month,"TCO")
descargar(txt,year,month,"PLP")
#descargar(txt,year,month,"PRO")
if fecha != "":
    print(fecha)
    reporte.cotas(fecha,zip)
    reporte.informe(fecha,zip)
    reporte.pdf(fecha)