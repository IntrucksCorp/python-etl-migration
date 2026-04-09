# 🔄 ETL Migración CRM — NowCerts → Trucker Space

* [ ] 

## 📋 Descripción

Este repositorio contiene los scripts de extracción, transformación y carga (ETL) necesarios para llevar a cabo la migración completa de datos entre ambos sistemas CRM. El proceso se ejecuta con **Python** y utiliza **Supabase** como capa de datos intermedia y/o destino.

## 🛠️ Tech Stack

| Tecnología        | Uso                                                   |
| ------------------ | ----------------------------------------------------- |
| **Python**   | Lógica del ETL (extracción, transformación, carga) |
| **Supabase** | Base de datos destino / capa intermedia               |

## 📂 Estructura del Proyecto

> _Se irá actualizando a medida que se agreguen módulos._

```
python-etl-migration/
├── readme.md
└── ...
```

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.10+
- Cuenta y proyecto en Supabase
- Acceso a la API / datos de NowCerts

### Instalación

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd python-etl-migration

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Instalar dependencias
pip install -r requirements.txt
```

### Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_key
NOWCERTS_API_KEY=tu_nowcerts_api_key
```

## 📌 Estado del Proyecto

🟡 **En desarrollo** — Fase inicial de planificación y estructura.

---

> _Este README se actualizará conforme avance el desarrollo del ETL._
