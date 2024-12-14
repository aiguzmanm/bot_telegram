import configparser
import os
import sys
from email.message import EmailMessage
import smtplib
import ssl

# Añadir el directorio raíz del proyecto al sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

def cargar_config():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
    return config

def send_mail(subjet,body,files):
    config = cargar_config()

    # Configura la información del correo electrónico
    sender_email = config.get('Email', 'sender_email')
    sender_password = config.get('Email', 'sender_password')
    recipient_email = config.get('Email', 'recipient_email')

    # Crea el mensaje
    msg = EmailMessage()
    msg.set_content(body)
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subjet

    # Adjunta el archivo
    with open(files, "rb") as attachment:
        msg.add_attachment(attachment.read(), maintype="application", subtype="octet-stream", filename=os.path.basename(files))

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)