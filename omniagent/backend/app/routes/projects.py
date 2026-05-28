import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.project import ProjectRequest, ProjectResponse, PushProjectRequest, PushProjectResponse
from app.services.project_builder import build_project_response
from app.tools.github_tool import create_repo_and_upload_project
from app.tools.project_tool import PROJECTS_DIR


router = APIRouter()


@router.get("/")
def home():
    return {"message": "OmniAgent Project Builder is running"}


def _validate_request(req: ProjectRequest):
    if req.push_to_github:
        github_target = req.github_link or req.github_username
        if not github_target or not github_target.strip():
            raise HTTPException(status_code=400, detail="GitHub link or username is required.")


def _suggest_repo_name(project_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", project_name.lower()).strip("-")
    return slug or "ai-agent-project"


@router.post("/build-project", response_model=ProjectResponse)
def build_project(req: ProjectRequest):
    _validate_request(req)
    return build_project_response(req)


@router.post("/push-project", response_model=PushProjectResponse)
def push_project(req: PushProjectRequest):
    repo_name = (req.repo_name or "").strip() or _suggest_repo_name(req.project_name)
    github_result = create_repo_and_upload_project(
        repo_name=repo_name,
        github_username=req.github_link,
        project_path=req.project_path,
        github_link=req.github_link,
        github_token=req.github_token,
    )
    return {"github": github_result}


@router.get("/download-project/{zip_name}")
def download_project(zip_name: str):
    safe_name = Path(zip_name).name
    if safe_name != zip_name or not safe_name.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Invalid zip file name.")

    zip_path = PROJECTS_DIR / safe_name
    if not zip_path.exists() or not zip_path.is_file():
        raise HTTPException(status_code=404, detail="Project zip was not found.")

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=safe_name,
    )


@router.post("/run", response_model=ProjectResponse)
def run_legacy(req: ProjectRequest):
    _validate_request(req)
    return build_project_response(req)
