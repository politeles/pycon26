from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field

DATA_FILE = Path(os.getenv("CONFERENCE_DATA_FILE", "pycon_data.json"))

mcp = FastMCP("PyCon Intelligence MCP Server")


def load_data() -> list[dict[str, Any]]:
    if not DATA_FILE.exists():
        return []

    with DATA_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("pycon_data.json debe contener una lista de eventos")

    return data


def normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def find_by_name(name: str, conferences: list[dict[str, Any]]) -> dict[str, Any] | None:
    target = normalize(name)

    for conf in conferences:
        names_to_check = [
            conf.get("name", ""),
            conf.get("short_name", ""),
            *conf.get("aliases", []),
        ]
        if any(normalize(candidate) == target for candidate in names_to_check if candidate):
            return conf

    for conf in conferences:
        haystack = " | ".join(
            [
                conf.get("name", ""),
                conf.get("short_name", ""),
                *conf.get("aliases", []),
            ]
        ).lower()
        if target in haystack:
            return conf

    return None


@mcp.tool()
def search_pycon_events(
    topic: str = Field(description="Tema de búsqueda, por ejemplo 'typing', 'web', 'data', 'packaging'"),
    year: int = Field(description="Año objetivo del evento, por ejemplo 2026"),
) -> list[dict[str, Any]]:
    """
    Busca eventos tipo PyCon relevantes por tema y año.
    """
    conferences = load_data()
    topic_norm = normalize(topic)

    results: list[dict[str, Any]] = []
    for conf in conferences:
        tags = [normalize(tag) for tag in conf.get("topics", [])]
        conf_year = conf.get("year")

        if conf_year != year:
            continue

        if any(topic_norm in tag or tag in topic_norm for tag in tags):
            results.append(
                {
                    "name": conf.get("name"),
                    "short_name": conf.get("short_name"),
                    "year": conf.get("year"),
                    "location": conf.get("location"),
                    "dates": conf.get("dates"),
                    "cfp_deadline": conf.get("deadlines", {}).get("cfp_submission"),
                    "official_url": conf.get("official_url"),
                    "topics": conf.get("topics", []),
                    "event_type": conf.get("event_type"),
                }
            )

    return results


@mcp.tool()
def get_pycon_info(
    name: str = Field(description="Nombre o alias del evento, por ejemplo 'PyCon US' o 'PyCon Italia'")
) -> dict[str, Any]:
    """
    Devuelve metadata de un evento PyCon.
    """
    conferences = load_data()
    conf = find_by_name(name, conferences)

    if conf is None:
        return {"error": f"No encontré un evento llamado '{name}'."}

    return {
        "name": conf.get("name"),
        "short_name": conf.get("short_name"),
        "year": conf.get("year"),
        "organizer": conf.get("organizer"),
        "location": conf.get("location"),
        "dates": conf.get("dates"),
        "topics": conf.get("topics", []),
        "official_url": conf.get("official_url"),
        "cfp_url": conf.get("cfp_url"),
        "description": conf.get("description"),
        "event_type": conf.get("event_type"),
        "language": conf.get("language"),
    }


@mcp.tool()
def get_pycon_deadlines(
    name: str = Field(description="Nombre o alias del evento PyCon")
) -> dict[str, Any]:
    """
    Devuelve deadlines de un evento PyCon.
    """
    conferences = load_data()
    conf = find_by_name(name, conferences)

    if conf is None:
        return {"error": f"No encontré un evento llamado '{name}'."}

    deadlines = conf.get("deadlines", {})
    return {
        "name": conf.get("name"),
        "short_name": conf.get("short_name"),
        "year": conf.get("year"),
        "cfp_open": deadlines.get("cfp_open"),
        "cfp_submission": deadlines.get("cfp_submission"),
        "notification": deadlines.get("notification"),
        "schedule_publish": deadlines.get("schedule_publish"),
        "official_url": conf.get("official_url"),
        "cfp_url": conf.get("cfp_url"),
    }


@mcp.tool()
def compare_pycons(
    names: list[str] = Field(description="Lista de eventos a comparar, por ejemplo ['PyCon US', 'PyCon Italia']")
) -> list[dict[str, Any]]:
    """
    Compara varios eventos del ecosistema PyCon.
    """
    conferences = load_data()
    results: list[dict[str, Any]] = []

    for name in names:
        conf = find_by_name(name, conferences)
        if conf is None:
            results.append({"query": name, "error": "No encontrado"})
            continue

        deadlines = conf.get("deadlines", {})
        results.append(
            {
                "name": conf.get("name"),
                "short_name": conf.get("short_name"),
                "year": conf.get("year"),
                "event_type": conf.get("event_type"),
                "location": conf.get("location"),
                "dates": conf.get("dates"),
                "topics": conf.get("topics", []),
                "cfp_submission": deadlines.get("cfp_submission"),
                "notification": deadlines.get("notification"),
                "official_url": conf.get("official_url"),
                "language": conf.get("language"),
            }
        )

    return results


@mcp.resource("pycon://{name}")
def pycon_resource(name: str) -> str:
    """
    Expone un evento PyCon como resource MCP.
    """
    conferences = load_data()
    conf = find_by_name(name, conferences)

    if conf is None:
        return f"No encontré un evento llamado '{name}'."

    deadlines = conf.get("deadlines", {})
    return (
        f"Event: {conf.get('name')} ({conf.get('short_name')})\n"
        f"Year: {conf.get('year')}\n"
        f"Organizer: {conf.get('organizer')}\n"
        f"Type: {conf.get('event_type')}\n"
        f"Location: {conf.get('location')}\n"
        f"Dates: {conf.get('dates')}\n"
        f"Language: {conf.get('language')}\n"
        f"Topics: {', '.join(conf.get('topics', []))}\n"
        f"CFP open: {deadlines.get('cfp_open')}\n"
        f"CFP submission deadline: {deadlines.get('cfp_submission')}\n"
        f"Notification: {deadlines.get('notification')}\n"
        f"Schedule publish: {deadlines.get('schedule_publish')}\n"
        f"Official URL: {conf.get('official_url')}\n"
        f"CFP URL: {conf.get('cfp_url')}\n"
        f"Description: {conf.get('description', '')}\n"
    )


if __name__ == "__main__":
    mcp.run()