bot_telegram/
├── README.md
├── requirements.txt
├── config.ini
├── bot_main.py
├── help.md
├── help_enso.md
├── balance/
│   ├── balance.py
│   └── balance_utils.py
├── cartas_cen/
│   ├── cartas_cen.py
│   ├── cartas_cen.sh
│   ├── cartas_cen2.py
│   ├── cartas_cen_utils.py
│   ├── cartas_cen_utils2.py
│   ├── cartas_sec.py
│   └── cartas_sec.sh
├── datos/
│   ├── links/
│   └── tmp/
├── enso/
│   ├── descargar_enso.py
│   └── descarga_enso_utils.py
├── envia_programas/
│   ├── envia_programas.py
│   └── envia_programas_utils.py
├── gen/
│   └── gen.py
├── informe/
│   ├── informe.py
│   ├── informe_sin_reporte.py
│   └── informe_utils.py
├── modules/
│   ├── data_processing.py
│   ├── download_utils.py
│   ├── email_utils.py
│   ├── graph_utils.py
│   └── telegram_utils.py
├── opreal/
│   ├── opreal.py
│   └── opreal_utils.py
├── rio/
│   ├── loop.py
│   ├── rio.py
│   └── rio_utils.py
└── sscc/
    ├── sscc.py
    └── sscc_utils.py

## Estructura general

- `bot_main.py`: punto de entrada principal del bot.
- `modules/`: utilidades compartidas para descarga, procesamiento, gráficos, correo y Telegram.
- `cartas_cen/`: lógica asociada a scraping y procesamiento de cartas.
- `envia_programas/`: envío y procesamiento de programas.
- `informe/`: generación de informes.
- `rio/`: procesamiento asociado a ríos/caudales.
- `sscc/`, `balance/`, `gen/`, `enso/`, `opreal/`: módulos específicos por funcionalidad.
- `datos/`: archivos temporales y links descargados/procesados.

## Instalación

Clonar el repositorio:

git clone https://github.com/aiguzmanm/bot_telegram.git
cd bot_telegram

Instalar dependencias:

pip install -r requirements.txt --break-system-packages

## Configuración

El archivo `config.ini` contiene parámetros locales y credenciales, por lo que no se incluye en el repositorio.

Debe crearse manualmente en cada entorno.