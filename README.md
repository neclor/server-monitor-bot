# Server Monitor Bot
A compact Python server monitor bot.

## Quick start
- Requirements: Python 3.10+ and dependencies in `requirements.txt`.
- Install: `pip install -r requirements.txt`
- Configure: copy `src/configs/example_api_keys.py` → `src/configs/api_keys.py` and set tokens.
- Run: `python src/main.py`

## Configuration
- Edit `src/configs/bot_config.py` and `src/configs/log_config.py`.
- Define monitored targets in `src/modules/server_manager.py`.

## Logs
- Default logs are written to the `logs/` folder.
