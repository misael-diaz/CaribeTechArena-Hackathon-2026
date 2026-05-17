---
name: US-05 Stock Alerts Architecture
description: Arquitectura de alertas de stock crítico con Signals + Cron fallback para cafetería
type: project
---

**Decisión:** Para la US-05 (Alertas de Stock Crítico), se implementó una arquitectura híbrida siguiendo el mismo patrón que las alertas de alérgenos (US-03).

**Why:** El administrador de cafetería necesita recibir alerta cuando un producto está por debajo del umbral mínimo de stock para realizar el pedido antes de que se agote. Se eligió Django Signals + Cron fallback por consistencia con la arquitectura existente y facilidad de mantenimiento.

**How to apply:**
- **Primary:** Django Signals (`post_save` en Inventory) dispara `StockAlertService.check_and_alert()` cuando se actualiza el inventario
- **Fallback:** Cron job `python manage.py alert_stock` corre diariamente (ej. 7:00 AM) para revisar todo el inventario
- **Service:** `cafeteria/services/stock_alert_service.py` contiene toda la lógica de negocio
- **Tests:** 5 tests cubren service, signals y cron job (`cafeteria/tests.py`)

**Estructura creada:**
```
cafeteria/
├── services/
│   ├── __init__.py
│   └── stock_alert_service.py
├── signals.py
├── management/
│   └── commands/
│       ├── __init__.py
│       └── alert_stock.py
├── apps.py (actualizado con ready())
└── tests.py
```

**Configurar cron:** Agregar al scheduler (ej. cron Linux o Task Scheduler Windows):
```bash
0 7 * * * cd /path/to/project && venv/bin/python manage.py alert_stock
```

**Fecha de implementación:** 2026-05-17
