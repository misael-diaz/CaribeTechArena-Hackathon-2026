---
name: School Portal - Login y Notificaciones
description: Portal web para colegios con login Django, dashboard y sistema de notificaciones
type: project
---

**Decisión:** Se creo un portal web para que los colegios puedan ver notificaciones en tiempo real, gestionar prestamos y monitorear la cafetería.

**Why:** Los administradores de colegios necesitan una interfaz web para ver alertas de prestamos, stock critico, alérgenos, etc. sin depender solo de WhatsApp.

**How to apply:**
- **Modelos:** `school/models.py` con `SchoolUser` (extiende Django User) y `Notification`
- **Views:** Login, logout, dashboard, lista de notificaciones
- **Templates:** HTML/CSS en `templates/school/`
- **Permisos:** Django permissions por rol (ADMIN, CAFETERIA, SECRETARIA)

**Modelos creados:**

```python
SchoolUser:
  - user (OneToOne con Django User)
  - school (FK a School)
  - role: ADMIN, CAFETERIA, SECRETARIA
  - permissions: can_view_dashboard, can_view_notifications, can_manage_loans, can_manage_inventory

Notification:
  - school (FK)
  - user (FK opcional)
  - title, message
  - priority: LOW, MEDIUM, HIGH, CRITICAL
  - type: LOAN, STOCK, ALLERGEN, BALANCE, GENERAL
  - is_read, read_at
  - action_url (para botones)
  - metadata (JSON)
```

**URLs:**

| URL | Vista | Descripcion |
|-----|-------|-------------|
| `/school/login/` | school_login | Login de usuarios |
| `/school/logout/` | school_logout | Cerrar sesion |
| `/school/register/` | school_register | Registrar usuario (admin only) |
| `/school/dashboard/` | school_dashboard | Dashboard principal |
| `/school/notifications/` | notifications_list | Lista de notificaciones |
| `/school/notifications/<id>/read/` | mark_notification_read | Marcar como leida |
| `/school/notifications/read-all/` | mark_all_notifications_read | Marcar todas leidas |

**Comandos de gestion:**

```bash
# Crear usuario de colegio
python manage.py create_school_user --username admin --password admin123 --school "Mi Colegio" --role ADMIN

# Crear notificaciones de prueba
python manage.py create_test_notifications
```

**Credenciales de prueba:**
- Username: `admin`
- Password: `admin123`
- URL: http://localhost:8000/school/login/

**Notificaciones automaticas:**

El sistema puede crear notificaciones automaticamente desde:

```python
# Ejemplo: Crear notificacion de prestamo
from school.models import Notification

Notification.objects.create(
    school=school,
    user=school_user,
    title='Nuevo prestamo solicitado',
    message=f'{student.name} solicito prestamo de ${amount}',
    priority='HIGH',
    type='LOAN',
    action_url='/transaction/api/loan/pending/'
)
```

**Integracion con prestamos:**

Cuando se crea un prestamo, se puede crear notificacion automatica:

```python
# En transaction/services/loan_service.py
def request_loan(self, student, amount):
    loan = Loan.objects.create(...)
    
    # Crear notificacion
    Notification.objects.create(
        school=student.school,
        title='Prestamo pendiente',
        message=f'{student.name} solicito ${amount}',
        type='LOAN',
        priority='HIGH'
    )
```

**Archivos creados:**

| Archivo | Proposito |
|---------|-----------|
| `school/models.py` | SchoolUser, Notification |
| `school/forms.py` | Login y registro forms |
| `school/views.py` | Vistas del portal |
| `school/urls.py` | URLs de la app |
| `school/apps.py` | Registro de app |
| `templates/school/base.html` | Template base |
| `templates/school/login.html` | Login |
| `templates/school/dashboard.html` | Dashboard |
| `templates/school/notifications.html` | Lista notificaciones |
| `school/management/commands/create_school_user.py` | Comando crear usuarios |
| `school/management/commands/create_test_notifications.py` | Comando crear notificaciones prueba |

**Fecha de implementacion:** 2026-05-17
