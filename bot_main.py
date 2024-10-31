# bot_main.py
import telebot
import datetime as dt
import configparser

from modules.telegram_utils import enviar_mensaje_telegram, enviar_archivo_telegram
import os

config = configparser.ConfigParser()
config.read('config.ini')
token = config['telegram']['token']
bot = telebot.TeleBot(token)

# Función para extraer argumentos del comando
def extract_arg(arg):
    return "".join(arg.split()[1:])

# Comando /informe
@bot.message_handler(commands=['informe'])
def command_informe(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha = argu[6:8] + argu[3:5] + argu[0:2]
        ruta_informe = f'./datos/informe/informe_{fecha}.pdf'  # Ruta ejemplo
        if os.path.exists(ruta_informe):
            enviar_archivo_telegram(ruta_informe, cid)
        else:
            enviar_mensaje_telegram("No se encontró el archivo de informe para esa fecha.", cid)
    except Exception as e:
        enviar_mensaje_telegram(f"Error en el comando /informe: {e}", m.chat.id)

# Comando /rio
@bot.message_handler(commands=['rio'])
def command_rio(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha = argu[6:8] + argu[3:5] + argu[0:2]
        ruta_rio = f'./datos/rio/RIO{fecha}.xls'
        if os.path.exists(ruta_rio):
            enviar_archivo_telegram(ruta_rio, cid)
        else:
            enviar_mensaje_telegram("No se encontró el archivo RIO para esa fecha.", cid)
    except Exception as e:
        enviar_mensaje_telegram(f"Error en el comando /rio: {e}", m.chat.id)

# Comando /prg
@bot.message_handler(commands=['prg'])
def command_prg(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha = argu[6:8] + argu[3:5] + argu[0:2]
        ruta_prg = f'./datos/prg/PRG{fecha}.xlsx'
        if os.path.exists(ruta_prg):
            enviar_archivo_telegram(ruta_prg, cid)
        else:
            enviar_mensaje_telegram("No se encontró el archivo PRG para esa fecha.", cid)
    except Exception as e:
        enviar_mensaje_telegram(f"Error en el comando /prg: {e}", m.chat.id)

# Comando /po
@bot.message_handler(commands=['po'])
def command_po(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha = argu[6:8] + argu[3:5] + argu[0:2]
        ruta_po = f'./datos/po/PO{fecha}.xlsx'
        if os.path.exists(ruta_po):
            enviar_archivo_telegram(ruta_po, cid)
        else:
            enviar_mensaje_telegram("No se encontró el archivo PO para esa fecha.", cid)
    except Exception as e:
        enviar_mensaje_telegram(f"Error en el comando /po: {e}", m.chat.id)

# Arrancar el bot
bot.polling()
