import json
from pathlib import Path
import re
import shutil
import textwrap
import zipfile

from app.services.blueprint_generator import generate_blueprint


PROJECTS_DIR = Path(__file__).resolve().parents[2] / "artifacts" / "generated_projects"


def slugify(value):
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "ai-project"


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def _json_dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _join_lines(items):
    return "\n".join(f"- {item}" for item in items)


def _endpoint_lines(endpoints):
    return "\n".join(f"- `{item['method']} {item['path']}`: {item['purpose']}" for item in endpoints)


def _py_list(values):
    return json.dumps(values)


def create_project(project_name, project_description, tech_stack):
    name = project_name.strip()
    description = project_description.strip()
    stack = tech_stack.strip() or "FastAPI + Streamlit + Python"

    if not name:
        return {
            "ok": False,
            "message": "Project name is required.",
            "project_path": "",
            "zip_path": "",
            "files": [],
        }

    if not description:
        return {
            "ok": False,
            "message": "Project description is required.",
            "project_path": "",
            "zip_path": "",
            "files": [],
        }

    slug = slugify(name)
    project_path = PROJECTS_DIR / slug
    zip_path = PROJECTS_DIR / f"{slug}.zip"

    if project_path.exists():
        shutil.rmtree(project_path)
    if zip_path.exists():
        zip_path.unlink()

    blueprint = generate_blueprint(name, description, stack)
    feature_lines = _join_lines(blueprint["core_features"])
    entity_lines = _join_lines(blueprint["key_entities"])
    section_lines = _join_lines(blueprint["frontend_sections"])
    sample_lines = _join_lines(blueprint["sample_inputs"])
    endpoint_lines = _endpoint_lines(blueprint["api_endpoints"])
    features_py = _py_list(blueprint["core_features"])
    entities_py = _py_list(blueprint["key_entities"])
    samples_py = _py_list(blueprint["sample_inputs"])

    files = {
        "README.md": f"""
        # {name}

        {blueprint["tagline"]}

        ## Overview

        {blueprint["primary_goal"]}

        Audience: {blueprint["audience"]}

        ## Tech Stack

        {stack}

        ## Core Features

        {feature_lines}

        ## Key Entities

        {entity_lines}

        ## Frontend Sections

        {section_lines}

        ## API Endpoints

        {endpoint_lines}

        ## Sample Inputs

        {sample_lines}

        ## Run Locally

        ```bash
        python -m venv .venv
        .venv\\Scripts\\activate
        pip install -r requirements.txt
        python -m uvicorn backend.main:app --reload
        ```

        In another terminal:

        ```bash
        streamlit run frontend/app.py
        ```

        ## API Quick Test

        ```bash
        curl -X POST http://127.0.0.1:8000/chat ^
          -H "Content-Type: application/json" ^
          -d "{{\\"message\\": \\"{blueprint['sample_inputs'][0]}\\"}}"
        ```

        ## Project Structure

        ```text
        backend/     FastAPI app, routes, schemas, services, and JSON storage
        frontend/    Streamlit user interface
        shared/      Generated blueprint used by backend and frontend
        tests/       Basic API smoke tests
        ```
        """,
        "requirements.txt": """
        fastapi
        uvicorn
        streamlit
        requests
        pydantic
        python-dotenv
        pytest
        httpx
        """,
        ".gitignore": """
        __pycache__/
        *.pyc
        .venv/
        venv/
        .env
        data/*.json
        !data/.gitkeep
        """,
        ".env.example": """
        APP_ENV=development
        API_HOST=http://127.0.0.1:8000
        """,
        "backend/__init__.py": "",
        "backend/main.py": """
        import json
        from pathlib import Path

        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        from backend.models import ChatRequest, ChatResponse, FeedbackRequest
        from backend.services.assistant import generate_reply
        from backend.storage import append_feedback, list_feedback

        PROJECT_ROOT = Path(__file__).resolve().parents[1]
        BLUEPRINT_PATH = PROJECT_ROOT / "shared" / "project_blueprint.json"
        BLUEPRINT = json.loads(BLUEPRINT_PATH.read_text(encoding="utf-8"))

        app = FastAPI(
            title=BLUEPRINT["project_name"],
            description=BLUEPRINT["primary_goal"],
            version="1.0.0",
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


        @app.get("/")
        def home():
            return {
                "status": "running",
                "project": BLUEPRINT["project_name"],
                "app_type": BLUEPRINT["app_type"],
            }


        @app.get("/health")
        def health():
            return {"ok": True}


        @app.get("/blueprint")
        def get_blueprint():
            return BLUEPRINT


        @app.post("/chat", response_model=ChatResponse)
        def chat(req: ChatRequest):
            return generate_reply(BLUEPRINT, req.message)


        @app.post("/run", response_model=ChatResponse)
        def run(req: ChatRequest):
            return generate_reply(BLUEPRINT, req.message)


        @app.post("/feedback")
        def feedback(req: FeedbackRequest):
            return append_feedback(req)


        @app.get("/feedback")
        def feedback_items():
            return {"items": list_feedback()}
        """,
        "backend/models.py": """
        from pydantic import BaseModel, Field


        class ChatRequest(BaseModel):
            message: str = Field(..., min_length=1)


        class ChatResponse(BaseModel):
            project: str
            message: str
            answer: str
            suggestions: list[str]
            next_steps: list[str]


        class FeedbackRequest(BaseModel):
            name: str = Field(default="Anonymous", max_length=80)
            rating: int = Field(..., ge=1, le=5)
            comment: str = Field(default="", max_length=1000)
        """,
        "backend/services/__init__.py": "",
        "backend/services/assistant.py": f"""
        DOMAIN_FEATURES = {features_py}
        DOMAIN_ENTITIES = {entities_py}
        SAMPLE_INPUTS = {samples_py}


        def _pick_relevant_terms(message: str) -> list[str]:
            lowered = message.lower()
            matches = [
                item for item in DOMAIN_FEATURES + DOMAIN_ENTITIES
                if any(part.lower() in lowered for part in item.split()[:2])
            ]
            return matches[:4] or DOMAIN_FEATURES[:3]


        def generate_reply(blueprint: dict, message: str) -> dict:
            terms = _pick_relevant_terms(message)
            focus = ", ".join(terms)
            answer = (
                f"Thanks for sharing that. For {{blueprint['project_name']}}, "
                f"the best response is to focus on {{focus}}. "
                f"Based on your input, start with the user's immediate need, "
                f"keep the workflow simple, and turn the result into clear next actions."
            )
            suggestions = [
                f"Ask about {{DOMAIN_ENTITIES[0]}} details",
                f"Use {{DOMAIN_FEATURES[0].lower()}}",
                SAMPLE_INPUTS[0],
            ]
            next_steps = [
                "Confirm the user's goal",
                "Collect the minimum required details",
                "Return a concise recommendation",
                "Offer one practical follow-up action",
            ]
            return {{
                "project": blueprint["project_name"],
                "message": message,
                "answer": answer,
                "suggestions": suggestions,
                "next_steps": next_steps,
            }}
        """,
        "backend/storage.py": """
        import json
        from datetime import datetime, timezone
        from pathlib import Path

        from backend.models import FeedbackRequest

        PROJECT_ROOT = Path(__file__).resolve().parents[1]
        DATA_DIR = PROJECT_ROOT / "data"
        FEEDBACK_PATH = DATA_DIR / "feedback.json"


        def list_feedback() -> list[dict]:
            if not FEEDBACK_PATH.exists():
                return []
            return json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))


        def append_feedback(req: FeedbackRequest) -> dict:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            items = list_feedback()
            item = {
                "name": req.name,
                "rating": req.rating,
                "comment": req.comment,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            items.append(item)
            FEEDBACK_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")
            return {"saved": True, "item": item}
        """,
        "frontend/app.py": """
        import requests
        import streamlit as st

        API_ROOT = "http://127.0.0.1:8000"
        CHAT_URL = f"{API_ROOT}/chat"
        FEEDBACK_URL = f"{API_ROOT}/feedback"
        BLUEPRINT_URL = f"{API_ROOT}/blueprint"


        def load_blueprint():
            try:
                response = requests.get(BLUEPRINT_URL, timeout=30)
                response.raise_for_status()
                return response.json(), None
            except requests.RequestException as exc:
                return None, str(exc)


        blueprint, blueprint_error = load_blueprint()

        if not blueprint:
            st.set_page_config(page_title="Generated Project", layout="wide")
            st.title("Generated Project")
            st.error(f"Could not load backend blueprint: {blueprint_error}")
            st.info("Start the backend first with: python -m uvicorn backend.main:app --reload")
            st.stop()

        st.set_page_config(page_title=blueprint["project_name"], layout="wide")
        st.title(blueprint["project_name"])
        st.caption(blueprint["tagline"])
        st.write(blueprint["primary_goal"])

        tabs = st.tabs(["Assistant", "Blueprint", "Feedback"])

        with tabs[0]:
            left, right = st.columns([1.3, 1])
            with left:
                message = st.text_area(
                    "Message",
                    placeholder=blueprint["sample_inputs"][0],
                    height=160,
                )

                if st.button("Generate Response", use_container_width=True):
                    if not message.strip():
                        st.warning("Enter a message first.")
                    else:
                        response = requests.post(CHAT_URL, json={"message": message}, timeout=30)
                        if response.status_code == 200:
                            data = response.json()
                            st.success(data["answer"])
                            st.subheader("Suggested Follow-ups")
                            for item in data["suggestions"]:
                                st.write(f"- {item}")
                            st.subheader("Next Steps")
                            for item in data["next_steps"]:
                                st.write(f"- {item}")
                        else:
                            st.error("Backend request failed.")

            with right:
                st.subheader("Sample Inputs")
                for item in blueprint["sample_inputs"]:
                    st.write(f"- {item}")

                st.subheader("Core Features")
                for item in blueprint["core_features"]:
                    st.write(f"- {item}")

        with tabs[1]:
            st.json(blueprint)

        with tabs[2]:
            name_input = st.text_input("Name", value="Anonymous")
            rating = st.slider("Rating", min_value=1, max_value=5, value=5)
            comment = st.text_area("Comment", height=120)
            if st.button("Save Feedback", use_container_width=True):
                response = requests.post(
                    FEEDBACK_URL,
                    json={"name": name_input, "rating": rating, "comment": comment},
                    timeout=30,
                )
                if response.status_code == 200:
                    st.success("Feedback saved.")
                else:
                    st.error("Could not save feedback.")
        """,
        "tests/test_api.py": """
        from fastapi.testclient import TestClient

        from backend.main import app


        client = TestClient(app)


        def test_health():
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["ok"] is True


        def test_chat():
            response = client.post("/chat", json={"message": "Hello"})
            assert response.status_code == 200
            data = response.json()
            assert data["answer"]
            assert data["suggestions"]
        """,
        "data/.gitkeep": "",
        "shared/project_blueprint.json": blueprint,
        "project_summary.txt": f"""
        Project: {name}

        Tagline:
        {blueprint["tagline"]}

        Goal:
        {blueprint["primary_goal"]}

        Tech Stack:
        {stack}

        Core Features:
        {feature_lines}

        API Endpoints:
        {endpoint_lines}

        Suggested Inputs:
        {sample_lines}
        """,
    }

    written_files = []
    for relative_path, content in files.items():
        target = project_path / relative_path
        if relative_path.endswith(".json"):
            _json_dump(target, content)
        else:
            _write(target, content)
        written_files.append(relative_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(project_path))

    return {
        "ok": True,
        "message": f"Generated project '{name}' with {len(written_files)} files.",
        "project_path": str(project_path),
        "zip_path": str(zip_path),
        "files": written_files,
    }
