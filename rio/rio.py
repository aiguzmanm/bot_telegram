import sys
import os
import datetime as dt

# Ruta del directorio del script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Añadir el directorio raíz al sys.path
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

# Importar módulos
from modules.telegram_utils import enviar_mensaje_telegram
from rio_utils import descargar_rio, detectar_fallas

def main():

    # Configurar el directorio base donde se almacenarán los archivos
    project_root = os.path.dirname(os.path.abspath(__file__))
    datos_dir = os.path.join(project_root,'..', 'datos')
    
    hoy_f = dt.datetime.now() - dt.timedelta(hours=4)
    fecha = hoy_f.strftime("%y%m%d")

    descargar_rio(fecha, base_dir=datos_dir)
   
    nuevas_fallas = detectar_fallas(fecha, base_dir=datos_dir)

    if nuevas_fallas is not None:
        falla = nuevas_fallas[['Hora', 'Planta', 'Estado']].to_string(index=False)
        mensaje = f"Aviso de centrales falladas:\n{falla}"
        mensaje = mensaje.replace("_", "-")
        enviar_mensaje_telegram(mensaje)
    else:
        print("No hay nuevas fallas.")

if __name__ == "__main__":
    main()


