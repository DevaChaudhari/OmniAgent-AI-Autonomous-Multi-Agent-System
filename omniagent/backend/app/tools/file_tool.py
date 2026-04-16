import os

def write_file(filename, content):
    os.makedirs("outputs", exist_ok=True)

    path = f"outputs/{filename}"

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return f"File saved at {path}"