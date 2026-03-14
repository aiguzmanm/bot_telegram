import os
import sys
import re
import html
import tempfile
from datetime import datetime
from typing import List, Dict, Optional, Callable

import requests as rq
import pandas as pd

# === Añadir el directorio raíz del proyecto al sys.path (para modules/*) ===
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Ahora podemos importar utilidades del proyecto principal
# (asegúrate que modules/email_utils.py exista y contenga send_mail(subjet, body, files))
from modules.email_utils import send_mail  # noqa: E402

# ---------- Constantes y patrones ----------
BASE = "https://cartas.coordinador.cl"

ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
TD_RE  = re.compile(r"<td\b[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)

# Correlativo + ID show: <a href="/show/<24hex>">DE05991-25</a>
SHOW_RE = re.compile(r'href="/show/([a-f0-9]{24})"[^>]*>([^<]+)</a>', re.IGNORECASE | re.DOTALL)

# Documento descargable: href="/download_saved_file/<24hex>"
DL_RE = re.compile(r'href="/download_saved_file/([a-f0-9]{24})"', re.IGNORECASE)

# Empresa(s): link a modal remoto
EMP_MODAL_RE = re.compile(r'href="/get_metadata_from_correo/([a-f0-9]+)/"', re.IGNORECASE)

# Referencia (texto extendido dentro de modal en el mismo TD)
MODAL_BODY_RE = re.compile(r'<div[^>]*class="modal-body"[^>]*>(.*?)</div>', re.IGNORECASE | re.DOTALL)

# Fecha dd/mm/yyyy (en TD 3)
DATE_RE = re.compile(r'(\d{2}/\d{2}/\d{4})')

COLS = [
    "Correlativo",
    "Documento",
    "Tipo Documento",
    "Fecha",
    "Empresa(s)",
    "Remitente",
    "Materia Macro",
    "Materia Micro",
    "Referencia",
    "link",     # URL absoluta /show/<id>
    "id_show",  # <id> de /show/<id> (24 hex)
]

# ---------- Utilidades de texto / encoding ----------
def strip_tags(s: str) -> str:
    """Elimina etiquetas HTML, convierte entidades (&oacute;) y normaliza espacios."""
    s = re.sub(r"<\s*br\s*/?>", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)  # &oacute; → ó; &ntilde; → ñ; etc.
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
    """
    Decodificación robusta para evitar mojibake:
    - intentar utf-8; si falla, latin-1;
    - si aparecen 'Ã'/'Â', reintenta reparando.
    """
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
    """
    Si Empresa(s) es un link tipo:
      https://cartas.coordinador.cl/get_metadata_from_correo/<hex>/
    extrae y devuelve solo <hex>. Si no es link, devuelve el texto tal cual.
    """
    if not val:
        return ""
    val = str(val).strip()
    m = re.search(r"/get_metadata_from_correo/([a-f0-9]+)/", val, flags=re.IGNORECASE)
    return m.group(1) if m else val

def _build_download_url_from_id(id_show: Optional[str]) -> Optional[str]:
    if not id_show:
        return None
    return f"{BASE}/download_saved_file/{id_show}"

# ---------- Parser principal ----------
def parse_df_cartas(html_text: str) -> pd.DataFrame:
    rows: List[Dict] = []
    for row_html in ROW_RE.findall(html_text):
        if "<th" in row_html.lower():
            continue
        tds = TD_RE.findall(row_html)
        if len(tds) < 9:
            continue

        id_show = None
        link = None
        m = SHOW_RE.search(tds[0])
        if m:
            id_show, correlativo_txt = m.groups()
            correlativo = correlativo_txt.strip()
            link = f"{BASE}/show/{id_show}"
        else:
            correlativo = strip_tags(tds[0])

        td1_text = strip_tags(tds[1]).upper()
        if "CONFIDENCIAL" in td1_text:
            documento = "CONFIDENCIAL"
        else:
            m = DL_RE.search(tds[1])
            documento = to_abs(f"/download_saved_file/{m.group(1)}") if m else None

        tipo_doc = strip_tags(tds[2])
        fecha_iso = parse_iso_date_ddmmyyyy(tds[3])

        m = EMP_MODAL_RE.search(tds[4])
        empresas = to_abs(f"/get_metadata_from_correo/{m.group(1)}/") if m else (strip_tags(tds[4]) or None)

        remitente = strip_tags(tds[5])
        materia_macro = strip_tags(tds[6])
        materia_micro = strip_tags(tds[7])

        m = MODAL_BODY_RE.search(tds[8])
        referencia = strip_tags(m.group(1)) if m else strip_tags(tds[8])

        rows.append({
            "Correlativo": correlativo,
            "Documento": documento,
            "Tipo Documento": tipo_doc,
            "Fecha": fecha_iso,
            "Empresa(s)": empresas,
            "Remitente": remitente,
            "Materia Macro": materia_macro,
            "Materia Micro": materia_micro,
            "Referencia": referencia,
            "link": link,
            "id_show": id_show,
        })
    return pd.DataFrame(rows, columns=COLS)

# ---------- CSV histórico ----------
def load_hist(path: str) -> pd.DataFrame:
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
            for c in COLS:
                if c not in df.columns:
                    df[c] = ""
            return df[COLS]
        except Exception:
            pass
    return pd.DataFrame(columns=COLS)

def _add_uniq_key(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clave única:
    - usa 'id_show' si existe,
    - si no, usa 'Tipo Documento|Correlativo'.
    """
    df = df.copy()
    fallback = (
        df.get("Tipo Documento", "").fillna("") + "|" + df.get("Correlativo", "").fillna("")
    ).astype(str)
    key = df.get("id_show")
    if key is None:
        df["_uniq_key"] = fallback
    else:
        key = key.fillna("")
        df["_uniq_key"] = key.where(key != "", fallback)
    return df

def save_hist(df: pd.DataFrame, path: str) -> None:
    df_tmp = _add_uniq_key(df)
    df_tmp = df_tmp.drop_duplicates(subset=["_uniq_key"], keep="last").drop(columns=["_uniq_key"])
    try:
        df_tmp["_Fecha_"] = pd.to_datetime(df_tmp["Fecha"], errors="coerce")
        df_tmp = df_tmp.sort_values(by=["_Fecha_", "Correlativo"], ascending=[False, False]).drop(columns=["_Fecha_"])
    except Exception:
        pass
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df_tmp.to_csv(path, index=False, encoding="utf-8-sig")

# ---------- Email helper ----------
def _build_email_body(row: pd.Series) -> str:
    """
    Arma el cuerpo del correo:
      - NO incluye 'Documento' ni 'link'
      - En 'Empresa(s)' solo envia el ID hex (si viene como URL)
    """
    fields_to_skip = {"Documento", "link"}
    lines = []
    for col in COLS:
        if col in fields_to_skip:
            continue
        val = row.get(col, "")
        if pd.isna(val):
            val = ""
        if col == "Empresa(s)":
            val = _extract_empresas_code(val)
        lines.append(f"{col}: {val}")
    return "\r\n".join(lines)

def _download_attachment(url: str, suggested_name: str) -> Optional[str]:
    """
    Descarga el archivo solo si es un PDF real.
    Si la respuesta es HTML u otro contenido, devuelve None.
    """
    if not url:
        return None

    try:
        resp = rq.get(url, timeout=120)
        resp.raise_for_status()

        content = resp.content

        # Validación mínima: un PDF real normalmente empieza con %PDF-
        if not content.startswith(b"%PDF-"):
            return None

        base_name = suggested_name if suggested_name else "carta"
        if not base_name.lower().endswith(".pdf"):
            base_name = f"{base_name}.pdf"

        tmp_dir = tempfile.mkdtemp(prefix="cartas_cen_")
        file_path = os.path.join(tmp_dir, base_name)

        with open(file_path, "wb") as f:
            f.write(content)

        return file_path

    except Exception:
        return None

# ---------- Callback por defecto ----------
def cartas_nuevas(row: pd.Series) -> None:
    """
    Nueva carta:
      - Asunto: 'Nueva carta CEN'
      - Body: sin 'Documento' ni 'link'
      - Adjuntos:
          * Si NO es confidencial y hay PDF válido: lo descarga y adjunta.
          * Si es confidencial, NO intenta descargar nada y adjunta TXT de control.
          * Si no es confidencial pero falla la descarga/validación, adjunta TXT de control.
      - Limpia temporales.
    """
    subject = "Nueva carta CEN"
    body = _build_email_body(row)

    doc_url = row.get("Documento", None)
    id_show = row.get("id_show", None)

    es_confidencial = isinstance(doc_url, str) and doc_url.upper() == "CONFIDENCIAL"

    attach_path = None
    tmp_dir = None

    try:
        # 1) Intentar bajar PDF SOLO si no viene marcada como confidencial
        if (not es_confidencial) and isinstance(doc_url, str) and doc_url:
            suggested = str(row.get("Correlativo", "carta")).replace("/", "-").replace("\\", "-")
            attach_path = _download_attachment(doc_url, suggested_name=suggested)

        # 2) Si no hay PDF, crear TXT de control
        if not attach_path:
            tmp_dir = tempfile.mkdtemp(prefix="cartas_cen_")
            safe_name = str(row.get("Correlativo", "carta")).replace("/", "-").replace("\\", "-") or "carta"
            txt_path = os.path.join(tmp_dir, f"{safe_name}_control.txt")

            if es_confidencial:
                motivo = "Carta marcada como CONFIDENCIAL en el sitio del CEN. No se intentó descargar PDF."
                url_intentada = ""
            else:
                motivo = "No se pudo descargar un PDF válido."
                url_intentada = str(doc_url or "")

            control_text = (
                "TIPO_ANEXO=CONTROL\r\n"
                "PDF_VALIDO=NO\r\n"
                f"ES_CONFIDENCIAL={'SI' if es_confidencial else 'NO'}\r\n"
                f"MOTIVO={motivo}\r\n"
                f"URL_INTENTADA={url_intentada}\r\n"
                f"ID_SHOW={id_show}\r\n"
                f"CORRELATIVO={row.get('Correlativo', '')}\r\n"
            )

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(control_text)

            attach_path = txt_path

        # 3) Enviar correo
        send_mail(subject, body, attach_path)

    finally:
        # 4) Limpiar archivo y carpeta temporal si aplica
        if attach_path and os.path.exists(attach_path):
            try:
                os.remove(attach_path)
            except Exception:
                pass
        if tmp_dir and os.path.isdir(tmp_dir):
            try:
                os.rmdir(tmp_dir)
            except OSError:
                pass

# ---------- Ejecución de una pasada ----------
def run_once(
    urls: List[str],
    csv_path: str,
    on_new: Optional[Callable[[pd.Series], None]] = None,
) -> pd.DataFrame:
    if on_new is None:
        on_new = cartas_nuevas

    frames = []
    for url in urls:
        resp = rq.get(url, timeout=60)
        html_text = decode_best(resp)
        frames.append(parse_df_cartas(html_text))

    df_cartas = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=COLS)

    # Dedup dentro de esta corrida por clave única
    df_cartas_tmp = _add_uniq_key(df_cartas)
    df_cartas = df_cartas_tmp.drop_duplicates(subset=["_uniq_key"], keep="last").drop(columns=["_uniq_key"])


    # Comparar con histórico
    df_hist = load_hist(csv_path)
    df_hist_tmp = _add_uniq_key(df_hist)
    seen_keys = set(df_hist_tmp["_uniq_key"].astype(str))

    df_cartas_cmp = _add_uniq_key(df_cartas)
    df_nuevas = df_cartas_cmp[~df_cartas_cmp["_uniq_key"].astype(str).isin(seen_keys)].drop(columns=["_uniq_key"])

    # Disparar callback por cada nueva
    for _, fila in df_nuevas.iterrows():
        on_new(fila)

    # Actualizar/crear CSV
    if not df_nuevas.empty:
        save_hist(pd.concat([df_hist, df_nuevas], ignore_index=True), csv_path)
    elif not os.path.exists(csv_path) and not df_cartas.empty:
        save_hist(df_cartas, csv_path)

    print(f"Cartas encontradas: {len(df_cartas)} | Nuevas: {len(df_nuevas)}")
    return df_cartas