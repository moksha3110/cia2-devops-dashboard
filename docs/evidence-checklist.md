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

## Cloud setup evidence

Recorded cloud evidence and original browser captures are available in `reports/evidence/`. The report maps them to the deliverables. Cloud-state images are explicitly labelled AWS CLI/kubectl evidence views, rather than AWS Console screenshots. Add institution-specific Console screenshots separately if required.

- [x] GitHub repository `moksha3110/cia2-devops-dashboard`, main branch, and workflow file.
- [x] Repository Actions variables; hide anything your institution treats as identifying information.
- [x] AWS EKS cluster active in `ap-south-1` and running amd64 compute.
- [x] OIDC IAM role trust restriction to this repository and main branch.
- [x] IAM policy with only the required cluster describe permission.
- [x] EKS access entry and namespace Role/RoleBinding.
- [x] GHCR package and full SHA tag/digest; public visibility or configured private pull access.

## End-to-end v1 evidence

Successful runs: push `38228880626` and manual `38228883729`. `reports/evidence/v1/` contains the exact image, deployment/pod/service state, public metadata, health and URL; `dashboard-v1.png` is the original browser capture. Downloaded JUnit XML proves 8 tests passed. `ansible-recap.txt` records 17 successful checks with no changes or failures.

- [x] Main push commit and matching workflow run.
- [x] All three jobs green: CI, publish, deploy. A skipped deploy is not end-to-end success.
- [x] Test reports and JAR artifact downloadable from the workflow.
- [x] Workflow summary showing the exact image digest and public URL.
- [x] `kubectl -n devops-dashboard get deployments,pods,svc -o wide`: two ready replicas, public hostname.
- [x] Public dashboard showing version v1, AWS environment, message, and commit SHA.
- [x] Public health JSON showing `UP`.

## Automatic v2 redeployment evidence

Source-change commit `ff59e4b8600af134c1f1c20a47370d6045e56efe` triggered successful run `38229922992`. Final recorded release `9a7d68992241ddca2566847172bc14dd905a833a` also persists cross-zone routing and triggered successful run `38230049122`. See `v2/`, `v2-run.json`, `pipeline-v2.png`, `dashboard-v2.png`, and `summary.json` for original evidence.

- [x] Git diff changing application HTML plus `APP_VERSION` and `DEPLOYMENT_MESSAGE` in the Kubernetes manifest.
- [x] New main commit and automatically triggered workflow; no manual `kubectl set image` used for this demonstration.
- [x] New SHA-tagged image and digest in GHCR.
- [x] Successful rolling update and two ready v2 pods.
- [x] The same public URL displaying v2, the updated message, and the new commit SHA.
- [x] Before/after images showing v1 and v2 clearly.
- [x] Optional Ansible recap showing verification success and `changed=0`.

## Useful viva questions

1. **What is CI versus CD?** CI compiles and tests each change; CD publishes a tested image and updates the cloud Deployment.
2. **Why two replicas?** They allow traffic to continue while pods are replaced; adequate cluster capacity is still required.
3. **Why SHA tags and digests?** The tag links to source; the digest fixes the exact deployed image.
4. **Why OIDC?** GitHub obtains a short-lived AWS role session instead of storing an AWS access key.
5. **Why does a PR not deploy?** Explicit event/ref gates and per-job permissions isolate PR validation.
6. **Why a Service?** Pods change addresses; the Service provides a stable traffic entry and cloud load balancer integration.
7. **Why separate probes?** Startup permits boot time, readiness gates traffic, and liveness triggers restarts.
8. **What is not proven?** Load performance, worker/AZ failure resilience, rollback, private-registry access, and cleanup have not been tested. Both replicas currently fit on one worker.
