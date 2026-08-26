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

def _aplanar_subcarpetas(tmp_dir: str) -> None:
    """
    Sube a tmp_dir todos los archivos que hayan quedado dentro de CUALQUIER
    subcarpeta tras descomprimir.

    (25-ago-2026) Antes se derivaba el nombre de la subcarpeta desde el nombre
    del zip (dir_name = file_name[:-4]). Eso se rompio cuando el Coordinador
    renombro el zip de "PID_{fecha}_{HH}.zip" a "RES{fecha}_{HH}.zip", porque
    la carpeta INTERNA siguio llamandose "PID_{fecha}_{HH}". Al no coincidir,
    os.path.isdir() daba False, los xlsx nunca subian a tmp_dir y el proceso
    terminaba sin enviar Telegram ni correos (pero igual registraba el zip en
    el CSV, quemando el registro). Ahora no se asume ningun nombre: se aplana
    lo que venga.
    """
    for raiz, _dirs, archivos in os.walk(tmp_dir):
        if raiz == tmp_dir:
            continue
        for file_in in archivos:
            origen = os.path.join(raiz, file_in)
            destino = os.path.join(tmp_dir, file_in)
            if not os.path.exists(destino):
                shutil.move(origen, destino)

def _candidatos_s3_pro(yyyymmdd: str) -> list[str]:
    """
    Devuelve las claves s3 candidatas para el programa diario (PRO), en orden
    de preferencia.

    (26-ago-2026) El Coordinador movio el programa diario de carpeta, pero NO
    le cambio el nombre al zip: sigue siendo "PROGRAMA{fecha}.zip", ahora en
    "PCP_RES/" en vez de "PCP/". Se prueban ambas rutas (la nueva primero, la
    vieja como fallback para dias previos) y se usa la PRIMERA que la API
    acepte (devuelva presigned URL).
    """
    return [
        f"PCP_RES/PROGRAMA{yyyymmdd}.zip",   # carpeta nueva (visto 26-ago-2026)
        f"PCP/PROGRAMA{yyyymmdd}.zip",       # ruta historica (fallback)
    ]

def descargar_PRO_API(ref_date=None):
    """
    PRO por API:
    - Prueba las claves candidatas (ver _candidatos_s3_pro) y usa la primera
      que la API acepte
    - Descarga ZIP a datos/tmp
    - Unzip en datos/tmp
    - Mueve archivos desde subcarpeta (si viene)
    - Procesa PRG/PO (telegram + gráfico + mails PRG/PO)
    - Registra en datos/links/links_PRO_API.csv para no repetir

    (26-ago-2026) El Coordinador movio el programa diario a la carpeta PCP_RES.
    El nombre del zip NO cambio (sigue siendo PROGRAMA{YYYYMMDD}.zip) y los
    archivos DENTRO del zip tampoco (siguen PRG*.xlsx y PO*.xlsx), asi que el
    resto del procesamiento queda igual.
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

    links_dir = os.path.abspath(os.path.join(project_root, "datos", "links"))
    csv_path = os.path.join(links_dir, "links_PRO_API.csv")
    existentes = _read_csv_set(csv_path, "s3_key")

    candidatos = _candidatos_s3_pro(yyyymmdd)

    # Si CUALQUIERA de las variantes ya fue procesada para esta fecha, no se
    # vuelve a bajar (evita reenviar Telegram/correos al cambiar la ruta).
    ya = next((k for k in candidatos if k in existentes), None)
    if ya:
        print(f"[descargar_PRO_API] Ya registrado: {ya}")
        return fecha_fin, zip_fin

    s3_key = None
    presigned = None
    for candidato in candidatos:
        url = _get_presigned_url(_b64_key(candidato), user_key)
        if url:
            s3_key = candidato
            presigned = url
            print(f"[descargar_PRO_API] Encontrado: {s3_key}")
            break

    if not presigned:
        print(f"[descargar_PRO_API] No disponible (aún) para {yyyymmdd}. Probado: {candidatos}")
        return fecha_fin, zip_fin

    encoded_key = _b64_key(s3_key)
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

    # (25-ago-2026) El ZIP puede traer los archivos dentro de una subcarpeta
    # (asi vienen los PID). Se aplana lo que venga; si ya estan en la raiz,
    # esta llamada no hace nada.
    _aplanar_subcarpetas(tmp_dir)

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
    - Mueve archivos desde subcarpeta
    - Procesa:
        * PRG -> telegram + gráfico + mail PID + guardar en datos/pid
        * PO  -> telegram + mail PO + guardar en datos/po
        * PDF -> telegram + guardar en datos/informe
    - Registra en datos/links/links_PID_API.csv

    (25-ago-2026) Ruta/nombre nuevos del Coordinador:
        antes:  PID/PID_{YYYYMMDD}_{HH}.zip
        ahora:  PID_RES/RES{YYYYMMDD}_{HH}.zip
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

    os.makedirs(os.path.join(project_root, 'datos', 'pid'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'datos', 'po'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'datos', 'informe'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'datos', 'plot_prg'), exist_ok=True)

    for periodo in range(1, 25):
        file_name = f"RES{yyyymmdd}_{periodo:02d}.zip"
        s3_key = f"PID_RES/{file_name}"
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

        # (25-ago-2026) Antes: dir_name = file_name[:-4] -> se asumia que la
        # subcarpeta se llamaba igual que el zip. Con el rename del Coordinador
        # (RES...zip pero carpeta interna PID_...) eso dejo de calzar. Ahora se
        # aplana cualquier subcarpeta, sin asumir nombres. Ver _aplanar_subcarpetas().
        _aplanar_subcarpetas(tmp_dir)

        try:
            prg_file = None
            po_file = None
            pdf_file = None

            for file in os.listdir(tmp_dir):
                file_dir = os.path.join(tmp_dir, file)

                if not os.path.isfile(file_dir):
                    continue

                if file.endswith('.xlsx') and file.startswith('PRG'):
                    prg_file = file

                elif file.endswith('.xlsx') and file.startswith('PO'):
                    po_file = file

                elif file.lower().endswith('.pdf'):
                    pdf_file = file

            if prg_file:
                print(prg_file)
                enviar_mensaje_telegram("Se ha publicado una nueva programación intradiaria")

                file_dir = os.path.join(tmp_dir, prg_file)
                pid_dir = os.path.join(project_root, 'datos', 'pid', prg_file)
                plot_dir = os.path.join(project_root, 'datos', 'plot_prg', prg_file + ".jpg")

                enviar_archivo_telegram(file_dir)
                generar_grafico_prg(file_dir, plot_dir)
                enviar_foto_telegram(plot_dir)

                shutil.move(file_dir, pid_dir)
                send_mail("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/PID", "eliminar", pid_dir)

            if po_file:
                print(po_file)

                file_dir = os.path.join(tmp_dir, po_file)
                po_dir = os.path.join(project_root, 'datos', 'po', po_file)

                enviar_archivo_telegram(file_dir)

                shutil.move(file_dir, po_dir)
                send_mail("/Shared Documents/Movimiento_energia/CDEC-SIC/PrgDia/PO", "eliminar", po_dir)

            if pdf_file:
                print(pdf_file)

                file_dir = os.path.join(tmp_dir, pdf_file)
                informe_dir = os.path.join(project_root, 'datos', 'informe', pdf_file)

                enviar_archivo_telegram(file_dir)

                shutil.move(file_dir, informe_dir)
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
