import logging
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

path_config = ConfigManager("json/paths.json", default_key="paths")
pat_list = path_config.all()

str1 = "已指定"
str2 = "当前 QQ 运行环境为"

def switch_sys_env():
    path_config.set("sys_env", "wsl") if pat_list["sys_env"] == "win" else path_config.set("sys_env", "win")
    pat_list = path_config.all() # Reload pat_list after update
    return str1+str2+f" {pat_list[pat_list['sys_env']]['desc']}。"

# 询问 QQ 和 NapCat 看到的 path
def bf_path():

    return pat_list[pat_list["sys_env"]]["botfile_path"]

# 询问 bot 后端程序（nonebot2）看到的 path
def nb_path():

    return pat_list[pat_list["sys_env"]]["backend_path"]
    
def ask_sys():

    return str2+f" {pat_list[pat_list['sys_env']]['desc']}。"
