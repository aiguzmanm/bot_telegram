import imaplib
import email
from email.header import decode_header
import os
import sys
import configparser
import re
import io
import requests

# ------------------------------------------------------------
# Alinear estructura con tus otros scripts
# ------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

from modules.email_utils import send_mail  # ✅ tu función original

# ------------------------------------------------------------
# Cargar configuración
# ------------------------------------------------------------
def cargar_config():
    config = configparser.ConfigParser()
    config.read(os.path.join(project_root, 'config.ini'))
    return config

config = cargar_config()
EMAIL_ACCOUNT = config.get("Email", "sender_email")
EMAIL_PASSWORD = config.get("Email", "sender_password")
IMAP_SERVER = "imap.gmail.com"

# Archivo de control de correos ya procesados
SEEN_FILE = os.path.join(project_root, "datos", "links", "cartas_sec_seen.txt")

# ------------------------------------------------------------
# Funciones auxiliares
# ------------------------------------------------------------
def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()

def save_seen(seen_ids):
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        f.write("\n".join(seen_ids))

# ------------------------------------------------------------
# Extraer link PDF desde el cuerpo del correo
# ------------------------------------------------------------
def extract_pdf_link(body):
    # Busca el patrón del link PDF
    match = re.search(r"https://wlhttp\.sec\.cl/timesM/global/imgPDF\.jsp\?[^ \n\r]+", body)
    if not match:
        return None
    link = match.group(0).strip()
    # Limpia posibles saltos de línea o retorno de carro
    link = link.replace("\r", "").replace("\n", "")
    return link

# ------------------------------------------------------------
# Revisa bandeja Gmail y procesa "Correo SEC"
# ------------------------------------------------------------
def check_correos_sec():
    seen_ids = load_seen()
    new_seen = set()

    with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")

        # Solo correos cuyo asunto sea exactamente "Correo SEC"
        status, messages = mail.search(None, '(UNSEEN SUBJECT "Correo SEC")')
        if status != "OK":
            print("⚠️ No se pudo buscar correos.")
            return

        for num in messages[0].split():
            status, data = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(data[0][1])
            msg_id = msg.get("Message-ID", num.decode())

            if msg_id in seen_ids:
                continue

            subject, encoding = decode_header(msg.get("Subject"))[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")

            # Obtener cuerpo de texto plano
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            print(f"\n📧 Correo SEC detectado: {subject}")
            print(f"ID: {msg_id}")

            # Buscar link al PDF
            link = extract_pdf_link(body)
            if not link:
                print("⚠️ No se encontró ningún link PDF en el cuerpo.")
                new_seen.add(msg_id)
                continue

            print(f"🔗 Link PDF encontrado: {link}")

            try:
                # Descargar PDF (solo en memoria)
                response = requests.get(link, timeout=20)
                response.raise_for_status()
                pdf_bytes = io.BytesIO(response.content)

                # Guardar temporalmente en memoria y enviar
                temp_filename = "Carta_SEC.pdf"
                with open(temp_filename, "wb") as temp_file:
                    temp_file.write(pdf_bytes.getbuffer())

                # Enviar correo con tu función original
                send_mail(
                    subjet="Nueva Carta SEC",
                    body=f"Se recibió una nueva carta desde la SEC.\nLink original:\n{link}",
                    files=temp_filename
                )

                # Elimina el temporal para no llenar el disco
                os.remove(temp_filename)

                print("✅ Carta SEC reenviada correctamente.")
            except Exception as e:
                print(f"❌ Error procesando correo SEC: {e}")

            new_seen.add(msg_id)

        # Actualiza lista de vistos
        all_seen = seen_ids.union(new_seen)
        save_seen(all_seen)

# ------------------------------------------------------------
if __name__ == "__main__":
    check_correos_sec()
