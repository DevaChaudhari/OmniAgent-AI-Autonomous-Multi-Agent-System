import html
import re
import sys
from pathlib import Path

import streamlit as st

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.project import ProjectRequest
from app.services.project_builder import build_project_response
from app.tools.github_tool import create_repo_and_upload_project


def agent_response_text(data):
    return data.get("final") or "No result"


def render_result(data):
    final_text = html.escape(data.get("final") or "No result")
    st.markdown(f"<div class='result-box'>{final_text}</div>", unsafe_allow_html=True)

    actions = data.get("actions", [])
    if actions:
        st.markdown("#### Agent activity")
        for action in actions:
            st.write(f"- {action}")

    generated_files = data.get("generated_files", [])
    if generated_files:
        st.markdown("#### Generated files")
        cols = st.columns(2)
        for index, file_name in enumerate(generated_files):
            cols[index % 2].write(f"- `{file_name}`")

    project_path = data.get("project_path", "")
    zip_path = data.get("zip_path", "")
    if project_path or zip_path:
        st.markdown("#### Artifacts")
        if project_path:
            st.code(project_path, language="text")
        if zip_path:
            zip_file = Path(zip_path)
            st.code(zip_path, language="text")
            if zip_file.exists():
                try:
                    zip_bytes = zip_file.read_bytes()
                except OSError as exc:
                    st.warning(f"Could not prepare zip download: {exc}")
                else:
                    st.download_button(
                        "Download project zip",
                        data=zip_bytes,
                        file_name=zip_file.name,
                        mime="application/zip",
                        use_container_width=True,
                    )
            else:
                st.warning("Zip file was not found in this Streamlit session.")

    st.download_button(
        "Download agent response",
        data=agent_response_text(data),
        file_name="agent-response.txt",
        mime="text/plain",
        use_container_width=True,
    )


def token_help():
    st.markdown("#### GitHub token checklist")
    st.write("Use a token from the same GitHub account that owns the target repo.")
    st.write("For a fine-grained token, choose the target repository and set `Contents` to `Read and write`.")
    st.write("If the agent should create a new repo, use all repositories access with the needed repository permissions, or use a classic token.")
    st.write("For a classic token, enable the `repo` scope.")
    st.write("The token is sent only for the push request and is not saved by this app.")


def suggest_repo_name(project_name):
    slug = re.sub(r"[^a-z0-9]+", "-", project_name.lower()).strip("-")
    return slug or "ai-agent-project"


if "generated_project" not in st.session_state:
    st.session_state.generated_project = None


st.set_page_config(
    page_title="ProjectPilot AI by Devendra Chaudhari",
    page_icon="OA",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background: #0b0f14;
        color: #f7fafc;
    }
    .main .block-container {
        max-width: 1120px;
        padding-top: 34px;
        padding-bottom: 56px;
    }
    .hero {
        border-bottom: 1px solid #233142;
        padding: 8px 0 24px 0;
        margin-bottom: 22px;
    }
    .creator-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 1px solid #31506d;
        background: #122033;
        color: #dbeafe;
        border-radius: 999px;
        padding: 7px 12px;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 14px;
    }
    .creator-dot {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: #2f81f7;
        box-shadow: 0 0 0 4px rgba(47, 129, 247, 0.18);
    }
    .hero h1 {
        margin: 0 0 8px 0;
        font-size: 38px;
        line-height: 1.15;
        letter-spacing: 0;
    }
    .hero p {
        margin: 0;
        color: #b8c3cf;
        font-size: 16px;
        line-height: 1.55;
        max-width: 780px;
    }
    .status-row {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin: 18px 0 8px 0;
    }
    .status-card {
        border: 1px solid #243447;
        background: #101820;
        border-radius: 8px;
        padding: 14px 16px;
        min-height: 96px;
    }
    .status-card strong {
        display: block;
        font-size: 15px;
        margin-bottom: 6px;
        color: #f3f7fb;
    }
    .status-card span {
        color: #aeb9c5;
        font-size: 14px;
        line-height: 1.45;
    }
    .result-box {
        border: 1px solid #244f36;
        background: #102f20;
        border-radius: 8px;
        padding: 18px;
        color: #d8ffe5;
        white-space: pre-wrap;
        line-height: 1.55;
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextArea"] label {
        color: #edf3f8;
        font-weight: 650;
    }
    div.stButton > button,
    div[data-testid="stDownloadButton"] > button {
        border-radius: 8px;
        border: 1px solid #2f81f7;
        background: #1f6feb;
        color: white;
        font-weight: 700;
        min-height: 44px;
    }
    div.stButton > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        border-color: #58a6ff;
        background: #2f81f7;
        color: white;
    }
    @media (max-width: 780px) {
        .status-row {
            grid-template-columns: 1fr;
        }
        .hero h1 {
            font-size: 30px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="creator-badge">
            <span class="creator-dot"></span>
            Agent made by Devendra Chaudhari
        </div>
        <h1>ProjectPilot AI</h1>
        <p>
            A personal AI project-building agent created by Devendra Chaudhari.
            Turn a project idea into a runnable starter app, package it as a zip,
            and push the generated files to GitHub when you are ready.
        </p>
    </div>
    <div class="status-row">
        <div class="status-card">
            <strong>1. Generate</strong>
            <span>Describe the project and create a FastAPI plus Streamlit starter.</span>
        </div>
        <div class="status-card">
            <strong>2. Push</strong>
            <span>Provide a GitHub link and token with write access, then upload.</span>
        </div>
        <div class="status-card">
            <strong>3. Review</strong>
            <span>Review and make changes directly on GitHub as needed.</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

build_tab, push_tab = st.tabs(["Build project", "Push to GitHub"])

with build_tab:
    left, right = st.columns([1, 1])
    with left:
        project_name = st.text_input(
            "Project name",
            placeholder="Example: Healthcare Chatbot",
        )
    with right:
        tech_stack = st.text_input(
            "Tech stack",
            value="FastAPI + Streamlit + Python",
            placeholder="Example: FastAPI + Streamlit + Python",
        )

    project_description = st.text_area(
        "Project description",
        placeholder=(
            "Example: Build a chatbot where users ask healthcare FAQs and receive "
            "simple, structured guidance with next steps."
        ),
        height=150,
    )

    if st.button("Generate project", use_container_width=True):
        if not project_name.strip():
            st.warning("Enter a project name.")
            st.stop()
        if not project_description.strip():
            st.warning("Enter a project description.")
            st.stop()

        with st.spinner("Generating files, README, and zip package..."):
            try:
                data = build_project_response(
                    ProjectRequest(
                        project_name=project_name.strip(),
                        project_description=project_description.strip(),
                        tech_stack=tech_stack.strip(),
                        push_to_github=False,
                    )
                )
            except Exception as exc:
                st.error(f"Project generation failed: {exc}")
                st.stop()

        st.session_state.generated_project = data | {"project_name": project_name.strip()}
        st.success("Project generated. Open the Push tab when you are ready to upload it.")

    if st.session_state.generated_project:
        st.markdown("### Latest generated project")
        st.info("Your codebase is ready now. Review it, and make changes accordingly.")
        render_result(st.session_state.generated_project)

with push_tab:
    generated_project = st.session_state.generated_project

    if generated_project:
        st.success(f"Ready to push: {generated_project.get('project_name', 'Generated project')}")
        st.caption(generated_project.get("project_path", ""))
    else:
        st.info("Generate a project first. The push form will use the latest generated project.")

    github_link = st.text_input(
        "GitHub profile, username, or repo URL",
        placeholder="Example: https://github.com/username/repo-name",
        help="Use a repo URL to push to that repo name, or a profile/username to let the agent create a repo name.",
    )
    github_token = st.text_input(
        "GitHub access token",
        type="password",
        help="The backend uses this token only for this push request and does not save it.",
    )
    repo_name = st.text_input(
        "Repository name override",
        placeholder="Optional: leave empty for automatic naming",
    )

    with st.expander("How to create the GitHub access token", expanded=True):
        token_help()

    if st.button("Push to GitHub", use_container_width=True):
        if not generated_project:
            st.warning("Generate a project first, then push it to GitHub.")
            st.stop()
        if not github_link.strip():
            st.warning("Enter the GitHub profile, username, or repo URL.")
            st.stop()
        if not github_token.strip():
            st.warning("Enter the GitHub token for the target GitHub account.")
            st.stop()

        with st.spinner("Creating or updating the GitHub repo..."):
            try:
                github_result = create_repo_and_upload_project(
                    repo_name=repo_name.strip() or suggest_repo_name(generated_project.get("project_name", "")),
                    github_username=github_link.strip(),
                    project_path=generated_project.get("project_path", ""),
                    github_link=github_link.strip(),
                    github_token=github_token.strip(),
                )
            except Exception as exc:
                st.error(f"GitHub push failed: {exc}")
                st.stop()

        if github_result.startswith("GitHub Error:"):
            st.error(github_result)
        else:
            st.success(github_result)
