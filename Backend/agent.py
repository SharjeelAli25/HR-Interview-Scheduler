import json
import os
import traceback
from typing import TYPE_CHECKING

try:
    from langchain_groq import ChatGroq  # type: ignore[reportMissingImports]
except Exception:
    ChatGroq = None

if TYPE_CHECKING:
    from langchain_groq import ChatGroq  # type: ignore[reportMissingImports]

try:
    from tools import TOOLS
except Exception:
    print("⚠ tools.py not found. Using dev stub TOOLS.")
    def _stub_create(title, description):
        pass
    def _stub_read():
        return []
    def _stub_update(interview_id, title, description):
        pass
    def _stub_delete(interview_id):
        pass
    TOOLS = {
        "create_interview": _stub_create,
        "read_interviews": _stub_read,
        "update_interview": _stub_update,
        "delete_interview": _stub_delete,
    }

try:
    from database import get_all_interviews
except Exception:
    print("⚠ database.py not found. Using dev stub get_all_interviews.")
    def get_all_interviews():
        return []

 
def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠ GROQ_API_KEY not set. Using simple rule-based responses.")
        return None
    if ChatGroq is None:
        print("⚠ langchain_groq not installed. Using simple rule-based responses.")
        return None
    try:
        print("✓ Using Groq LLM")
        return ChatGroq(model="mixtral-8x7b-32768", temperature=0.3, groq_api_key=api_key)
    except Exception as e:
        print(f"⚠ Failed to initialize Groq LLM, falling back: {e}")
        return None
 

SYSTEM_PROMPT = """
 
Tools:
- create_interview(title, description)
- read_interviews()
- update_interview(interview_id, title, description)
- delete_interview(interview_id)
 
Always respond in JSON, either:
{"action":"respond","response":"..."}
or
{"action":"create_interview|read_interviews|update_interview|delete_interview","params":{...},"response":"..."}
"""
 
class SimpleAgent:
    """
    A simple AI agent that:
    1. Receives a user message
    2. Decides whether to call a tool or just respond
    3. Calls the appropriate tool if needed
    4. Returns a response with the updated interview list
    """
   
    def __init__(self):
        self.llm = get_llm()
        self.conversation_history = []
   
    def process_message(self, user_message: str) -> dict:
        """
        Process a user message and return AI response.
       
        Args:
            user_message: The message from the user
       
        Returns:
            Dictionary with:
            - response: AI's text response
            - action: What the agent did (tool name or "respond")
            - interviews: Updated interview list
        """
       
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
       
        # Decide with LLM if available; else rule-based fallback
        if self.llm is not None:
            prompt = self._build_prompt(user_message)
            try:
                result = self.llm.invoke(prompt)
                llm_response = getattr(result, "content", str(result))
            except Exception as e:
                print(f"Error calling LLM: {e}")
                llm_response = self._get_fallback_response(user_message)
        else:
            llm_response = self._get_fallback_response(user_message)
       
        # Parse the LLM response
        result = self._parse_llm_response(llm_response, user_message)
       
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": result["response"]
        })
       
        return result
   
    def _build_prompt(self, user_message: str) -> str:
        prompt = SYSTEM_PROMPT + "\n\n"
       
        # Add last 5 messages of conversation history
        for msg in self.conversation_history[-5:]:
            role = msg["role"].upper()
            prompt += f"{role}: {msg['content']}\n"
       
        prompt += f"USER: {user_message}\nAGENT: "
       
        return prompt
   
    def _parse_llm_response(self, llm_response: str, user_message: str) -> dict:
        try:
            # Try to parse as JSON
            parsed = json.loads(llm_response)
            action = parsed.get("action", "respond")
            response_text = parsed.get("response", "Understood.")
            params = parsed.get("params", {})
           
        except json.JSONDecodeError:
            # If not JSON, treat as a simple response
            action = "respond"
            response_text = llm_response
            params = {}
       
        # Validate action
        if action != "respond" and action not in TOOLS:
            response_text = f"Unrecognized action '{action}'. No tool called."
            action = "respond"
       
        # Execute tool if requested
        if action in TOOLS and action != "respond":
            tool_func = TOOLS[action]
            try:
                if action == "create_interview":
                    tool_func(params.get("title", "New Interview"), params.get("description", ""))
                elif action == "update_interview":
                    tool_func(params.get("interview_id"), params.get("title"), params.get("description"))
                elif action == "delete_interview":
                    tool_func(params.get("interview_id"))
                elif action == "read_interviews":
                    tool_func()
            except Exception as e:
                tb = traceback.format_exc()
                print(f"Error executing tool '{action}': {e}\n{tb}")
                response_text = f"Error executing tool '{action}': {e}"
 
        # Always return latest interviews
        interviews = get_all_interviews()
        return {"response": response_text, "action": action, "interviews": interviews}
   
    def _get_fallback_response(self, user_message: str) -> str:
        """
        Fallback response if LLM fails.
        Simple pattern matching for demo purposes.
        """
        message_lower = user_message.lower()
       
        if any(w in message_lower for w in ("create", "schedule", "add", "book")):
            return '{"action":"create_interview","params":{"title":"New Interview","description":""},"response":"Scheduled."}'
        if any(w in message_lower for w in ("view", "list", "show", "check")):
            return '{"action":"read_interviews","response":"Here are all the interviews."}'
        if any(w in message_lower for w in ("delete", "cancel", "remove")):
            return '{"action":"respond","response":"Which interview ID should I delete?"}'
        return '{"action":"respond","response":"How can I help with your interviews?"}'
 
# Create a global agent instance
agent = None
 
def init_agent():
    """Initialize the agent (called on startup)."""
    global agent
    agent = SimpleAgent()
    print("✓ AI Agent initialized")
 
def get_agent() -> SimpleAgent:
    """Get the agent instance."""
    global agent
    if agent is None:
        init_agent()
    return agent