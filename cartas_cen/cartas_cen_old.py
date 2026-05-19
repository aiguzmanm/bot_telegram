"""
Script autocontenido para extraer cartas CEN desde el sitio del Coordinador.
Procesa página por página, extrae campos y texto del PDF, guarda en JSON sin enviar correos.

Campos guardados: Correlativo, Tipo Documento, Fecha, Empresa(s), Remitente,
Materia Macro, Referencia, id_show, Grupo_Enel, Empresas_detalle (string con comas), Texto.

Pausable y reanudable usando cartas_progress.json.
"""

import os
import sys
import re
import html
import json
import time
import tempfile
from datetime import datetime
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional, Tuple

import requests as rq
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import argparse

# === CONFIGURACIÓN ===
START_PAGE = 1500
END_PAGE = 15000

BASE = "https://cartas.coordinador.cl"
EMPRESAS_GRUPO_ENEL = [
    "Enel Generación Chile S.A.",
    "Geotérmica del Norte S.A.",
    "Enel Green Power Chile S.A.",
    "Empresa Eléctrica Pehuenche S.A."
]

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS_DIR = os.path.join(PROJECT_ROOT, 'datos', 'links')
os.makedirs(DATOS_DIR, exist_ok=True)

OUTPUT_JSON = os.path.join(DATOS_DIR, 'cartas_procesadas.json')
PROGRESS_JSON = os.path.join(DATOS_DIR, 'cartas_progress.json')

# Patrones regex
ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
TD_RE = re.compile(r"<td\b[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
SHOW_RE = re.compile(r'href="/show/([a-f0-9]{24})"[^>]*>([^<]+)</a>', re.IGNORECASE | re.DOTALL)
DL_RE = re.compile(r'href="/download_saved_file/([a-f0-9]{24})"', re.IGNORECASE)
EMP_MODAL_RE = re.compile(r'href="/get_metadata_from_correo/([a-f0-9]+)/"', re.IGNORECASE)
MODAL_BODY_RE = re.compile(r'<div[^>]*class="modal-body"[^>]*>(.*?)</div>', re.IGNORECASE | re.DOTALL)
DATE_RE = re.compile(r'(\d{2}/\d{2}/\d{4})')

_empresas_cache: Dict[str, Tuple[str, str]] = {}

RETRY_STRATEGY = Retry(
    total=5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"],
    backoff_factor=1,
    raise_on_status=False,
)
SESSION = rq.Session()
SESSION.mount("https://", HTTPAdapter(max_retries=RETRY_STRATEGY))
SESSION.mount("http://", HTTPAdapter(max_retries=RETRY_STRATEGY))
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Accept-Language': 'es-CL,es;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
})
MAX_PAGE_ATTEMPTS = 3
RETRY_SLEEP_SECONDS = 3
MAX_PDF_PAGES = 5


def request_get(url: str, timeout: int = 60, **kwargs) -> rq.Response:
    return SESSION.get(url, timeout=timeout, **kwargs)


# ---------- UTILIDADES ----------
def strip_tags(s: str) -> str:
    """Elimina etiquetas HTML, convierte entidades y normaliza espacios."""
    s = re.sub(r"<\s*br\s*/?>", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return " ".join(s.split())


def to_abs(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    if path.startswith("http"):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return BASE + path


def parse_iso_date_ddmmyyyy(s: str) -> str:
    m = DATE_RE.search(s)
    if not m:
        return strip_tags(s)
    ddmmyyyy = m.group(1)
    try:
        d = datetime.strptime(ddmmyyyy, "%d/%m/%Y").date()
        return d.isoformat()
    except Exception:
        return ddmmyyyy


def decode_best(resp: rq.Response) -> str:
    """Decodificación robusta."""
    raw = resp.content
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="replace")
    if "Ã" in text or "Â" in text:
        try:
            text = text.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            pass
    if not text.strip():
        resp.encoding = resp.apparent_encoding or "utf-8"
        text = resp.text
    return text


def _extract_empresas_code(val: str) -> str:
    """Extrae hex code de URL /get_metadata_from_correo/<hex>/ o devuelve el texto."""
    if not val:
        return ""
    val = str(val).strip()
    m = re.search(r"/get_metadata_from_correo/([a-f0-9]+)/", val, flags=re.IGNORECASE)
    return m.group(1) if m else val


def _fetch_empresas_detalle(hex_code: str, limite: int = 10) -> Tuple[str, str]:
    """
    Consulta /get_metadata_from_correo/<hex>/ y extrae empresas.
    
    Returns: (empresas_detalle_str, grupo_enel_str)
      - empresas_detalle_str: Empresas separadas por comas (string)
      - grupo_enel_str: "Sí" o "No"
    """
    if not hex_code or hex_code == "":
        return "Sin información", "No"

    if hex_code in _empresas_cache:
        return _empresas_cache[hex_code]

    url = f"{BASE}/get_metadata_from_correo/{hex_code}/"

    try:
        resp = request_get(url, timeout=40)
        resp.raise_for_status()

        html_text = decode_best(resp)

        empresas = []
        for match in re.finditer(r'<li[^>]*>(.*?)</li>', html_text, re.IGNORECASE | re.DOTALL):
            texto = strip_tags(match.group(1))
            if texto and texto.lower() != 'cerrar':
                empresas.append(texto)

        if not empresas:
            resultado = ("Sin información", "No")
        else:
            empresas_enel = []
            empresas_otras = []

            for empresa in empresas:
                es_enel = False
                for empresa_grupo in EMPRESAS_GRUPO_ENEL:
                    if empresa_grupo.lower() in empresa.lower() or empresa.lower() in empresa_grupo.lower():
                        es_enel = True
                        if empresa not in empresas_enel:
                            empresas_enel.append(empresa)
                        break

                if not es_enel:
                    empresas_otras.append(empresa)

            grupo_enel = "Sí" if empresas_enel else "No"

            partes = []
            if len(empresas_otras) >= limite:
                partes.append("Varias Empresas")
            elif empresas_otras:
                partes.extend(empresas_otras)

            if empresas_enel:
                partes.extend(empresas_enel)

            if not partes:
                partes = empresas_enel if empresas_enel else ["Sin información"]

            texto_empresas = ", ".join(partes)
            resultado = (texto_empresas, grupo_enel)

        _empresas_cache[hex_code] = resultado
        return resultado

    except Exception as e:
        resultado = (f"Error: {str(e)[:50]}", "No")
        _empresas_cache[hex_code] = resultado
        return resultado


def _download_and_extract_text(url: str) -> Optional[str]:
    """Descarga PDF y extrae texto (primeras 5 páginas)."""
    if not url:
        return None

    try:
        resp = request_get(url, timeout=120)
        resp.raise_for_status()

        content = resp.content

        if not content.startswith(b"%PDF-"):
            return None

        # Guardar en temp
        tmp_dir = tempfile.mkdtemp(prefix="cartas_cen_")
        tmp_file = os.path.join(tmp_dir, "carta.pdf")

        with open(tmp_file, "wb") as f:
            f.write(content)

        # Extraer texto
        try:
            import fitz
            with fitz.open(tmp_file) as doc:
                text_pages = []
                for page in doc[:5]:
                    text_pages.append(page.get_text())
                texto = "\n".join(text_pages).strip()
                
                if not texto:
                    texto = "[El PDF parece ser una imagen escaneada sin texto seleccionable]"
                elif len(texto) > 25000:
                    texto = texto[:25000] + "\n\n... [TEXTO TRUNCADO POR LONGITUD] ..."
                
                return texto
        except Exception as e:
            return f"[Error extrayendo texto: {e}]"
        finally:
            # Limpiar
            try:
                os.remove(tmp_file)
                os.rmdir(tmp_dir)
            except Exception:
                pass

    except Exception:
        return None


def parse_page_cartas(html_text: str) -> List[Dict]:
    """Parsea una página HTML y devuelve lista de cartas."""
    rows: List[Dict] = []
    for row_html in ROW_RE.findall(html_text):
        if "<th" in row_html.lower():
            continue
        tds = TD_RE.findall(row_html)
        if len(tds) < 9:
            continue

        id_show = None
        correlativo = ""
        m = SHOW_RE.search(tds[0])
        if m:
            id_show, correlativo_txt = m.groups()
            correlativo = correlativo_txt.strip()
        else:
            correlativo = strip_tags(tds[0])

        td1_text = strip_tags(tds[1]).upper()
        es_confidencial = "CONFIDENCIAL" in td1_text
        doc_url = None
        if not es_confidencial:
            m = DL_RE.search(tds[1])
            doc_url = to_abs(f"/download_saved_file/{m.group(1)}") if m else None

        tipo_doc = strip_tags(tds[2])
        fecha_iso = parse_iso_date_ddmmyyyy(tds[3])

        m = EMP_MODAL_RE.search(tds[4])
        empresas_raw = to_abs(f"/get_metadata_from_correo/{m.group(1)}/") if m else strip_tags(tds[4])

        remitente = strip_tags(tds[5])
        materia_macro = strip_tags(tds[6])
        referencia_raw = strip_tags(tds[8])

        m = MODAL_BODY_RE.search(tds[8])
        if m:
            referencia = strip_tags(m.group(1))
        else:
            referencia = referencia_raw

        materia_micro = strip_tags(tds[7]) if len(tds) > 7 else ""

        rows.append({
            "Correlativo": correlativo,
            "Tipo Documento": tipo_doc,
            "Fecha": fecha_iso,
            "Empresa(s)": empresas_raw,
            "Materia Micro": materia_micro,
            "Remitente": remitente,
            "Materia Macro": materia_macro,
            "Referencia": referencia,
            "id_show": id_show,
            "doc_url": doc_url,
            "es_confidencial": es_confidencial,
        })

    return rows


def load_processed_ids() -> set:
    """Carga los id_show ya procesados."""
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                return set(item.get('id_show') for item in data if item.get('id_show'))
        except Exception:
            pass
    return set()


def save_processed_carta(carta: Dict) -> None:
    """Guarda una carta nueva en el JSON (appends)."""
    # Cargar existentes
    existentes = []
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
                existentes = json.load(f)
        except Exception:
            existentes = []

    if not isinstance(existentes, list):
        existentes = []

    # Añadir nueva
    existentes.append(carta)

    # Guardar
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(existentes, f, ensure_ascii=False, indent=2)


def build_urls(start: int = 1, end: int = 10000) -> List[Tuple[int, str]]:
    """Construye lista de (page_number, url)."""
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

    if start <= 1:
        urls.append((1, f"{BASE}/?{urlencode(common_params)}"))

    first_search = max(2, start)
    for page in range(first_search, end + 1):
        params = common_params.copy()
        params["page"] = page
        urls.append((page, f"{BASE}/search?{urlencode(params)}"))

    return urls


def load_progress() -> Optional[int]:
    """Carga la página de último éxito desde cartas_progress.json."""
    if os.path.exists(PROGRESS_JSON):
        try:
            with open(PROGRESS_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
            last = data.get('last_successful_page')
            if isinstance(last, int):
                return last
        except Exception:
            pass
    return None


def save_progress(page: int, success: bool = False, error: Optional[str] = None) -> None:
    """Guarda progreso en cartas_progress.json."""
    last_success = load_progress()
    if success:
        data = {
            'last_successful_page': page,
            'failed_page': None,
            'error': None,
            'timestamp': int(time.time()),
        }
    else:
        data = {
            'last_successful_page': last_success,
            'failed_page': page,
            'error': error,
            'timestamp': int(time.time()),
        }
    with open(PROGRESS_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def main():
    # Intentar reanudar
    start = START_PAGE
    last_success = load_progress()
    if last_success is not None:
        start = max(1, last_success - 100)
        print(f"Reanudando desde página {start} (último éxito: {last_success})")

    urls = build_urls(start=start, end=END_PAGE)
    processed_ids = load_processed_ids()

    for page, url in urls:
        print(f"Página {page}: consultando {url}")
        page_error = None

        for attempt in range(1, MAX_PAGE_ATTEMPTS + 1):
            try:
                resp = request_get(url, timeout=60)
                resp.raise_for_status()
                html_text = decode_best(resp)

                cartas_raw = parse_page_cartas(html_text)
                nuevas_count = 0

                for carta_raw in cartas_raw:
                    id_show = carta_raw.get('id_show')

                    # Saltar si ya procesada
                    if id_show and id_show in processed_ids:
                        continue

                    # Extraer empresas_detalle
                    empresas_code = _extract_empresas_code(carta_raw.get('Empresa(s)', ''))
                    empresas_detalle_str, grupo_enel_str = _fetch_empresas_detalle(empresas_code)

                    # Extraer texto del PDF
                    doc_url = carta_raw.get('doc_url')
                    es_conf = carta_raw.get('es_confidencial', False)
                    
                    if es_conf:
                        texto = "[Carta marcada como CONFIDENCIAL en el sitio del CEN]"
                    else:
                        texto = _download_and_extract_text(doc_url)
                        if not texto:
                            texto = "[No se pudo descargar o extraer texto del PDF]"

                    # Armar objeto final (sin doc_url ni es_confidencial)
                    carta_final = {
                        "Correlativo": carta_raw.get('Correlativo'),
                        "Tipo Documento": carta_raw.get('Tipo Documento'),
                        "Fecha": carta_raw.get('Fecha'),
                        "Empresa(s)": carta_raw.get('Empresa(s)'),
                        "Materia Micro": carta_raw.get('Materia Micro'),
                        "Remitente": carta_raw.get('Remitente'),
                        "Materia Macro": carta_raw.get('Materia Macro'),
                        "Referencia": carta_raw.get('Referencia'),
                        "id_show": id_show,
                        "Grupo_Enel": grupo_enel_str,
                        "Empresas_detalle": empresas_detalle_str,
                        "Texto": texto,
                    }

                    # Guardar
                    save_processed_carta(carta_final)
                    if id_show:
                        processed_ids.add(id_show)

                    nuevas_count += 1

                # Guardar progreso
                save_progress(page, success=True)

                print(f"Página {page}: cartas={len(cartas_raw)} | nuevas procesadas={nuevas_count}")
                time.sleep(0.5)
                page_error = None
                break

            except rq.exceptions.HTTPError as e:
                code = e.response.status_code if hasattr(e, 'response') else '?'
                page_error = f"HTTPError {code}"
                print(f"Página {page}: {page_error} -> {e}")
            except Exception as e:
                page_error = str(e)
                print(f"Página {page}: Error -> {e}")

            if attempt < MAX_PAGE_ATTEMPTS:
                print(f"Página {page}: reintentando ({attempt}/{MAX_PAGE_ATTEMPTS}) en {RETRY_SLEEP_SECONDS} s...")
                time.sleep(RETRY_SLEEP_SECONDS)
            else:
                print(f"Página {page}: salto después de {MAX_PAGE_ATTEMPTS} intentos.")
                save_progress(page, success=False, error=page_error)

    print(f"Proceso completo.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper de cartas CEN (pausable y reanudable)")
    parser.add_argument("--reset", action="store_true", help="Borrar archivos de salida y progreso antes de iniciar (reinicia desde START_PAGE)")
    parser.add_argument("--end-page", type=int, default=None, help="(Opcional) reemplaza END_PAGE para pruebas rápidas")
    parser.add_argument("--test", action="store_true", help="Procesar sólo la página de inicio para prueba rápida")
    args = parser.parse_args()

    if args.reset:
        for p in (OUTPUT_JSON, PROGRESS_JSON):
            try:
                if os.path.exists(p):
                    os.remove(p)
                    print(f"Borrado: {p}")
            except Exception:
                pass
        print("Reiniciando desde START_PAGE (archivos borrados).")

    if args.end_page is not None:
        END_PAGE = args.end_page

    if args.test:
        END_PAGE = START_PAGE

    main()
