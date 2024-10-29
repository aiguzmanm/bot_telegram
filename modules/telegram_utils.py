import requests as rq
import configparser
import os

def cargar_config():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
    return config

def enviar_mensaje_telegram(mensaje):
    config = cargar_config()
    token = config['telegram']['token']
    chat_id = config['telegram']['chat_id']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    params = {
        'chat_id': chat_id,
        'text': mensaje,
        'parse_mode': 'Markdown'
    }
    rq.get(url, params=params)
