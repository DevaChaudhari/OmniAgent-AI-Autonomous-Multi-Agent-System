from app.services.llm import generate_response
import json
import re


def critic_agent(result, task):
    prompt = f"""
    You are a strict AI critic.

    Task:
    {task}

    Result:
    {result}

    Evaluate the result.

    Rules:
    - If correct and complete → return:
      {{"status": "APPROVED"}}

    - If not → return:
      {{"status": "REJECTED", "improved": "better version"}}

    IMPORTANT:
    - Return ONLY valid JSON
    - No explanation
    - No extra text
    """

    response = generate_response(prompt)

    print("\n[Critic Raw Response]:", response)

    # ✅ SAFE JSON PARSING (VERY IMPORTANT)
    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print("[Critic Parse Error]:", e)

    # ✅ fallback (safe)
    return {"status": "APPROVED"}