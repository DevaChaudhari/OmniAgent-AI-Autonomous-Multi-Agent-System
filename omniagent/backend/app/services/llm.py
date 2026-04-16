from langchain_community.llms import Ollama

llm = Ollama(model="phi3")

def generate_response(prompt):
    system_prompt = """
    You are a professional AI assistant.

    Rules:
    - Be clear and structured
    - No random or meaningless text
    - Stay on topic
    - Be concise
    """

    final_prompt = system_prompt + "\n\n" + prompt

    return llm.invoke(final_prompt)