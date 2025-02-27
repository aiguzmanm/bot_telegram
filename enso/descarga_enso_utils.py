import os
import requests
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import fitz
import re
import shutil
from PIL import Image
import sys
from datetime import datetime

# Añadir el directorio raíz del proyecto al sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

# Importar las funciones de telegram_utils
from modules.telegram_utils import enviar_reporte_enso

# Configurar la carpeta base de destino
carpeta_destino = os.path.abspath(os.path.join(project_root, 'datos', 'enso'))

# Ruta del archivo CSV donde guardamos los enlaces descargados
links_file = os.path.join(carpeta_destino, 'links.csv')

def es_primera_ejecucion():
    return not os.path.exists(links_file) or os.stat(links_file).st_size == 0

def convertir_formato_fecha(fecha_str):
    # Diccionario para mapear los meses a números
    meses = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    
    # Extraer el mes y el año
    mes = fecha_str[:3].lower()  # Tomar los primeros 3 caracteres y convertirlos a minúsculas
    año = fecha_str[3:]          # Tomar el resto de la cadena como el año
    
    # Obtener el número del mes del diccionario
    mes_numero = meses.get(mes, '00')  # '00' en caso de que el mes no sea válido
    
    # Formatear el año a dos dígitos
    año_corto = año[-2:]
    
    # Combinar el año y el mes en el formato deseado
    formato_aamm = f"{año_corto}{mes_numero}"
    
    return formato_aamm

def obtener_enlaces_disponibles():
    año_actual = datetime.now().year
    descargar_todos = es_primera_ejecucion()
    url_base = "https://www.cpc.ncep.noaa.gov/products/expert_assessment/ENSO_DD_archive.php"
    scraper = cloudscraper.create_scraper()

    try:
        response = scraper.get(url_base)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    enlaces_disponibles = []

    for link in soup.find_all('a', href=True):
        url = link['href']
        if "enso_disc_" in url:
            enlace_completo = f"https://www.cpc.ncep.noaa.gov{url}" if url.startswith('/products') else url
            partes = enlace_completo.rstrip('/').split("_")[-1]
            año = ''.join(filter(str.isdigit, partes))

            if año.isdigit() and (descargar_todos or int(año) == año_actual):
                pdf_url = enlace_completo.rstrip('/') + "/ensodisc_Sp.pdf"
                response = requests.head(pdf_url)

                if response.status_code == 200:
                    enlaces_disponibles.append(enlace_completo)

    if not enlaces_disponibles:
        return []

    return enlaces_disponibles


def cargar_links_descargados():
    if os.path.exists(links_file):
        try:
            df = pd.read_csv(links_file)
            return set(df['Link'])
        except Exception:
            return set()
    return set()

def guardar_link_descargado(link):
    df = pd.DataFrame({'Link': [link]})
    if os.path.exists(links_file):
        df.to_csv(links_file, mode='a', header=False, index=False)
    else:
        df.to_csv(links_file, index=False)

def guardar_grafico_recortado(imagen_extraida, carpeta_archivo, nombre_pdf):
    try:
        # Cargar la imagen extraída
        with Image.open(imagen_extraida) as img:
            width, height = img.size
            grafico_nino_34 = img.crop((0, height * 0.25, width, height * 0.5))
            destino = os.path.join(carpeta_archivo, f"Grafico_Niño_3_4_{nombre_pdf}.png")
            grafico_nino_34.save(destino)
    except Exception as e:
        print(f"Error al recortar y guardar el gráfico Niño 3.4: {e}")

def descargar_archivo_enso():
    enlaces = obtener_enlaces_disponibles()

    if not enlaces:
        print("No se encontraron nuevos archivos para el año actual.")
        return

    links_descargados = cargar_links_descargados()
    archivos_descargados = []

    for link in enlaces:
        if link in links_descargados:
            continue

        partes = link.rstrip('/').split("_")
        if len(partes) < 2:
            continue
        
        nombre_carpeta = convertir_formato_fecha(partes[-1])  # Formato: "oct2024"
        carpeta_archivo = os.path.join(carpeta_destino, nombre_carpeta)
        os.makedirs(carpeta_archivo, exist_ok=True)

        nombre_archivo = "ensodisc_Sp.pdf"
        ruta_archivo = os.path.join(carpeta_archivo, nombre_archivo)

        if os.path.exists(ruta_archivo):
            continue

        try:
            response = requests.get(link + "/" + nombre_archivo, stream=True)
            if response.status_code == 200:
                with open(ruta_archivo, "wb") as file:
                    file.write(response.content)

                guardar_link_descargado(link)
                archivos_descargados.append(ruta_archivo)
                doc = fitz.open(ruta_archivo)

                nombre_pdf = os.path.basename(ruta_archivo).replace(".pdf", "")
                
                texto_completo = "\n".join([pagina.get_text() for pagina in doc])
                patron_estatus = r"Estatus del Sistema de alerta del ENSO:\s*(.*?\.)(?:\s|\n)"
                coincidencia_estatus = re.search(patron_estatus, texto_completo, re.DOTALL)
                estatus = coincidencia_estatus.group(1).strip() if coincidencia_estatus else "Estatus no encontrado"
                
                patron_fecha = r"(\d{1,2} de [a-zA-Z]+ de \d{4})"
                coincidencia_fecha = re.search(patron_fecha, texto_completo)
                fecha = coincidencia_fecha.group(1) if coincidencia_fecha else "Fecha no encontrada"
                
                ruta_info = os.path.join(carpeta_archivo, "informacion_enso.txt")
                with open(ruta_info, "w", encoding="utf-8") as f:
                    f.write(f"Fecha: {fecha}\n")
                    f.write(f"Estatus: {estatus}\n")
                
                for num_pagina, descripcion in [(2, "Series de Tiempo de las anomalías"), (4, "Pronóstico SST Niño 3.4"), (5, "Probabilidad SST Niño 3.4")]:
                    if num_pagina < len(doc):
                        pagina = doc[num_pagina]
                        imagenes = pagina.get_images(full=True)
                        
                        if imagenes:
                            ultima_imagen = imagenes[-1]
                            xref = ultima_imagen[0]
                            imagen = doc.extract_image(xref)
                            img_bytes = imagen["image"]
                            ext = imagen["ext"]
                            
                            ruta_imagen_temp = os.path.join(carpeta_archivo, f"temp_imagen.{ext}")
                            with open(ruta_imagen_temp, "wb") as f:
                                f.write(img_bytes)
                            
                            if descripcion == "Series de Tiempo de las anomalías":
                                guardar_grafico_recortado(ruta_imagen_temp, carpeta_archivo, nombre_pdf)
                            else:
                                ruta_imagen = os.path.join(carpeta_archivo, f"{descripcion}_{nombre_pdf}.{ext}")
                                shutil.copy(ruta_imagen_temp, ruta_imagen)
                            os.remove(ruta_imagen_temp)
                
                doc.close()
            enviar_reporte_enso()
        except Exception as e:
            print(f"Error procesando el PDF: {e}")

    if not archivos_descargados:
        print("No se encontraron nuevos archivos para descargar.")




def data_ONI():
    # Definir la URL del archivo .txt
    url_txt = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

    # Descargar el archivo .txt
    response = requests.get(url_txt)
    response.raise_for_status()

    # Guardar el archivo en el directorio enso
    salida_txt = os.path.join(carpeta_destino, 'ONI_data.txt')

    with open(salida_txt, 'w') as file:
        file.write(response.text)

    print(f"Archivo ONI guardado exitosamente en {salida_txt}")

    # Leer el archivo .txt en un DataFrame
    oni_df = pd.read_csv(salida_txt, delim_whitespace=True)
    
    # Guardar el DataFrame en un archivo Excel
    salida_excel = os.path.join(carpeta_destino, 'ONI_data.xlsx')
    oni_df.to_excel(salida_excel, index=False)