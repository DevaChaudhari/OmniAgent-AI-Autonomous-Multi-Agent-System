# OmniAgent Kubernetes Deployment

This folder contains Kubernetes manifests for the OmniAgent frontend and backend services.

## Build local images

From `omniagent/`:

```powershell
docker build -f Docker/backend/Dockerfile -t ghcr.io/devachaudhari/omniagent-backend:latest .
docker build -f Docker/frontend/Dockerfile -t ghcr.io/devachaudhari/omniagent-frontend:devendra-branding .
```

## Push images to GitHub Container Registry

Images can be published automatically by the GitHub Actions workflow at:

```text
.github/workflows/docker-images.yml
```

After pushing to the `main` branch, check the GitHub Actions tab for the build status.

To push manually from your machine instead, use the commands below.

Login with a GitHub token that has `write:packages` permission:

```powershell
docker login ghcr.io -u DevaChaudhari
docker push ghcr.io/devachaudhari/omniagent-backend:latest
docker push ghcr.io/devachaudhari/omniagent-frontend:devendra-branding
```

If the packages are private, either make them public in GitHub Packages or create an image pull secret:

```powershell
kubectl create secret docker-registry ghcr-secret `
  --namespace omniagent `
  --docker-server=ghcr.io `
  --docker-username=DevaChaudhari `
  --docker-password=<github_token_with_read_packages>
```

## Deploy to Kubernetes

```powershell
kubectl apply -k K8s
kubectl get pods -n omniagent
kubectl get svc -n omniagent
```

## Access the app

- Try the NodePort first: `http://localhost:30080`
- Backend service is available inside the cluster at `http://omniagent-backend:8000`

If Docker Desktop does not expose the NodePort on localhost, use port-forwarding:

```powershell
kubectl port-forward -n omniagent service/omniagent-frontend 30080:8501
```

Keep that terminal open, then visit `http://localhost:30080`.

## Logs

```powershell
kubectl logs -n omniagent deployment/omniagent-backend
kubectl logs -n omniagent deployment/omniagent-frontend
```

## Tear down

```powershell
kubectl delete -k K8s
```
