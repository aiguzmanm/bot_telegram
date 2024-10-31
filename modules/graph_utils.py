import pandas as pd
import matplotlib.pyplot as plt
import os

def generar_grafico_cmg(fecha, ruta_csv, ruta_guardado):
    # Convertir 'fecha' de formato 'yymmdd' a 'dd/mm/yy' para el título
    fecha_formateada = f"{fecha[4:6]}/{fecha[2:4]}/{fecha[0:2]}"
    print(ruta_csv)
    # Cargar datos del CSV
    df = pd.read_csv(ruta_csv, index_col=0)
    # Generar el gráfico
    columnas_a_graficar = ["CRUCERO__220", "P.AZUCAR__220", "QUILLOTA__220",
                           "A.JAHUEL__220", "CHARRUA__220", "P.MONTT___220"]
    df[columnas_a_graficar].plot(
        figsize=(10, 4), xlabel="Horas", ylabel="CMG [USD/MWh]"
    )
    plt.xticks(range(1, 25, 1))
    plt.legend(loc='lower left', prop={'size': 8})
    plt.grid()
    plt.title(f"Costos Marginales {fecha_formateada}")

    # Asegurarse de que el directorio de guardado exista
    os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
    
    # Guardar el gráfico
    plt.savefig(ruta_guardado)
    plt.close()

