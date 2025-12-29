from datetime import timedelta
import logging
import psutil
import time
import subprocess


logger: logging.Logger = logging.getLogger(__name__)


def get_status() -> str:
    cpu_percent: float = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage("/").percent
    uptime = str(timedelta(seconds=int(time.time() - psutil.boot_time())))

    status_message: str = f"""
**CPU** - {cpu_percent}%
**Memory** - {memory_percent}%
**Disk** - {disk_percent}%
**Uptime** - {uptime}
"""
    return status_message


def git_pull() -> None:
    result: subprocess.CompletedProcess[str] = subprocess.run(["git", "pull"], capture_output=True, text=True)
    if result.returncode != 0: raise Exception(result.stderr)
