#!/usr/bin/env bash
# Executed by the deploy job after AWS authentication and kubectl installation.
set -euo pipefail

: "${IMAGE:?IMAGE must include the published tag and digest}"
: "${GITHUB_SHA:?GITHUB_SHA is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"
: "${GITHUB_ENV:?GITHUB_ENV is required}"
: "${GITHUB_STEP_SUMMARY:?GITHUB_STEP_SUMMARY is required}"
namespace="${K8S_NAMESPACE:-devops-dashboard}"
app=devops-dashboard

# The administrator bootstraps the namespace and RBAC; this role cannot create them.
kubectl auth can-i create deployments -n "$namespace" | grep -qx yes
manifest_dir="$RUNNER_TEMP/dashboard-manifests"
mkdir -p "$manifest_dir"

# Render locally first, so the placeholder image is never applied to the cluster.
kubectl set image --local -f k8s/deployment.yaml \
  "$app=$IMAGE" -o yaml > "$manifest_dir/image.yaml"
kubectl set env --local -f "$manifest_dir/image.yaml" \
  "COMMIT_SHA=$GITHUB_SHA" -o yaml > "$manifest_dir/deployment.yaml"
if [[ -n "${GHCR_PULL_SECRET:-}" ]]; then
  [[ "$GHCR_PULL_SECRET" =~ ^[a-z0-9]([-a-z0-9.]*[a-z0-9])?$ ]] || {
    echo 'GHCR_PULL_SECRET must be a Kubernetes secret name.' >&2
    exit 1
  }
  kubectl patch --local -f "$manifest_dir/deployment.yaml" --type merge \
    -p "{\"spec\":{\"template\":{\"spec\":{\"imagePullSecrets\":[{\"name\":\"$GHCR_PULL_SECRET\"}]}}}}" \
    -o yaml > "$manifest_dir/private.yaml"
  cp "$manifest_dir/private.yaml" "$manifest_dir/deployment.yaml"
fi

kubectl -n "$namespace" apply -f "$manifest_dir/deployment.yaml" -f k8s/service.yaml
kubectl -n "$namespace" rollout status "deployment/$app" --timeout=300s
kubectl -n "$namespace" get pods -l "app.kubernetes.io/name=$app" -o wide
kubectl -n "$namespace" get deployment "$app" -o json > "$manifest_dir/status.json"
jq -e --arg image "$IMAGE" '
  .spec.replicas == 2 and
  .status.updatedReplicas == .spec.replicas and
  .status.readyReplicas == .spec.replicas and
  .status.availableReplicas == .spec.replicas and
  ([.spec.template.spec.containers[] | select(.name == "devops-dashboard")][0].image == $image)
' "$manifest_dir/status.json" > /dev/null

kubectl -n "$namespace" get pods -l "app.kubernetes.io/name=$app" -o json \
  | jq -e --arg image "$IMAGE" '
    [.items[] | select(.metadata.deletionTimestamp == null)] |
    length == 2 and all(.[];
      any(.spec.containers[]; .name == "devops-dashboard" and .image == $image) and
      any(.status.conditions[]?; .type == "Ready" and .status == "True"))
  ' > /dev/null

public_host=''
for ((attempt=1; attempt<=60; attempt++)); do
  public_host=$(kubectl -n "$namespace" get service "$app" \
    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
  if [[ -z "$public_host" ]]; then
    public_host=$(kubectl -n "$namespace" get service "$app" \
      -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
  fi
  [[ -n "$public_host" ]] && break
  echo "Waiting for the load balancer address ($attempt/60)..."
  sleep 10
done
[[ -n "$public_host" ]] || { echo 'Load balancer address timed out.' >&2; exit 1; }

expected_version=$(jq -r '
  .spec.template.spec.containers[] | select(.name == "devops-dashboard") |
  .env[] | select(.name == "APP_VERSION") | .value
' "$manifest_dir/status.json")
printf 'PUBLIC_URL=http://%s\nEXPECTED_VERSION=%s\n' "$public_host" "$expected_version" >> "$GITHUB_ENV"
printf 'Deployment image: `%s`\n\nDashboard: http://%s\n' "$IMAGE" "$public_host" >> "$GITHUB_STEP_SUMMARY"
