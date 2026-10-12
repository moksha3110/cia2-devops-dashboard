# DevOps Deployment Dashboard

University assignment: **Design and Implementation of an End-to-End Cloud-Based CI/CD Pipeline**.

This Spring Boot application displays deployment metadata so that a change from v1 to v2 is visible immediately. The project includes the application, automated tests, Docker image build, Kubernetes manifests, GitHub Actions pipeline, optional Ansible verification, and assignment guides. The cloud target is **AWS EKS**, changed from the original GKE requirement at the user's request.

**Pipeline:** Git push → Java compilation/tests/package → Docker build → SHA-tagged GHCR publication → AWS EKS rolling deployment → public HTTP verification.

The code and configuration are implemented. End-to-end cloud execution still requires GitHub/AWS setup and approval; local success is not cloud-deployment evidence.

## Project layout

```text
.
├── pom.xml, mvnw, mvnw.cmd, .mvn/wrapper/
├── src/main/java/com/example/devopsdashboard/
├── src/main/resources/application.yml
├── src/main/resources/static/              # HTML, CSS, JavaScript
├── src/test/java/com/example/devopsdashboard/
├── Dockerfile, .dockerignore, .gitignore, .gitattributes
├── .github/workflows/ci-cd.yml
├── k8s/deployment.yaml, service.yaml, rbac.yaml
├── scripts/deploy.sh, verify-deployment.py
├── ansible/inventory.ini, verify.yml
└── docs/architecture.md, deployment-guide.md,
         evidence-checklist.md, troubleshooting.md
```

## Cloud setup and assignment guides

- [Architecture and viva explanation](docs/architecture.md)
- [AWS/GitHub setup and automatic v1-to-v2 deployment](docs/deployment-guide.md)
- [Evidence screenshot checklist](docs/evidence-checklist.md)
- [Troubleshooting](docs/troubleshooting.md)

Defaults: GitHub `moksha3110/cia2-devops-dashboard`, AWS account `906555057481`, Mumbai `ap-south-1`, cluster `cia2-devops-dashboard`. The AWS role authenticates through GitHub OIDC. Registry publication uses the provided `GITHUB_TOKEN`; no AWS access keys are stored in GitHub.

Keep repository variable `DEPLOY_ENABLED` unset or `false` until cloud setup is approved and ready. Main pushes still run CI and publish to GHCR once the repository is pushed; PRs run CI only. Set `DEPLOY_ENABLED=true` to activate automatic cloud deployment after setup. The [guide](docs/deployment-guide.md) lists all required variables, IAM/RBAC setup, image-pull access, costs, and cleanup.

## Application endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Responsive HTML dashboard |
| `GET /api/info` | Application name, version, environment, message, and optional commit SHA |
| `GET /actuator/health` | Overall health |
| `GET /actuator/health/liveness` | Process liveness for future Kubernetes probes |
| `GET /actuator/health/readiness` | Readiness for future Kubernetes probes |

The delivery path shown on the dashboard describes pipeline stages; it does not report GitHub Actions execution results.

## Run locally with PowerShell

Run these commands from the project root. Install JDK 21 and set `JAVA_HOME` to its installation directory. Maven Wrapper downloads Maven automatically on first use; dependency resolution requires internet access.

```powershell
# Example for the JDK currently installed on this workstation:
$env:JAVA_HOME = 'C:\Program Files\Microsoft\jdk-21.0.12.101-hotspot'
& "$env:JAVA_HOME\bin\java.exe" -version

.\mvnw.cmd clean test
.\mvnw.cmd package
.\mvnw.cmd spring-boot:run
```

Open <http://localhost:8080>. Stop the application with Ctrl+C. Alternatively, after packaging, run the executable JAR:

```powershell
& "$env:JAVA_HOME\bin\java.exe" -jar .\target\devops-dashboard.jar
```

## Build the Docker image

Install and start Docker Desktop with its Linux container engine enabled. Check that both the client and server are available:

```powershell
docker version
docker info --format '{{.OSType}}'
```

The engine OS should be `linux`. Build from this directory:

```powershell
docker build --pull --tag devops-dashboard:v1 .
```

The first stage uses a Java 21 JDK and the checked-in Maven Wrapper to compile, run tests, and package the application. A failed test stops the image build. The second stage contains a Java 21 JRE and the executable JAR. It runs with numeric user and group `10001`, without Maven or project sources.

The base images use Java 21 tags so they can receive updates when pulled. These tags can change; production builds should pin reviewed image digests. Later pipeline phases will tag the application image with the Git commit SHA.

See the official [Docker multi-stage build guide](https://docs.docker.com/build/building/multi-stage/) and [Adoptium container sources](https://github.com/adoptium/containers).

## Run and verify the container

Stop any local Java process using port 8080 first, or change the host port below to `8081:8080` and use port 8081 in the URLs.

```powershell
docker run --detach --name devops-dashboard --publish 8080:8080 --memory 512m --env APP_VERSION=v1 --env APP_ENVIRONMENT=docker --env 'DEPLOYMENT_MESSAGE=Version 1 is running in Docker.' devops-dashboard:v1

docker logs --follow devops-dashboard
```

Ctrl+C stops log following; the detached container continues running. Once the startup log says the application has started, verify in PowerShell:

```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8080/).StatusCode
Invoke-RestMethod http://localhost:8080/api/info
Invoke-RestMethod http://localhost:8080/actuator/health
docker inspect --format '{{.State.Health.Status}}' devops-dashboard
docker exec devops-dashboard id
```

Expected results after a successful startup: dashboard HTTP `200`, version `v1` and environment `docker`, health status `UP`, container health eventually `healthy`, and process UID/GID `10001`. Docker checks health every 30 seconds, so its status can initially be `starting`. These are expected results, not recorded container test results.

`EXPOSE 8080` documents the container port; `--publish 8080:8080` makes it reachable from the host. The runtime health check requests the application health endpoint using Alpine's built-in `wget`. Java receives stop signals directly, allowing Spring Boot's graceful shutdown.

Clean up the local container:

```powershell
docker stop --timeout 30 devops-dashboard
docker rm devops-dashboard
```

## Deployment metadata and a local v2 demonstration

| Environment variable | Default |
| --- | --- |
| `APP_NAME` | `DevOps Deployment Dashboard` |
| `APP_VERSION` | `v1` |
| `APP_ENVIRONMENT` | `local` |
| `DEPLOYMENT_MESSAGE` | `Version 1 is running. Ready for the next deployment!` |
| `COMMIT_SHA` | Empty; omitted from JSON when empty |

These values are public dashboard information. Keep credentials out of them. In EKS, version/message/environment are committed in the Deployment manifest; the workflow supplies the exact source commit SHA.

After removing the v1 container, use the same image with different runtime configuration:

```powershell
docker run --detach --name devops-dashboard --publish 8080:8080 --memory 512m --env APP_VERSION=v2 --env APP_ENVIRONMENT=docker --env 'DEPLOYMENT_MESSAGE=Version 2 is running with updated deployment metadata.' devops-dashboard:v1
```

Refresh the dashboard to see `v2` and the new message. Environment variables are supplied when creating a container; changing them in a host shell does not update an existing container. This local exercise demonstrates configurable metadata. The [GitHub Actions/EKS walkthrough](docs/deployment-guide.md#9-full-automatic-v1-to-v2-redeployment) demonstrates a Git push building and automatically deploying a new SHA-tagged image.

## Verification status

- Phase 2: `clean test` and `package` succeeded on Windows using JDK 21. Eight automated tests passed with zero failures, errors, or skipped tests.
- Phase 3: Docker Desktop's Linux engine was verified. The multi-stage build succeeded, including all eight tests. The local container `javaweb-dashboard-local` returned dashboard HTTP 200 and health UP; Docker reported `healthy`, and `id` reported UID/GID 10001.
- Kubernetes schema validation passed for all five resources across the three manifest files, plus a locally rendered Deployment.
- GitHub Actions workflow validation passed with actionlint v1.7.12. Bash syntax and Ansible syntax (ansible-core 2.21.5 on Linux) passed.
- Local kubectl rendering verified the exact SHA-tag/digest reference, commit metadata, and optional image-pull secret. No cluster was contacted for rendering.
- The Python HTTP verifier passed against local v1/v2 containers and rejected an intentionally wrong version. The v2 container also passed with a read-only filesystem, dropped capabilities, and UID/GID 10001. This was a local container check, not a cloud redeployment.
- No image publication or cloud deployment has been performed. No paid resources have been created.

The verified local dashboard is available at <http://localhost:8080> while `javaweb-dashboard-local` is running. Its name differs from the example container above. To stop that specific verification container:

```powershell
docker stop --timeout 30 javaweb-dashboard-local
```

## Local troubleshooting

- **`docker` is not recognized:** install Docker Desktop, then reopen PowerShell so its updated `PATH` is loaded.
- **Cannot connect to the Docker daemon:** start Docker Desktop and wait until its Linux engine is ready.
- **Port already allocated:** stop the process/container using port 8080 or publish `8081:8080`.
- **Maven cannot download dependencies:** check network/proxy access to Maven Central. The Docker build needs that access too.
- **Container fails to start:** inspect `docker logs devops-dashboard`. Confirm enough memory is available and the image built successfully.
- **Container name already in use:** stop and remove the previous `devops-dashboard` container before creating another.
