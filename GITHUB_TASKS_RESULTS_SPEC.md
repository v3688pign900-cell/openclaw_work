# GitHub tasks/ results/ Spec

## 1. Directory Role

- `tasks/`：大蝦派給小蝦的 task JSON
- `results/`：小蝦回傳給大蝦的 result JSON

## 2. File Naming

### tasks/

```text
<timestamp>-<slug>.task.json
```

example:

```text
20260427-0945-fix-nginx-restart.task.json
```

### results/

```text
<timestamp>-<slug>.result.json
```

example:

```text
20260427-0958-fix-nginx-restart.result.json
```

## 3. Mapping Rule

- `slug` 必須一致，方便對應 task / result
- result 內容內的 `task_id` 必須回指原 task
- 一個 task 預設對應一個 result
- 若部分完成，`status=partial`

## 4. Task JSON Schema

```json
{
  "task_id": "task-<timestamp>-<slug>",
  "from": "大蝦",
  "to": "小蝦",
  "role": "execution",
  "task_type": "coding | debug | analysis | sop | translation | summary | config",
  "title": "",
  "goal": "",
  "background": "",
  "inputs": {},
  "constraints": [],
  "expected_output": {
    "format": "json | markdown | text",
    "sections": []
  },
  "acceptance_criteria": [],
  "priority": "low | medium | high",
  "deadline_hint": "immediate | normal",
  "assumptions_allowed": true
}
```

## 5. Result JSON Schema

```json
{
  "task_id": "",
  "completed_by": "小蝦",
  "executor_role": "RD",
  "reviewed_by": "大蝦",
  "reported_by": "大蝦",
  "status": "completed | partial | failed | missing_info | blocked",
  "summary": "",
  "result": {
    "artifacts": [],
    "notes": [],
    "executor_signature": "RD-xiaoxia"
  },
  "issues": [],
  "next_action_suggestion": ""
}
```

## 6. Required Rules

### AM side

- 沒有 `goal` 不派工
- 沒有 `constraints` 不做高風險任務
- 沒有 `acceptance_criteria` 不算完整 task
- task 要明確指向檔案、範圍、輸出格式

### RD side

- 只吃 `tasks/*.task.json`
- 只吐 `results/*.result.json`
- result 必須標明 `completed_by` / `executor_role`
- result 建議標明 `reviewed_by` / `reported_by`
- result `result.executor_signature` 必須存在
- 不直接對 CEO 回覆
- 不做策略決策
- 有 blocker 就用 `blocked` 或 `missing_info`

## 7. Status Meaning

- `completed`：全部完成且可驗收
- `partial`：部分完成，但仍有可交付內容
- `failed`：執行失敗
- `missing_info`：缺必要資訊
- `blocked`：有明確外部阻塞

## 8. Minimal SOP

### CEO → 大蝦
1. 收需求
2. 大蝦判斷是否要委派

### 大蝦 → tasks/
1. 建立 `tasks/<timestamp>-<slug>.task.json`
2. 補齊 goal / constraints / expected_output / acceptance_criteria

### 小蝦 → results/
1. 讀對應 task
2. 執行
3. 產出 `results/<timestamp>-<slug>.result.json`

### 大蝦 QA
1. 檢查 `task_id`
2. 檢查 `status`
3. 驗收 artifacts / notes / issues
4. 整理後回 Telegram

## 9. Recommended Slug Style

```text
verb-object-context
```

examples:

- `fix-nginx-restart`
- `write-openclaw-healthcheck`
- `analyze-telegram-routing`

## 10. Acceptance Checklist

大蝦驗收時至少檢查：

- task / result slug 對得上
- result `task_id` 正確
- output format 符合 task 要求
- artifact 存在
- issues 有沒有影響 final answer
