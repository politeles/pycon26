from __future__ import annotations
from dotenv import load_dotenv
import asyncio
import json
import os
from typing import Optional

import requests

from smolagents import ToolCallingAgent, DuckDuckGoSearchTool,InferenceClientModel, tool


load_dotenv()

HF_TOKEN = os.environ["HF_TOKEN"] 
A2A_PY_URL = os.getenv("A2A_PY_URL", "http://localhost:8001")


def is_PY_topic(query: str) -> bool:
    q = query.lower()
    keywords = [
        "PYCON", "python conference", "cfp", "call for papers", "deadline",
        "submission", "camera ready", "workshop", "symposium",
        "transactions"
    ]
    return any(k in q for k in keywords)


@tool
def ask_PY_agent_via_a2a(question: str) -> str:
    """
    Envía una pregunta al agente especializado en PY conferences vía A2A/HTTP.
    Úsalo cuando la consulta trate sobre conferencias PY, CFPs, deadlines,
    sedes, ranking, tracks o comparación entre congresos PY.
    Args:
        question (str): Pregunta sobre conferencias PYCON, CFPs, deadlines,
            sedes, ranking, tracks o comparación entre congresos PYCON.

    Returns:
        str: Respuesta generada por el agente especializado.
    """
    # Paso 1: resolver Agent Card
    card_url = f"{A2A_PY_URL}/.well-known/agent-card.json"
    card_resp = requests.get(card_url, timeout=20)
    card_resp.raise_for_status()
    card = card_resp.json()

    # Paso 2: enviar mensaje al agente remoto
    # En una integración A2A más completa, aquí usarías el cliente oficial
    # de a2a-sdk para construir la conexión desde la URL/card.
    send_url = f"{card['url']}/send_message"
    msg_resp = requests.post(send_url, json={"message": question}, timeout=60)
    msg_resp.raise_for_status()
    data = msg_resp.json()

    return data["output_text"]


def main() -> None:

    model = InferenceClientModel(model_id="Qwen/Qwen2.5-Coder-32B-Instruct")

    web_agent = ToolCallingAgent(
        model=model,
        tools=[
            DuckDuckGoSearchTool(),
            ask_PY_agent_via_a2a,
        ],
        max_steps=10,
        name="web_research_agent",
        description=(
            "Agente generalista de búsqueda web. "
            "Cuando el tema sea PYCON conferences, delega en el agente especializado vía A2A."
        ),
        instructions=(
            "Eres un agente generalista de investigación web.\n"
            "Usa DuckDuckGoSearchTool para búsqueda general.\n"
            "Si la consulta es sobre PYCON conferences, CFPs, deadlines, venues, "
            "tracks o comparativas de congresos PY, usa ask_PY_agent_via_a2a.\n"
            "No inventes datos. Si te faltan evidencias, dilo."
        ),
    )

    question = input("Pregunta: ").strip()
    answer = web_agent.run(question)
    print("\n=== RESPUESTA ===\n")
    print(answer)


if __name__ == "__main__":
    main()