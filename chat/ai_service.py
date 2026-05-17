import os
import time
import logging
from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek
from deepagents import create_deep_agent, SubAgent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
class AIService:
    def __init__(self):
        self.api_key = os.getenv('PROVIDER_API_KEY')
        
        if self.api_key:
            # Use ChatDeepSeek as requested
            self.llm = ChatDeepSeek(
                model="deepseek-chat",
                api_key=self.api_key,
                temperature=0,
                max_tokens=None,
                timeout=60,
                max_retries=0,
            )
            
            # Read the system prompt (full_prompt)
            try:
                prompt_path = os.path.join(os.path.dirname(__file__), 'system_prompt.md')
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    self.full_prompt = f.read()
            except Exception:
                self.full_prompt = "You are a BioFood Assistant."

            from chat.skill.get_one_today_meals.tool import get_one_today_meals
            from chat.skill.get_childs.tool import get_childs
            from chat.skill.get_student_balance.tool import get_student_balance
            from chat.skill.get_student_allergens.tool import get_student_allergens
            from chat.skill.get_recent_recharges.tool import get_recent_recharges
            from chat.skill.get_healthy_recommendations.tool import get_healthy_recommendations
            from chat.skill.get_balance_forecast.tool import get_balance_forecast
            from chat.skill.get_product_nutrition.tool import get_product_nutrition
            from chat.skill.check_allergen_safety.tool import check_allergen_safety
            from chat.skill.suggest_healthy_alternatives.tool import suggest_healthy_alternatives
            from chat.skill.get_student_summary.tool import get_student_summary, get_multi_student_summary
            from chat.skill.approve_loan.tool import approve_loan, get_pending_loans, get_loan_summary

            self.tools = [
                get_one_today_meals,
                get_childs,
                get_student_balance,
                get_student_allergens,
                get_recent_recharges,
                get_healthy_recommendations,
                get_balance_forecast,
                get_product_nutrition,
                check_allergen_safety,
                suggest_healthy_alternatives,
                get_student_summary,
                get_multi_student_summary,
                approve_loan,
                get_pending_loans,
                get_loan_summary
            ]
            
            from deepagents.backends.filesystem import FilesystemBackend
            from langgraph.checkpoint.memory import MemorySaver
            
            # Define root dir and backend for skills
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            backend = FilesystemBackend(root_dir=root_dir)
            checkpointer = MemorySaver()
            
            # Create the deep agent passing the skills folder
            self.agent = create_deep_agent(
                model=self.llm,
                system_prompt=self.full_prompt,
                tools=self.tools,
                backend=backend,
                checkpointer=checkpointer,
                skills=["/chat/skill/"]
            )
        else:
            self.llm = None
            self.agent = None

    def get_response(self, user_input, parent_phone=None):
        if not self.agent:
            return "Lo siento, el agente no está configurado."

        if parent_phone:
            from parent.models import Parent
            if not Parent.objects.filter(phone_e164=parent_phone).exists():
                return (f"El número {parent_phone} no está registrado en el sistema de BioFood "
                        "como un padre o tutor vinculado.\n\n"
                        "Por favor, comunícate con la administración de la escuela para registrar "
                        "tu número en la plataforma y acceder a los servicios.")

        # Add context to input
        content = user_input
        if parent_phone:
            content = f"[PARENT_PHONE: {parent_phone}] {user_input}"

        try:
            # Using the invoke pattern from the snippet
            start_time = time.time()
            result = self.agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": content,
                        }
                    ]
                },
                config={"configurable": {"thread_id": parent_phone or "default_thread"}}
            )
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Agent processed request for {parent_phone} in {duration:.2f} segundos")
            
            # Handle the result (result is usually a dict or an object with content)
            if isinstance(result, dict):
                if "output" in result:
                    return result["output"]
                elif "messages" in result and len(result["messages"]) > 0:
                    return result["messages"][-1].content
                else:
                    return str(result)
            elif hasattr(result, 'content'):
                return result.content
            else:
                return str(result)
                
        except Exception as e:
            print(f"Error in Agent: {e}")
            return "Lo siento, no tengo información disponible en este momento."
