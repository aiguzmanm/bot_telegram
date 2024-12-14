import sys
import os
import datetime as dt

# Ruta del directorio del script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Añadir el directorio raíz al sys.path
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

# Importar módulos
from modules.telegram_utils import enviar_foto_telegram, enviar_mensaje_telegram
from modules.graph_utils import generar_graficos_sscc
from sscc_utils import procesar_datos_sscc

def main(fecha=None):
    # Configurar el directorio base
    datos_dir = os.path.abspath(os.path.join(project_root, 'datos', 'sscc'))
    os.makedirs(datos_dir, exist_ok=True)  # Crear el directorio si no existe

    # Configurar fecha
    if fecha is None and len(sys.argv) > 1:
        fecha = sys.argv[1]
    if not fecha:
        fecha = (dt.datetime.now() - dt.timedelta(hours=4)).strftime("%y%m%d")  # Ajuste según tu zona horaria

    # Procesar datos y guardar DataFrames como archivos .xlsx en datos/sscc
    procesar_datos_sscc(fecha, datos_dir)

    # Generar gráficos y guardarlos en datos/sscc
    generar_graficos_sscc(fecha, datos_dir, datos_dir)  # Gráficos también se guardarán en datos_dir

    # Enviar gráficos a Telegram
    for archivo in ["CPF.jpg", "CSF.jpg", "CTF.jpg"]:
        ruta = os.path.join(datos_dir, archivo)
        enviar_foto_telegram(ruta)

if __name__ == "__main__":
    main()