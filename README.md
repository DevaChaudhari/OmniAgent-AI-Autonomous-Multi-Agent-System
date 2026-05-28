# OmniAgent AI Autonomous Multi-Agent System

OmniAgent is a full-stack AI project-building agent created by **Devendra Chaudhari**. It takes a project idea, generates a runnable starter application, packages the output as a zip file, and can push the generated project to GitHub.

The application includes a FastAPI backend, a Streamlit frontend, Docker support, Kubernetes manifests, and a GitHub Actions workflow for publishing container images to GitHub Container Registry.

## Features

- Generate runnable starter projects from a project name, description, and tech stack.
- Create project files, README content, setup instructions, and a downloadable zip artifact.
- Push generated projects to GitHub using a user-provided GitHub token.
- Streamlit web interface for project generation and GitHub upload.
- FastAPI backend with structured request and response models.
- LangGraph workflow for planning, project generation, GitHub handling, and final response assembly.
- Docker Compose setup for local containerized development.
- Kubernetes manifests for frontend and backend deployment.
- GitHub Actions workflow for publishing Docker images to GHCR.

## Tech Stack

- Python 3.11
- FastAPI
- Streamlit
- LangGraph
- Pydantic
- PyGithub
- Docker
- Kubernetes
- GitHub Actions
- GitHub Container Registry

## Project Structure

```text
.
|-- .github/
|   `-- workflows/
|       `-- docker-images.yml
|-- omniagent/
|   |-- backend/
|   |   |-- app/
|   |   |   |-- routes/
|   |   |   |-- schemas/
|   |   |   |-- services/
|   |   |   |-- tools/
|   |   |   `-- main.py
|   |   |-- artifacts/
|   |   |-- .env.example
|   |   `-- requirements.txt
|   |-- frontend/
|   |   |-- UI.py
|   |   `-- requirements.txt
|   |-- Docker/
|   |   |-- backend/
|   |   |   `-- Dockerfile
|   |   |-- frontend/
|   |   |   `-- Dockerfile
|   |   `-- Docker-compose.yml
|   |-- K8s/
|   |   |-- backend-deployment.yaml
|   |   |-- backend-service.yaml
|   |   |-- frontend-deployment.yaml
|   |   |-- frontend-service.yaml
|   |   |-- kustomization.yaml
|   |   |-- namespace.yaml
|   |   `-- README.md
|   |-- .dockerignore
|   `-- .gitignore
`-- README.md
```

## How It Works

```text
User input
  -> Streamlit frontend
  -> FastAPI backend
  -> LangGraph workflow
  -> Project generator
  -> Zip artifact
  -> Optional GitHub repository upload
```

The backend graph follows four main stages:

1. Plan the requested project.
2. Generate runnable starter project files.
3. Optionally push files to GitHub.
4. Return generated file paths, artifact paths, actions, and final status.

## Prerequisites

- Python 3.11+
- Docker Desktop
- Kubernetes enabled in Docker Desktop, if using Kubernetes locally
- Git
- GitHub account
- GitHub personal access token for GitHub push features

For GitHub repository upload, use a token with repository write permissions. For GitHub Container Registry publishing, use `write:packages`.

## Local Development

From the repository root:

```powershell
cd omniagent
```

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend URL:

```text
http://localhost:8000
```

### Frontend

Open a second terminal:

```powershell
cd omniagent\frontend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
$env:BACKEND_HOST="http://127.0.0.1:8000"
streamlit run UI.py --server.port 8501
```

Frontend URL:

```text
http://localhost:8501
```

## Environment Variables

The backend supports an optional fallback GitHub token for local/admin testing:

```text
GITHUB_TOKEN=your_optional_github_personal_access_token
```

Normal users can enter their GitHub token directly in the Streamlit UI. The token is used for the push request and is not saved by the app.

## API Endpoints

### Health Check

```http
GET /
```

Returns a simple status message.

### Build Project

```http
POST /build-project
```

Example request:

```json
{
  "project_name": "Healthcare Chatbot",
  "project_description": "Build a chatbot for healthcare FAQs.",
  "tech_stack": "FastAPI + Streamlit + Python",
  "push_to_github": false
}
```

### Push Project to GitHub

```http
POST /push-project
```

Example request:

```json
{
  "project_name": "Healthcare Chatbot",
  "project_path": "path/to/generated/project",
  "github_link": "https://github.com/username/repo-name",
  "github_token": "github_token_here",
  "repo_name": "healthcare-chatbot"
}
```

## Docker Compose

Run the full application with Docker Compose:

```powershell
cd omniagent
docker compose -f Docker/Docker-compose.yml up --build
```

Services:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:8501`

Stop the stack:

```powershell
docker compose -f Docker/Docker-compose.yml down
```

## Kubernetes

Build images:

```powershell
cd omniagent
docker build -f Docker/backend/Dockerfile -t ghcr.io/devachaudhari/omniagent-backend:latest .
docker build -f Docker/frontend/Dockerfile -t ghcr.io/devachaudhari/omniagent-frontend:devendra-branding .
```

Deploy:

```powershell
kubectl apply -k K8s
kubectl get pods -n omniagent
kubectl get svc -n omniagent
```

Access the frontend:

```text
http://localhost:30080
```

If Docker Desktop does not expose the NodePort directly, use port-forwarding:

```powershell
kubectl port-forward -n omniagent service/omniagent-frontend 30080:8501
```

Then open:

```text
http://localhost:30080
```

View logs:

```powershell
kubectl logs -n omniagent deployment/omniagent-backend
kubectl logs -n omniagent deployment/omniagent-frontend
```

Delete the deployment:

```powershell
kubectl delete -k K8s
```

## Container Registry Deployment

The Kubernetes manifests use GitHub Container Registry image names:

```text
ghcr.io/devachaudhari/omniagent-backend:latest
ghcr.io/devachaudhari/omniagent-frontend:devendra-branding
```

The workflow at `.github/workflows/docker-images.yml` builds and publishes both images when changes are pushed to `main`.

To push manually:

```powershell
docker login ghcr.io -u DevaChaudhari
docker push ghcr.io/devachaudhari/omniagent-backend:latest
docker push ghcr.io/devachaudhari/omniagent-frontend:devendra-branding
```

If the GHCR packages are private, create an image pull secret in your cluster:

```powershell
kubectl create secret docker-registry ghcr-secret `
  --namespace omniagent `
  --docker-server=ghcr.io `
  --docker-username=DevaChaudhari `
  --docker-password=<github_token_with_read_packages>
```

## GitHub Workflow

The included GitHub Actions workflow:

- Checks out the repository.
- Sets up Docker Buildx.
- Logs in to GitHub Container Registry.
- Builds the backend image.
- Builds the frontend image.
- Pushes both images to GHCR.

After pushing to GitHub, open the repository's **Actions** tab and check `Build and Publish Docker Images`.

## Notes

- The frontend reads the backend URL from `BACKEND_HOST`.
- Docker Compose sets `BACKEND_HOST=http://backend:8000`.
- Kubernetes sets `BACKEND_HOST=http://omniagent-backend:8000`.
- Generated artifacts are stored under `backend/artifacts`.
- The optional Ollama integration is used only when available; the project generator falls back to deterministic blueprint generation if Ollama is not running.

## Author

Created by **Devendra Chaudhari**.
