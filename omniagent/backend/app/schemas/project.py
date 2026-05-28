from pydantic import BaseModel, Field


class ProjectRequest(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=120)
    project_description: str = Field(..., min_length=1, max_length=4000)
    tech_stack: str = Field(default="FastAPI + Streamlit + Python", max_length=300)
    github_link: str | None = Field(default=None, max_length=300)
    github_username: str | None = Field(default=None, max_length=100)
    repo_name: str | None = Field(default=None, max_length=100)
    push_to_github: bool = False


class ProjectResponse(BaseModel):
    final: str
    actions: list[str]
    project_path: str
    zip_path: str
    generated_files: list[str]
    github: str


class PushProjectRequest(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=120)
    project_path: str = Field(..., min_length=1, max_length=1000)
    github_link: str = Field(..., min_length=1, max_length=300)
    github_token: str = Field(..., min_length=1, max_length=500)
    repo_name: str | None = Field(default=None, max_length=100)


class PushProjectResponse(BaseModel):
    github: str
