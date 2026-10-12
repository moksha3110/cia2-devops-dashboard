"""Create an explicitly labelled evidence view from saved raw cloud records."""
import json
from html import escape
from pathlib import Path

e = Path(__file__).resolve().parents[1] / 'reports' / 'evidence'
def load(path):
    return json.loads((e / path).read_text(encoding='utf-8-sig'))

cluster = load('v2/cluster.json')
deploy = load('v2/deployment.json')
pods = load('v2/pods.json')['items']
info = load('v2/info.json')
workers = load('workers.json')
stack = load('cloudformation.json')
lines = [
    '$ aws cloudformation describe-stacks --stack-name cia2-eks --region ap-south-1',
    f"{stack['Name']}: {stack['Status']}",
    '', '$ aws eks describe-cluster --name cia2-devops-dashboard --region ap-south-1',
    f"Cluster: {cluster['name']}    Status: {cluster['status']}    Kubernetes: {cluster['version']}",
    '', '$ aws ec2 describe-instances --include-managed-resources --region ap-south-1',
]
for worker in workers:
    lines.append(f"{worker['Id']}    {worker['Type']}    {worker['State']}    {worker['AZ']}")
lines.extend(['', '$ kubectl -n devops-dashboard get deployment,pods,service',
    f"Deployment: {deploy['metadata']['name']}   Ready: {deploy['status']['readyReplicas']}/{deploy['spec']['replicas']}   Updated: {deploy['status']['updatedReplicas']}   Available: {deploy['status']['availableReplicas']}"])
for pod in pods:
    ready = next((c['status'] for c in pod['status']['conditions'] if c['type']=='Ready'), '?')
    lines.append(f"{pod['metadata']['name']}    {pod['status']['phase']}    Ready={ready}")
lines.extend(['', 'Public HTTP /api/info:',
    f"version={info['version']}    environment={info['environment']}",
    f"message={info['message']}",
    f"commitSha={info['commitSha']}",
    'Public HTTP /actuator/health: ' + json.dumps(load('v2/health.json'))])
content = '\n'.join(lines)
(e/'cloud-kubernetes.html').write_text('''<!doctype html><html><head><meta charset="utf-8"><title>Recorded cloud evidence</title>
<style>body{margin:0;background:#0b1420;color:#dbeafe;font:17px system-ui;padding:25px}h1{color:#5eead4;margin:0 0 8px}p{color:#94a3b8}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:17px/1.3 Consolas,monospace;border:1px solid #334155;border-radius:12px;background:#111e30;padding:20px}</style>
</head><body><h1>CIA 2 | Recorded cloud evidence</h1><p>Actual AWS CLI and GitHub workflow kubectl records · 12 October 2026 · This evidence view is not the AWS Console.</p><pre>'''+escape(content)+'</pre></body></html>', encoding='utf-8')
print('Rendered labelled evidence view from raw JSON records.')
