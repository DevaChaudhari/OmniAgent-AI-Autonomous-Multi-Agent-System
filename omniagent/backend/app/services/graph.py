from typing import TypedDict
import re

from langgraph.graph import StateGraph

from app.tools.github_tool import create_repo_and_upload_project
from app.tools.project_tool import create_project


class AgentState(TypedDict, total=False):
    project_name: str
    project_description: str
    tech_stack: str
    github_link: str
    github_username: str
    repo_name: str
    push_to_github: bool
    plan: list[str]
    project_result: dict
    github_result: str
    result: str
    actions: list[str]


def _suggest_repo_name(project_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", project_name.lower()).strip("-")
    return slug or "ai-agent-project"


def planner_node(state: AgentState):
    plan = [
        "Understand the requested project",
        "Generate a runnable starter project",
        "Create README and setup instructions",
        "Package the generated files",
    ]

    if state.get("push_to_github"):
        repo_name = state.get("repo_name") or _suggest_repo_name(state.get("project_name", ""))
        plan.append(f"Create GitHub repo '{repo_name}' and upload the generated project")

    return {
        **state,
        "plan": plan,
        "actions": ["Created implementation plan"],
    }


def project_node(state: AgentState):
    project_result = create_project(
        state.get("project_name", ""),
        state.get("project_description", ""),
        state.get("tech_stack", ""),
    )

    actions = state.get("actions", []) + [
        "Generated runnable project files",
        "Created README and setup instructions",
        "Created downloadable project zip",
    ]

    return {
        **state,
        "project_result": project_result,
        "actions": actions,
    }


def github_node(state: AgentState):
    project_result = state.get("project_result", {})
    github_result = "GitHub push skipped."
    actions = state.get("actions", [])

    if state.get("push_to_github"):
        repo_name = state.get("repo_name") or _suggest_repo_name(state.get("project_name", ""))
        github_result = create_repo_and_upload_project(
            repo_name,
            state.get("github_username", ""),
            project_result.get("project_path"),
            state.get("github_link", ""),
        )
        actions = actions + [f"Attempted GitHub repo creation and upload to '{repo_name}'"]

    return {
        **state,
        "github_result": github_result,
        "actions": actions,
    }


def final_node(state: AgentState):
    project_result = state.get("project_result", {})
    files = project_result.get("files", [])
    github_result = state.get("github_result", "GitHub push skipped.")

    if not project_result.get("ok"):
        final = project_result.get("message", "Project generation failed.")
    else:
        file_list = "\n".join(f"- {file_name}" for file_name in files)
        final = f"""
Project generated successfully.

Project name: {state.get("project_name")}
Project path: {project_result.get("project_path")}
Zip file: {project_result.get("zip_path")}

Generated files:
{file_list}

GitHub:
{github_result}

How to run the generated project:
1. Open the generated project folder.
2. Run: python -m venv .venv
3. Run: .venv\\Scripts\\activate
4. Run: pip install -r requirements.txt
5. Run backend: python -m uvicorn backend.main:app --reload
6. Run frontend in another terminal: streamlit run frontend/app.py
        """.strip()

    return {
        **state,
        "result": final,
    }


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("project", project_node)
    graph.add_node("github", github_node)
    graph.add_node("final", final_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "project")
    graph.add_edge("project", "github")
    graph.add_edge("github", "final")
    graph.set_finish_point("final")

    return graph.compile()
