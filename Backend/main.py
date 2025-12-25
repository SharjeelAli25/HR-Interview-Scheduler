from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # type: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[reportMissingImports]
from fastapi.staticfiles import StaticFiles  # type: ignore[reportMissingImports]
import json
import asyncio
import traceback
from database import init_db, get_all_interviews
from agent import init_agent, get_agent

 
app = FastAPI(
    title="AI HR Interview Scheduler",
    description="A simple chat-based interview scheduling system"
)
 
# Enable CORS so frontend can communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*50)
    print("🚀 AI HR Interview Scheduler Starting Up")
    print("="*50)
   
    init_db()  # Create/initialize SQLite database
    init_agent()  # Initialize the AI agent
   
    print("\n✓ Server ready at http://localhost:8000")
    print("✓ WebSocket endpoint at ws://localhost:8000/ws")
    print("✓ Swagger docs at http://localhost:8000/docs")
    print("="*50 + "\n")
 
# Health check endpoint
@app.get("/health")
async def health_check(): #check server status is it running or not
    return {
        "status": "ok",
        "message": "AI HR Interview Scheduler is running"
    }
 
ACTIVE_CONNECTIONS = set()
_LAST_AGENT_MESSAGE = {}

async def _broadcast_interviews():
    interviews = get_all_interviews()
    payload = {
        "text": "Updated interviews",
        "sender": "server",
        "action": "broadcast",
        "interviews": interviews
    }
    dead = []
    for ws in list(ACTIVE_CONNECTIONS):
        try:
            await ws.send_json(payload)
        except Exception:
            # collect dead websockets for cleanup
            dead.append(ws)
    for ws in dead:
        ACTIVE_CONNECTIONS.discard(ws)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    
    """

    await websocket.accept()
    print(f"📱 New WebSocket connection from {websocket.client}")
    ACTIVE_CONNECTIONS.add(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                # Treat raw text as chat text
                message = {"text": data}

            # Normalize
            user_text = message.get("text", "").strip()
            action = message.get("action")
            params = message.get("params", {})

            # If the user replied with just a number and the last agent message asked
            # for an ID, convert it to a delete action for convenience.
            last_agent = _LAST_AGENT_MESSAGE.get(id(websocket), "")
            if user_text.isdigit() and "delete" in last_agent.lower():
                action = "delete_interview"
                params = {"interview_id": int(user_text)}
                user_text = ""  # clear so we don't send it to the LLM

            try:
                # If client requested an explicit action, run the tool directly
                if action is not None:
                    # Load tool map and validate the action against available tools
                    try:
                        from tools import TOOLS as TOOL_MAP
                    except Exception:
                        TOOL_MAP = {}

                    tool_func = TOOL_MAP.get(action)
                    if tool_func is None:
                        await websocket.send_json({"text": f"Unrecognized or missing tool for action '{action}'", "sender": "server", "interviews": get_all_interviews()})
                    else:
                        result_str = await asyncio.to_thread(tool_func, **params)
                        # Send immediate result back to the requesting client
                        await websocket.send_json({"text": result_str, "sender": "server", "action": action, "interviews": get_all_interviews()})

                        # Broadcast updated interviews to everyone
                        await _broadcast_interviews()

                # Otherwise, treat as chat text and let the AI agent process it
                elif user_text:
                    print(f"💬 User: {user_text}")
                    agent = get_agent()
                    result = await asyncio.to_thread(agent.process_message, user_text)

                    # Send response back to the requesting client
                    response = {
                        "text": result["response"],
                        "sender": "agent",
                        "action": result.get("action"),
                        "interviews": result["interviews"]
                    }

                    _LAST_AGENT_MESSAGE[id(websocket)] = result["response"]

                    print(f"🤖 Agent: {result['response']}")
                    await websocket.send_json(response)

                    # Always broadcast interviews after processing - keep all clients in sync
                    await _broadcast_interviews()

                else:
                    await websocket.send_json({"text": "Please send a message.", "sender": "agent", "interviews": get_all_interviews()})

            except Exception as e:
                print(f"❌ Error processing message: {e}\n{traceback.format_exc()}")
                await websocket.send_json({"text": f"Error processing your request: {str(e)}", "sender": "agent", "interviews": get_all_interviews()})

    except WebSocketDisconnect:
        print(f"📴 WebSocket disconnected from {websocket.client}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        ACTIVE_CONNECTIONS.discard(websocket)
        _LAST_AGENT_MESSAGE.pop(id(websocket), None)
 
if __name__ == "__main__":
    """
    Run the server:
    python -m uvicorn main:app --reload
   
    Then:
    - Go to http://localhost:8000/docs for Swagger UI
    - Frontend connects to ws://localhost:8000/ws
    """
    import uvicorn  # type: ignore[reportMissingImports]
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )