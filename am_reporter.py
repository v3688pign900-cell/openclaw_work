#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def save_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def build_report(result):
    task_id = result.get("task_id", "unknown")
    status = result.get("status", "unknown")
    summary = result.get("summary", "")
    completed_by = result.get("completed_by", "unknown")
    reviewed_by = result.get("reviewed_by", "大蝦")
    artifacts = result.get("result", {}).get("artifacts", [])
    issues = result.get("issues", [])

    lines = [
        f"結論：{summary}",
        f"Status：{status}",
        f"執行：{completed_by}",
        f"驗收/回報：{reviewed_by}",
        f"task_id：{task_id}",
    ]
    if artifacts:
        lines.append("Artifacts：")
        lines.extend([f"- {a}" for a in artifacts])
    if issues:
        lines.append("Issues：")
        lines.extend([f"- {i}" for i in issues])
    else:
        lines.append("Issues：none")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        print("usage: am_reporter.py <result.json>", file=sys.stderr)
        sys.exit(1)

    result_path = Path(sys.argv[1])
    if not result_path.is_absolute():
        result_path = (ROOT / result_path).resolve()

    result = load_json(result_path)
    report = build_report(result)
    out_path = REPORTS_DIR / (result_path.stem + ".report.txt")
    save_text(out_path, report)
    print(report)


if __name__ == "__main__":
    main()
