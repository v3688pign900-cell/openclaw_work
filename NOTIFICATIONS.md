# Notifications

## Flow

當 `result` 完成後：

1. `coordinator.py` 觸發 `am_reporter.py`
2. `am_reporter.py` 產生：
   - `reports/*.report.txt`
   - `notifications/pending/*.notify.txt`
3. 主 session 可掃 `notifications/pending/`
4. 發到 Telegram 後，把檔案移到：
   - `notifications/sent/`

## Purpose

- `pending/`：待回 Telegram
- `sent/`：已回過，避免重複發送
