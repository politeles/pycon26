from __future__ import annotations
from dotenv import load_dotenv
from pathlib import Path
import os
from typing import Any

from fastapi import FastAPI
import uvicorn
from mcp import StdioServerParameters
from smolagents import ToolCallingAgent, DuckDuckGoSearchTool,InferenceClientModel, MCPClient


load_dotenv()
# Nota:
# El SDK oficial A2A evoluciona rápido.
# Este ejemplo usa el patrón recomendado:
# - FastAPI como transporte HTTP
# - un endpoint A2A "send_message"
# - Agent Card publicada en /.well-known/agent-card.json
#
# Dependiendo de la versión exacta de a2a-sdk,
# los nombres importables pueden variar ligeramente.
# La idea central es estable: publicar AgentCard + aceptar mensaje + devolver respuesta.

try:
    from a2a.types import AgentCard
except ImportError:
    AgentCard = dict  # fallback simple para mantener el ejemplo legible


HOST = os.getenv("PY_AGENT_HOST", "0.0.0.0")
PORT = int(os.getenv("PY_AGENT_PORT", "8001"))
BASE_URL = os.getenv("PY_AGENT_URL", f"http://localhost:{PORT}")
HF_TOKEN = os.environ["HF_TOKEN"] 

app = FastAPI(title="PY Conferences Agent")


model = InferenceClientModel(model_id="Qwen/Qwen2.5-Coder-32B-Instruct")

server_params = StdioServerParameters(
    command="python",
    args=[str(Path("Comms/MCP/conference_mcp_server.py").resolve())],
)
mcp_context = MCPClient(server_params,structured_output=True)




PY_agent = ToolCallingAgent(
    model=model,
    tools=[DuckDuckGoSearchTool(),*mcp_context.get_tools()],
    max_steps=8,
    name="PY_conferences_agent",
    description=(
        "Especialista en el congreso de Python PyCon. "
        "Responde preguntas sobre CFPs, deadlines, tracks, ranking, indexación, "
        "fechas, sedes, call for papers y diferencias entre los distintos tipos de congresos. "
        "Debe priorizar fuentes oficiales del dominio python.org."
    ),
    instructions=(
        "Eres un especialista en congresos de Python PyCon.\n"
        "Prioriza siempre la web oficial del congreso, y el dominio python.org, "
        "Si no estás seguro, dilo claramente.\n"
        "Devuelve respuestas estructuradas y breves."
    ),
)

# Agent Card muy básica
agent_card: Any = {
    "name": "PyCon Agent expert",
    "description": "Especialista en congresos de Python PyCon",
    "url": BASE_URL,
    "version": "1.0.0",
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "skills": [
        {
            "id": "pycon-expertise",
            "name": "PyCon expertise",
            "description": "Preguntas sobre congresos de Python PyCon, CFP, deadlines, tracks y sedes",
            "tags": ["python", "conference", "cfp", "research"],
        }
    ],
}


@app.get("/.well-known/agent-card.json")
async def get_agent_card():
    return agent_card


@app.post("/send_message")
async def send_message(payload: dict):
    """
    Payload esperado:
    {
        "message": "When are the deadlines for PyCon 2026?"
    }
    """
    user_message = payload["message"]
    answer = PY_agent.run(user_message)
    return {"output_text": str(answer)}


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)