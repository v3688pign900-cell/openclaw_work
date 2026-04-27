#!/usr/bin/env python3
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "state" / "coordinator"
TASKS_DIR = ROOT / "tasks"
RESULTS_DIR = ROOT / "results"
LOG_DIR.mkdir(parents=True, exist_ok=True)
TASKS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TaskLog:
    task_id: str
    from_agent: str
    to_agent: str
    status: str
    created_at: str
    updated_at: str
    retry_count: int
    artifacts: list


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def resolve_repo_path(path: Path):
    return path if path.is_absolute() else (ROOT / path).resolve()


def load_json(path: Path):
    path = resolve_repo_path(path)
    with path.open() as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def normalize_task(task):
    normalized = dict(task)
    if "role" not in normalized and "type" in normalized:
        normalized["role"] = normalized["type"]
    if "task_type" not in normalized:
        normalized["task_type"] = normalized.get("type", "analysis")
    if "title" not in normalized and "task" in normalized:
        normalized["title"] = normalized["task"]
    if "background" not in normalized:
        normalized["background"] = ""
    if "inputs" not in normalized and "input" in normalized:
        normalized["inputs"] = normalized["input"]
    if "inputs" not in normalized:
        normalized["inputs"] = {}
    if "priority" not in normalized:
        normalized["priority"] = "medium"
    if "deadline_hint" not in normalized:
        normalized["deadline_hint"] = "normal"
    if "assumptions_allowed" not in normalized:
        normalized["assumptions_allowed"] = True
    return normalized


def validate_task(task):
    required = [
        "task_id", "from", "to", "role", "task_type", "title",
        "goal", "background", "inputs", "constraints", "expected_output",
        "priority", "deadline_hint", "assumptions_allowed"
    ]
    missing = [k for k in required if k not in task]
    if missing:
        raise ValueError(f"missing task fields: {', '.join(missing)}")


def validate_result(result):
    required = ["task_id", "status", "summary", "result", "issues", "next_action_suggestion"]
    missing = [k for k in required if k not in result]
    if missing:
        raise ValueError(f"missing result fields: {', '.join(missing)}")


def init_log(task):
    ts = now_iso()
    return TaskLog(
        task_id=task["task_id"],
        from_agent=task["from"],
        to_agent=task["to"],
        status="queued",
        created_at=ts,
        updated_at=ts,
        retry_count=0,
        artifacts=[],
    )


def apply_result(log: TaskLog, result):
    log.status = result["status"]
    log.updated_at = now_iso()
    log.artifacts = result.get("result", {}).get("artifacts", [])
    return log


def run_git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def run_reporter(result_path: Path):
    reporter = ROOT / "am_reporter.py"
    if not reporter.exists():
        return {"ok": False, "reason": "reporter_missing"}

    res = subprocess.run(
        [sys.executable, str(reporter), str(result_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        return {"ok": False, "reason": "report_failed", "stderr": res.stderr.strip()}
    report_path = ROOT / "reports" / f"{result_path.stem}.report.txt"
    return {
        "ok": True,
        "reason": "report_generated",
        "report_file": str(report_path.relative_to(ROOT)) if report_path.exists() else None,
        "stdout": res.stdout.strip(),
    }


def git_remote_exists():
    res = run_git("config", "--get", "remote.origin.url")
    return res.returncode == 0 and bool(res.stdout.strip())


def git_has_changes(paths):
    res = run_git("status", "--short", "--", *paths)
    return bool(res.stdout.strip())


def git_commit_and_push(paths, message):
    if not git_remote_exists():
        return {"ok": False, "reason": "missing_remote"}

    run_git("add", *paths)
    if not git_has_changes(paths):
        return {"ok": True, "reason": "no_changes"}

    commit = run_git("commit", "-m", message)
    if commit.returncode != 0:
        return {"ok": False, "reason": "commit_failed", "stderr": commit.stderr.strip()}

    push = run_git("push", "origin", run_git("branch", "--show-current").stdout.strip())
    if push.returncode != 0:
        return {"ok": False, "reason": "push_failed", "stderr": push.stderr.strip()}

    return {"ok": True, "reason": "pushed"}


def handle_submit_task(task_path: Path):
    task_path = resolve_repo_path(task_path)
    task = normalize_task(load_json(task_path))
    validate_task(task)

    log = init_log(task)
    log_path = LOG_DIR / f"{task['task_id']}.json"
    save_json(log_path, asdict(log))

    sync = git_commit_and_push(
        [str(task_path.relative_to(ROOT)), str(log_path.relative_to(ROOT))],
        f"task: {task['task_id']}"
    )

    print(json.dumps({
        "task": task["task_id"],
        "status": log.status,
        "log_file": str(log_path.relative_to(ROOT)),
        "git_sync": sync,
    }, ensure_ascii=False, indent=2))


def handle_submit_result(task_path: Path, result_path: Path):
    task_path = resolve_repo_path(task_path)
    result_path = resolve_repo_path(result_path)
    task = normalize_task(load_json(task_path))
    result = load_json(result_path)

    validate_task(task)
    validate_result(result)

    if task["task_id"] != result["task_id"]:
        raise ValueError("task_id mismatch")

    log = init_log(task)
    log.status = "running"
    log.updated_at = now_iso()
    log = apply_result(log, result)

    log_path = LOG_DIR / f"{task['task_id']}.json"
    save_json(log_path, asdict(log))

    report = run_reporter(result_path)

    paths_to_sync = [
        str(result_path.relative_to(ROOT)),
        str(log_path.relative_to(ROOT))
    ]
    if report.get("ok") and report.get("report_file"):
        paths_to_sync.append(report["report_file"])

    sync = git_commit_and_push(
        paths_to_sync,
        f"result: {task['task_id']} [{log.status}]"
    )

    output = {
        "task": task["task_id"],
        "status": log.status,
        "log_file": str(log_path.relative_to(ROOT)),
        "artifacts": log.artifacts,
        "report": report,
        "git_sync": sync,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "submit-task":
        handle_submit_task(Path(sys.argv[2]))
        return

    if len(sys.argv) >= 4 and sys.argv[1] == "submit-result":
        handle_submit_result(Path(sys.argv[2]), Path(sys.argv[3]))
        return

    if len(sys.argv) == 3:
        handle_submit_result(Path(sys.argv[1]), Path(sys.argv[2]))
        return

    print(
        "usage:\n"
        "  coordinator.py submit-task <task.json>\n"
        "  coordinator.py submit-result <task.json> <result.json>\n"
        "  coordinator.py <task.json> <result.json>",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
