import requests
import re
import os
import pickle
from urllib.parse import urljoin

# ----------------------------------------------------
# Configuración de paths
# ----------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
tmp_dir = os.path.join(project_root, 'datos', 'tmp')
os.makedirs(tmp_dir, exist_ok=True)
cookies_file = os.path.join(tmp_dir, 'sec_cookies.txt')

# ----------------------------------------------------
# URL fija de prueba
# ----------------------------------------------------
link = "https://wlhttp.sec.cl/timesM/global/imgPDF.jsp?pa=4065353&pd=4746884&pc=2348036"
out_file = os.path.join(script_dir, "Carta_SEC.pdf")

print(f"🔍 Descargando PDF SEC:\n{link}\n")

# ----------------------------------------------------
# Crear sesión y cargar cookies previas si existen
# ----------------------------------------------------
session = requests.Session()
if os.path.exists(cookies_file):
    try:
        with open(cookies_file, "rb") as f:
            session.cookies.update(pickle.load(f))
        print("🍪 Cookies previas cargadas.")
    except Exception as e:
        print(f"⚠️ No se pudieron cargar cookies previas: {e}")

headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}

# 1️⃣ Primer request
r1 = session.get(link, headers=headers, timeout=20)
r1.raise_for_status()

# Guardar cookies nuevas
try:
    with open(cookies_file, "wb") as f:
        pickle.dump(session.cookies, f)
    print(f"💾 Cookies guardadas en {cookies_file}")
except Exception:
    pass

# 2️⃣ Revisar redirección
content = r1.content
if b"window.location.href" in content:
    match = re.search(r'window\.location\.href\s*=\s*[\'"]([^\'"]+)[\'"]', r1.text)
    if match:
        redirect_path = match.group(1)
        next_url = urljoin(link, redirect_path)
        print(f"➡️ Redirección detectada: {redirect_path}")
        print(f"🔗 URL resuelta: {next_url}")

        headers["Referer"] = link
        r2 = session.get(next_url, headers=headers, timeout=20)
        r2.raise_for_status()
        content = r2.content

# 3️⃣ Validar y guardar PDF
if content.startswith(b"%PDF"):
    with open(out_file, "wb") as f:
        f.write(content)
    print(f"✅ PDF descargado correctamente en:\n{out_file}")
    print(f"📏 Tamaño: {len(content)} bytes")
else:
    print("❌ El contenido recibido no parece un PDF:")
    print(content[:300])


