from config_manager import ConfigManager

misc_config = ConfigManager("json/misc.json")
misc_data = misc_config.all()

def writeback():
    misc_config.update(misc_data)

tasks = []

from datetime import datetime
from zoneinfo import ZoneInfo

def april_fools_flag():
    now_utc8 = datetime.now(ZoneInfo('Asia/Shanghai'))
    return now_utc8.month == 4 and now_utc8.day == 1