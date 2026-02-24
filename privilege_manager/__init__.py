from config_manager import ConfigManager

user_config = ConfigManager("json/user_list.json", default_key="user_list")
user_list = user_config.all()

su_list = user_list["superadmin"]
ad_list = user_list["admin"]

def checkuser(id):
    # 超级管理员
    if id in su_list:
        return 2
    # 管理员
    elif id in ad_list:
        return 1
    # 非管理员
    else:
        return 0

def add_admin(id):
    if checkuser(id):
        return "该用户已经是管理员！"
    ad_list.append(id)
    user_config.update(user_list)
    return "已添加 "+id+" 为管理员。"

def rem_admin(id):
    if checkuser(id) == 0:
        return "该用户没有管理员权限！"
    ad_list.remove(id)
    user_config.update(user_list)
    return "已移除 "+id+" 的管理员权限。"


def get_admin_list():
    astr = "管理员用户有："
    for i in ad_list:
        astr += str(i)
        if i != ad_list[-1]:
            astr += "、"
    return astr