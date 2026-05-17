---
name: Loan System - Integracion Twilio Completa
description: Sistema de prestamos con notificaciones WhatsApp automaticas via Twilio
type: project
---

**Flujo completo con Twilio:**

```
1. Estudiante sin saldo → Solicita prestamo
2. LoanService.request_loan() → Crea Loan PENDING
3. LoanService._send_loan_notification() → Envía WhatsApp via Twilio
4. Padre recibe mensaje en su WhatsApp
5. Padre responde "SI" o "NO" → Twilio webhook lo procesa
6. chat/views.py twilio_webhook → Aprueba/Rechaza automaticamente
7. Padre recibe confirmacion por WhatsApp
```

**Mensaje WhatsApp que recibe el padre:**

```
🔔 SOLICITUD DE PRESTAMO BioFood

Tu hijo/a Juanito se quedo sin saldo y solicita 
un prestamo de $5.00.

¿Quieres aprobar este prestamo?
- Se cargara a tu cuenta como deuda
- Podras pagarlo con tu proxima recarga

Para APROBAR responde: SI
Para RECHAZAR responde: NO

O usa este link: https://biofood.app/loan/approve/abc123...

Token: abc123def456...
```

**Respuestas que procesa el webhook:**

| Respuesta | Accion |
|-----------|--------|
| SI, SÍ, YES, APROBAR, APPROVE | Aprueba ultimo prestamo pendiente |
| NO, RECHAZAR, REJECT | Rechaza ultimo prestamo pendiente |
| Otra | Pasa al chatbot AI normal |

**Configuracion Twilio:**

1. **Webhook URL:** Apuntar a `https://tu-dominio/chat/twilio-webhook/`
2. **Phone Number:** Configurar WhatsApp number en Twilio Console
3. **Environment:**
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```

**Archivos actualizados:**

| Archivo | Cambio |
|---------|--------|
| `transaction/services/loan_service.py` | Agregado `_send_loan_notification()` |
| `chat/views.py` | Webhook ahora procesa SI/NO para prestamos |

**Pruebas:**

```bash
# 1. Crear prestamo manualmente
python manage.py shell
>>> from transaction.services import LoanService
>>> from student.models import Student
>>> s = Student.objects.get(id=1)
>>> service = LoanService()
>>> loan = service.request_loan(s, 5.00)
# Verificar que llego WhatsApp

# 2. Probar webhook (simular respuesta Twilio)
curl -X POST http://localhost:8000/chat/twilio-webhook/ \
  -d "From=whatsapp:+573001234567&Body=SI"
```

**Nota:** En desarrollo, Twilio puede estar en modo mock (no envia SMS real).
Para produccion, configurar credenciales reales en `.env`.
