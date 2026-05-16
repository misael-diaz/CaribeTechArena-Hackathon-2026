import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Byte.settings')
django.setup()

from chat.ai_service import AIService
service = AIService()
try:
    print("Response:", service.get_response('¿Qué comió Juan hoy?', '+573001234567'))
except Exception as e:
    print("Error:", e)
