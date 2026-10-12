# Evidence checklist

Capture real results as you perform each step. Do not label a diagram, configuration file, or expected output as a successful deployment. Never include tokens, login URLs containing session data, kubeconfig credentials, or access keys in screenshots.

## Local evidence already reproducible

- [ ] Project tree showing Maven Wrapper, source, tests, Docker, workflow, Kubernetes, Ansible, and documentation.
- [ ] `java -version` showing Java 21.
- [ ] `./mvnw.cmd clean test` summary: 8 tests, 0 failures/errors/skips.
- [ ] `./mvnw.cmd package` success and `target/devops-dashboard.jar`.
- [ ] Docker multi-stage build output showing tests succeeded and image exported.
- [ ] `docker images devops-dashboard` showing the local image.
- [ ] `docker inspect` showing container `healthy` and `docker exec ... id` showing UID/GID 10001.
- [ ] Local dashboard, `/api/info`, and `/actuator/health`.

Recorded on 12 October 2026: Maven tests/package passed on Windows; Docker build passed with all eight tests; the local container returned HTTP 200, health UP, and UID/GID 10001. The initial image download stalled, and one retry completed. No AWS resources were created during these checks.

Additional local checks passed: actionlint workflow validation, Kubernetes schemas (all five resources), local image/commit/pull-secret rendering, Bash syntax, Ansible syntax, and Python HTTP verification. A temporary v2 container passed with read-only root filesystem and all capabilities dropped. The verifier rejected an intentionally wrong version. These checks do not prove public AWS deployment.

## Cloud setup evidence still to collect

- [ ] GitHub repository `moksha3110/cia2-devops-dashboard`, main branch, and workflow file.
- [ ] Repository Actions variables; hide anything your institution treats as identifying information.
- [ ] AWS EKS cluster active in `ap-south-1` and running amd64 compute.
- [ ] OIDC IAM role trust restriction to this repository and main branch.
- [ ] IAM policy with only the required cluster describe permission.
- [ ] EKS access entry and namespace Role/RoleBinding.
- [ ] GHCR package and full SHA tag/digest; public visibility or configured private pull access.

## End-to-end v1 evidence still to collect

- [ ] Main push commit and matching workflow run.
- [ ] All three jobs green: CI, publish, deploy. A skipped deploy is not end-to-end success.
- [ ] Test reports and JAR artifact downloadable from the workflow.
- [ ] Workflow summary showing the exact image digest and public URL.
- [ ] `kubectl -n devops-dashboard get deployments,pods,svc -o wide`: two ready replicas, public hostname.
- [ ] Public dashboard showing version v1, AWS environment, message, and commit SHA.
- [ ] Public health JSON showing `UP`.

## Automatic v2 redeployment evidence still to collect

- [ ] Git diff changing only `APP_VERSION` and `DEPLOYMENT_MESSAGE` in the Kubernetes manifest.
- [ ] New main commit and automatically triggered workflow; no manual `kubectl set image` used for this demonstration.
- [ ] New SHA-tagged image and digest in GHCR.
- [ ] Successful rolling update and two ready v2 pods.
- [ ] The same public URL displaying v2, the updated message, and the new commit SHA.
- [ ] Before/after images showing v1 and v2 clearly.
- [ ] Optional Ansible recap showing verification success and `changed=0`.

## Useful viva questions

1. **What is CI versus CD?** CI compiles and tests each change; CD publishes a tested image and updates the cloud Deployment.
2. **Why two replicas?** They allow traffic to continue while pods are replaced; adequate cluster capacity is still required.
3. **Why SHA tags and digests?** The tag links to source; the digest fixes the exact deployed image.
4. **Why OIDC?** GitHub obtains a short-lived AWS role session instead of storing an AWS access key.
5. **Why does a PR not deploy?** Explicit event/ref gates and per-job permissions isolate PR validation.
6. **Why a Service?** Pods change addresses; the Service provides a stable traffic entry and cloud load balancer integration.
7. **Why separate probes?** Startup permits boot time, readiness gates traffic, and liveness triggers restarts.
8. **What is not proven yet?** Until cloud evidence is collected, only local execution and static configuration checks are proven.
