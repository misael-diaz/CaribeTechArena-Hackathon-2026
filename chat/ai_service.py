import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class AIService:
    def __init__(self):
        self.api_key = os.getenv('PROVIDER_API_KEY')
        self.base_url = os.getenv('PROVIDER_URL', 'https://api.openai.com/v1')
        
        if self.api_key:
            # Flexible configuration using ChatOpenAI (compatible with DeepSeek and others)
            self.llm = ChatOpenAI(
                model="deepseek-chat", # Keeping the model name as it's likely what the provider needs
                openai_api_key=self.api_key,
                base_url=self.base_url,
                temperature=0,
                max_tokens=None,
                timeout=60,
                max_retries=0,
            )
        else:
            self.llm = None

    def get_response(self, user_input, conversation_history=None):
        if not self.llm:
            return "Lo siento, el proveedor de IA no está configurado. Por favor, revisa tu PROVIDER_API_KEY en el archivo .env."

        # Read the system prompt from the external markdown file
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), 'system_prompt.md')
            with open(prompt_path, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
        except Exception as e:
            print(f"Error reading prompt file: {e}")
            system_prompt = "Eres un asistente virtual de BioFood."

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        try:
            result = chain.invoke({"input": user_input})
            return result
        except Exception as e:
            print(f"Error in AI Service: {e}")
            return "Lo siento, tuve un problema procesando tu solicitud."
