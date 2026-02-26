# envia_programas_utils.py
import os
import sys
import pandas as pd
import warnings
import zipfile as zp
import shutil
import base64
import datetime as dt
import requests as rq

warnings.filterwarnings('ignore')

# Añadir el directorio raíz del proyecto al sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

from modules.telegram_utils import enviar_mensaje_telegram, enviar_archivo_telegram, enviar_foto_telegram, cargar_config
from modules.graph_utils import generar_grafico_prg
from modules.email_utils import send_mail

API_PRESIGNED = "https://administracion.api.coordinador.cl/programa-operacion/bucket-s3/s3/presigned-url-download"

def reporte_prg(zip_name, file):
    tmp_dir = os.path.join(project_root, 'datos', 'tmp')
    file_dir = os.path.join(tmp_dir, file)

    df_PRG = pd.read_excel(file_dir, sheet_name='PROGRAMA')
    df_PRG = df_PRG.iloc[:, 2:]
    df_PRG.columns = df_PRG.iloc[df_PRG[df_PRG.iloc[:, 0] == 'Hidroeléctricas de Pasada'].index[0]]

    demanda = int(df_PRG.iloc[df_PRG[df_PRG.iloc[:, 0] == 'Generación Total [MWh]'].index[0], -1])
    fv = int(df_PRG.iloc[df_PRG[df_PRG.iloc[:, 0] == 'Solares'].index[0] + 1, -1])
    hp = int(df_PRG.iloc[df_PRG[df_PRG.iloc[:, 0] == 'Hidroeléctricas de Pasada'].index[0] + 1, -1])
    eo = int(df_PRG.iloc[df_PRG[df_PRG.iloc[:, 0] == 'Eólicas'].index[0] + 1, -1])
    ter = int(df_PRG.iloc[df_PRG[df_PRG.iloc[:, 0] == 'Térmicas'].index[0] + 1, -1])
    he = int(df_PRG.iloc[df_PRG[df_PRG.iloc[:, 0] == 'Embalses y Reguladas'].index[0] + 1, -1])
    car = int(df_PRG[df_PRG.iloc[:, 0].str.contains('_CAR', na=False, regex=True)].iloc[:, -1].sum())
    gas = int(df_PRG[df_PRG.iloc[:, 0].str.contains('_GN', na=False, regex=True)].iloc[:, -1].sum())
    diesel = int(df_PRG[df_PRG.iloc[:, 0].str.contains('_DIE', na=False, regex=True)].iloc[:, -1].sum())
    hidro = hp + he

    demanda = "{:,}".format(demanda)
    fv = "{:,}".format(fv)
    hp = "{:,}".format(hp)
    eo = "{:,}".format(eo)
    ter = "{:,}".format(ter)
    he = "{:,}".format(he)
    car = "{:,}".format(car)
    gas = "{:,}".format(gas)
    diesel = "{:,}".format(diesel)
    hidro = "{:,}".format(hidro)

    resu = (
        f"**Nuevo programa publicado:** {zip_name}\n\n"
        f"**Resumen del programa:**\n\n"
        f"Demanda Total: {demanda} MWh\n"
        f"Generación Solar FV: {fv} MWh\n"
        f"Generación Hidroeléctrica de Pasada: {hp} MWh\n"
        f"Generación Eólica: {eo} MWh\n"
        f"Generación Térmica: {ter} MWh\n"
        f"Generación Embalses y Reguladas: {he} MWh\n"
        f"Generación Hidroeléctrica Total: {hidro} MWh\n"
        f"Generación a Carbón: {car} MWh\n"
        f"Generación a Gas Natural: {gas} MWh\n"
        f"Generación a Diesel: {diesel} MWh\n"
    )
    return resu

def limpiar_dir(dir_path):
    if not os.path.isdir(dir_path):
        return
    for nombre in os.listdir(dir_path):
        ruta = os.path.join(dir_path, nombre)
        if os.path.isfile(ruta):
            os.remove(ruta)
        elif os.path.isdir(ruta):
            shutil.rmtree(ruta)

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _b64_key(s3_key: str) -> str:
    return base64.b64encode(s3_key.encode("utf-8")).decode("ascii")

def _get_presigned_url(encoded_key: str, user_key: str) -> str | None:
    params = {"encodedKey": encoded_key, "user_key": user_key}
    headers = {
        "accept": "application/json, text/plain, */*",
        "referer": "https://programa.coordinador.cl/",
        "user-agent": "Mozilla/5.0",
    }
    r = rq.get(API_PRESIGNED, params=params, headers=headers, timeout=30)
    if r.status_code != 200:
        return None
    try:
        data = r.json()
    except Exception:
        return None

    url = data.get("presignedUrlDownload")
    return url if isinstance(url, str) and url.startswith("http") else None

def _read_csv_set(csv_path: str, col: str) -> set:
    try:
        df = pd.read_csv(csv_path)
        if col in df.columns:
            return set(df[col].dropna().astype(str).tolist())
        return set()
    except FileNotFoundError:
        return set()

def _append_csv(csv_path: str, rows: list[dict]) -> None:
    _ensure_dir(os.path.dirname(csv_path))
    try:
        df_old = pd.read_csv(csv_path)
    except FileNotFoundError:
        df_old = pd.DataFrame()

    df_new = pd.DataFrame(rows)
    df = pd.concat([df_old, df_new], ignore_index=True)
    df.to_csv(csv_path, index=False)

def _download_file(url: str, out_path: str) -> None:
    with rq.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)

def _get_user_key() -> str:
    try:
        config = cargar_config()
        return config.get("programa_operacion", "user_key", fallback="").strip()
    except Exception as e:
        print(f"[API] Error leyendo config.ini: {e}")
        return ""

def descargar_PRO_API(ref_date=None):
    """
    PRO por API:
    - Descarga ZIP a datos/tmp
    - Unzip en datos/tmp
    - Procesa PRG/PO (telegram + gráfico + mails PRG/PO)
    - Registra en datos/links/links_PRO_API.csv para no repetir
    """
    fecha_fin = ""
    zip_fin = ""

    if ref_date is None:
        ref_date = dt.datetime.now()

    user_key = _get_user_key()
    if not user_key:
        print("[descargar_PRO_API] Falta programa_operacion.user_key en config.ini")
        return fecha_fin, zip_fin

    tmp_dir = os.path.join(project_root, 'datos', 'tmp')
    limpiar_dir(tmp_dir)

    yyyymmdd = ref_date.strftime("%Y%m%d")
    s3_key = f"PCP/PROGRAMA{yyyymmdd}.zip"
    encoded_key = _b64_key(s3_key)

    links_dir = os.path.abspath(os.path.join(project_root, "datos", "links"))
    csv_path = os.path.join(links_dir, "links_PRO_API.csv")

    existentes = _read_csv_set(csv_path, "s3_key")
    if s3_key in existentes:
        print(f"[descargar_PRO_API] Ya registrado: {s3_key}")
        return fecha_fin, zip_fin

    presigned = _get_presigned_url(encoded_key, user_key)
    if not presigned:
        print(f"[descargar_PRO_API] No disponible (aún): {s3_key}")
        return fecha_fin, zip_fin

    zip_name = os.path.basename(s3_key)
    zip_path = os.path.join(tmp_dir, zip_name)

    try:
        _download_file(presigned, zip_path)
        print(f"[descargar_PRO_API] ZIP descargado: {zip_path}")
    except Exception as e:
        print(f"[descargar_PRO_API] Error descargando {zip_name}: {e}")
        limpiar_dir(tmp_dir)
        return fecha_fin, zip_fin

    try:
        with zp.ZipFile(zip_path, "r") as POzip:
            POzip.extractall(path=tmp_dir)
    except Exception as e:
        print(f"[descargar_PRO_API] Error descomprimiendo {zip_name}: {e}")
        limpiar_dir(tmp_dir)
        return fecha_fin, zip_fin

    try:
        for file in os.listdir(tmp_dir):
            if file.endswith('.xlsx'):
                if file.startswith('PRG'):
                    msj = reporte_prg(zip_name, file)
                    enviar_mensaje_telegram(msj)

                    file_dir = os.path.join(tmp_dir, file)
                    prg_dir = os.path.join(project_root, 'datos', 'prg', file)
                    plot_dir = os.path.join(project_root, 'datos', 'plot_prg', file + ".jpg")

                    enviar_archivo_telegram(file_dir)
                    generar_grafico_prg(file_dir, plot_dir)
                    enviar_foto_telegram(plot_dir)

                    shutil.move(file_dir, prg_dir)
                    send_mail("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/PRG", "eliminar", prg_dir)

                elif file.startswith('PO'):
                    fecha_fin = file[2:8]
                    zip_fin = zip_name

                    file_dir = os.path.join(tmp_dir, file)
                    po_dir = os.path.join(project_root, 'datos', 'po', file)

                    enviar_archivo_telegram(file_dir)
                    shutil.move(file_dir, po_dir)
                    send_mail("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/PO", "eliminar", po_dir)
    finally:
        limpiar_dir(tmp_dir)

    _append_csv(csv_path, [{
        "fecha": yyyymmdd,
        "s3_key": s3_key,
        "encodedKey": encoded_key,
        "zip": zip_name,
    }])

    return fecha_fin, zip_fin

def descargar_PID_API(ref_date=None):
    """
    PID por API:
    - Para ref_date prueba periodos 01..24 (pueden salir varios o ninguno)
    - Descarga ZIP a datos/tmp
    - Unzip en datos/tmp
    - Mueve XLSX desde subcarpeta
    - Procesa PRG (telegram + gráfico + mail PID)
    - Registra en datos/links/links_PID_API.csv
    """
    if ref_date is None:
        ref_date = dt.datetime.now()

    user_key = _get_user_key()
    if not user_key:
        print("[descargar_PID_API] Falta programa_operacion.user_key en config.ini")
        return

    tmp_dir = os.path.join(project_root, 'datos', 'tmp')
    limpiar_dir(tmp_dir)

    links_dir = os.path.abspath(os.path.join(project_root, "datos", "links"))
    csv_path = os.path.join(links_dir, "links_PID_API.csv")
    existentes = _read_csv_set(csv_path, "s3_key")

    yyyymmdd = ref_date.strftime("%Y%m%d")
    nuevos = 0

    for periodo in range(1, 25):
        file_name = f"PID_{yyyymmdd}_{periodo:02d}.zip"
        s3_key = f"PID/{file_name}"
        if s3_key in existentes:
            continue

        encoded_key = _b64_key(s3_key)
        presigned = _get_presigned_url(encoded_key, user_key)
        if not presigned:
            continue

        zip_path = os.path.join(tmp_dir, file_name)
        try:
            _download_file(presigned, zip_path)
            print(f"[descargar_PID_API] ZIP descargado: {file_name}")
        except Exception as e:
            print(f"[descargar_PID_API] Error descargando {file_name}: {e}")
            limpiar_dir(tmp_dir)
            continue

        try:
            with zp.ZipFile(zip_path, "r") as POzip:
                POzip.extractall(path=tmp_dir)
        except Exception as e:
            print(f"[descargar_PID_API] Error descomprimiendo {file_name}: {e}")
            limpiar_dir(tmp_dir)
            continue

        dir_name = file_name[:-4]
        sub_dir = os.path.join(tmp_dir, dir_name)
        if os.path.isdir(sub_dir):
            for file_in in os.listdir(sub_dir):
                file_path = os.path.join(sub_dir, file_in)
                if os.path.isfile(file_path):
                    shutil.move(file_path, tmp_dir)

        try:
            for file in os.listdir(tmp_dir):
                if file.endswith('.xlsx') and file.startswith('PRG'):
                    print(file)
                    enviar_mensaje_telegram("Se ha publicado una nueva programación intradiaria")

                    file_dir = os.path.join(tmp_dir, file)
                    pid_dir = os.path.join(project_root, 'datos', 'pid', file)
                    plot_dir = os.path.join(project_root, 'datos', 'plot_prg', file + ".jpg")

                    enviar_archivo_telegram(file_dir)
                    generar_grafico_prg(file_dir, plot_dir)
                    enviar_foto_telegram(plot_dir)

                    shutil.move(file_dir, pid_dir)
                    send_mail("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/PID", "eliminar", pid_dir)
        finally:
            limpiar_dir(tmp_dir)

        _append_csv(csv_path, [{
            "fecha": yyyymmdd,
            "s3_key": s3_key,
            "encodedKey": encoded_key,
            "zip": file_name,
        }])

        nuevos += 1
        existentes.add(s3_key)

    if nuevos == 0:
        print("No hay programas intradiarios nuevos (API)")