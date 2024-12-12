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

def enviar_foto_telegram(ruta_foto):
    config = cargar_config()
    token = config['telegram']['token']
    chat_id = config['telegram']['chat_id']
    
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