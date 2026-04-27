# STATUS

## Quick Check

進 repo 後直接跑：

```bash
./scripts/dashboard.sh
```

## How To Read

### 大蝦待處理 / 小蝦進行中
代表：
- 大蝦已派工
- 小蝦尚未完成，或正在跑

狀態來源：
- `queued`
- `running`

### 小蝦已完成 / 已回交
代表：
- 小蝦已產出 result
- 大蝦接下來可做 QA / 回 Telegram

狀態來源：
- `completed`
- `partial`

### 卡住 / 失敗 / 缺資訊
代表：
- 需要大蝦補資料、改 task、或重新派工

狀態來源：
- `failed`
- `missing_info`
- `blocked`

## Source of Truth

- `tasks/`：大蝦派工
- `results/`：小蝦交付
- `state/coordinator/`：流程狀態

如果你只想一眼看總表，優先看：

```bash
./scripts/dashboard.sh
```
