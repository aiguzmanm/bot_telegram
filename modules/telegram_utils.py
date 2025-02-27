import requests as rq
import configparser
import os
import sys

# Añadir el directorio raíz del proyecto al sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

# modules/telegram_utils.py
from modules.data_processing import generar_reporte_parcial

# 定义一个函数，用于加载配置文件
def cargar_config():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
    return config

def enviar_mensaje_telegram(mensaje, chat_id=None):
    config = cargar_config()
    token = config['telegram']['token']
    chat_id = chat_id if chat_id else config['telegram']['chat_id']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    params = {
        'chat_id': chat_id,
        'text': mensaje,
        'parse_mode': 'Markdown'
    }
    rq.get(url, params=params)


def enviar_reporte_telegram(fecha,base_dir = os.path.join(project_root, 'datos')):
    """Envía un mensaje de reporte parcial a Telegram"""
    # Cargar configuración
    config = cargar_config()
    token = config['telegram']['token']
    chat_id = config['telegram']['chat_id']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    
    # Generar mensaje
    mensaje = generar_reporte_parcial(fecha, base_dir=base_dir)
    
    # Enviar mensaje a Telegram
    params = {
        'chat_id': chat_id,
        'text': mensaje,
        'parse_mode': 'Markdown'
    }
    response = rq.get(url, params=params)
    return response.json()

def enviar_foto_telegram(ruta_foto, chat_id=None):
    config = cargar_config()
    token = config['telegram']['token']
    chat_id = chat_id if chat_id else config['telegram']['chat_id']
    
    # Comprobar si el archivo existe antes de enviarlo
    if not os.path.exists(ruta_foto):
        print(f"Archivo no encontrado: {ruta_foto}")
        return
    
    files = {'photo': open(ruta_foto, 'rb')}
    url = f'https://api.telegram.org/bot{token}/sendPhoto'
    params = {
        'chat_id': chat_id
    }

    # Enviar la solicitud
    response = rq.post(url, files=files, data=params)
    files['photo'].close()  # Cerrar el archivo después de la solicitud
    
    # Verificar la respuesta
    if response.status_code == 200:
        print("Foto enviada correctamente.")
    else:
        print("Error al enviar la foto:", response.text)


def enviar_archivo_telegram(ruta, chat_id=None):
    config = cargar_config()
    token = config['telegram']['token']
    chat_id = chat_id or config['telegram']['chat_id']
    url = f'https://api.telegram.org/bot{token}/sendDocument'
    with open(ruta, 'rb') as file:
        files = {'document': file}
        return rq.post(url, files=files, data={'chat_id': chat_id})
    

def enviar_reporte_enso(fecha=None):

    config = cargar_config()
    chat_id_enso = config['telegram']['chat_id_enso']

    data_path = os.path.abspath(os.path.join(project_root, 'datos','enso'))
    ultimo_informe = fecha_ajustada(fecha,data_path)
    ruta_archivos = os.path.join(data_path, ultimo_informe)
    texto = os.path.join(ruta_archivos, 'informacion_enso.txt')
    foto1 = os.path.join(ruta_archivos, 'Grafico_Niño_3_4_ensodisc_Sp.png')
    foto2 = os.path.join(ruta_archivos, 'Probabilidad SST Niño 3.4_ensodisc_Sp.png')
    foto3 = os.path.join(ruta_archivos, 'Pronóstico SST Niño 3.4_ensodisc_Sp.png')
    pdf = os.path.join(ruta_archivos, 'ensodisc_Sp.pdf')

    # Verificar si los archivos existen antes de enviarlos
    if not os.path.exists(texto):
        raise FileNotFoundError(f"No se encontró el archivo de texto: {texto}")
    if not os.path.exists(foto1):
        raise FileNotFoundError(f"No se encontró la foto: {foto1}")
    if not os.path.exists(foto2):
        raise FileNotFoundError(f"No se encontró la foto: {foto2}")
    if not os.path.exists(foto3):
        raise FileNotFoundError(f"No se encontró la foto: {foto3}")
    if not os.path.exists(pdf):
        raise FileNotFoundError(f"No se encontró el archivo PDF: {pdf}")

    with open(texto, "r", encoding="utf-8") as file:
        mensaje = file.read()
    enviar_mensaje_telegram(mensaje,chat_id_enso)
    enviar_foto_telegram(foto1,chat_id_enso)
    enviar_foto_telegram(foto2,chat_id_enso)
    enviar_foto_telegram(foto3,chat_id_enso)
    enviar_archivo_telegram(pdf,chat_id_enso)

def enviar_reporte_enso(fecha=None):
    import glob
    config = cargar_config()
    chat_id_enso = config['telegram']['chat_id_enso']
    data_path = os.path.abspath(os.path.join(project_root, 'datos', 'enso'))
    
    # Si no se proporciona una fecha, usar la última disponible
    if fecha is None:
        ultimo_informe = encontrar_ultima_fecha_disponible(data_path)
    else:
        ultimo_informe = fecha_ajustada(fecha, data_path)
    
    ruta_archivos = os.path.join(data_path, ultimo_informe)

    # Definir los nombres base de los archivos (sin extensión)
    archivos = {
        'texto': 'informacion_enso',
        'fotos': [
            'Grafico_Niño_3_4_ensodisc_Sp',
            'Probabilidad SST Niño 3.4_ensodisc_Sp',
            'Pronóstico SST Niño 3.4_ensodisc_Sp'
        ],
        'pdf': 'ensodisc_Sp'
    }

    # Construir las rutas completas
    ruta_texto = os.path.join(ruta_archivos, archivos['texto'] + '.txt')
    ruta_pdf = os.path.join(ruta_archivos, archivos['pdf'] + '.pdf')
    
    # Buscar fotos con cualquier extensión
    rutas_fotos = []
    for foto_base in archivos['fotos']:
        # Buscar archivos que coincidan con el nombre base y cualquier extensión
        coincidencias = glob.glob(os.path.join(ruta_archivos, foto_base + '.*'))
        if coincidencias:
            # Agregar la primera coincidencia (puedes ajustar esto si hay múltiples)
            rutas_fotos.append(coincidencias[0])
        else:
            print(f"Advertencia: No se encontró ningún archivo para {foto_base}.")

    # Verificar si los archivos existen
    if not os.path.exists(ruta_texto):
        raise FileNotFoundError(f"No se encontró el archivo de texto: {ruta_texto}")

    if not os.path.exists(ruta_pdf):
        raise FileNotFoundError(f"No se encontró el archivo PDF: {ruta_pdf}")

    # Leer y enviar el mensaje de texto
    with open(ruta_texto, "r", encoding="utf-8") as file:
        mensaje = file.read()
    enviar_mensaje_telegram(mensaje, chat_id_enso)

    # Enviar las fotos (solo las que existen)
    for foto in rutas_fotos:
        if os.path.exists(foto):
            enviar_foto_telegram(foto, chat_id_enso)
        else:
            print(f"La foto {foto} no existe y no se enviará.")

    # Enviar el archivo PDF
    enviar_archivo_telegram(ruta_pdf, chat_id_enso)

def encontrar_ultima_fecha_disponible(ruta):
    # Obtener todas las carpetas en la ruta
    carpetas = [nombre for nombre in os.listdir(ruta) if os.path.isdir(os.path.join(ruta, nombre))]
    
    # Filtrar carpetas que siguen el formato AAMM
    carpetas_fechas = [carpeta for carpeta in carpetas if len(carpeta) == 4 and carpeta.isdigit()]
    
    if not carpetas_fechas:
        raise ValueError("No se encontraron carpetas con formato AAMM en la ruta proporcionada.")
    
    # Encontrar la carpeta más reciente
    ultima_carpeta = max(carpetas_fechas)
    return ultima_carpeta


def fecha_ajustada(fecha,ruta):
    from datetime import datetime, timedelta
    fecha_actual = datetime.strptime(fecha, '%y%m%d')
    data_path = ruta
    # Intentar encontrar la carpeta correspondiente a la fecha actual
    while True:
        # Formatear la fecha actual en formato AAMM
        carpeta_actual = fecha_actual.strftime('%y%m')
        ruta_carpeta = os.path.join(data_path, carpeta_actual)
        # Verificar si la carpeta existe
        if os.path.exists(ruta_carpeta):
            # Si la carpeta existe, devolver la fecha en formato AAMM
            return fecha_actual.strftime('%y%m')
        # Si no existe, retroceder un mes
        fecha_actual = fecha_actual - timedelta(days=fecha_actual.day)
        fecha_actual = fecha_actual.replace(day=1)