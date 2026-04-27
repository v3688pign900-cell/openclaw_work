#!/usr/bin/env python3
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS_DIR = ROOT / "tasks"
RESULTS_DIR = ROOT / "results"


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def result_path_for_task(task_path: Path):
    name = task_path.name
    if name.endswith(".task.json"):
        return RESULTS_DIR / name.replace(".task.json", ".result.json")
    if name.endswith(".json") and name.startswith("task-"):
        return RESULTS_DIR / name.replace(".json", ".result.json")
    return RESULTS_DIR / f"{task_path.stem}.result.json"


def normalize_task(task):
    normalized = dict(task)
    if "task_type" not in normalized:
        normalized["task_type"] = normalized.get("type", "analysis")
    return normalized


def build_placeholder_result(task, task_path: Path):
    task = normalize_task(task)
    task_type = task.get("task_type", "analysis")
    now = datetime.now().isoformat()
    return {
        "task_id": task["task_id"],
        "status": "partial",
        "summary": f"小蝦已收到 task，建立本地 result stub，等待實際執行邏輯接入。 ({task_type})",
        "result": {
            "artifacts": [
                str(task_path.relative_to(ROOT))
            ],
            "notes": [
                f"task_type={task_type}",
                f"generated_at={now}",
                "local runner detected new task",
                "execution logic not yet specialized"
            ]
        },
        "issues": [
            "目前是本地 auto-stub flow，尚未接真正執行器"
        ],
        "next_action_suggestion": "由大蝦決定是否補 task detail，或接上對應 task_type 的 executor。"
    }


def run_git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def git_pull():
    remote = run_git("config", "--get", "remote.origin.url")
    if remote.returncode != 0 or not remote.stdout.strip():
        return {"ok": False, "reason": "missing_remote"}

    branch = run_git("branch", "--show-current")
    current_branch = branch.stdout.strip() or "main"
    pull = run_git("pull", "--rebase", "origin", current_branch)
    if pull.returncode != 0:
        return {"ok": False, "reason": "pull_failed", "stderr": pull.stderr.strip()}
    return {"ok": True, "reason": "pulled", "stdout": pull.stdout.strip()}


def submit_result(task_path: Path, result_path: Path):
    res = subprocess.run(
        [sys.executable, str(ROOT / "coordinator.py"), "submit-result", str(task_path), str(result_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return res.returncode, res.stdout, res.stderr


def process_task(task_path: Path):
    task = load_json(task_path)
    result_path = result_path_for_task(task_path)
    if not result_path.exists():
        result = build_placeholder_result(task, task_path)
        save_json(result_path, result)

    code, out, err = submit_result(task_path, result_path)
    return {
        "task": task["task_id"],
        "status": "submitted" if code == 0 else "submit_failed",
        "result_file": str(result_path.relative_to(ROOT)),
        "coordinator_stdout": out.strip(),
        "coordinator_stderr": err.strip(),
    }


def run_once(pull_first=False):
    meta = {}
    if pull_first:
        meta["git_pull"] = git_pull()
    task_files = sorted(TASKS_DIR.glob("*.json"))
    outputs = [process_task(p) for p in task_files]
    return {"meta": meta, "results": outputs}


def watch_loop(interval_seconds=30, pull_first=True):
    while True:
        output = run_once(pull_first=pull_first)
        print(json.dumps(output, ensure_ascii=False, indent=2), flush=True)
        time.sleep(interval_seconds)


def main():
    args = sys.argv[1:]
    if args and args[0] == "watch":
        interval = int(args[1]) if len(args) > 1 else 30
        watch_loop(interval_seconds=interval, pull_first=True)
        return

    output = run_once(pull_first="--pull" in args)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
