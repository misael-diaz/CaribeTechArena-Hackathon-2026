import os
from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek
from deepagents import create_deep_agent, SubAgent


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

            # Define tools
            from chat.skill.get_one_today_meals.tool import get_one_today_meals
            from chat.skill.get_childs.tool import get_childs
            self.tools = [get_one_today_meals, get_childs]
            
            # Create the agent using the requested pattern
            self.agent = create_agent(
                model=self.llm,
                system_prompt=self.full_prompt,
                tools=self.tools
            )
        else:
            self.llm = None
            self.agent = None

    def get_response(self, user_input, parent_phone=None):
        if not self.agent:
            return "Lo siento, el agente no está configurado."

        # Add context to input
        content = user_input
        if parent_phone:
            content = f"[PARENT_PHONE: {parent_phone}] {user_input}"

        try:
            # Using the invoke pattern from the snippet
            result = self.agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": content,
                        }
                    ]
                }
            )
            
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
