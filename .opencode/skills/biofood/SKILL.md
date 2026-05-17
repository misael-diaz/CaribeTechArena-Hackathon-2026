---
name: biofood
description: Guía del proyecto BioFood — estructura Django, apps, convenciones, y cómo restartear el servicio en :8000
---

## Proyecto: BioFood
Backend Django 6.0.5 para gestión de alimentación escolar, alérgenos y transacciones en cafeterías.

## Apps del proyecto
- **school** — colegios y admins de cafetería
- **student** — perfiles, saldos, alérgenos
- **product** — catálogo de productos y alérgenos
- **transaction** — ventas y recargas
- **cafeteria** — inventario y stock por colegio
- **parent** — mapeo padres → estudiantes por teléfono
- **chat** — sesiones para chatbot

## Servicio
- Corre con Gunicorn en puerto 8000
- Para restartear después de cambios:
  ```
  sudo systemctl restart biofood  (o)
  kill -HUP <PID>
  ```

## Convenciones
- Scripts temporales/test del agente: prefijo `agent_` (ej: `agent_test_db.py`)
- Usar `python manage.py <command>` para tareas Django
- DB local: SQLite, DB externa: PostgreSQL

## Comandos comunes
- `python manage.py runserver` — dev server
- `python manage.py migrate` — migraciones
- `python manage.py makemigrations` — crear migraciones
- `python import_all_data.py` — importar datos reales desde DB externa
