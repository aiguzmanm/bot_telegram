# Proyecto Bot Telegram para Procesamiento de Datos Energéticos

Este proyecto es una implementación de un bot de Telegram que automatiza el procesamiento y análisis de datos del Coordinador. El bot descarga, procesa y organiza datos provenientes de diversas fuentes, generando informes y gráficos que se almacenan en estructuras de carpetas específicas. La configuración del bot y las descargas están centralizadas en un archivo `config.ini`.

## Estructura del Proyecto

```plaintext
bot_telegram/
│
├── modules/                     # Módulos de utilidades y procesamiento
│   ├── data_processing.py        # Funciones de procesamiento de datos (e.g., cálculo de CMG, gestión de zonas)
│   ├── file_utils.py             # Utilidades para gestión y almacenamiento de archivos
│   ├── graph_utils.py            # Funciones para generación de gráficos
│   └── parches_rio.py            # Funciones de parcheo de datos específicos (e.g., columnas renombradas)
│
├── rio/                          # Módulos y utilidades específicas de datos RIO
│   ├── rio.py                    # Función principal para descargar y procesar datos de RIO
│   ├── rio_utils.py              # Funciones auxiliares para operaciones con datos RIO
│
├── informe/                      # Módulos relacionados con informes y reportes
│   ├── informe.py                # Script principal de generación de informes
│   ├── informe_utils.py          # Funciones específicas del informe (e.g., cálculos detallados)
│
├── datos/                        # Directorio de almacenamiento de datos generados
│   ├── rio/                      # Archivos de datos de RIO descargados y procesados
│   ├── zon/                      # Archivos de zonas procesados
│   ├── des/                      # Archivos de desacoples procesados
│   ├── cmg/                      # Archivos de costos marginales generados
│   └── plot/                     # Archivos de gráficos generados
│
├── config.ini                    # Archivo de configuración para personalizar ajustes del bot y del procesamiento
│
└── ... (otros archivos y directorios)
