import asyncio
from datetime import timedelta
import logging
import subprocess
import psutil
import time


logger: logging.Logger = logging.getLogger(__name__)


async def get_status() -> str:
    return await asyncio.to_thread(_get_status)


def _get_status() -> str:
    cpu_percent: float = psutil.cpu_percent(interval=1)
    memory_percent: float = psutil.virtual_memory().percent
    disk_percent: float = psutil.disk_usage("/").percent
    uptime: str = str(timedelta(seconds=int(time.time() - psutil.boot_time())))

    temp: float = 0.0
    try:
        temps: dict = psutil.sensors_temperatures()  # type: ignore
        cores = temps.get("coretemp", [])
        if cores:
            temp = sum(t.current for t in cores) / len(cores)
    except Exception: pass

    return f"""
**CPU** - {cpu_percent}%
**Temp** - {temp}
**Memory** - {memory_percent}%
**Disk** - {disk_percent}%
**Uptime** - {uptime}
"""
