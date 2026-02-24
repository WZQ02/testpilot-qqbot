from config_manager import ConfigManager

misc_config = ConfigManager("json/misc.json")
misc_data = misc_config.all()

def writeback():
    misc_config.update(misc_data)

tasks = []