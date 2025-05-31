import json

pat_file = open("json/paths.json","r",encoding="utf-8")
pat_list_raw = pat_file.read()
pat_file.close()
pat_list = json.loads(pat_list_raw)['paths']

str1 = "已指定"
str2 = "当前 QQ 运行环境为"

def switch_sys_env():
    if pat_list["sys_env"] == "win":
        pat_list["sys_env"] = "wsl"
        writeback()
        return str1+str2+" WSL (Linux 子系统)。"
    elif pat_list["sys_env"] == "wsl":
        pat_list["sys_env"] = "win"
        writeback()
        return str1+str2+" Windows。"

# 询问 QQ 和 NapCat 看到的 path
def bf_path():
    if pat_list["sys_env"] == "wsl":
        return pat_list["wsl_botfile_path"]
    else:
        return pat_list["win_botfile_path"]

# 询问 bot 后端程序（nonebot2）看到的 path
def nb_path():
    return pat_list["bot_backend_path"]
    
def ask_sys():
    if pat_list["sys_env"] == "wsl":
        return str2+" WSL (Linux 子系统)。"
    else:
        return str2+" Windows。"

def writeback():
    file = open("json/paths.json","w",encoding="utf-8")
    json.dump({'paths':pat_list},file,ensure_ascii=False,sort_keys=True)