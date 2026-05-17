from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Conversation
from .twilio_service import TwilioService
from .ai_service import AIService
import json

@csrf_exempt
def twilio_webhook(request):
    if request.method == 'POST':
        # Get data from Twilio POST request
        from_number = request.POST.get('From', '').replace('whatsapp:', '')
        body = request.POST.get('Body', '').strip()

        # PRIMERO: Verificar si es respuesta a préstamo (SI/NO o token)
        upper_body = body.upper()
        
        if upper_body in ['SI', 'SÍ', 'YES', 'APROBAR', 'APPROVE']:
            # Intentar aprobar el último préstamo pendiente
            from transaction.services import LoanService
            from transaction.models import Loan
            from parent.models import Parent
            
            parent = Parent.objects.filter(phone_e164=from_number).first()
            if parent:
                pending_loan = Loan.objects.filter(
                    parent=parent,
                    status='PENDING'
                ).order_by('-created_at').first()
                
                if pending_loan:
                    service = LoanService()
                    loan = service.approve_loan(pending_loan.approval_token)
                    
                    if loan:
                        twilio = TwilioService()
                        twilio.send_message(
                            from_number,
                            f"✅ PRESTAMO APROBADO\n\n"
                            f"Se agregaron ${loan.amount} al saldo de {loan.student.name}.\n"
                            f"Este monto se cargo a tu cuenta como deuda."
                        )
                        return HttpResponse("OK", status=200)
        
        elif upper_body in ['NO', 'RECHAZAR', 'REJECT']:
            # Rechazar último préstamo pendiente
            from transaction.services import LoanService
            from transaction.models import Loan
            from parent.models import Parent
            
            parent = Parent.objects.filter(phone_e164=from_number).first()
            if parent:
                pending_loan = Loan.objects.filter(
                    parent=parent,
                    status='PENDING'
                ).order_by('-created_at').first()
                
                if pending_loan:
                    service = LoanService()
                    loan = service.reject_loan(pending_loan.approval_token)
                    
                    if loan:
                        twilio = TwilioService()
                        twilio.send_message(
                            from_number,
                            f"❌ PRESTAMO RECHAZADO\n\n"
                            f"El prestamo de ${loan.amount} para {loan.student.name} ha sido cancelado."
                        )
                        return HttpResponse("OK", status=200)
        
        # SEGUNDO: Si no es respuesta a préstamo, usar AI
        conv, created = Conversation.objects.get_or_create(phone_e164=from_number)

        ai_service = AIService()
        reply_text = ai_service.get_response(body, parent_phone=from_number)

        twilio_service = TwilioService()
        twilio_service.send_message(from_number, reply_text)

        session = conv.session_json or {}
        session['last_message'] = body
        conv.session_json = session
        conv.save()

        return HttpResponse("OK", status=200)

    return HttpResponse("Method not allowed", status=405)
