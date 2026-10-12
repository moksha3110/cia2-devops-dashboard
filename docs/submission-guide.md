# Submission and viva guide

## Open these first

- Repository: https://github.com/moksha3110/cia2-devops-dashboard
- Actions: https://github.com/moksha3110/cia2-devops-dashboard/actions
- Registry: https://github.com/moksha3110/cia2-devops-dashboard/pkgs/container/cia2-devops-dashboard
- Application: http://k8s-devopsda-devopsda-fb98dd518c-5089fdf68ed45b95.elb.ap-south-1.amazonaws.com
- Report: [PDF](../reports/CIA2-Technical-Report.pdf), [editable Word](../reports/CIA2-Technical-Report.docx), [Markdown](../reports/CIA2-Technical-Report.md).
- Original evidence: [reports/evidence](../reports/evidence/).

The public application depends on keeping the billable AWS resources running. Do not assume the URL remains available after cleanup.

## What was demonstrated

1. The v1 source commit `10eddd2d8f4bbe0fe77c84feb1353485590d3171` passed CI, publication, deployment and public HTTP checks.
2. Manual run `38228883729` also passed all 17 read-only Ansible tasks with `changed=0`, `unreachable=0`, and `failed=0`.
3. Commit `ff59e4b8600af134c1f1c20a47370d6045e56efe` changed the application HTML and deployment metadata to v2. Its push automatically triggered successful run `38229922992`.
4. Follow-up commit `9a7d68992241ddca2566847172bc14dd905a833a` persisted cross-zone NLB routing for the single-worker demonstration topology. Recorded evidence identifies the exact release commit and image digest.
5. The temporary, explicitly approved administrator grant used to bootstrap namespace RBAC was removed. Routine deployment uses namespace-scoped permissions and short-lived OIDC sessions.

## Repeat the live demonstration

The current release is v2. For a fresh viva demonstration, edit the visible subtitle in `src/main/resources/static/index.html` and change `APP_VERSION` and `DEPLOYMENT_MESSAGE` in `k8s/deployment.yaml` to v3 and a new message. Keep the image placeholder; the workflow supplies the SHA and digest.

```powershell
# Review changes before publishing. These commands are instructions, not a second executed demo.
git diff
git add src/main/resources/static/index.html k8s/deployment.yaml
git commit -m "Demonstrate v3 automatic deployment"
git push origin main
```

Watch the three jobs complete in Actions, then refresh the same application URL. Compare `/api/info` commitSha with the pushed commit. Download the `cloud-evidence` and `junit-reports` artifacts. The deployment job, rather than a manual kubectl command, performs the rollout.

## Explain these files

| File | Viva explanation |
| --- | --- |
| `pom.xml` / Maven Wrapper | Dependencies, Java version, executable JAR and repeatable build tool version. |
| Java controller / configuration record | REST metadata supplied by environment, no external service dependencies. |
| Tests | Context, configuration, optional SHA, HTML, metadata and three health checks. |
| `Dockerfile` | Build/test stage, smaller runtime stage, non-root user and health check. |
| `ci-cd.yml` | Event guards, job dependencies, per-job permissions, SHA publication and OIDC deployment. |
| `deployment.yaml` | Two replicas, resources, probes, rolling updates and container security. |
| `service.yaml` | Stable public NLB entry on port 80 to container port 8080. |
| `rbac.yaml` | Namespace-scoped deployment access, installed once by an administrator. |
| `infra/eks.yaml` | Reproducible AWS networking, cluster, infrastructure roles and access entry. |
| `ansible/verify.yml` | Read-only checks of rollout, pod images, health, metadata and HTML. |

## Reporting tools

The report is generated from recorded evidence, not invented output. Its cloud image is explicitly labelled as a view of AWS CLI/kubectl records rather than an AWS Console screenshot. Dashboard, registry, repository and pipeline images are real browser captures. You can add instructor-specific AWS Console screenshots if requested.

Reporting tools do not change the application's dependencies. From a separate Python virtual environment, install `reportlab`, `pillow`, `python-docx`, `playwright`, and `pymupdf`; Edge is used for screenshots. Run `python scripts/render-evidence.py` and `python scripts/build-report.py` after collecting all evidence. The report builder currently uses the Windows Arial font for its diagram.

## Limits and cleanup

The demo proves the delivery path, not multi-node/AZ resilience: both replicas currently fit on one worker. HTTP is public without TLS. Rollback, load testing, failure injection and cleanup were not executed. EKS, compute, storage, public IPv4 and NLB charges continue until resources are removed. Follow the deployment guide for intentional cleanup after assessment; deleting only pods does not stop all charges.
