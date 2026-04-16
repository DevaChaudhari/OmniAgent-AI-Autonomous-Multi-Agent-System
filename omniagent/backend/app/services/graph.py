from typing import TypedDict
from langgraph.graph import StateGraph

from app.agents.planner import planner_agent
from app.agents.execution_agent import execution_agent
from app.agents.tool_agent import tool_agent


# ✅ Strong typed state
class AgentState(TypedDict, total=False):
    input: str
    plan: str
    result: str
    tool_result: str


# 🧠 Planner Node
def planner_node(state: AgentState):
    user_input = state.get("input", "")

    print("\n[Planner Agent Running]")
    print("[Input]:", user_input)

    plan = planner_agent(user_input)

    return {
        "input": user_input,
        "plan": plan
    }


# ⚙️ Execution Node
def execution_node(state: AgentState):
    task = state.get("input", "")

    print("\n[Execution Agent Running]")
    print("[Task]:", task)

    result = execution_agent(task)

    return {
        **state,
        "result": result
    }


# 🛠 Tool Node
def tool_node(state: AgentState):
    user_input = state.get("input", "")
    result = state.get("result", "")

    print("\n[Tool Agent Running]")
    print("[User Input]:", user_input)

    # ✅ Ensure outputs folder exists
    import os
    os.makedirs("outputs", exist_ok=True)

    # ✅ Save result (logging + persistence)
    file_path = "outputs/output.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result)

    # ✅ Tool decision (intent + context)
    tool_result = tool_agent(user_input + "\n" + result)

    print("[Tool Output]:", tool_result)

    return {
        **state,
        "tool_result": f"Saved to {file_path}\n{tool_result}"
    }


# 🚀 Build Graph
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("execute", execution_node)
    graph.add_node("tool", tool_node)

    graph.set_entry_point("planner")

    # 🔥 Clean flow
    graph.add_edge("planner", "execute")
    graph.add_edge("execute", "tool")

    graph.set_finish_point("tool")

    return graph.compile()