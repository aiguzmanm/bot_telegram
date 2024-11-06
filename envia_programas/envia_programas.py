import os
import sys
import pandas as pd
import datetime as dt
import requests as rq

from envia_programas_utils import descargar_PRO, descargar_PID


# Añadir el directorio raíz del proyecto al sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

def main():

    url='https://www.coordinador.cl/operacion/documentos/programas-de-operacion-2021/'
    datos = rq.get(url, verify=False)
    txt = datos.text
    url2='https://www.coordinador.cl/operacion/documentos/programacion-intradiaria/'
    datos2 = rq.get(url2)
    txt2 = datos2.text
    
    now = dt.datetime.now()
    year = now.year
    month = now.month
    fecha,zip=descargar_PRO(txt,year,month,"PRO")
    descargar_PID(txt2,year,month,"PID")


    now = dt.datetime.now() - dt.timedelta(days=1)
    year = now.year
    month = now.month
    fecha,zip=descargar_PRO(txt,year,month,"PRO")
    descargar_PID(txt2,year,month,"PID")

if __name__ == "__main__":
    main()