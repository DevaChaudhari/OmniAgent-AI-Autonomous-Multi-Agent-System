from app.services.llm import generate_response

def research_agent(task):
    prompt = f"""
    Extract only useful and relevant information for this task:

    {task}

    Keep it short and focused.
    """

    return generate_response(prompt)