import sys
import os
import datetime as dt

# Ruta del directorio del script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Añadir el directorio raíz al sys.path
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

# Importar módulos
from modules.telegram_utils import enviar_mensaje_telegram, cargar_config
from rio_utils import descargar_rio, detectar_fallas

def main(fecha=None):
    
    config = cargar_config()
    #cargar deltatime como int
    deltatime = int(config['timezone']['adjustment_hours'])

    
    # Configurar el directorio base donde se almacenarán los archivos
    project_root = os.path.dirname(os.path.abspath(__file__))
    datos_dir = os.path.abspath(os.path.join(project_root,'..', 'datos'))
    
    # Si se proporciona un argumento de fecha, úsalo
    if fecha is None and len(sys.argv) > 1:
        fecha = sys.argv[1]

    # Si la fecha sigue siendo None, usa la fecha de hoy
    if not fecha:
        hoy = dt.datetime.now() - dt.timedelta(hours=deltatime)
        fecha = hoy.strftime("%y%m%d")
        msg = 1
    descargar_rio(fecha, datos_dir)
   
    nuevas_fallas = detectar_fallas(fecha, base_dir=datos_dir)

    if nuevas_fallas is not None:
        falla = nuevas_fallas[['Hora', 'Planta', 'Estado']].to_string(index=False)
        mensaje = f"Aviso de centrales falladas en {fecha}:\n{falla}"
        mensaje = mensaje.replace("_", "-")
        if msg == 1:
            enviar_mensaje_telegram(mensaje)
    else:
        print("No hay nuevas fallas.")

if __name__ == "__main__":
    main()


