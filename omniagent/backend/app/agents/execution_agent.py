from app.services.llm import generate_response

def execution_agent(task):
    prompt = f"""
    You are an AI assistant.

    Task:
    {task}

    Rules:
    - Do NOT generate code
    - Do NOT simulate implementation
    - Just explain briefly what will be done
    - Keep it short

    Answer:
    """

    return generate_response(prompt)