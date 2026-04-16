from app.services.llm import generate_response

def planner_agent(user_input):
    prompt = f"""
    You are a planner AI.

    Break this task into steps:
    {user_input}

    Return steps clearly.
    """
    return generate_response(prompt)