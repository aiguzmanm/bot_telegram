import imaplib
import email
from email.header import decode_header
import os
import sys
import configparser
import re
import io
import requests
import pickle
import tempfile
from urllib.parse import urljoin

# ------------------------------------------------------------
# Estructura de proyecto (idéntica a tus otros scripts)
# ------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

from modules.email_utils import send_mail  # 👈 tu función original

# ------------------------------------------------------------
# Configuración
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

def extract_pdf_link(body):
    """Busca un link PDF válido en el cuerpo del correo"""
    match = re.search(r"https://wlhttp\.sec\.cl/timesM/global/imgPDF\.jsp\?[^ \n\r]+", body)
    if not match:
        return None
    link = match.group(0).strip()
    return link.replace("\r", "").replace("\n", "")

# ------------------------------------------------------------
# Descarga de PDF con cookies y referer
# ------------------------------------------------------------
def get_pdf_bytes_from_sec(link: str) -> bytes:
    tmp_dir = os.path.join(project_root, 'datos', 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    cookies_file = os.path.join(tmp_dir, 'sec_cookies.txt')

    session = requests.Session()
    # Cargar cookies previas si existen
    if os.path.exists(cookies_file):
        try:
            with open(cookies_file, "rb") as f:
                session.cookies.update(pickle.load(f))
        except Exception:
            pass

    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}

    # 1️⃣ Primer GET
    r1 = session.get(link.strip(), headers=headers, timeout=20)
    r1.raise_for_status()

    # Guardar cookies nuevas
    try:
        with open(cookies_file, "wb") as f:
            pickle.dump(session.cookies, f)
    except Exception:
        pass

    content = r1.content

# 2️⃣ Seguir redirección (../MuestraArchivo)
if b"window.location.href" in content:
    m = re.search(r'window\.location\.href\s*=\s*[\'"]([^\'"]+)[\'"]', r1.text)
    if m:
        next_url = urljoin(link, m.group(1))
        headers["Referer"] = link
        print(f"  → URL redirección: {next_url}")
        print(f"  → Cookies activas: {dict(session.cookies)}")
        print(f"  → Respuesta r1 completa:\n{r1.text[:1000]}")
        r2 = session.get(next_url, headers=headers, timeout=20)
        print(f"  → Status r2: {r2.status_code}")
        r2.raise_for_status()
        content = r2.content

    # 3️⃣ Validar PDF
    if not content.startswith(b"%PDF"):
        raise ValueError("El contenido recibido no es un PDF válido.")
    return content

# ------------------------------------------------------------
# Revisa bandeja Gmail y procesa correos "Correo SEC"
# ------------------------------------------------------------
def check_correos_sec():
    seen_ids = load_seen()
    new_seen = set()

    with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")

        # Solo correos nuevos con asunto "Correo SEC"
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

            # Obtener cuerpo del correo
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            print(f"\n📧 Correo detectado: {subject}")
            print(f"ID: {msg_id}")

            # Buscar link al PDF
            link = extract_pdf_link(body)
            if not link:
                print("⚠️ No se encontró link PDF en el cuerpo.")
                new_seen.add(msg_id)
                continue

            print(f"🔗 Link PDF encontrado: {link}")

            try:
                # Descargar PDF (bytes en memoria)
                pdf_bytes = get_pdf_bytes_from_sec(link)

                # Guardar temporalmente para enviarlo
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(pdf_bytes)
                    temp_filename = tmp.name

                # Enviar correo usando tu función original
                send_mail(
                    subjet="Nueva Carta SEC",
                    body=f"Se recibió una nueva carta desde la SEC.\nLink original:\n{link}",
                    files=temp_filename
                )

                os.remove(temp_filename)
                print("✅ Carta SEC reenviada correctamente.")
            except Exception as e:
                print(f"❌ Error procesando correo SEC: {e}")

            new_seen.add(msg_id)

        # Actualizar registros
        all_seen = seen_ids.union(new_seen)
        save_seen(all_seen)

# ------------------------------------------------------------
if __name__ == "__main__":
    check_correos_sec()
