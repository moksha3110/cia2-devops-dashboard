# Deployment guide: Windows, GitHub, GHCR, and AWS EKS

## 1. Chosen settings and approval boundary

| Setting | Value |
| --- | --- |
| GitHub owner | `moksha3110` |
| Proposed repository | `cia2-devops-dashboard` |
| AWS account | `906555057481` |
| AWS region | `ap-south-1` (Mumbai) |
| Proposed EKS cluster | `cia2-devops-dashboard` |
| Kubernetes namespace | `devops-dashboard` |
| Proposed GitHub deploy role | `cia2-github-deployer` |
| Cluster integration | EKS Auto Mode, amd64 compute, public NLB |

The repository and cluster names are proposed names, not proof that remote resources exist. Region is configurable if an existing cluster is elsewhere.

On 12 October 2026, the user approved creating billable infrastructure, publishing the repository and deploying the application. CloudFormation stack `cia2-eks` reached CREATE_COMPLETE in Mumbai using [infra/eks.yaml](../infra/eks.yaml), and the cluster reached ACTIVE. GitHub publication, OIDC deployment, public HTTP verification and Ansible verification passed. Historical records and screenshots are under `reports/evidence/`; check live state separately when demonstrating.

The template creates a dedicated VPC with two public subnets, an internet gateway, EKS Auto Mode on Kubernetes 1.36 (standard support at creation), infrastructure roles, and a separate Kubernetes administrator role. Public-IP assignment provides worker egress without a NAT gateway. Security groups control inbound access; there is no SSH access configured. This is a short-lived demonstration topology. The public Kubernetes API requires authenticated and authorized requests. The template selects standard support to avoid opting into extended-support pricing.

```powershell
# Read-only provisioning status
aws cloudformation describe-stacks --stack-name cia2-eks --region ap-south-1
aws cloudformation describe-stack-events --stack-name cia2-eks --region ap-south-1
# Once ready, use the AdministratorRoleArn output for local Kubernetes authentication.
aws cloudformation describe-stacks --stack-name cia2-eks --region ap-south-1 --query 'Stacks[0].Outputs'
```

For cleanup after the demonstration, delete the Kubernetes LoadBalancer Service first and wait for its AWS load balancer to disappear, then delete any workloads and confirm Auto Mode compute is removed. Only then delete stack `cia2-eks` through CloudFormation. Inspect deletion status and remaining EC2 volumes, interfaces, load balancers, and public IPs; do not assume deleting a cluster removes every related resource. Do not delete shared resources. No cleanup has been executed.

EKS is not a zero-cost demo. On 12 October 2026, standard-support control-plane pricing is $0.10/cluster-hour, or $2.40 for 24 hours, before compute, load balancers, storage, IPv4, data transfer, and any Auto Mode charges. Extended-support versions cost more. See [EKS pricing](https://aws.amazon.com/eks/pricing/) and estimate the full resources in the [AWS Pricing Calculator](https://calculator.aws/). Set a budget alert and plan cleanup before creating a cluster.

## 2. Local prerequisites and AWS login

Use PowerShell from `C:\Projects\javaweb`, the existing project root. Install Git, JDK 21, Docker Desktop with Linux containers, AWS CLI v2, and kubectl. Ansible is optional and runs on Linux/WSL. AWS CLI and Docker are already installed on this workstation; kubectl was not found on PATH during implementation.

```powershell
aws --version
aws login
aws sts get-caller-identity
aws eks list-clusters --region ap-south-1
```

Complete the browser login yourself. Confirm the identity account is `906555057481`. The latest read-only check authenticated successfully to this account and found no EKS clusters in Mumbai. The current local identity is root; use a non-root administrator identity for routine setup, and the dedicated OIDC role for GitHub deployment. If your organization uses IAM Identity Center, use its configured profile and `aws sso login --profile <profile>` instead; set `$env:AWS_PROFILE` as appropriate.

Use a suitably authorized administrator identity for one-time setup, not the AWS root user. Never paste access keys, session tokens, or passwords into this repository or chat.

For local Java/Docker commands, see [README](../README.md). For Windows kubectl installation, use the [official instructions](https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/).

## 3. Create the GitHub repository and publish the initial source

After approval, create an empty repository named `cia2-devops-dashboard` under `moksha3110` on GitHub. A public repository/package is simplest for this public demonstration. Do not initialize the remote with another README if you will push this workspace.

Before the first push, add the variables below in **Settings → Secrets and variables → Actions → Variables**. Leave deployment disabled until AWS setup and image-pull access are ready.

| Variable | Value / purpose |
| --- | --- |
| `AWS_ACCOUNT_ID` | `906555057481` |
| `AWS_REGION` | `ap-south-1` |
| `EKS_CLUSTER_NAME` | `cia2-devops-dashboard` or your existing cluster name |
| `AWS_ROLE_ARN` | `arn:aws:iam::906555057481:role/cia2-github-deployer` after role creation |
| `DEPLOY_ENABLED` | `false` initially; exactly `true` enables automatic cloud deployment |
| `GHCR_PULL_SECRET` | Leave unset for public images; `ghcr-pull` for a private package |

These identifiers are variables, not credentials. `GITHUB_TOKEN` is provided automatically by GitHub Actions. No AWS access-key secret or service-account JSON is required. No personal token is required to publish from the workflow.

For this currently uninitialized workspace, the following commands prepare and push the initial repository **after approval**:

```powershell
git init -b main
git add .
git diff --cached --stat
git status
git commit -m "Implement CIA 2 Java dashboard and AWS CI/CD pipeline"
git remote add origin https://github.com/moksha3110/cia2-devops-dashboard.git
git push -u origin main
```

If Git is already initialized, inspect `git status`, `git branch`, and `git remote -v` first and omit initialization/remote creation as appropriate. Use Git Credential Manager's browser authentication. The push automatically starts CI and GHCR publication; cloud deployment is skipped while `DEPLOY_ENABLED` is false. Repository/org policies must permit GitHub Actions and the listed actions. The publish job explicitly requests `packages: write`.

Protect main with PR review and the CI job as a required status check when practical. PRs run tests and package artifacts without image publication or AWS authentication.

## 4. Provision or reuse an EKS cluster

Skip creation if a suitable cluster already exists. This guide defaults to **EKS Auto Mode** to avoid separately installing and maintaining a load-balancer controller for the assignment.

After reviewing costs and obtaining approval, use the AWS Console in Mumbai:

1. Open EKS → Add cluster → Create. Name it `cia2-devops-dashboard` and enable EKS Auto Mode. Choose a Kubernetes version currently in standard support.
2. Create/select the recommended EKS cluster IAM role and Auto Mode node IAM role through the console's role setup. The workflow deploy role is a separate role and must not be used as either of these infrastructure roles.
3. Enable the general-purpose/system node pools and ensure amd64 instances can be provisioned. The Deployment selects amd64 because the workflow builds linux/amd64.
4. Choose a VPC with subnets in at least two availability zones. Internet-facing NLBs need suitable public subnets tagged `kubernetes.io/role/elb=1`. Nodes/pods need outbound access to GHCR and DNS; private subnets normally need an appropriate egress path, such as NAT. That can add cost.
5. Enable API-based EKS access entries (`API` or `API_AND_CONFIG_MAP`). Ensure your administrator identity can access Kubernetes for bootstrap.
6. The Kubernetes API must be reachable from the GitHub runner. This workflow uses GitHub-hosted runners; a private-only endpoint needs a runner in the VPC and workflow changes. A reachable public API still requires AWS authentication and Kubernetes authorization. Plan endpoint CIDR restrictions for your runner network rather than assuming local access proves runner access.
7. Wait for the cluster to become active. Auto Mode may provision nodes as workloads require them. Allow capacity for two 256 MiB requested replicas plus one extra replica during rollout and system workloads.

The console's recommended roles include the infrastructure permissions required by Auto Mode. Review current [Auto Mode setup](https://docs.aws.amazon.com/eks/latest/userguide/automode-get-started-console.html) and [NLB configuration](https://docs.aws.amazon.com/eks/latest/userguide/auto-configure-nlb.html), especially subnet discovery and cluster-role permissions.

For **standard EKS** instead, install/configure the [AWS Load Balancer Controller](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html), including its AWS permissions, and change `spec.loadBalancerClass` in `k8s/service.yaml` to `service.k8s.aws/nlb` before first deployment. The Auto Mode class is not interchangeable with that controller. An already-created Service cannot generally change its load-balancer class in place; plan a controlled Service replacement if migrating.

## 5. Configure GitHub OIDC and a least-privilege AWS role

An administrator performs this once, after approval. Check whether the account already has the GitHub IAM OIDC provider before creating it:

```powershell
aws iam get-open-id-connect-provider --open-id-connect-provider-arn arn:aws:iam::906555057481:oidc-provider/token.actions.githubusercontent.com
# Only if it does not already exist:
aws iam create-open-id-connect-provider --url https://token.actions.githubusercontent.com --client-id-list sts.amazonaws.com
```

The trust policy must match the exact main-branch OIDC subject. Current GitHub defaults for newly created repositories include immutable owner/repository IDs. Older repositories may still use the legacy name-only subject. Do not use `repo:moksha3110/*` or a wildcard branch trust. See [GitHub's AWS OIDC guide](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws) and [subject formats](https://docs.github.com/en/actions/reference/security/oidc).

For a **new public repository**, prepare the policy using its actual IDs:

```powershell
$repoData = Invoke-RestMethod https://api.github.com/repos/moksha3110/cia2-devops-dashboard
$oidcSubject = "repo:moksha3110@$($repoData.owner.id)/cia2-devops-dashboard@$($repoData.id):ref:refs/heads/main"
# For an existing repository that still uses legacy subjects, use instead:
# $oidcSubject = 'repo:moksha3110/cia2-devops-dashboard:ref:refs/heads/main'

$trustPolicy = @{
    Version = '2012-10-17'
    Statement = @(@{
        Effect = 'Allow'
        Principal = @{ Federated = 'arn:aws:iam::906555057481:oidc-provider/token.actions.githubusercontent.com' }
        Action = 'sts:AssumeRoleWithWebIdentity'
        Condition = @{ StringEquals = @{
            'token.actions.githubusercontent.com:aud' = 'sts.amazonaws.com'
            'token.actions.githubusercontent.com:sub' = $oidcSubject
        } }
    })
}
$trustFile = Join-Path $env:TEMP 'cia2-github-trust.json'
[IO.File]::WriteAllText($trustFile, ($trustPolicy | ConvertTo-Json -Depth 8))
aws iam create-role --role-name cia2-github-deployer --assume-role-policy-document "file://$trustFile"

$permissions = @{
    Version = '2012-10-17'
    Statement = @(@{
        Effect = 'Allow'
        Action = 'eks:DescribeCluster'
        Resource = 'arn:aws:eks:ap-south-1:906555057481:cluster/cia2-devops-dashboard'
    })
}
$permissionsFile = Join-Path $env:TEMP 'cia2-github-permissions.json'
[IO.File]::WriteAllText($permissionsFile, ($permissions | ConvertTo-Json -Depth 5))
aws iam put-role-policy --role-name cia2-github-deployer --policy-name DescribeCia2Cluster --policy-document "file://$permissionsFile"
```

For a private repository, retrieve those IDs while authenticated through GitHub CLI/API, rather than assuming the unauthenticated API works. If reusing an IAM role, review and update its trust/policy instead of blindly recreating it. Adjust the cluster ARN if using another name or region. The workflow intentionally has no IAM, EC2, EKS provisioning, or ECR permissions. GHCR publication uses GitHub permissions, not AWS.

This workflow does not declare a GitHub environment, so its trust subject is branch-based. Adding an environment later changes the OIDC subject and requires updating trust and branch protections.

## 6. Grant namespace-scoped Kubernetes access

As the cluster administrator:

```powershell
aws eks describe-cluster --name cia2-devops-dashboard --region ap-south-1 --query cluster.accessConfig.authenticationMode
aws eks update-kubeconfig --name cia2-devops-dashboard --region ap-south-1 --alias cia2-eks
kubectl config current-context
kubectl apply -f k8s/rbac.yaml

aws eks create-access-entry --cluster-name cia2-devops-dashboard --region ap-south-1 --principal-arn arn:aws:iam::906555057481:role/cia2-github-deployer --type STANDARD --kubernetes-groups github-deployer
```

If the cluster is `CONFIG_MAP` only, an administrator must first enable API access entries, for example with `aws eks update-cluster-config --name cia2-devops-dashboard --region ap-south-1 --access-config authenticationMode=API_AND_CONFIG_MAP`, then wait for the update. Do not run that conversion on a cluster already using `API` mode. Review the mode migration before changing an existing cluster.

Do not attach cluster-admin access to the workflow role. The access entry maps it to the `github-deployer` group, and the checked-in RoleBinding grants permissions in `devops-dashboard` only. IAM `eks:DescribeCluster` and Kubernetes RBAC solve different parts of access. See [EKS access entries](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html).

## 7. Allow EKS to pull the GHCR image

After the first successful publish, open GitHub → your profile → Packages → `cia2-devops-dashboard` → Package settings. **New GHCR packages are normally private even if the source repository is public.** For this public assignment demo, explicitly set package visibility to public. Anonymous EKS pulls then need no registry secret. Confirm the package's linked source repository and Actions access if publication is denied.

For a private image, create a classic GitHub PAT with `read:packages` and package access, then create a namespaced pull secret as administrator. `GITHUB_TOKEN` from a workflow is temporary and should not be stored as a long-lived cluster pull credential.

This optional PowerShell example prompts locally and sends the Secret through stdin, without putting a token in command arguments or a file:

```powershell
$registryCredential = Get-Credential -UserName moksha3110 -Message 'Enter a GHCR read:packages PAT as the password'
$registryAuth = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("moksha3110:$($registryCredential.GetNetworkCredential().Password)"))
$dockerConfig = @{ auths = @{ 'ghcr.io' = @{ auth = $registryAuth } } } | ConvertTo-Json -Depth 4 -Compress
$pullSecret = @{
    apiVersion = 'v1'; kind = 'Secret'
    metadata = @{ name = 'ghcr-pull'; namespace = 'devops-dashboard' }
    type = 'kubernetes.io/dockerconfigjson'
    data = @{ '.dockerconfigjson' = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($dockerConfig)) }
}
$pullSecret | ConvertTo-Json -Depth 6 -Compress | kubectl apply -f -
Remove-Variable registryCredential,registryAuth,dockerConfig,pullSecret
```

Set Actions variable `GHCR_PULL_SECRET=ghcr-pull`. Rotate/recreate this secret when the PAT expires. Base64 is encoding, not encryption. Do not print or commit the generated object. The pipeline references the pre-created secret but has no secret read/write permissions. See [GHCR authentication and visibility](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

## 8. Enable deployment and verify v1

Only after approval and setup, set `DEPLOY_ENABLED=true`. In Actions → Java CI and AWS EKS CD → Run workflow, select **main**. The run tests, publishes, authenticates to AWS, deploys, and checks public HTTP automatically. Subsequent main pushes need no manual deployment.

Do not directly apply `k8s/deployment.yaml` with its placeholder image. The workflow substitutes the SHA-tagged image and digest locally before applying it. APP_VERSION and the deployment message come from the committed manifest; COMMIT_SHA is supplied by the workflow.

```powershell
kubectl --context cia2-eks -n devops-dashboard rollout status deployment/devops-dashboard --timeout=300s
kubectl --context cia2-eks -n devops-dashboard get deployments,pods,svc -o wide
$publicHost = kubectl --context cia2-eks -n devops-dashboard get svc devops-dashboard -o 'jsonpath={.status.loadBalancer.ingress[0].hostname}'
$publicUrl = "http://$publicHost"
Invoke-RestMethod "$publicUrl/api/info"
Invoke-RestMethod "$publicUrl/actuator/health"
Start-Process $publicUrl
```

Use the public URL from the workflow summary if preferred. NLB provisioning and target health can take several minutes. The workflow waits for an address and retries HTTP verification. A private/local URL is not public deployment evidence.

## 9. Full automatic v1-to-v2 redeployment

1. Save v1 screenshots of the public dashboard, its commit SHA, two ready pods, GHCR digest, and the successful workflow.
2. In `k8s/deployment.yaml`, change the `APP_VERSION` value from `v1` to `v2`, and change `DEPLOYMENT_MESSAGE` to `CIA 2 version 2 was automatically deployed after a Git push.` Keep the image placeholder; the workflow replaces it.
3. Commit and push that change to main after approval:

```powershell
git diff -- k8s/deployment.yaml
git add k8s/deployment.yaml
git commit -m "Demonstrate automatic v2 deployment"
git push origin main
```

4. Observe the newly triggered run. Tests must pass before image publication. A new SHA tag/digest is published, and Kubernetes performs a rolling update with no manually issued deployment command.
5. Refresh the same public URL. Verify v2, the changed message, environment `aws-eks`, and the new commit SHA. The dashboard refreshes metadata every 30 seconds, or immediately with its Refresh button.

```powershell
$expectedSha = git rev-parse HEAD
python scripts/verify-deployment.py --url $publicUrl --expected-sha $expectedSha --expected-version v2 --expected-environment aws-eks --attempts 12 --delay 5
kubectl --context cia2-eks -n devops-dashboard get deployment devops-dashboard -o 'jsonpath={.spec.template.spec.containers[0].image}'
```

Changing environment values in an existing local container is a configuration demonstration. This main-push procedure is the actual cloud CI/CD redeployment demonstration.

## 10. Optional Ansible verification

Ansible runs on Linux/WSL; its control node is not native Windows. Install an appropriate Python environment, `ansible-core`, AWS CLI, and kubectl there. Log in and generate a kubeconfig **inside that environment**; Windows login and kubeconfig files are not assumed to transfer automatically.

From WSL in this project directory (`/mnt/c/Projects/javaweb`), after authentication:

```bash
python3 -m venv /tmp/cia2-ansible
. /tmp/cia2-ansible/bin/activate
python -m pip install 'ansible-core==2.21.5'
aws eks update-kubeconfig --name cia2-devops-dashboard --region ap-south-1 --alias cia2-eks
ansible-playbook -i ansible/inventory.ini ansible/verify.yml --syntax-check
ansible-playbook -i ansible/inventory.ini ansible/verify.yml \
  -e expected_version=v2 -e expected_sha="$(git rev-parse HEAD)"
```

Use Python 3.12 or newer for the documented Ansible version. If installing another version, check its control-node Python requirement. The playbook verifies rollout, two ready pods, matching pod images, public health, metadata, and HTML. All checks are read-only; no credentials are in inventory. Supply `expected_image` if you also want an independent comparison to a specific published image reference.

## 11. Failure recovery and cleanup

A failed rollout stops CD and shows diagnostics. Inspect events and logs before retrying. A manual rollback is an explicit remote change; review it first:

```powershell
kubectl --context cia2-eks -n devops-dashboard rollout history deployment/devops-dashboard
# After approving rollback:
kubectl --context cia2-eks -n devops-dashboard rollout undo deployment/devops-dashboard
kubectl --context cia2-eks -n devops-dashboard rollout status deployment/devops-dashboard --timeout=300s
```

Rollback restores the previous pod template, including its image and metadata. The next push reapplies the committed configuration, so also fix or revert the source of the failure.

After collecting evidence, disable `DEPLOY_ENABLED`. With approval, delete the application's LoadBalancer Service while the cluster/controller still exists so AWS can remove the NLB, then delete the application/namespace and the cluster/compute if they were created solely for this assignment. Verify removal of load balancers, target groups, nodes, volumes, NAT gateways, public IPv4 resources, and unused VPC infrastructure in the AWS Console. Deleting only the Deployment does not stop all charges. Do not delete shared infrastructure. Remove unused OIDC role/access entries last, and rotate/delete any private registry PAT.

## Verification limits

The Java tests, Docker execution, workflow/schema/syntax checks, AWS infrastructure creation, GitHub OIDC role assumption, GHCR publication, EKS rollout, NLB provisioning, public HTTP checks and live Ansible verification passed. Ansible reported 17 successful checks and no changes/failures. The root session could not assume the administrator role, so the user explicitly approved a temporary GitHub cluster-admin access policy for bootstrap. That policy and the one-time bootstrap workflow were removed immediately after success. The ongoing role uses namespace RBAC. Local kubeconfig administrator-role authentication still requires a non-root IAM identity authorized to assume that role; root login is not sufficient. Rollback, load/failure testing, cleanup and private-registry mode remain untested.
