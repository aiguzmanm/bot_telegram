import os
import telebot
import InformeA as IA
import datetime as dt
import bal_fech as BF
import gen_fech as GF
import opreal as OR
import requests as rq

token = '1702011759:AAET9BGHMjrTZr3mcs3nOVmDPMPK9xT4jMc'
bot = telebot.TeleBot(token)
Chat = '-1001437637888'

#################### Enviar Archivos#######################

def enviar_file(Chat,token,ruta):
    Chat=str(Chat)
    token=str(token)
    ruta=str(ruta)
    files = {'document': open(ruta, 'rb')}
    txt = 'https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + Chat
    prueba=rq.post(txt,files=files)


#################### ENVÃOS DEL DÃA #######################
def EnerAflu():
    os.chdir('/home/ubuntu/')
    os.system('/home/ubuntu/EnerAflu/aut.sh')
    os.chdir('./real_time/')

def Gen():
    os.chdir('/home/ubuntu/')
    os.system('/home/ubuntu/BAL/file.sh')
    os.chdir('./real_time/')
def Gen_sen():
    os.chdir('/home/ubuntu/')
    os.system('/home/ubuntu/BAL/file_sen.sh')
    os.chdir('./real_time/')
def Balance():
    os.chdir('/home/ubuntu/')
    os.system('/home/ubuntu/BAL/aut.sh')
    os.chdir('./real_time/')

#################################################

################### SSCC  #####################
def enviar_SSCC(fecha,cid,argu,token):
    if(argu != ""):
        if(len(argu)!=8):
            bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
        else:    
            try:
#               date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
                exec(open("./SSCC/sub_SSCC.py").read())
            except ValueError:
                bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
    else:
        hoy_F = dt.datetime.now() - dt.timedelta(hours=4) # - dt.timedelta(days=3)
        fecha= str(hoy_F.year)[2:4]+ str(hoy_F.month).zfill(2)+ str(hoy_F.day).zfill(2)
        exec(open("./SSCC/sub_SSCC.py").read())

#############################################################

################### Gen  #####################

def enviar_gen(fecha,cid,argu,token):
    if(argu != ""):
        if(len(argu)!=8):
            bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
        else:    
            try:
                date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
                gen_fecha(argu,cid,token)
            except ValueError:
                bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
    else:
        Gen()


def gen_fecha(argu,cid,token):
    hoy = dt.datetime.now() - dt.timedelta(hours=4)
    inicio = dt.datetime(2022,10,20)
    fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
    date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
    if date > hoy- dt.timedelta(days=1):
        bot.send_message(cid, "No puedo enviar informes del futuro")
    else:
        if (date < inicio):
            bot.send_message(cid, "SÃ³lo tengo informes a contar del 20/10/22")
        else:
            fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
            hora=24
            GF.Gen(fecha,hora)


#############################################################
################### Gen_SEN  #####################

def enviar_gen_sen(fecha,cid,argu,token):
    if(argu != ""):
        if(len(argu)!=8):
            bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
        else:    
            try:
                date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
                gen_fecha_sen(argu,cid,token)
            except ValueError:
                bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
    else:
        Gen_sen()


def gen_fecha_sen(argu,cid,token):
    hoy = dt.datetime.now() - dt.timedelta(hours=4)
    inicio = dt.datetime(2022,10,20)
    fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
    date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
    if date > hoy- dt.timedelta(days=1):
        bot.send_message(cid, "No puedo enviar informes del futuro")
    else:
        if (date < inicio):
            bot.send_message(cid, "SÃ³lo tengo informes a contar del 20/10/22")
        else:
            fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
            hora=24
            GF.Gen_sen(fecha,hora)


#############################################################
################### BALANCE  #####################

def enviar_bal(fecha,cid,argu,token):
    if(argu != ""):
        if(len(argu)!=8):
            bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
        else:    
            try:
                date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
                bal_fecha(argu,cid,token)
            except ValueError:
                bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
    else:
        Balance()


def bal_fecha(argu,cid,token):
    hoy = dt.datetime.now() - dt.timedelta(hours=4)
    inicio = dt.datetime(2022,10,20)
    fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
    date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
    if date > hoy- dt.timedelta(days=1):
        bot.send_message(cid, "No puedo enviar informes del futuro")
    else:
        if (date < inicio):
            bot.send_message(cid, "SÃ³lo tengo informes a contar del 20/10/22")
        else:
            fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
            hora=24
            BF.Bal(fecha,hora)


#############################################################

############# Informes ######################################

def enviar_inf(fecha,cid,argu,token):
    if(argu != ""):
        if(len(argu)!=8):
            bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
        else:    
            try:
                date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
                info_fecha(argu,cid,token)
            except ValueError:
                bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
    else:
        os.chdir('/home/ubuntu/')
        os.system('python3 ./real_time/real_time.py')
        os.chdir('./real_time/')

def info_fecha(argu,cid,token):
    hoy = dt.datetime.now() - dt.timedelta(hours=4)
    inicio = dt.datetime(2020,1,1)
    fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
    date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
    if date > hoy- dt.timedelta(days=1):
        bot.send_message(cid, "No puedo enviar informes del futuro")
    else:
        if (date < inicio):
            bot.send_message(cid, "SÃ³lo tengo informes a contar del 01/01/20")
        else:
            IA.Rep(argu,token,cid)

def extract_arg(arg):
    return "".join(arg.split()[1:])


#############################################################

################### Opreal  #####################

def enviar_OR(fecha,cid,argu,token):
    if(argu != ""):
        if(len(argu)!=8):
            bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
        else:    
            try:
                date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
                fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
                OR.Get(fecha)
            except ValueError:
                bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
    else:
        hoy = dt.datetime.now() - dt.timedelta(hours=4)
        fecha = str(hoy.year)[2:4]+ str(hoy.month).zfill(2)+ str(hoy.day).zfill(2)
        OR.Get(fecha)

######################################################

################### bar-cen  #####################

def enviar_bar_cen(fecha,cid,argu,token):
    if(argu != ""):
        if(len(argu)!=8):
            bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
        else:    
            try:
                hoy = dt.datetime.now() - dt.timedelta(hours=4)
                inicio = dt.datetime(2023,6,10)                
                date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
                if date > hoy- dt.timedelta(days=1):
                    bot.send_message(cid, "No puedo enviar informes del futuro")
                else:
                    if (date < inicio):
                        bot.send_message(cid, "SÃ³lo tengo informes a contar del 10/06/23")
                    else:
                        ruta = './bar-cen/'+fecha+'.csv'
                        enviar_file(cid,token,ruta)
            except ValueError:
                bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
    else:
        hoy = dt.datetime.now() - dt.timedelta(hours=4)
        fecha = str(hoy.year)[2:4]+ str(hoy.month).zfill(2)+ str(hoy.day).zfill(2)
        ruta = './bar-cen/'+fecha+'.csv'
        enviar_file(cid,token,ruta)

######################################################

################### PO  #####################

def enviar_po(fecha,cid,argu,token):
    if(argu != ""):
        if(len(argu)!=8):
            bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
        else:    
            try:
                hoy = dt.datetime.now() - dt.timedelta(hours=4)
                inicio = dt.datetime(2022,1,1)                
                date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
                if date > hoy:
                    bot.send_message(cid, "No puedo enviar informes del futuro")
                else:
                    if (date < inicio):
                        bot.send_message(cid, "SÃ³lo tengo informes a contar del 01/01/22")
                    else:
                        ruta = './PO/PO'+fecha+'.xlsx'
                        enviar_file(cid,token,ruta)
            except ValueError:
                bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
    else:
        hoy = dt.datetime.now() - dt.timedelta(hours=4)
        fecha = str(hoy.year)[2:4]+ str(hoy.month).zfill(2)+ str(hoy.day).zfill(2)
        ruta = './PO/PO'+fecha+'.xlsx'
        enviar_file(cid,token,ruta)

######################################################
################### PRG  #####################

def enviar_prg(fecha,cid,argu,token):
    if(argu != ""):
        if(len(argu)!=8):
            bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
        else:    
            try:
                hoy = dt.datetime.now() - dt.timedelta(hours=4)
                inicio = dt.datetime(2022,1,1)                
                date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
                if date > hoy:
                    bot.send_message(cid, "No puedo enviar informes del futuro")
                else:
                    if (date < inicio):
                        bot.send_message(cid, "SÃ³lo tengo informes a contar del 01/01/22")
                    else:
                        ruta = './PRG/PRG'+fecha+'.xlsx'
                        enviar_file(cid,token,ruta)
            except ValueError:
                bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
    else:
        hoy = dt.datetime.now() - dt.timedelta(hours=4)
        fecha = str(hoy.year)[2:4]+ str(hoy.month).zfill(2)+ str(hoy.day).zfill(2)
        ruta = './PRG/PRG'+fecha+'.xlsx'
        enviar_file(cid,token,ruta)

######################################################
################### RIO  #####################

def enviar_rio(fecha,cid,argu,token):
    if(argu != ""):
        if(len(argu)!=8):
            bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
        else:    
            try:
                hoy = dt.datetime.now() - dt.timedelta(hours=4)
                inicio = dt.datetime(2022,1,1)                
                date = dt.datetime(int("20"+fecha[0:2]),int(fecha[2:4]), int(fecha[4:6]))
                if date > hoy:
                    bot.send_message(cid, "No puedo enviar informes del futuro")
                else:
                    if (date < inicio):
                        bot.send_message(cid, "SÃ³lo tengo informes a contar del 01/01/22")
                    else:
                        ruta = './RIO/RIO'+fecha+'.xls'
                        enviar_file(cid,token,ruta)
            except ValueError:
                bot.send_message(cid, "Fecha ErrÃ³nea, debes ingresar fecha en formato DD/MM/AA")
    else:
        hoy = dt.datetime.now() - dt.timedelta(hours=4)
        fecha = str(hoy.year)[2:4]+ str(hoy.month).zfill(2)+ str(hoy.day).zfill(2)
        ruta = './RIO/RIO'+fecha+'.xls'
        enviar_file(cid,token,ruta)

######################################################

############## ESCUCHANDO ############################

##########Texto de ayuda##################

@bot.message_handler(commands=['help'])
def help(m):
    helpf = open("help.txt", 'r', encoding="utf-8").read()
    bot.reply_to(m,helpf)

########iNFORME#####

@bot.message_handler(commands=['informe'])
def command_informe(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
        enviar_inf(fecha,cid,argu,token)
    except:
        bot.send_message(cid, "Error")

      
        
########bALANCE######################################
        
@bot.message_handler(commands=['balance'])
def command_informe(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
        enviar_bal(fecha,cid,argu,token)
    except:
        bot.send_message(cid, "Error")

########Gen#####################################
    

@bot.message_handler(commands=['gen'])
def command_informe(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
        enviar_gen(fecha,cid,argu,token)
    except:
        bot.send_message(cid, "Error")

########Gen_SEN#####################################
    

@bot.message_handler(commands=['gen_sen'])
def command_informe(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
        enviar_gen_sen(fecha,cid,argu,token)
    except:
        bot.send_message(cid, "Error")
######## EnerAflu ###################################
@bot.message_handler(commands=['EnerAflu'])
def command_informe(m):
    try:
        cid = m.chat.id
        #argu = extract_arg(m.text)
        #fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
        EnerAflu()
    except:
        bot.send_message(cid, "Error")

#####################################################

########Opreal#####
       
@bot.message_handler(commands=['opreal'])
def command_opreal(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha= argu[6:8]+ argu[3:5]+ argu[0:2]   
        enviar_OR(fecha,cid,argu,token)
    except:
        bot.send_message(cid, "Error  !")

#####################################################

########bar-cen#####

@bot.message_handler(commands=['bar_cen'])
def command_informe(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
        enviar_bar_cen(fecha,cid,argu,token)
    except:
        bot.send_message(cid, "Error  !")

#####################################################


########PO#####

@bot.message_handler(commands=['po'])
def command_informe(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
        enviar_po(fecha,cid,argu,token)
    except:
        bot.send_message(cid, "Error  !")

#################################################

########PRG#####

@bot.message_handler(commands=['prg'])
def command_informe(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
        enviar_prg(fecha,cid,argu,token)
    except:
        bot.send_message(cid, "Error  !")

#####################################################


########RIO#####

@bot.message_handler(commands=['rio'])
def command_informe(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
        enviar_rio(fecha,cid,argu,token)
    except:
        bot.send_message(cid, "Error  !")

#####################################################

########Comando SSCC#####

@bot.message_handler(commands=['SSCC', 'sscc', 'Sscc', 'sScS'])
def command_SSCC(m):
    try:
        cid = m.chat.id
        argu = extract_arg(m.text)
        fecha= argu[6:8]+ argu[3:5]+ argu[0:2]
        enviar_SSCC(fecha,cid,argu,token)
    except:
        bot.send_message(cid, "Error")


#####################################################




bot.polling(True)
