import os
from datetime import datetime
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from cartas_cen_utils import run_once, cartas_nuevas

# === Parámetros de ejecución ===
paginas = 20  # cuántas páginas recorrer

# Project root (un nivel arriba de este archivo)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

# CSV en project_root/datos/links/cartas.csv
CSV_DIR = os.path.join(PROJECT_ROOT, 'datos', 'links')
os.makedirs(CSV_DIR, exist_ok=True)
CSV_PATH = os.path.join(CSV_DIR, 'cartas.csv')

BASE = "https://cartas.coordinador.cl"

def build_urls(paginas: int = 10):
    """
    Construye las URLs del día actual usando la nueva lógica del sitio:
    - página 1: https://cartas.coordinador.cl/?...
    - página 2+: https://cartas.coordinador.cl/search?...&page=N

    Usa zona horaria de Chile para evitar desfases cerca de medianoche.
    """
    hoy = datetime.now(ZoneInfo("America/Santiago"))
    fecha = hoy.strftime("%d/%m/%Y")

    periodo_reporte = f"{fecha} 00:00:00 - {fecha} 23:59:59"

    common_params = {
        "q": "",
        "periodo_reporte": periodo_reporte,
        "model_type": "todos",
        "search_type": "basic",
    }

    urls = []

    # Página 1
    urls.append(f"{BASE}/?{urlencode(common_params)}")

    # Página 2 en adelante
    for page in range(2, paginas + 1):
        params = common_params.copy()
        params["page"] = page
        urls.append(f"{BASE}/search?{urlencode(params)}")

    return urls

def main():
    urls = build_urls(paginas=paginas)
    run_once(urls=urls, csv_path=CSV_PATH, on_new=cartas_nuevas)

if __name__ == "__main__":
    main()
