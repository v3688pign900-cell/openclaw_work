# Coordinator State

這個資料夾是 **流程狀態區**。

如果你在 GitHub 上想快速看現在任務跑到哪，先看這裡。

## 每個 JSON 是什麼

- 一個 `task_id` 對應一個狀態檔
- 檔名通常像：

```text
task-20260427-1049-debug-test.json
```

## 重要欄位

```json
{
  "task_id": "",
  "from_agent": "大蝦",
  "to_agent": "小蝦",
  "status": "queued | running | completed | partial | failed | missing_info | blocked",
  "created_at": "",
  "updated_at": "",
  "retry_count": 0,
  "artifacts": []
}
```

## Status Meaning

### `queued`
- 大蝦已派工
- 小蝦還沒完成
- 通常代表任務剛進來

### `running`
- 小蝦正在處理
- 代表任務執行中

### `completed`
- 小蝦已完成
- 大蝦可以驗收並回 Telegram

### `partial`
- 小蝦有交付內容
- 但還沒完全完成
- 通常需要大蝦判斷要不要再派下一手

### `failed`
- 執行失敗
- 通常要看 `results/` 裡的 `issues`

### `missing_info`
- 缺資訊
- 代表 task 不夠完整，或缺必要輸入
- 需要大蝦補資料

### `blocked`
- 有外部阻塞
- 例如權限、路徑限制、外部依賴、repo 狀態問題

## 你怎麼看

### 想知道現在誰在做事
先看：
- `status=queued` / `running`

### 想知道哪些已經做完
看：
- `status=completed` / `partial`

### 想知道哪些卡住
看：
- `status=failed` / `missing_info` / `blocked`

## 搭配其他資料夾

- `tasks/`：大蝦派工內容
- `results/`：小蝦交付內容
- `state/coordinator/`：流程狀態

## 最短結論

如果你只想在 GitHub 上快速知道目前狀況：

1. 先看 `state/coordinator/`
2. 再看對應 `results/`
3. 最後需要時再回頭看 `tasks/`
