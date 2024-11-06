import os
import datetime as dt
from modules.download_utils import descarga_prg  # Asegúrate de que la ruta sea correcta
from modules.telegram_utils import cargar_config


def main():

    config = cargar_config()
    #cargar deltatime como int
    deltatime = int(config['timezone']['adjustment_hours'])

    # Configurar el directorio base donde se almacenarán los archivos
    project_root = os.path.dirname(os.path.abspath(__file__))
    datos_dir = os.path.join(project_root, 'datos')
    
    # Obtener la fecha actual en formato YYMMDD
    hoy = dt.datetime.now() - dt.timedelta(hours=deltatime)  # Ajusta la hora si es necesario
    fecha = hoy.strftime("%y%m%d")

    # Llamar a la función de descarga PRG
    print(f"Iniciando descarga para la fecha: {fecha}")
    descarga_prg(fecha, base_dir=datos_dir)
    print("Descarga completada.")

if __name__ == "__main__":
    main()
