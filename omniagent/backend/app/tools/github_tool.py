import os
from github import Github
from dotenv import load_dotenv
import time
load_dotenv()



def create_repo(repo_name):
    g = Github(os.getenv("GITHUB_TOKEN"))
    user = g.get_user()

    unique_name = f"{repo_name}-{int(time.time())}"

    try:
        repo = user.create_repo(unique_name)
        return f"Repo created: {repo.html_url}"

    except Exception as e:
        return f"GitHub Error: {str(e)}"