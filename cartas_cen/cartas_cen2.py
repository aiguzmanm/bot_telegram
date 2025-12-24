# cartas_cen2.py
import os
from cartas_cen_utils2 import run_once, cartas_nuevas

# === Parámetros de ejecución ===
paginas = 100  # cuántas páginas recorrer (1 = solo la principal)

# Timeouts (ajusta según realidad del sitio)
CONNECT_TIMEOUT = 15   # segundos para conectar
READ_TIMEOUT = 600     # segundos para leer respuesta (10 min)

# Project root (un nivel arriba de este archivo)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# CSV en project_root/datos/links/cartas.csv
CSV_DIR = os.path.join(PROJECT_ROOT, "datos", "links")
os.makedirs(CSV_DIR, exist_ok=True)
CSV_PATH = os.path.join(CSV_DIR, "cartas.csv")

# URLs autogeneradas
BASE = "https://cartas.coordinador.cl"
URLS = [f"{BASE}/"] + [f"{BASE}/search?page={i}" for i in range(2, paginas + 1)]


def main():
    run_once(
        urls=URLS,
        csv_path=CSV_PATH,
        on_new=cartas_nuevas,
        connect_timeout=CONNECT_TIMEOUT,
        read_timeout=READ_TIMEOUT,
        verbose=True,
    )


if __name__ == "__main__":
    main()
