import json
import re

import requests


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"


def _slug_to_title(value):
    return " ".join(part.capitalize() for part in re.split(r"[^a-zA-Z0-9]+", value) if part)


def _detect_app_type(project_name, project_description):
    text = f"{project_name} {project_description}".lower()
    mapping = [
        ("chatbot", ["chatbot", "assistant", "support bot", "conversation"]),
        ("analyzer", ["analyzer", "analysis", "insight", "review", "score"]),
        ("dashboard", ["dashboard", "analytics", "metrics", "monitoring"]),
        ("tracker", ["tracker", "tracking", "planner", "management", "workflow"]),
        ("generator", ["generator", "builder", "creator", "automation"]),
        ("marketplace", ["marketplace", "store", "shop", "catalog"]),
    ]
    for app_type, keywords in mapping:
        if any(keyword in text for keyword in keywords):
            return app_type
    return "productivity-app"


def _heuristic_blueprint(project_name, project_description, tech_stack):
    app_type = _detect_app_type(project_name, project_description)
    audience = "students, developers, founders, and operations teams"

    feature_map = {
        "chatbot": [
            "Conversational question input",
            "Context-aware answer panel",
            "Suggested follow-up prompts",
            "Session summary and notes",
        ],
        "analyzer": [
            "Upload or paste source material",
            "Structured analysis results",
            "Highlights, risks, and recommendations",
            "Actionable next-step summary",
        ],
        "dashboard": [
            "Summary metrics and health indicators",
            "Filterable detail views",
            "Insight and trend panels",
            "Operational action list",
        ],
        "tracker": [
            "Create and organize work items",
            "Status overview and prioritization",
            "Upcoming tasks and reminders",
            "Progress summary and next actions",
        ],
        "generator": [
            "Project idea capture",
            "Generated deliverables and summaries",
            "Downloadable outputs",
            "Guided next-step workflow",
        ],
        "marketplace": [
            "Browse featured catalog items",
            "Search and compare items",
            "Item details and recommendations",
            "Saved selections and follow-ups",
        ],
        "productivity-app": [
            "Capture project inputs",
            "Generate structured results",
            "Review outputs and recommendations",
            "Download and share artifacts",
        ],
    }

    entity_map = {
        "chatbot": ["conversation", "message", "topic", "advice"],
        "analyzer": ["document", "score", "finding", "recommendation"],
        "dashboard": ["metric", "trend", "alert", "report"],
        "tracker": ["task", "status", "owner", "deadline"],
        "generator": ["brief", "artifact", "template", "summary"],
        "marketplace": ["item", "category", "comparison", "selection"],
        "productivity-app": ["request", "result", "section", "summary"],
    }

    endpoint_map = {
        "chatbot": [
            {"method": "GET", "path": "/", "purpose": "Service status"},
            {"method": "GET", "path": "/blueprint", "purpose": "Project configuration"},
            {"method": "POST", "path": "/run", "purpose": "Generate a structured assistant reply"},
        ],
        "analyzer": [
            {"method": "GET", "path": "/", "purpose": "Service status"},
            {"method": "GET", "path": "/blueprint", "purpose": "Project configuration"},
            {"method": "POST", "path": "/run", "purpose": "Analyze submitted content"},
        ],
        "dashboard": [
            {"method": "GET", "path": "/", "purpose": "Service status"},
            {"method": "GET", "path": "/blueprint", "purpose": "Project configuration"},
            {"method": "POST", "path": "/run", "purpose": "Generate dashboard insight summary"},
        ],
        "tracker": [
            {"method": "GET", "path": "/", "purpose": "Service status"},
            {"method": "GET", "path": "/blueprint", "purpose": "Project configuration"},
            {"method": "POST", "path": "/run", "purpose": "Generate work planning guidance"},
        ],
        "generator": [
            {"method": "GET", "path": "/", "purpose": "Service status"},
            {"method": "GET", "path": "/blueprint", "purpose": "Project configuration"},
            {"method": "POST", "path": "/run", "purpose": "Generate project-specific output"},
        ],
        "marketplace": [
            {"method": "GET", "path": "/", "purpose": "Service status"},
            {"method": "GET", "path": "/blueprint", "purpose": "Project configuration"},
            {"method": "POST", "path": "/run", "purpose": "Generate shopping or comparison guidance"},
        ],
        "productivity-app": [
            {"method": "GET", "path": "/", "purpose": "Service status"},
            {"method": "GET", "path": "/blueprint", "purpose": "Project configuration"},
            {"method": "POST", "path": "/run", "purpose": "Generate structured app output"},
        ],
    }

    sample_map = {
        "chatbot": [
            "What questions can I ask this assistant?",
            "Give me a quick summary for a first-time user.",
            "What should I do next based on this issue?",
        ],
        "analyzer": [
            "Review this resume and suggest improvements.",
            "Analyze this product brief and highlight gaps.",
            "Summarize strengths, risks, and next steps.",
        ],
        "dashboard": [
            "Summarize the current performance snapshot.",
            "What should the team pay attention to today?",
            "List the biggest risks and opportunities.",
        ],
        "tracker": [
            "Help me organize this sprint plan.",
            "What should I prioritize next?",
            "Summarize outstanding work and blockers.",
        ],
        "generator": [
            "Generate the first version of this project output.",
            "Summarize the deliverables and what to do next.",
            "What can I improve in this generated project?",
        ],
        "marketplace": [
            "Compare the best options for a first-time buyer.",
            "Summarize the catalog in plain language.",
            "What should I consider before making a choice?",
        ],
        "productivity-app": [
            "Summarize the current request in plain language.",
            "What are the next steps for this project?",
            "Turn this input into a useful response.",
        ],
    }

    return {
        "project_name": project_name.strip(),
        "tagline": f"{_slug_to_title(project_name)} built with {tech_stack.strip() or 'FastAPI + Streamlit + Python'}",
        "app_type": app_type,
        "primary_goal": project_description.strip(),
        "audience": audience,
        "core_features": feature_map[app_type],
        "key_entities": entity_map[app_type],
        "api_endpoints": endpoint_map[app_type],
        "frontend_sections": [
            "Overview",
            "Primary Input",
            "Response Output",
            "Suggested Actions",
        ],
        "sample_inputs": sample_map[app_type],
        "response_style": "structured, concise, and practical",
        "tech_stack": tech_stack.strip() or "FastAPI + Streamlit + Python",
    }


def _ask_ollama_for_blueprint(project_name, project_description, tech_stack):
    prompt = f"""
You are helping generate a runnable starter application.

Project name: {project_name}
Project description: {project_description}
Tech stack: {tech_stack}

Return only valid JSON with this shape:
{{
  "tagline": "short tagline",
  "app_type": "chatbot | analyzer | dashboard | tracker | generator | marketplace | productivity-app",
  "primary_goal": "one sentence goal",
  "audience": "target users",
  "core_features": ["feature 1", "feature 2", "feature 3", "feature 4"],
  "key_entities": ["entity 1", "entity 2", "entity 3", "entity 4"],
  "api_endpoints": [
    {{"method": "GET", "path": "/", "purpose": "status"}},
    {{"method": "GET", "path": "/blueprint", "purpose": "project config"}},
    {{"method": "POST", "path": "/run", "purpose": "main action"}}
  ],
  "frontend_sections": ["section 1", "section 2", "section 3", "section 4"],
  "sample_inputs": ["sample input 1", "sample input 2", "sample input 3"],
  "response_style": "brief style guidance"
}}
"""

    session = requests.Session()
    session.trust_env = False
    response = session.post(
        OLLAMA_URL,
        json={
            "model": "llama3:8b",
            "prompt": prompt,
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    raw = response.json().get("response", "")
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("Ollama did not return JSON")
    return json.loads(match.group())


def generate_blueprint(project_name, project_description, tech_stack):
    blueprint = _heuristic_blueprint(project_name, project_description, tech_stack)

    try:
        llm_blueprint = _ask_ollama_for_blueprint(project_name, project_description, tech_stack)
        blueprint.update({
            "tagline": llm_blueprint.get("tagline") or blueprint["tagline"],
            "app_type": llm_blueprint.get("app_type") or blueprint["app_type"],
            "primary_goal": llm_blueprint.get("primary_goal") or blueprint["primary_goal"],
            "audience": llm_blueprint.get("audience") or blueprint["audience"],
            "core_features": llm_blueprint.get("core_features") or blueprint["core_features"],
            "key_entities": llm_blueprint.get("key_entities") or blueprint["key_entities"],
            "api_endpoints": llm_blueprint.get("api_endpoints") or blueprint["api_endpoints"],
            "frontend_sections": llm_blueprint.get("frontend_sections") or blueprint["frontend_sections"],
            "sample_inputs": llm_blueprint.get("sample_inputs") or blueprint["sample_inputs"],
            "response_style": llm_blueprint.get("response_style") or blueprint["response_style"],
        })
    except Exception:
        pass

    return blueprint
