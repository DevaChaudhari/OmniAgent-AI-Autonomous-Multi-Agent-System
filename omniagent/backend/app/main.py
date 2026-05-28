from fastapi import FastAPI

from app.routes.projects import router as projects_router


app = FastAPI(title="ProjectPilot AI")
app.include_router(projects_router)
