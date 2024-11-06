import pandas as pd
import matplotlib.pyplot as plt
import os

def generar_grafico_cmg(ruta_csv, ruta_guardado):
    # Convertir 'fecha' de formato 'yymmdd' a 'dd/mm/yy' para el título
    fecha_formateada = f"{fecha[4:6]}/{fecha[2:4]}/{fecha[0:2]}"
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

def generar_grafico_prg(ruta_prg, ruta_guardado):
    programa_df = pd.read_excel(ruta_prg, sheet_name='PROGRAMA')
        # Extraer la fecha del programa
    program_date = programa_df.iloc[2, 2]
    formatted_date = pd.to_datetime(program_date).strftime('%d-%b-%y')
    
    # Extraer tecnologías y valores de generación
    column_c = programa_df['Unnamed: 2']
    technologies = []
    generation_values = []
    empty_count = 0

    # Recorrer la columna C para encontrar las tecnologías y valores
    for i, value in enumerate(column_c):
        if pd.isna(value):
            empty_count += 1
        else:
            empty_count = 0
        if empty_count == 3:
            break
        if value == 'Total':
            current_technology = column_c[i - 1]
            current_generation = programa_df.iloc[i, 4:4 + 24].tolist()
            # Transformar los valores de generación a mayores o iguales a 0
            generation_values.append([max(0, val) for val in current_generation])
            technologies.append(current_technology)

    # Buscar "Sistemas de Almacenamiento" y transformar los valores
    for i, value in enumerate(column_c):
        if value == 'Sistemas de Almacenamiento':
            if column_c[i + 1] == 'Total':
                storage_generation = programa_df.iloc[i + 1, 4:4 + 24].tolist()
                generation_values.insert(0, [max(0, val) for val in storage_generation])
                technologies.insert(0, 'Sistemas de Almacenamiento')
            break

    # Colores y abreviaciones
    final_with_storage_colors = ['orange', 'lightblue', 'mediumpurple', 'yellow', 'orange', 'lightgray', 'blue']
    updated_technologies = ['Baterías' if tech == 'Sistemas de Almacenamiento' else
                            'H. Pasada' if tech == 'Hidroeléctricas de Pasada' else
                            'CSP' if tech == 'Centrales de concentración solar' else
                            'Embalses' if tech == 'Embalses y Reguladas' else
                            tech for tech in technologies]

    # Extraer "Costos Marginales" y transformar los valores
    costs_technology = []
    costs_data = []
    found_costs_marginales = False
    for i, value in enumerate(column_c):
        if value == "Costos Marginales":
            found_costs_marginales = True
            continue
        if found_costs_marginales:
            if pd.isna(value):
                break
            costs_technology.append(value)
            costs_data.append([max(0, val) for val in programa_df.iloc[i, 4:4 + 24].tolist()])  # Transformar costos
    costs_dict = dict(zip(costs_technology, costs_data))
    selected_bars = ['Crucero220', 'Quillota220', 'Charrua220', 'PMontt220']
    selected_costs = {bar: costs_dict[bar] for bar in selected_bars if bar in costs_dict}

    # Graficar el programa de generación y costos marginales
    fig, ax1 = plt.subplots(figsize=(12, 6))
    bottom = [0] * 24
    hours = list(range(1, 25))  # Horas de 1 a 24
    bar_width = 0.85
    for tech, gen, color in zip(updated_technologies, generation_values, final_with_storage_colors):
        ax1.bar(hours, gen, bar_width, bottom=bottom, label=tech, color=color)
        bottom = [sum(x) for x in zip(bottom, gen)]
    ax1.set_xlabel('Hour of the Day')
    ax1.set_ylabel('Generation (MW)', color='black')
    ax2 = ax1.twinx()
    for bar, costs in selected_costs.items():
        ax2.plot(hours, costs, label=bar, linestyle='-', linewidth=2)
    ax2.set_ylabel('Marginal Costs (USD/MWh)', color='black')
    ax1.legend(loc='upper left', bbox_to_anchor=(1.1, 1), title="Generation")
    ax2.legend(loc='lower left', bbox_to_anchor=(1.1, 0.3), title="Marginal Costs")
    plt.title(f'Programa de generación horaria día {formatted_date}')
    plt.tight_layout()
        # Asegurarse de que el directorio de guardado exista
    os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
    
    # Guardar el gráfico
    plt.savefig(ruta_guardado)
    plt.close()

