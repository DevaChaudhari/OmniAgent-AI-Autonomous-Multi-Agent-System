from app.services.graph import build_graph
from app.schemas.project import ProjectRequest


graph = build_graph()


def build_project_response(req: ProjectRequest):
    result = graph.invoke({
        "project_name": req.project_name,
        "project_description": req.project_description,
        "tech_stack": req.tech_stack,
        "github_link": req.github_link or "",
        "github_username": req.github_username or "",
        "repo_name": req.repo_name or "",
        "push_to_github": req.push_to_github,
    })

    project_result = result.get("project_result", {})

    return {
        "final": result.get("result", ""),
        "actions": result.get("actions", []),
        "project_path": project_result.get("project_path", ""),
        "zip_path": project_result.get("zip_path", ""),
        "generated_files": project_result.get("files", []),
        "github": result.get("github_result", "GitHub push skipped."),
    }
