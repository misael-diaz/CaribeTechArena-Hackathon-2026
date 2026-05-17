---
name: School Portal - Integracion con Alertas
description: Las alertas de stock y alérgenos ahora crean notificaciones automaticas en el portal
type: project
---

**Problema:** El usuario noto que las alertas de la cafetería (stock, alérgenos) no se mostraban en el portal del colegio.

**Solucion implementada:**

1. **StockAlertService** (`cafeteria/services/stock_alert_service.py`):
   - Cuando detecta stock crítico, AHORA crea notificación en el portal
   - Prioridad: CRITICAL si stock=0, HIGH si 0<stock<=minimum
   - Tipo: STOCK
   - Incluye metadata con inventory_id, product_id, current_stock, minimum_stock

2. **AllergenAlertService** (`student/services/allergen_alert_service.py`):
   - Cuando detecta alérgeno en transacción, AHORA crea notificación en el portal
   - Prioridad: CRITICAL (siempre)
   - Tipo: ALLERGEN
   - Incluye metadata con student_id, product_id, allergens, parent_id

**Flujo completo:**

```
┌─────────────────────────────────────────────────────────────┐
│ EVENTO: Stock crítico detectado                             │
│ (via signal o cron job)                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ StockAlertService.check_and_alert(inventory)                │
│ 1. Envía WhatsApp a admins de cafetería                     │
│ 2. Crea Notification en el portal                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Portal del Colegio (/school/notifications/)                 │
│ Notificación visible para administradores del colegio       │
│ - Título: "Stock CRITICO: Coca-Cola"                        │
│ - Mensaje: "El producto tiene 0 unidades (minimo: 10)"      │
│ - Prioridad: CRITICAL (rojo)                                │
│ - Botón: Ver en inventario                                  │
└─────────────────────────────────────────────────────────────┘
```

**Codigos actualizados:**

```python
# cafeteria/services/stock_alert_service.py
def _send_alert(self, admin, inventory):
    # ... enviar WhatsApp ...
    
    # CREAR NOTIFICACION EN EL PORTAL
    from school.models import Notification
    priority = 'CRITICAL' if current == 0 else 'HIGH'
    
    Notification.objects.create(
        school=inventory.school,  # ← AISLAMIENTO: Solo esta escuela
        title=f'Stock {"CRITICO" if current == 0 else "BAJO"}: {product_name}',
        message=f'El producto {product_name} tiene {current} unidades...',
        priority=priority,
        type='STOCK',
        action_url='/cafeteria/inventory/',
        metadata={...}
    )
```

**Comandos para probar:**

```bash
# 1. Ejecutar cron job de stock (crea notificaciones)
python manage.py alert_stock

# 2. Ejecutar ingesta de notificaciones existentes
python manage.py ingest_notifications

# 3. Ver notificaciones en el portal
http://localhost:8000/school/notifications/
```

**Aislamiento garantizado:**

Todas las notificaciones se crean con `school=inventory.school` o `school=student.school`, asegurando que cada colegio solo vea SUS propias alertas.

**Fecha de actualizacion:** 2026-05-17
