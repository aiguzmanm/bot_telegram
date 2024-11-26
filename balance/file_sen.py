import requests as rq
import datetime as dt
import os

hoy_F = dt.datetime.now() - dt.timedelta(hours=3) # - dt.timedelta(days=3)
hora = hoy_F.hour
fecha= str(hoy_F.year)[2:4]+ str(hoy_F.month).zfill(2)+ str(hoy_F.day).zfill(2)

os.chdir('/home/ubuntu/BAL')

import spot_sen as SP
SP.SQL(fecha)
os.chdir('/home/ubuntu/')

files1 = {'photo': open('./BAL/graf_gen_sen/'+fecha+'.png', 'rb')}
files2 = {'photo': open('./BAL/tab_gen_sen/'+fecha+'.png', 'rb')}
files3 = {'document': open('./BAL/Iny_sen/'+fecha+'.csv', 'rb')}

Chat = '-1001437637888'
token = '1702011759:AAET9BGHMjrTZr3mcs3nOVmDPMPK9xT4jMc'

txt1 = 'https://api.telegram.org/bot' + token + '/sendPhoto?chat_id=' + Chat
txt2 = 'https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + Chat
prueba1 = rq.post(txt1,files=files1)
prueba2 = rq.post(txt1,files=files2)
prueba3 = rq.post(txt2,files=files3)
