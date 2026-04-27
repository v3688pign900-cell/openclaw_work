# Local RD Flow

## Goal

讓小蝦在本地自動吃 `tasks/`，產生 `results/`，再交給 coordinator 記錄。

## Files

- `rd_runner.py`：本地 RD runner
- `scripts/run_local_rd_once.sh`：one-shot 執行入口
- `scripts/run_local_rd_watch.sh`：常駐輪詢入口
- `coordinator.py`：接收 task/result，寫 lifecycle log

## Current Behavior

### runner 會做的事

1. 掃描 `tasks/*.json`
2. 找對應 `results/*.result.json`
3. 若沒有 result，就自動建立一份 result stub
4. 呼叫：

```bash
python3 coordinator.py submit-result <task.json> <result.json>
```

5. 讓 coordinator 寫入：

```text
state/coordinator/<task_id>.json
```

## Run Once

```bash
./scripts/run_local_rd_once.sh
```

或：

```bash
python3 rd_runner.py --pull
```

## Watch Mode

```bash
./scripts/run_local_rd_watch.sh
```

或：

```bash
python3 rd_runner.py watch 30
```

說明：
- 每 30 秒掃一次 `tasks/`
- 每輪先 `git pull --rebase`
- 再提交新的 `results/`

## Current Limitation

目前 `rd_runner.py` 是 **auto-stub mode**：
- 會自動接 task
- 會自動產 result
- 但還沒依 `task_type` 做真正 execution

也就是說，現在已經有：
- 任務流轉
- result 回填
- coordinator 記錄

但還沒有：
- coding executor
- debug executor
- sop executor

## Why This Matters

先把 flow 跑通，之後再逐步把小蝦的真正執行能力接進去。

## Next Recommended Step

下一步建議接一個最小 executor：

- `task_type=sop` → 產 steps/commands
- `task_type=analysis` → 產 summary/issues
- `task_type=coding` → 交給真正子代理或腳本
