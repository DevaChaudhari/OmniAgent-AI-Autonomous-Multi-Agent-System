from fastapi import FastAPI
from pydantic import BaseModel
from app.agents.planner import planner_agent
from app.services.graph import build_graph

app = FastAPI()

class TaskRequest(BaseModel):
    query: str

# build graph once
graph = build_graph()

@app.get("/")
def home():
    return {"message": "OmniAgent is running 🚀"}

@app.post("/run")
def run_task(req: TaskRequest):
    result = graph.invoke({"input": req.query})

    return {
        "final": result.get("result"),
        "tool": result.get("tool_result")
    }