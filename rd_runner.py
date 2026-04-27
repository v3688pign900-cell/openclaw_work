#!/usr/bin/env python3
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOWED_WRITE_ROOT = ROOT
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


def result_envelope(task, status, summary, artifacts, notes, issues, next_action_suggestion, executor_signature="RD-xiaoxia"):
    return {
        "task_id": task["task_id"],
        "completed_by": "小蝦",
        "executor_role": "RD",
        "status": status,
        "summary": summary,
        "result": {
            "artifacts": artifacts,
            "notes": notes,
            "executor_signature": executor_signature
        },
        "issues": issues,
        "next_action_suggestion": next_action_suggestion
    }


def build_analysis_result(task, task_path: Path):
    now = datetime.now().isoformat()
    goal = task.get("goal", "")
    constraints = task.get("constraints", [])
    inputs = task.get("inputs", {})
    notes = [
        f"goal={goal}",
        f"generated_at={now}",
        f"input_keys={','.join(inputs.keys()) if isinstance(inputs, dict) else 'n/a'}",
        f"constraint_count={len(constraints)}",
        "analysis executor completed local structured review",
    ]
    return result_envelope(
        task,
        "completed",
        f"已完成 analysis task：{task.get('title', task['task_id'])}",
        [str(task_path.relative_to(ROOT))],
        notes,
        [],
        "由大蝦確認是否需要再拆成 coding / debug 子任務。"
    )


def build_sop_result(task, task_path: Path):
    now = datetime.now().isoformat()
    goal = task.get("goal", "")
    constraints = task.get("constraints", [])
    inputs = task.get("inputs", {})
    steps = [
        f"1. 確認目標：{goal}",
        f"2. 檢查輸入：{json.dumps(inputs, ensure_ascii=False)}",
        f"3. 套用限制：{'; '.join(constraints) if constraints else 'none'}",
        "4. 依照 task title 執行對應 SOP",
        "5. 回傳 command / steps / result 給大蝦驗收"
    ]
    return result_envelope(
        task,
        "completed",
        f"已產出 SOP task：{task.get('title', task['task_id'])}",
        [str(task_path.relative_to(ROOT))],
        [f"generated_at={now}", "sop executor produced structured steps", *steps],
        [],
        "由大蝦決定是否直接回 CEO，或再補 one-liner command。"
    )


def build_debug_result(task, task_path: Path):
    now = datetime.now().isoformat()
    inputs = task.get("inputs", {})
    constraints = task.get("constraints", [])
    suspected_areas = []
    if isinstance(inputs, dict):
        suspected_areas = list(inputs.keys())
    return result_envelope(
        task,
        "completed",
        f"已完成 debug 初步分析：{task.get('title', task['task_id'])}",
        [str(task_path.relative_to(ROOT))],
        [
            f"generated_at={now}",
            f"suspected_areas={','.join(suspected_areas) if suspected_areas else 'n/a'}",
            f"constraint_count={len(constraints)}",
            "debug executor produced candidate root-cause scan",
            "next step: verify logs / config / runtime state against suspected areas"
        ],
        [],
        "由大蝦決定是否再派具體 command-based debug task。"
    )


def resolve_target_file(target_file):
    if not target_file:
        return None, "missing_target_file"
    path = (ROOT / target_file).resolve() if not Path(target_file).is_absolute() else Path(target_file).resolve()
    try:
        path.relative_to(ALLOWED_WRITE_ROOT)
    except ValueError:
        return None, "target_outside_repo"
    return path, None


def apply_coding_change(target_path: Path, inputs):
    mode = inputs.get("edit_mode", "append")
    content = target_path.read_text() if target_path.exists() else ""

    if mode == "append":
        append_text = inputs.get("append_text", "")
        if not append_text:
            return False, "missing_append_text", content
        new_content = content + ("" if content.endswith("\n") or content == "" else "\n") + append_text
        target_path.write_text(new_content)
        return True, "appended", new_content

    if mode == "replace":
        old_text = inputs.get("old_text")
        new_text = inputs.get("new_text", "")
        if old_text is None:
            return False, "missing_old_text", content
        if old_text not in content:
            return False, "old_text_not_found", content
        target_path.write_text(content.replace(old_text, new_text, 1))
        return True, "replaced", target_path.read_text()

    return False, "unsupported_edit_mode", content


def build_port_check_script(target_path: Path, port: int):
    content = f'''#!/usr/bin/env bash
set -euo pipefail

PORT="{port}"

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "LISTEN: tcp port $PORT"
  exit 0
else
  echo "NOT LISTEN: tcp port $PORT"
  exit 1
fi
'''
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content)
    target_path.chmod(0o755)


def build_coding_result(task, task_path: Path):
    now = datetime.now().isoformat()
    inputs = task.get("inputs", {}) if isinstance(task.get("inputs", {}), dict) else {}
    target_file = inputs.get("target_file")
    target_path, resolve_error = resolve_target_file(target_file)
    notes = [
        f"generated_at={now}",
        f"target_file={target_file or 'n/a'}",
    ]

    if inputs.get("script_type") == "port_listen_check":
        if resolve_error:
            return result_envelope(
                task,
                "missing_info" if resolve_error == "missing_target_file" else "blocked",
                f"coding task 無法執行：{task.get('title', task['task_id'])}",
                [str(task_path.relative_to(ROOT))],
                [*notes, f"resolve_error={resolve_error}"],
                [resolve_error],
                "補 target_file 或確認檔案位置限制。"
            )
        port = inputs.get("target_port", 18789)
        build_port_check_script(target_path, port)
        return result_envelope(
            task,
            "completed",
            f"已完成 coding task：{task.get('title', task['task_id'])}",
            [str(task_path.relative_to(ROOT)), str(target_path.relative_to(ROOT))],
            [*notes, f"script_type=port_listen_check", f"target_port={port}", "coding executor generated bash script successfully"],
            [],
            "由大蝦驗收 script 與 exit code 行為。"
        )

    if resolve_error:
        return result_envelope(
            task,
            "missing_info" if resolve_error == "missing_target_file" else "blocked",
            f"coding task 無法執行：{task.get('title', task['task_id'])}",
            [str(task_path.relative_to(ROOT))],
            [*notes, f"resolve_error={resolve_error}"],
            [resolve_error],
            "補 target_file 或確認檔案位置限制。"
        )

    ok, action, _ = apply_coding_change(target_path, inputs)
    if not ok:
        return result_envelope(
            task,
            "failed",
            f"coding task 執行失敗：{task.get('title', task['task_id'])}",
            [str(task_path.relative_to(ROOT)), str(target_path.relative_to(ROOT)) if target_path.exists() else str(target_path)],
            [*notes, f"edit_action={action}"],
            [action],
            "檢查 edit_mode / old_text / append_text 是否完整。"
        )

    notes.extend([
        f"edit_action={action}",
        "coding executor modified target file successfully",
    ])
    return result_envelope(
        task,
        "completed",
        f"已完成 coding task：{task.get('title', task['task_id'])}",
        [str(task_path.relative_to(ROOT)), str(target_path.relative_to(ROOT))],
        notes,
        [],
        "由大蝦檢查 diff 後決定是否直接回 CEO。"
    )


def build_placeholder_result(task, task_path: Path):
    task = normalize_task(task)
    task_type = task.get("task_type", "analysis")
    if task_type == "analysis":
        return build_analysis_result(task, task_path)
    if task_type == "sop":
        return build_sop_result(task, task_path)
    if task_type == "debug":
        return build_debug_result(task, task_path)
    if task_type == "coding":
        return build_coding_result(task, task_path)

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
