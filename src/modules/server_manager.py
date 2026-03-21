from datetime import timedelta
import logging
import psutil
import time
import subprocess


logger: logging.Logger = logging.getLogger(__name__)


def get_status() -> str:
    cpu_percent: float = psutil.cpu_percent(interval=1)
    memory_percent: float = psutil.virtual_memory().percent
    disk_percent: float = psutil.disk_usage("/").percent
    uptime: str = str(timedelta(seconds=int(time.time() - psutil.boot_time())))

    temp: float = 0.0
    try:
        temps: dict = psutil.sensors_temperatures()
        cores = temps["coretemp"]
        temp = sum(t.current for t in cores) / len(cores)
    except Exception: pass

    status_message: str = f"""
**CPU** - {cpu_percent}%
**Temp** - {temp}
**Memory** - {memory_percent}%
**Disk** - {disk_percent}%
**Uptime** - {uptime}
"""
    return status_message


def git_pull() -> None:
    result: subprocess.CompletedProcess[str] = subprocess.run(["git", "pull"], capture_output=True, text=True)
    if result.returncode != 0: raise Exception(result.stderr)
