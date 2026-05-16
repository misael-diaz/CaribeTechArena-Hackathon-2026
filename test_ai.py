import os
import django
from dotenv import load_dotenv

# Load env before anything else
load_dotenv()

# Setup Django (needed because AIService reads prompt from file relative to its location)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Byte.settings')
django.setup()

from chat.ai_service import AIService

def test_ai():
    print("Testing AIService with DeepSeek...")
    ai = AIService()
    
    question = "Hola, ¿quién eres y qué puedes hacer por mí en BioFood?"
    print(f"User: {question}")
    
    response = ai.get_response(question)
    try:
        print(f"\nAI: {response}")
    except UnicodeEncodeError:
        print(f"\nAI: {response.encode('ascii', 'ignore').decode('ascii')} (Note: Emojis were removed for console display)")

if __name__ == "__main__":
    test_ai()
