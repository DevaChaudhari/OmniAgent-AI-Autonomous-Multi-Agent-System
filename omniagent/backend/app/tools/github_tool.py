import os
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from github import Github, GithubException

load_dotenv()

SKIP_DIRS = {
    ".git",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "outputs",
}
SKIP_FILES = {
    ".env",
    "backend.err",
    "backend.log",
    "backend2.err",
    "backend2.log",
    "streamlit.err",
    "streamlit.log",
}
MAX_FILE_BYTES = 900_000
PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


@contextmanager
def _without_proxy_env():
    saved = {key: os.environ.pop(key) for key in PROXY_ENV_KEYS if key in os.environ}
    try:
        yield
    finally:
        os.environ.update(saved)


def _github_user(github_token=""):
    token = (github_token or "").strip() or os.getenv("GITHUB_TOKEN")
    if not token:
        return None, "GitHub token is required"

    g = Github(token)
    return g.get_user(), None


def _clean_repo_name(repo_name):
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in repo_name.strip())
    return cleaned.strip(".-_") or "ai-agent-project"


def _parse_github_target(github_target):
    value = (github_target or "").strip()
    if not value:
        return "", ""

    if "github.com" in value:
        parsed = urlparse(value if "://" in value else f"https://{value}")
        parts = [part for part in parsed.path.split("/") if part]
        owner = parts[0] if parts else ""
        repo = parts[1].removesuffix(".git") if len(parts) > 1 else ""
        return owner, repo

    cleaned = value.removesuffix(".git").strip("/")
    parts = [part for part in cleaned.split("/") if part]
    if len(parts) >= 2:
        return parts[0], parts[1]
    return cleaned, ""


def _validate_owner(user, github_username):
    if not github_username:
        return "Enter your GitHub username or GitHub profile link before creating or pushing a repo"

    if user.login.lower() != github_username.strip().lower():
        return (
            f"GitHub username mismatch: token belongs to '{user.login}', "
            f"but the request used '{github_username}'"
        )

    return None


def _iter_project_files(project_root):
    project_root = Path(project_root).resolve()

    for path in project_root.rglob("*"):
        if not path.is_file():
            continue

        relative = path.relative_to(project_root)
        parts = set(relative.parts)

        if parts & SKIP_DIRS:
            continue

        if path.name in SKIP_FILES or path.suffix in {".pyc", ".pyo"}:
            continue

        if path.stat().st_size > MAX_FILE_BYTES:
            continue

        yield path, relative.as_posix()


def _get_or_create_repo(user, repo_name):
    unique_name = _clean_repo_name(repo_name)

    try:
        repo = user.get_repo(unique_name)
        return repo, False
    except GithubException as exc:
        if exc.status != 404:
            raise

    return user.create_repo(unique_name), True


def _friendly_github_error(exc):
    message = str(exc)
    if isinstance(exc, GithubException):
        data = exc.data if isinstance(exc.data, dict) else {}
        api_message = data.get("message", "")

        if exc.status == 403 and "Resource not accessible by personal access token" in api_message:
            return (
                "GitHub Error: Your token can access GitHub, but it cannot write files to this repo. "
                "For a fine-grained token, select the target repository and enable "
                "'Contents: Read and write'. If the repo must be created by the app, also allow "
                "repository creation or use a classic token with the 'repo' scope."
            )

        if exc.status == 401:
            return "GitHub Error: Bad credentials. Check that the GitHub token is correct and not expired."

        return f"GitHub Error: {exc.status} {api_message or message}"

    return f"GitHub Error: {message}"


def create_repo(repo_name, github_username="", github_link="", github_token=""):
    target_owner, target_repo = _parse_github_target(github_link or github_username)
    github_username = target_owner or github_username
    repo_name = repo_name or target_repo

    if not repo_name:
        return "GitHub Error: Enter a repository name before creating or pushing a repo"

    try:
        with _without_proxy_env():
            user, error = _github_user(github_token)
            if error:
                return f"GitHub Error: {error}"

            owner_error = _validate_owner(user, github_username)
            if owner_error:
                return f"GitHub Error: {owner_error}"

            repo, created = _get_or_create_repo(user, repo_name)
            action = "created" if created else "already exists"
            return f"Repo {action}: {repo.html_url}"

    except Exception as e:
        return _friendly_github_error(e)


def create_repo_and_upload_project(
    repo_name,
    github_username="",
    project_path=None,
    github_link="",
    github_token="",
):
    target_owner, target_repo = _parse_github_target(github_link or github_username)
    github_username = target_owner or github_username
    repo_name = repo_name or target_repo

    if not repo_name:
        return "GitHub Error: Enter a repository name before creating or pushing a repo"

    try:
        with _without_proxy_env():
            user, error = _github_user(github_token)
            if error:
                return f"GitHub Error: {error}"

            owner_error = _validate_owner(user, github_username)
            if owner_error:
                return f"GitHub Error: {owner_error}"

            repo, created = _get_or_create_repo(user, repo_name)
            uploaded = 0
            updated = 0
            source_path = Path(project_path).resolve() if project_path else None

            if not source_path or not source_path.exists() or not source_path.is_dir():
                return "GitHub Error: Generated project folder was not found"

            for path, repo_path in _iter_project_files(source_path):
                content = path.read_bytes()
                try:
                    existing = repo.get_contents(repo_path, ref=repo.default_branch)
                    repo.update_file(
                        repo_path,
                        f"Update {repo_path}",
                        content,
                        existing.sha,
                        branch=repo.default_branch,
                    )
                    updated += 1
                except GithubException as exc:
                    if exc.status != 404:
                        raise
                    repo.create_file(
                        repo_path,
                        f"Add {repo_path}",
                        content,
                        branch=repo.default_branch,
                    )
                    uploaded += 1

            repo_action = "created" if created else "updated"
            return (
                f"Repo {repo_action} and project pushed: {repo.html_url} "
                f"({uploaded} files added, {updated} files updated)"
            )

    except Exception as e:
        return _friendly_github_error(e)
