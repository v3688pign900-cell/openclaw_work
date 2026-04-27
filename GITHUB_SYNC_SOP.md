# GitHub Push/Pull Flow SOP

## Goal

把 `tasks/` / `results/` 從本地資料夾流程，改成真的 git + GitHub sync flow。

## Flow

### 大蝦派工

```bash
python3 coordinator.py submit-task tasks/<timestamp>-<slug>.task.json
```

作用：
- validate task schema
- 建立 `state/coordinator/<task_id>.json`
- `git add`
- `git commit`
- `git push origin <current-branch>`

### 小蝦交付

```bash
python3 coordinator.py submit-result tasks/<timestamp>-<slug>.task.json results/<timestamp>-<slug>.result.json
```

作用：
- validate task/result schema
- 更新 coordinator log
- `git add`
- `git commit`
- `git push origin <current-branch>`

## Required Conditions

以下 2 個條件沒滿足，GitHub sync 不會真的 push：

1. repo 要有 `origin`
2. git / GitHub auth 要可 push

## Check Commands

### 檢查 remote

```bash
git remote -v
```

### 設定 remote

```bash
git remote add origin <repo-url>
```

或若已有錯的 remote：

```bash
git remote set-url origin <repo-url>
```

### 檢查 GitHub CLI auth

```bash
gh auth status
```

### 登入 GitHub CLI

```bash
gh auth login
```

## Recommended Repo Layout

```text
tasks/
results/
deliverables/
state/coordinator/
```

## Current Behavior

- 若沒有 `origin`，coordinator 仍會寫本地 log，但 `git_sync.reason=missing_remote`
- 若沒有變更，`git_sync.reason=no_changes`
- 若 commit 失敗，會回 `commit_failed`
- 若 push 失敗，會回 `push_failed`

## One-liner Test

### submit task

```bash
python3 coordinator.py submit-task tasks/20260427-0940-sample.task.json
```

### submit result

```bash
python3 coordinator.py submit-result tasks/20260427-0940-sample.task.json results/20260427-0940-sample.result.json
```
