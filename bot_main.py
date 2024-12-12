import os
import datetime as dt
from modules.telegram_utils import enviar_archivo_telegram, enviar_mensaje_telegram, cargar_config
import telebot
import configparser

# Añadir el directorio raíz del proyecto al sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir))
#convertir projec_root a una cadena
project_root = str(project_root)

# Cargar configuraciones
config = cargar_config()
CHAT_ID_CONFIGURADO = config['telegram']['chat_id']
token = config['telegram']['token']
deltatime = int(config['timezone']['adjustment_hours'])

# Crear BOT
bot = telebot.TeleBot(token)

def extract_arg(text):
    # Esta función toma el texto después del comando y lo retorna como el argumento
    return " ".join(text.split()[1:])

def validar_fecha(fecha_str):
    try:
        fecha = dt.datetime.strptime(fecha_str, "%d/%m/%y")
        return fecha
    except ValueError:
        return None

def verificar_fecha_valida(fecha):
    hoy = dt.datetime.now() - dt.timedelta(hours=deltatime)
    inicio = dt.datetime(2020, 1, 1)
    
    if fecha > hoy:
        return "No puedo enviar información del futuro."
    elif fecha < inicio:
        return "Solo tengo información a partir del 01/01/20."
    return None

def enviar_archivo_programa(fecha_str, cid, tipo):
    # Define las rutas para 'po' y 'prg'
    if tipo == 'rio':
        archivo_ruta = project_root+f"/datos/{tipo}/{tipo.upper()}{fecha_str}.xls"
    else:
        archivo_ruta = project_root+f"/datos/{tipo}/{tipo.upper()}{fecha_str}.xlsx"
    print(archivo_ruta)
    if os.path.exists(archivo_ruta):
        enviar_archivo_telegram(archivo_ruta, cid)
    else:
        enviar_mensaje_telegram(f"No se encontró el archivo {tipo.upper()} para la fecha solicitada.", cid)

@bot.message_handler(commands=['informe'])
def command_informe(m):
    cid = m.chat.id
    # Solo permitir al chat configurado en config.ini
    if str(cid) != CHAT_ID_CONFIGURADO:
        enviar_mensaje_telegram("No tienes permiso para solicitar esta información.", cid)
        return
    
    # Procesar argumento de fecha
    argu = extract_arg(m.text)
    if argu:
        fecha = validar_fecha(argu)
        if not fecha:
            enviar_mensaje_telegram("Fecha errónea, debes ingresar fecha en formato DD/MM/AA", cid)
            return
    else:
        # Usar la fecha de hoy si no hay argumento
        fecha = dt.datetime.now() - dt.timedelta(hours=deltatime)
    
    # Verificar si la fecha es válida
    error_fecha = verificar_fecha_valida(fecha)
    if error_fecha:
        enviar_mensaje_telegram(error_fecha, cid)
        return

    # Convertir la fecha a string en el formato deseado
    fecha_str = fecha.strftime("%y%m%d")
   
    # Ejecutar el script de generación de informes y luego enviar el archivo
    try:
        os.system(f"python3 ./informe/informe.py {fecha_str}")
    except Exception as e:
        enviar_mensaje_telegram(f"Error al generar el informe: {e}", cid)

@bot.message_handler(commands=['po'])
def command_po(m):
    cid = m.chat.id
    if str(cid) != CHAT_ID_CONFIGURADO:
        enviar_mensaje_telegram("No tienes permiso para solicitar esta información.", cid)
        return
    
    argu = extract_arg(m.text)
    if argu:
        fecha = validar_fecha(argu)
        if not fecha:
            enviar_mensaje_telegram("Fecha errónea, debes ingresar fecha en formato DD/MM/AA", cid)
            return
    else:
        fecha = dt.datetime.now() - dt.timedelta(hours=deltatime)
    
    error_fecha = verificar_fecha_valida(fecha)
    if error_fecha:
        enviar_mensaje_telegram(error_fecha, cid)
        return

    fecha_str = fecha.strftime("%y%m%d")
    enviar_archivo_programa(fecha_str, cid, "po")


@bot.message_handler(commands=['prg'])
def command_prg(m):
    cid = m.chat.id
    if str(cid) != CHAT_ID_CONFIGURADO:
        enviar_mensaje_telegram("No tienes permiso para solicitar esta información.", cid)
        return
    
    argu = extract_arg(m.text)
    if argu:
        fecha = validar_fecha(argu)
        if not fecha:
            enviar_mensaje_telegram("Fecha errónea, debes ingresar fecha en formato DD/MM/AA", cid)
            return
    else:
        fecha = dt.datetime.now() - dt.timedelta(hours=deltatime)
    
    error_fecha = verificar_fecha_valida(fecha)
    if error_fecha:
        enviar_mensaje_telegram(error_fecha, cid)   
        return

    fecha_str = fecha.strftime("%y%m%d")
    enviar_archivo_programa(fecha_str, cid, "prg")


@bot.message_handler(commands=['rio'])
def command_prg(m):
    cid = m.chat.id
    if str(cid) != CHAT_ID_CONFIGURADO:
        enviar_mensaje_telegram("No tienes permiso para solicitar esta información.", cid)
        return
    
    argu = extract_arg(m.text)
    if argu:
        fecha = validar_fecha(argu)
        if not fecha:
            enviar_mensaje_telegram("Fecha errónea, debes ingresar fecha en formato DD/MM/AA", cid)
            return
    else:
        fecha = dt.datetime.now() - dt.timedelta(hours=deltatime)
    
    error_fecha = verificar_fecha_valida(fecha)
    if error_fecha:
        enviar_mensaje_telegram(error_fecha, cid)
        return

    fecha_str = fecha.strftime("%y%m%d")
    enviar_archivo_programa(fecha_str, cid, "rio")

@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    # Verificar que sea el chat correcto
    if str(cid) != CHAT_ID_CONFIGURADO:
        enviar_mensaje_telegram("No tienes permiso para solicitar esta información.", cid)
        return
    
    # Leer el contenido de help.md y enviar el mensaje formateado
    with open("help.md", "r", encoding="utf-8") as file:
        help_text = file.read()
    
    # Enviar mensaje de ayuda con MarkdownV2
    bot.send_message(cid, help_text, parse_mode="MarkdownV2")


bot.polling(True)

