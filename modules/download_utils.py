import os
import requests as rq
import wget
import zipfile as zp
import datetime as dt
import shutil
import ssl

def descarga_prg(fecha, base_dir="./datos"):

    date2 = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6])) - dt.timedelta(days=10)
    fecha2 = str(date2.year)[2:4]+ str(date2.month).zfill(2)+ str(date2.day).zfill(2)


    # Define rutas para TMP, PO, y PRG
    tmp_dir = os.path.join(base_dir, "tmp")
    po_dir = os.path.join(base_dir, "po")
    prg_dir = os.path.join(base_dir, "prg")
    
    # Asegurarse de que los directorios existen
    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(po_dir, exist_ok=True)
    os.makedirs(prg_dir, exist_ok=True)

    # Define la ruta de descarga del archivo zip
    dest = os.path.join(tmp_dir, f"{fecha}.zip")
    
    # Elimina cualquier archivo zip existente en TMP
    if os.path.exists(dest):
        os.remove(dest)

    # Intenta descargar desde la URL principal; si falla, usa la alternativa
    try:
        url = f"https://www.coordinador.cl/wp-content/uploads/20{fecha[:2]}/{fecha[2:4]}/PROGRAMA20{fecha}.zip"
        print(url)
        wget.download(url, dest)
        print(f"Descargado desde URL: {url}")
    except:
        url = f"https://www.coordinador.cl/wp-content/uploads/20{fecha[:2]}/{fecha2[2:4]}/PROGRAMA20{fecha}.zip"
        wget.download(url, dest)
        print(f"Descargado desde URL alternativa: {url}")

    # Descomprimir el archivo y limpiar archivos no deseados
    with zp.ZipFile(dest, "r") as po_zip:
        po_zip.extractall(path=tmp_dir)
    os.remove(dest)

    # Limpiar PDF innecesario
    informe_pcp_path = os.path.join(tmp_dir, f"Informe PCP {fecha[4:6]}-{fecha[2:4]}-20{fecha[:2]}.pdf")
    if os.path.exists(informe_pcp_path):
        os.remove(informe_pcp_path)

    # Mover archivos PO y PRG al directorio correspondiente
    po_path = os.path.join(tmp_dir, f"PO{fecha}.xlsx")
    prg_path = os.path.join(tmp_dir, f"PRG{fecha}.xlsx")
    if os.path.exists(po_path):
        shutil.move(po_path, os.path.join(po_dir, f"PO{fecha}.xlsx"))
    if os.path.exists(prg_path):
        shutil.move(prg_path, os.path.join(prg_dir, f"PRG{fecha}.xlsx"))

    print("Descarga y procesamiento de PRG completado.")

def descarga_rio_api(fecha, dest_csv, dest_xlsx):
    url = f'https://www.coordinador.cl/wp-admin/admin-ajax.php?action=export_energia_csv&fecha_inicio=20{fecha[:2]}-{fecha[2:4]}-{fecha[4:6]}&fecha_termino=20{fecha[:2]}-{fecha[2:4]}-{fecha[4:6]}&hora_inicio=00:00:00&hora_termino=23:59:59'
    #print(f"Descargando desde URL: {url}")
    descargar_archivo(url, dest_csv)
    

def descarga_rio_web(fecha, dest_xlsx):
    url_base = 'https://www.coordinador.cl/operacion/documentos/registro-de-instrucciones-de-operacion-rio/'
    datos = rq.get(url_base).text
    pos = datos.find('RIO'+fecha)
    if pos == -1:
        raise Exception(f"No se encontró RIO{fecha} en la página.")
    nombre = datos[pos:pos+30]
    pos_ext = nombre.find('.xlsx')
    nombre = nombre[:pos_ext+5]
    url = f"https://www.coordinador.cl/wp-content/uploads/20{fecha[:2]}/{fecha[2:4]}/{nombre}"
    #print(f"Descargando desde URL: {url}")
    descargar_archivo(url, dest_xlsx)

def descarga_rio_recdec(fecha, dest_xlsx):
    url = f"https://aplicaciones-sic.coordinador.cl/redcdec/RedCDEC/CdecSIC/Mov_Cent/20{fecha[:2]}/{fecha[:4]}/RIO{fecha}.xlsx"
    #print(f"Descargando desde URL: {url}")
    descargar_archivo(url, dest_xlsx)
    
def descargar_archivo(url, destino):
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    # Descargar el archivo
    ssl._create_default_https_context = ssl._create_unverified_context
    if os.path.exists(destino):
        os.remove(destino)
    #print(f"Descargando archivo desde {url} a {destino}")
    wget.download(url, destino)
    print(f"\nArchivo descargado: {destino}")
