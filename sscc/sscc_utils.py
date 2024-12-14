import pandas as pd
import os

def procesar_datos_sscc(fecha, datos_dir):
    """
    Procesa los datos de SSCC a partir de archivos Excel y los guarda como .xlsx en el directorio especificado.

    :param fecha: Fecha en formato YYMMDD para buscar los archivos correspondientes.
    :param datos_dir: Directorio donde se guardarán los archivos procesados.
    """
    # Ruta de los archivos PRG dentro de bot_telegram/datos/prg
    prg_dir = os.path.join(os.path.dirname(datos_dir), 'prg')  # Asume datos_dir = bot_telegram/datos/sscc
    archivo_prg = os.path.join(prg_dir, f"PRG{fecha}.xlsx")
    hojas = ["Reservas CPF", "Reservas CSF", "Reservas CTF"]

    # Leer hojas del archivo Excel
    try:
        dfPRGCPF = pd.read_excel(archivo_prg, sheet_name=hojas[0])
        dfPRGCSF = pd.read_excel(archivo_prg, sheet_name=hojas[1])
        dfPRGCTF = pd.read_excel(archivo_prg, sheet_name=hojas[2])
    except FileNotFoundError:
        raise FileNotFoundError(f"El archivo {archivo_prg} no existe en {prg_dir}.")
    except Exception as e:
        raise Exception(f"Error al leer las hojas del archivo Excel: {e}")

    # Buscar y procesar las columnas de bajada
    def procesar_dataframe(df, hoja):
        col_bajada = df.columns[df.iloc[2].astype(str).str.contains('BAJADA', case=False)].tolist()
        if not col_bajada:
            raise ValueError(f"No se encontró la columna 'BAJADA' en la hoja {hoja}")
        val_bajada = int(col_bajada[0].split(': ')[1]) - 1

        # Recortar y limpiar el DataFrame
        df = df.iloc[:, 1:].iloc[3:].reset_index(drop=True)
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)

        # Recortar hasta la fila que contiene "total"
        fila_total = df[df.iloc[:, 0].str.contains('total', case=False)].index[0]
        df = df[:fila_total]

        # Dividir en subida y bajada
        df_subida = df.iloc[:, 0:val_bajada]
        df_bajada = df.iloc[:, [0] + list(range(val_bajada, len(df.columns)))]

        # Eliminar filas con suma 0
        df_subida = df_subida[df_subida.iloc[:, 1:].sum(axis=1) != 0]
        df_bajada = df_bajada[df_bajada.iloc[:, 1:].sum(axis=1) != 0]

        return df_subida, df_bajada

    # Procesar CPF, CSF y CTF
    datos = [
        procesar_dataframe(dfPRGCPF, hojas[0]),
        procesar_dataframe(dfPRGCSF, hojas[1]),
        procesar_dataframe(dfPRGCTF, hojas[2]),
    ]

    # Guardar DataFrames procesados como archivos .xlsx
    nombres_archivos = ["dfPRGCPFS.xlsx", "dfPRGCSFS.xlsx", "dfPRGCTFS.xlsx", 
                        "dfPRGCPFB.xlsx", "dfPRGCSFB.xlsx", "dfPRGCTFB.xlsx"]
    for i, (df_subida, df_bajada) in enumerate(datos):
        df_subida.to_excel(os.path.join(datos_dir, nombres_archivos[i * 2]), index=False)
        df_bajada.to_excel(os.path.join(datos_dir, nombres_archivos[i * 2 + 1]), index=False)
