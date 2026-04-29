# ETL Migración CRM — NowCerts → Trucker Space

Scripts de extracción, transformación y carga (ETL) para migrar datos del CRM anterior (NowCerts) al nuevo CRM interno (Trucker Space / Supabase).

## Estado del Proyecto

🟡 **En desarrollo** — Estructura completa, transformers validados contra la API real. Listo para prueba de pipelines.

## Tech Stack

| Tecnología | Uso |
|---|---|
| Python 3.10+ | Lógica ETL (extracción, transformación, carga) |
| Supabase (service role) | Base de datos destino |
| NowCerts OData API | Fuente de datos |
| `requests` + `tenacity` | HTTP con reintentos |
| `supabase-py` | Cliente Supabase |

## Estructura del Proyecto

```
python-etl-migration/
├── main.py                        # Punto de entrada (--only <pipeline>)
├── requirements.txt
├── .env.example                   # Variables de entorno requeridas
│
├── config/
│   └── settings.py                # Carga variables de entorno
│
├── extractors/                    # Clientes HTTP por endpoint de NowCerts
│   ├── nowcerts_client.py         # Autenticación Bearer + paginación
│   ├── insured_extractor.py       # InsuredList, InsuredLocationList
│   ├── vehicle_extractor.py       # VehicleList
│   ├── driver_extractor.py        # DriverList
│   ├── policy_extractor.py        # PolicyDetailList, MotorTruckDetailList, CLCommercialAutoRatingDetailList
│   ├── opportunity_extractor.py   # OpportunitiesList
│   ├── notes_extractor.py         # NotesList
│   └── tasks_extractor.py         # TasksList
│
├── transformers/                  # Mapeo de campos NowCerts → Supabase
│   ├── profiles_transformer.py
│   ├── vehicles_transformer.py
│   ├── drivers_transformer.py
│   ├── opportunities_transformer.py
│   ├── insurance_folders_transformer.py
│   ├── insurance_folder_carriers_transformer.py
│   ├── policy_coverages_transformer.py
│   ├── activities_transformer.py
│   └── cases_transformer.py
│
├── loaders/
│   └── supabase_loader.py         # Inserts en batch (200 filas), bypass RLS
│
├── pipelines/                     # Orquesta E→T→L por entidad
│   ├── profiles_pipeline.py
│   ├── vehicles_pipeline.py
│   ├── drivers_pipeline.py
│   ├── opportunities_pipeline.py
│   ├── insurance_folders_pipeline.py
│   ├── policy_coverages_pipeline.py
│   ├── activities_pipeline.py
│   └── cases_pipeline.py
│
├── scripts/
│   └── inspect_endpoint.py        # Inspecciona campos y tipos de un endpoint
│
├── utils/
│   ├── logger.py                  # Logs a consola + logs/migration.log
│   └── helpers.py                 # safe_str, parse_date, etc.
│
└── logs/
    └── migration.log
```

## Instalación

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con las credenciales reales
```

## Variables de Entorno

```env
NOWCERTS_API_BASE_URL=https://api.nowcerts.com/api
NOWCERTS_USERNAME=your_username
NOWCERTS_PASSWORD=your_password
# Opcional: token pre-generado (omite el login automático)
# NOWCERTS_ACCESS_TOKEN=your_bearer_token

SUPABASE_URL=https://eovqdeaocpccpwwqrbyb.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

TARGET_ORG_ID=a249ded6-d74a-4739-ba2b-4667043893c3

PAGE_SIZE=500
REQUEST_DELAY=0.3
LOG_LEVEL=INFO
```

## Uso

```bash
# Inspeccionar campos de un endpoint antes de migrar
python scripts/inspect_endpoint.py InsuredList
python scripts/inspect_endpoint.py --all

# Correr un pipeline individual (recomendado para pruebas)
python main.py --only profiles
python main.py --only vehicles

# Correr la migración completa
python main.py
```

## Orden de Ejecución de Pipelines

El orden respeta las dependencias de claves foráneas entre tablas:

| # | Pipeline | NowCerts → Supabase |
|---|---|---|
| 1 | `profiles` | InsuredList + InsuredLocationList → `profiles` |
| 2 | `vehicles` | VehicleList → `vehicles` |
| 3 | `drivers` | DriverList → `drivers` |
| 4 | `opportunities` | OpportunitiesList → `opportunities` |
| 5 | `insurance_folders` | InsuredList + PolicyDetailList → `insurance_folders` + `insurance_folder_carriers` |
| 6 | `policy_coverages` | PolicyDetailList + CLCommercialAutoRatingDetailList → `policy_coverages` |
| 7 | `activities` | NotesList → `activities` |
| 8 | `cases` | TasksList → `cases` |

## Notas de Migración

- **Vehículos y trailers**: en NowCerts están juntos en `VehicleList`; se separan por `typeDescription`.
- **GVW**: el campo `vehicleWeight` no existe en el endpoint — se migra como `null`.
- **Titularidad de vehículos**: no existe en NowCerts — se migra vacío.
- **`owner` en conductores**: corresponde al checkbox `excluded` de NowCerts.
- **`analyst`/`agent`/`producer_name`** en insurance_folders: se migran vacíos.
- **`quote_id`** en insurance_folder_carriers: usa el número de póliza (`number`).
- **Actividades**: el contenido de NotesList está en el campo `subject` (puede contener HTML).
- **Todos los vehículos** se migran con `status = active`.
