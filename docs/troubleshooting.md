# Troubleshooting

## Windows, Java, and Maven

**JAVA_HOME is missing or invalid.** Point `$env:JAVA_HOME` to the JDK 21 installation directory, not its `bin` directory. Confirm `& "$env:JAVA_HOME\bin\java.exe" -version`, then run `./mvnw.cmd clean test`. A system Maven installation is unnecessary.

**Dependencies cannot be resolved.** Check network/proxy access to `repo.maven.apache.org`. The initial wrapper run also downloads Maven. Do not change dependency versions merely to hide a connectivity error. Corporate proxies can require approved Maven proxy settings outside the repository.

**Tests fail while checking health content type.** Actuator can return a vendor JSON media type. The health test explicitly requests `application/json`. Inspect `target/surefire-reports` for the actual failure; do not weaken the expected health status to make a failing app pass.

**The dashboard is stale after a redeployment.** Press Refresh, reload the page, and inspect `/api/info`. The API and static resources request no-store caching; compare the returned commit SHA with the deployed commit. Metadata is read at process startup, so changing a host environment variable does not modify a running container.

## Docker

**Docker is not recognized after installation.** Reopen PowerShell/VS Code to refresh PATH. On this workstation Docker was installed per-user under `%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin`. Confirm `docker version` shows both client and server and `docker info --format '{{.OSType}}'` returns `linux`.

**Cannot reach the daemon.** Start Docker Desktop and wait for its engine. Check WSL requirements and Linux-container mode. An agent sandbox can also block the local Docker pipe even when Desktop works; this is a tooling permission issue, not a Docker Hub login requirement.

**Base image download stalls.** Public Temurin images do not require your Docker password. Check network/proxy access, cancel the stuck build, and retry. A first download stalled during implementation; the retry succeeded. Avoid clearing all Docker data, which would discard useful cached layers and unrelated resources.

**`mvnw: not found` or carriage-return errors in Linux.** The Dockerfile invokes `sh` and normalizes wrapper CRLF. `.gitattributes` keeps the wrapper and shell scripts LF in future Git checkouts.

**Container name or port is in use.** Inspect `docker ps -a` and the local processes. Remove only your stopped project container, or publish `8081:8080` and use localhost:8081. Do not remove unrelated containers.

**Health remains starting/unhealthy.** Check `docker logs <container>`. The health interval is 30 seconds; initial `starting` is normal. Check `/actuator/health` and confirm adequate memory. The image health check needs no extra curl installation because Alpine includes wget.

## GitHub Actions and GHCR

**Workflow is missing.** It must be committed under `.github/workflows/ci-cd.yml`. Manual dispatch becomes available after the workflow exists on the default branch. Review Actions policy and the run's triggering branch/event.

**Deploy is skipped.** This is expected for PRs, manual non-main runs, failed earlier jobs, or when `DEPLOY_ENABLED` is unset/not exactly `true`. A successful CI run with deploy skipped does not prove cloud CD.

**Push to GHCR is denied.** Check `packages: write` on the publish job, repository/org restrictions, and the package's linked repository Actions access. The workflow uses its provided `GITHUB_TOKEN`; do not replace it with an AWS access key.

**ImagePullBackOff or unauthorized GHCR pull.** A public Git repository does not automatically make its GHCR package public. Make the package public for this demo, or create a `read:packages` pull secret in `devops-dashboard` and set `GHCR_PULL_SECRET`. Check that the secret exists in the same namespace, has type `kubernetes.io/dockerconfigjson`, and has a valid token. Never print its contents to workflow logs.

**Image not found.** Check the lowercase owner/repository image path, full 40-character SHA tag, and digest. Do not manually apply the manifest's `replace-with-commit-sha` placeholder. Build/publish must complete before deployment.

## AWS authentication and authorization

**AWS CLI session expired.** Run `aws login`, or your configured SSO profile's login command, and verify `aws sts get-caller-identity`. The account should be `906555057481`. Local browser sessions and GitHub OIDC sessions are separate.

**AssumeRoleWithWebIdentity is denied.** Check the role's exact OIDC provider ARN, audience `sts.amazonaws.com`, and subject for this repository's main branch. New repositories can include immutable owner/repository IDs in the subject. A legacy name-only condition will not match those tokens. Do not loosen trust to all repositories or branches. If a GitHub environment was added, its name changes the subject format.

**DescribeCluster is denied.** Check the IAM permission on the exact cluster ARN, region, and account. The workflow role needs cluster describe access and the trust policy; it does not need general AdministratorAccess.

**kubectl returns Unauthorized or Forbidden.** Check the EKS authentication mode, access entry for the IAM role ARN (not the STS session ARN), `github-deployer` group mapping, and namespaced RoleBinding. Run `kubectl auth can-i create deployments -n devops-dashboard` with the intended identity. IAM authentication and Kubernetes RBAC are separate layers. Do not fix this by giving the workflow cluster-admin.

**API endpoint times out.** A private-only EKS API cannot be reached from the default GitHub-hosted runner. Use an appropriately secured runner in the VPC or an approved reachable API endpoint. Check endpoint CIDRs, DNS, routing, and security controls.

**Expired token during a long job.** Reauthenticate locally as needed. Actions assumes a one-hour role session; do not store the issued token. Investigate prolonged downloads/rollouts rather than replacing short-lived auth with committed keys.

## Kubernetes rollout and public access

Useful read-only diagnostics, with an authenticated kubeconfig:

```powershell
kubectl --context cia2-eks -n devops-dashboard get deployments,pods,svc -o wide
kubectl --context cia2-eks -n devops-dashboard describe deployment devops-dashboard
kubectl --context cia2-eks -n devops-dashboard get events --sort-by=.lastTimestamp
kubectl --context cia2-eks -n devops-dashboard logs deployment/devops-dashboard --tail=100
```

**Pod stays Pending.** Check compute capacity, amd64 node availability, scheduling events, resource requests, and Auto Mode node provisioning. Rolling updates need capacity for one extra pod. Two replicas on one node provide pod redundancy, not protection against that node's failure.

**CrashLoopBackOff or OOMKilled.** Check logs and previous container termination reason. Runtime memory is limited to 512 MiB; the JVM heap cap is only part of process memory. Tune limits/heap together if the application grows. Do not remove probes merely to conceal a startup failure.

**Readiness/liveness fails.** Confirm port 8080 and the configured Actuator paths. Startup permits up to about 150 seconds. Ensure `/tmp` is writable with UID 10001 while the root filesystem is read-only. Check Kubernetes events and actual HTTP responses.

**Service EXTERNAL-IP stays pending.** EKS often fills that column with a DNS hostname, not an IP. If neither appears, inspect Service events, public subnet tags, available subnets/AZs, cluster-role permissions, and load-balancer quotas. The default `eks.amazonaws.com/nlb` class requires EKS Auto Mode. Standard EKS instead needs the AWS Load Balancer Controller and `service.k8s.aws/nlb`.

**NLB exists but HTTP times out.** Check internet-facing scheme, routes, security groups, IP targets, readiness health checks, VPC CNI connectivity, and target-group health. A LoadBalancer address alone does not prove the app is reachable. The workflow retries while DNS and target health settle.

**Public commit/version check fails.** Compare GitHub's published SHA/digest with the Deployment image and `/api/info`. Check that the rollout completed and that you are using the current Service URL. Do not change expected SHA to an old value to make a wrong deployment pass.

**Failed rollout.** The workflow fails and prints diagnostics; it does not silently roll back. Inspect the cause, then explicitly approve a rollback/revert. See the [deployment guide](deployment-guide.md).

## Ansible

Use Linux/WSL and the documented Python version. Install AWS CLI and kubectl and authenticate there, then generate the `cia2-eks` kubeconfig context. Native Windows is not the supported Ansible control environment. An inventory containing localhost still needs those local tools and credentials; it does not provide authentication itself.

`--syntax-check` proves only playbook syntax. A live successful recap requires real Kubernetes and HTTP access. If using a custom context or URL, pass `-e kube_context=<context>` or `-e deployment_url=http://<hostname>`.
