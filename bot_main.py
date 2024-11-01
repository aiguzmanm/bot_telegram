import os
import datetime as dt
from telegram_utils import enviar_archivo_telegram, enviar_mensaje_telegram, cargar_config

# Cargar configuraciones
config = cargar_config()
CHAT_ID_CONFIGURADO = config['telegram']['chat_id']

def validar_fecha(fecha_str):
    try:
        fecha = dt.datetime.strptime(fecha_str, "%d/%m/%y")
        return fecha
    except ValueError:
        return None

def verificar_fecha_valida(fecha):
    hoy = dt.datetime.now() - dt.timedelta(hours=4)
    inicio = dt.datetime(2020, 1, 1)
    
    if fecha > hoy:
        return "No puedo enviar informes del futuro."
    elif fecha < inicio:
        return "Solo tengo informes a partir del 01/01/20."
    return None

@bot.message_handler(commands=['informe'])
def command_informe(m):
    cid = m.chat.id
    # Solo permitir al chat configurado en config.ini
    if str(cid) != CHAT_ID_CONFIGURADO:
        enviar_mensaje_telegram("No tienes permiso para solicitar este informe.", cid)
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
        fecha = dt.datetime.now() - dt.timedelta(hours=4)
    
    # Verificar si la fecha es válida
    error_fecha = verificar_fecha_valida(fecha)
    if error_fecha:
        enviar_mensaje_telegram(error_fecha, cid)
        return
    
    # Formatear la fecha para el nombre del archivo
    fecha_str = fecha.strftime("%y%m%d")
    ruta_informe = f'./datos/informe/informe_{fecha_str}.pdf'  # Ruta del informe
    
    # Ejecutar el script de generación de informes y luego enviar el archivo
    try:
        os.system(f"python3 ./informe/informe.py {fecha_str}")
        if os.path.exists(ruta_informe):
            enviar_archivo_telegram(ruta_informe, cid)
        else:
            enviar_mensaje_telegram("No se encontró el archivo de informe para esa fecha.", cid)
    except Exception as e:
        enviar_mensaje_telegram(f"Error al generar el informe: {e}", cid)
