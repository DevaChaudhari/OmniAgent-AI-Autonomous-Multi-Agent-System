from app.tools.github_tool import create_repo
from app.tools.file_tool import write_file
from app.tools.api_tool import fetch_data
from app.tools.browser_tool import browse_website
from app.services.llm import generate_response

import json
import re


def tool_agent(task):
    print("\n[Tool Agent Decision Phase]")

    # Ask AI for tools
    prompt = f"""
    You are an AI agent.

    Task: {task}

    Available tools:
    - github
    - file
    - api
    - browser

    Return ONLY JSON:
    {{"tools": ["browser", "api"]}}
    """

    decision = generate_response(prompt)
    print("[Raw Decision]:", decision)

    # PARSE
    try:
        match = re.search(r'\{.*\}', decision, re.DOTALL)
        if match:
            tools = json.loads(match.group()).get("tools", [])
        else:
            tools = []
    except:
        tools = []

    print("[Initial Tools]:", tools)

    task_lower = task.lower()

    if "api" in task_lower and "api" not in tools:
        tools.append("api")

    if any(word in task_lower for word in ["file", "save", "write"]):
        if "file" not in tools:
            tools.append("file")

    if any(word in task_lower for word in ["repo", "github"]):
        if "github" not in tools:
            tools.append("github")

    if any(word in task_lower for word in ["browse", "website"]):
        if "browser" not in tools:
            tools.append("browser")

    print("[Final Tools]:", tools)

    # EXECUTE TOOLS
    results = []

    for tool in tools:
        tool = tool.lower()

        # GITHUB
        if tool in ["github", "git", "repo", "repository"]:
            res = create_repo("ai-agent-project")
            results.append(res)

        # FILE
        elif tool in ["file", "save", "write"]:
            content = generate_response(f"Write content for: {task}")
            write_file("output.txt", content)
            results.append("File: saved")

        # API
        elif tool in ["api", "fetch", "data"]:
            fetch_data("https://api.github.com")
            results.append("API: data fetched")

        # BROWSER
        elif tool in ["browser", "browse", "web"]:
            browse_website("https://example.com")
            results.append("Browser: content fetched")

    if not results:
        return "No tools executed"

    # Order priority
    order = ["Browser", "API", "File", "Repo"]

    # sort results properly
    sorted_results = sorted(
        results,
        key=lambda x: next(
            (i for i, k in enumerate(order) if k.lower() in x.lower()),
            99
        )
    )

    # format nicely
    formatted_output = "\n".join(sorted_results)

    return formatted_output
