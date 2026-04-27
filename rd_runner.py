#!/usr/bin/env python3
import json
import subprocess
import sys
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


def main():
    task_files = sorted(TASKS_DIR.glob("*.json"))
    outputs = [process_task(p) for p in task_files]
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
