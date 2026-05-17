---
name: School Portal - Aislamiento de Datos
description: Cada colegio solo ve sus propios datos - Implementado aislamiento completo
type: project
---

**Problema identificado:** El usuario pregunto si los datos eran mocks y si un colegio podia ver datos de otros.

**Solucion implementada:**

1. **Datos NO son mocks** - Se creo comando `ingest_notifications` que ingesta datos reales desde:
   - Prestamos (Loan)
   - Inventario critico (Inventory)
   - Transacciones con alérgenos (Transaction + StudentAllergen)

2. **Aislamiento total por escuela** - Todas las views filtran por `school=school_user.school`:

```python
# Dashboard
school = school_user.school  # ← ESCUELA DEL USUARIO
unread_notifications = Notification.objects.filter(
    school=school  # ← FILTRO POR ESCUELA ACTUAL
)

# Notificaciones
notifications = Notification.objects.filter(school=school)  # ← FILTRO POR ESCUELA

# Prestamos
recent_loans = Loan.objects.filter(
    parent__students__school=school  # ← FILTRO POR ESCUELA ACTUAL
)
```

**Comandos disponibles:**

```bash
# Ingestar notificaciones reales desde la DB
python manage.py ingest_notifications

# Esto crea notificaciones automaticamente desde:
# - Prestamos pendientes
# - Stock critico (current_stock <= 0)
# - Stock bajo (0 < current_stock <= minimum_stock)
# - Alertas de alérgenos (ultimas 24h)
```

**Seguridad de datos:**

| Usuario | Puede ver |
|---------|-----------|
| Colegio A | Solo datos de Colegio A |
| Colegio B | Solo datos de Colegio B |
| Superusuario | Todos los datos (admin Django) |

**Fecha de actualizacion:** 2026-05-17
