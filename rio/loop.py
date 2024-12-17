import subprocess
from datetime import datetime, timedelta

def ejecutar_opreal(fecha_inicio, fecha_fin):
    """
    Ejecuta opreal.py con fechas en formato aammdd, desde una fecha inicial hacia atrás hasta una fecha definida.

    Parámetros:
        fecha_inicio (str): Fecha inicial en formato 'dd/mm/aa'.
        fecha_fin (str): Fecha final en formato 'dd/mm/aa'.
    """
    # Convertir fechas de texto a objetos datetime
    fecha_inicio_dt = datetime.strptime(fecha_inicio, "%d/%m/%y")
    fecha_fin_dt = datetime.strptime(fecha_fin, "%d/%m/%y")

    # Iterar hacia atrás desde la fecha inicial hasta la fecha final
    fecha_actual = fecha_inicio_dt
    while fecha_actual >= fecha_fin_dt:
        # Formatear la fecha en aammdd
        fecha_formateada = fecha_actual.strftime("%y%m%d")
        print(f"Ejecutando rio.py para la fecha: {fecha_formateada}")
        
        # Ejecutar el script usando subprocess
        try:
            subprocess.run(["python3", "rio.py", fecha_formateada], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar opreal.py para la fecha {fecha_formateada}: {e}")
        
        # Restar un día
        fecha_actual -= timedelta(days=1)

if __name__ == "__main__":
    # Fecha inicial y final
    fecha_inicio = "31/12/23"  # Formato 'dd/mm/aa'
    fecha_fin = "01/01/23"     # Formato 'dd/mm/aa'

    # Ejecutar la función
    ejecutar_opreal(fecha_inicio, fecha_fin)
