import os
import spot as SP
import datetime as dt

#os.chdir('../real_time/')
#exec(open("./rtcmg.py").read())
#os.chdir('../BAL/')


hoy_F = dt.datetime.now() - dt.timedelta(hours=3) #- dt.timedelta(days=1)
fecha= str(hoy_F.year)[2:4]+ str(hoy_F.month).zfill(2)+ str(hoy_F.day).zfill(2)
hora = SP.SQL(fecha)
SP.Consulta(fecha)
SP.Graf(fecha,hora)
SP.Telegram(fecha)
