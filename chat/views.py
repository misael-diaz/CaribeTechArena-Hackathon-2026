from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Conversation
from .services import TwilioService
from .ai_service import AIService
import json

@csrf_exempt
def twilio_webhook(request):
    if request.method == 'POST':
        # Get data from Twilio POST request
        from_number = request.POST.get('From', '').replace('whatsapp:', '')
        body = request.POST.get('Body', '').strip()
        
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
