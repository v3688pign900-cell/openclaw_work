#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found"
  exit 1
fi

python3 <<'PY'
import json
from pathlib import Path

root = Path('.')
state_dir = root / 'state' / 'coordinator'

logs = []
for path in sorted(state_dir.glob('*.json')):
    with path.open() as f:
        data = json.load(f)
        data['_file'] = str(path)
        logs.append(data)

am_pending = []
rd_done = []
blocked = []

for item in logs:
    status = item.get('status', 'unknown')
    task_id = item.get('task_id', 'unknown')
    artifacts = item.get('artifacts', [])
    artifact_summary = ', '.join(artifacts[:2]) if artifacts else '-'

    if status in ('queued', 'running'):
        am_pending.append((task_id, status, artifact_summary))
    elif status in ('completed', 'partial'):
        rd_done.append((task_id, status, artifact_summary))
    elif status in ('failed', 'missing_info', 'blocked'):
        blocked.append((task_id, status, artifact_summary))

print('=== DASHBOARD ===')
print()
print('大蝦待處理 / 小蝦進行中')
if am_pending:
    for task_id, status, artifacts in am_pending:
        print(f'- {task_id} [{status}] :: {artifacts}')
else:
    print('- none')

print()
print('小蝦已完成 / 已回交')
if rd_done:
    for task_id, status, artifacts in rd_done:
        print(f'- {task_id} [{status}] :: {artifacts}')
else:
    print('- none')

print()
print('卡住 / 失敗 / 缺資訊')
if blocked:
    for task_id, status, artifacts in blocked:
        print(f'- {task_id} [{status}] :: {artifacts}')
else:
    print('- none')

print()
print(f'total_logs={len(logs)}')
PY
