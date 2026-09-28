"""
AI Agent
========
The main agent loop using httpx (already installed via FastAPI).
"""

import json
import httpx
from typing import Optional

from app.agent.router import select_model, get_model_name, ModelRole
from app.agent.tools import call_tool, get_tools_for_ai, TOOL_REGISTRY


OLLAMA_URL = "http://host.docker.internal:11434"
TIMEOUT = 120.0


def query_ollama(
    model: str,
    messages: list[dict],
    tools: Optional[list[dict]] = None,
) -> dict:
    """Send a chat request to Ollama using httpx."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools

    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        return {"error": str(e)}


SYSTEM_PROMPT = """You are VeggieOps AI, an expert assistant for a vegetable resale business.

You help the shop owner make data-driven decisions by answering questions about:
- Lots (acquisition, status, location, profit/loss)
- Farmers (performance, reliability, quality)
- Inventory (current stock, value, expiring items)
- Sales (revenue, customers, trends)
- Purchase orders (status, overdue, expected deliveries)

You have access to tools that query the real database. Use them to get accurate, up-to-date data.

Guidelines:
1. ALWAYS use tools when the question requires data. Never guess numbers.
2. If a tool call fails, explain what went wrong and suggest an alternative question.
3. When presenting data, format numbers clearly (e.g., "$1,234.56" not "1234.56").
4. Give actionable insights, not just raw data. If a lot is losing money, explain why.
5. Be concise but thorough. The shop owner is busy.
6. When listing multiple items, summarize the most important ones first.

Today's date is 2026-09-28. The shop has been operating for 6 months.
"""


def run_agent(
    user_query: str,
    conversation_history: Optional[list[dict]] = None,
    override_model: Optional[ModelRole] = None,
) -> dict:
    """
    Run the AI agent with a user query.
    
    Returns:
        {
            "response": "AI's text response",
            "model_used": "model name",
            "tools_called": ["tool1", "tool2"],
            "conversation": [full message history]
        }
    """
    role = select_model(user_query, override=override_model)
    model = get_model_name(role)
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_query})
    
    tools = get_tools_for_ai()
    tools_called = []
    max_iterations = 5
    
    for iteration in range(max_iterations):
        response = query_ollama(model, messages, tools=tools)
        
        if "error" in response:
            return {
                "response": f"Error calling AI: {response['error']}",
                "model_used": model,
                "tools_called": tools_called,
                "conversation": messages,
            }
        
        message = response.get("message", {})
        messages.append(message)
        
        tool_calls = message.get("tool_calls")
        
        if not tool_calls:
            return {
                "response": message.get("content", ""),
                "model_used": model,
                "tools_called": tools_called,
                "conversation": messages,
            }
        
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = tool_call["function"]["arguments"]
            
            if isinstance(tool_args, str):
                tool_args = json.loads(tool_args)
            
            print(f"  [Tool Call] {tool_name}({tool_args})")
            
            result = call_tool(tool_name, tool_args)
            tools_called.append(tool_name)
            
            messages.append({
                "role": "tool",
                "content": json.dumps(result, default=str),
            })
    
    return {
        "response": "I apologize, but I'm having trouble completing this request. Could you rephrase?",
        "model_used": model,
        "tools_called": tools_called,
        "conversation": messages,
    }
