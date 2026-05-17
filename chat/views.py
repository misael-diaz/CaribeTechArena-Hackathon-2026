from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Conversation
from .twilio_service import TwilioService
from .ai_service import AIService
import json

MAX_CHUNK = 10

_ai_service = None

def get_ai_service():
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service

_twilio_service = None

def get_twilio_service():
    global _twilio_service
    if _twilio_service is None:
        _twilio_service = TwilioService()
    return _twilio_service

@csrf_exempt
def twilio_webhook(request):
    if request.method == 'POST':
        from_number = request.POST.get('From', '').replace('whatsapp:', '')
        body = request.POST.get('Body', '').strip()

        conv, created = Conversation.objects.get_or_create(phone_e164=from_number)
        session = conv.session_json or {}
        history = session.get('history', [])

        history.append({'role': 'user', 'content': body})
        if len(history) > MAX_CHUNK:
            history = history[-MAX_CHUNK:]

        twilio_service = get_twilio_service()
        twilio_service.send_message(from_number, '✍️ Un momento, estoy consultando...')

        ai_service = get_ai_service()
        reply_text = ai_service.get_response(body, parent_phone=from_number, history=history)

        twilio_service.send_message(from_number, reply_text)

        history.append({'role': 'assistant', 'content': reply_text})
        if len(history) > MAX_CHUNK:
            history = history[-MAX_CHUNK:]

        session['history'] = history
        conv.session_json = session
        conv.save()

        return HttpResponse("OK", status=200)

    return HttpResponse("Method not allowed", status=405)
