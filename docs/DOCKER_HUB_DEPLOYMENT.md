# Docker Hub Deployment

This repo now includes a pull-only deployment path for machines that should run the stack from prebuilt images.

## Images to publish

- `cloud-attack-lab-dashboard`
- `cloud-attack-lab-graph-writer`
- `cloud-attack-lab-neo4j-sync`
- `cloud-attack-lab-caldera` (optional but recommended if you want a fully portable stack)

## One-time setup

1. Log in to Docker Hub:
   `docker login`
2. Copy [infra/.env.dockerhub.example](/c:/Users/91895/Desktop/projects/cloud-attack-lab/infra/.env.dockerhub.example) to `infra/.env.dockerhub`
3. Fill in:
   - `DOCKERHUB_NAMESPACE`
   - `NEO4J_PASSWORD`
   - `CALDERA_API_KEY`
   - `DASHBOARD_PASS`
   - `FLASK_SECRET_KEY`
   - `GEMINI_API_KEY` if you want chatbot responses

## Push images

Push the app images:

```powershell
.\scripts\push-dockerhub.ps1 -Namespace your-dockerhub-username
```

Push the CALDERA image too:

```powershell
.\scripts\push-dockerhub.ps1 -Namespace your-dockerhub-username -PushCaldera
```

## Run anywhere

On another machine:

```powershell
docker login
docker compose --env-file infra/.env.dockerhub -f docker-compose.hub.yml pull
docker compose --env-file infra/.env.dockerhub -f docker-compose.hub.yml up -d
```

The dashboard will be available on `http://localhost:5000` and CALDERA on `http://localhost:8888`.

## Notes

- The Hub compose file uses official `neo4j` and `redis` images and your published app images.
- If you skip `-PushCaldera`, replace the `caldera` service image in [docker-compose.hub.yml](/c:/Users/91895/Desktop/projects/cloud-attack-lab/docker-compose.hub.yml) with another reachable CALDERA image or service.
