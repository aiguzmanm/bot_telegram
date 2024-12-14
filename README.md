bot_telegram/
├── balance/                     # Módulos relacionados con balances
│   ├── balance.py               # (Por implementar) Función principal para cálculo de balances
│   ├── balance_utils.py         # (Por implementar) Funciones auxiliares para balances
│
├── sscc/                        # Módulos relacionados con SSCC
│   ├── sscc.py                  # (Por implementar) Procesamiento de datos SSCC
│   ├── sscc_utils.py            # (Por implementar) Funciones auxiliares para SSCC
│
├── envia_programas/             # Módulos para el manejo de programas de operación
│   ├── envia_programas.py       # Función principal para búsqueda y envío de programas
│   ├── envia_programas_utils.py # Funciones auxiliares para manejo de programas
│
├── modules/                     # Utilidades generales del proyecto
│   ├── data_processing.py       # Procesamiento de datos (e.g., cálculo de CMG)
│   ├── file_utils.py            # Gestión y almacenamiento de archivos
│   ├── graph_utils.py           # Generación de gráficos
│   └── telegram_utils.py        # Envío de mensajes y archivos por Telegram
│
├── rio/                         # Módulos específicos para datos RIO
│   ├── rio.py                   # Descarga y procesamiento de datos RIO
│   ├── rio_utils.py             # Funciones auxiliares para manejo de datos RIO
│
├── informe/                     # Módulos para generación de informes
│   ├── informe.py               # Script principal para creación de informes
│   ├── informe_utils.py         # Funciones específicas para cálculos detallados
│
├── datos/                       # Almacenamiento de datos procesados y generados
│   ├── rio/                     # Archivos relacionados con datos RIO
│   ├── zon/                     # Datos de zonas procesados
│   ├── des/                     # Archivos de desacoples procesados
│   ├── cmg/                     # Datos de costos marginales
│   └── plot/                    # Gráficos generados
│
├── bot_main.py                  # Código principal del bot de Telegram
├── config.ini                   # Archivo de configuración del proyecto
├── help.md                      # Documentación para el comando `/help`
├── requirements.txt             # Dependencias del proyecto
├── README.md                    # Documentación del proyecto
