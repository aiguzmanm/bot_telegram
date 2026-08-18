import imaplib
import email
from email.header import decode_header
import os
import sys
import configparser
import re
import io
import requests
import tempfile
import traceback
from urllib.parse import urljoin

def log(msg):
    print(msg)

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
    # Sesión nueva y limpia por descarga — NO persistir cookies entre
    # ejecuciones del script. Una TSANTIAGO_JSESSIONID vieja/expirada
    # mezclada con la sesión nueva es lo que produce el 500 en MuestraArchivo.
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.9",
    }

    # 1️⃣ Primer GET
    r1 = session.get(link.strip(), headers=headers, timeout=20)
    r1.raise_for_status()

    # La SEC envía la cookie de sesión con domain= vacío (malformado), lo que
    # hace que requests la descarte y el 2º GET falle con 500. La extraemos
    # del Set-Cookie crudo y la reponemos con el dominio correcto.
    if "TSANTIAGO_JSESSIONID" not in session.cookies:
        set_cookie = r1.headers.get("Set-Cookie", "")
        m_cookie = re.search(r"TSANTIAGO_JSESSIONID=([^;]+)", set_cookie)
        if m_cookie:
            session.cookies.set(
                "TSANTIAGO_JSESSIONID",
                m_cookie.group(1),
                domain="wlhttp.sec.cl",
                path="/",
            )

    content = r1.content

    # 2️⃣ Seguir redirección (../MuestraArchivo)
    if b"window.location.href" in content:
        m = re.search(r'window\.location\.href\s*=\s*[\'"]([^\'"]+)[\'"]', r1.text)
        if m:
            next_url = urljoin(link, m.group(1))
            headers2 = dict(headers)
            headers2["Referer"] = link
            r2 = session.get(next_url, headers=headers2, timeout=20)
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
        try:
            mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
            mail.select("inbox")
        except Exception:
            log("❌ Falló login/select IMAP:\n" + traceback.format_exc())
            return

        # Solo correos nuevos con asunto "Correo SEC"
        status, messages = mail.search(None, '(UNSEEN SUBJECT "Correo SEC")')
        if status != "OK":
            log("⚠️ No se pudo buscar correos (status != OK).")
            return

        num_encontrados = len(messages[0].split()) if messages and messages[0] else 0
        log(f"🔍 Correos UNSEEN con asunto 'Correo SEC' encontrados: {num_encontrados}")

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

            # Obtener cuerpo del correo (con fallback a text/html)
            body = ""
            html_body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    if ctype == "text/plain" and not body:
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    elif ctype == "text/html" and not html_body:
                        html_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            if not body and html_body:
                # SEC/Gmail puede mandar solo HTML — no descartar el correo por eso
                body = re.sub(r"<[^>]+>", " ", html_body)
                log("ℹ️ Correo sin text/plain, usando fallback de text/html.")

            log(f"\n📧 Correo detectado: {subject}")
            log(f"ID: {msg_id}")

            # Buscar link al PDF
            link = extract_pdf_link(body)
            if not link:
                log("⚠️ No se encontró link PDF en el cuerpo. Body extraído (primeros 300 chars):")
                log(body[:300] if body else "(body vacío)")
                new_seen.add(msg_id)
                continue

            log(f"🔗 Link PDF encontrado: {link}")

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
                log("✅ Carta SEC reenviada correctamente.")
            except Exception:
                log("❌ Error procesando correo SEC:\n" + traceback.format_exc())

            new_seen.add(msg_id)

        # Actualizar registros
        all_seen = seen_ids.union(new_seen)
        save_seen(all_seen)

# ------------------------------------------------------------
if __name__ == "__main__":
    check_correos_sec()