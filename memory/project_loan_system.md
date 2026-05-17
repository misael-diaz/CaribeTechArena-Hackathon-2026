---
name: Loan System - Prestamos en Tiempo Real
description: Sistema de prestamos temporales cuando estudiantes se quedan sin saldo
type: project
---

**Decisión:** Se implemento un sistema de prestamos temporales para que los estudiantes puedan comprar cuando se quedan sin saldo, con aprobacion del padre via WhatsApp/chatbot.

**Why:** Los ninos se quedan sin saldo y no pueden comprar. Con este sistema, el nino puede solicitar un prestamo y el padre recibe una notificacion para aprobarlo con un click.

**How to apply:**
- **Modelo:** `transaction/models.py` con `Loan` (prestamos)
- **Servicio:** `transaction/services/loan_service.py` para gestion de prestamos
- **API:** `transaction/views.py` con endpoints para solicitar/aprobar/rechazar
- **Chatbot:** 3 tools nuevos (`approve_loan`, `get_pending_loans`, `get_loan_summary`)
- **URLs:** `transaction/urls.py` registradas en `/transaction/api/loan/`

**Flujo de uso:**

```
1. Estudiante intenta comprar pero tiene saldo $0
2. Sistema detecta saldo insuficiente y sugiere: "¿Quieres solicitar un prestamo de $5?"
3. Estudiante acepta → Se crea Loan con estado PENDING
4. Padre recibe WhatsApp: "Juanito se quedo sin saldo. ¿Quieres agregar $5 a tu cuenta como deuda?"
5. Padre responde "SI" o usa link: https://biofood.app/loan/approve/{token}/
6. Sistema aprueba prestamo → Agrega $5 al saldo del estudiante
7. Deuda queda registrada hasta que el padre recargue
```

**Modelo Loan:**

```python
Loan:
  - student (FK a Student)
  - parent (FK a Parent)
  - amount (Decimal)
  - status: PENDING, APPROVED, REJECTED, PAID
  - created_at
  - approved_at
  - paid_at
  - transaction (FK opcional a Transaction que origino el prestamo)
  - approval_token (unico, para aprobar via link)
```

**Endpoints API:**

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/transaction/api/loan/request/` | POST | Solicitar prestamo |
| `/transaction/api/loan/approve/{token}/` | GET/POST | Aprobar prestamo |
| `/transaction/api/loan/reject/{token}/` | POST | Rechazar prestamo |
| `/transaction/api/loan/pending/?parent_phone=+57...` | GET | Ver prestamos pendientes |

**Tools del Chatbot:**

| Tool | Descripcion |
|------|-------------|
| `approve_loan(token, action)` | Aprueba/rechaza prestamo con token |
| `get_pending_loans(parent_phone)` | Lista prestamos pendientes |
| `get_loan_summary(parent_phone)` | Resumen de deuda total |

**Configuracion:**

```python
# LoanService configuracion
DEFAULT_MAX_LOAN = 10.00  # Monto maximo por prestamo
MAX_PENDING_LOANS = 3     # Maximo prestamos pendientes por padre
```

**Elegibilidad para prestamo:**
- Estudiante debe tener saldo $0
- Padre no puede tener mas de 3 prestamos pendientes
- Deuda total no puede exceder 3x el prestamo base ($30)

**Migracion aplicada:** `transaction/migrations/0004_loan.py` (auto-generada)

**Fecha de implementacion:** 2026-05-17

**Proximos pasos:**
- Integrar con notificaciones push en tiempo real (WebSocket)
- Agregar boton en UI del estudiante: "Solicitar prestamo"
- Enviar WhatsApp automatico al padre cuando se crea prestamo
