import json
from config_manager import ConfigManager
import privilege_manager

feature_config = ConfigManager("json/fea_list.json", default_key="fea_list")
fea_list = feature_config.all()

# 权限级别：0=禁用，1=仅管理员可用，2=全员可用
PERM_DISABLED = 0
PERM_ADMIN = 1
PERM_ALL = 2
LEVEL_TEXT = {0: "禁用", 1: "仅管理员可用", 2: "全员可用"}

# 不参与三级权限管理的功能（硬编码超管专属 或 依附主功能的子开关），仅能用 enable/disable 二元控制
NO_PERM_FEATURES = {"cmd", "websearch", "pixiv-r18", "fake_headpic", "fakeclaw"}

# 迁移到三级权限时，这些功能的默认级别为“仅管理员”（与历史代码中的硬编码门控保持一致）
DEFAULT_ADMIN_FEATURES = {"echocq", "webss", "web_agent"}

# 内置功能种子：存量数据中缺失时自动补注册（幂等），默认仅管理员可用
FEATURE_SEED = {
    "broadcast": {"desc": "广播消息至bot所在所有群聊", "perm": PERM_ADMIN},
}

def _ensure_seed():
    """补注册内置但 fea_list 中尚不存在的功能。"""
    changed = False
    for name, seed in FEATURE_SEED.items():
        if name not in fea_list:
            fea_list[name] = {
                "desc": seed["desc"],
                "enable": seed["perm"] > PERM_DISABLED,
                "perm": seed["perm"],
            }
            changed = True
    if changed:
        feature_config.update(fea_list)

_ensure_seed()

def _migrate():
    """为旧版仅含 enable 的条目补充 perm 字段（幂等）。"""
    changed = False
    for name, info in fea_list.items():
        if "perm" not in info:
            if name in NO_PERM_FEATURES:
                continue
            if not info.get("enable", False):
                info["perm"] = PERM_DISABLED
            elif name in DEFAULT_ADMIN_FEATURES:
                info["perm"] = PERM_ADMIN
            else:
                info["perm"] = PERM_ALL
            changed = True
    if changed:
        feature_config.update(fea_list)

_migrate()

def get_all_features():
    resp = ""
    for i in fea_list:
        resp += i+"（"+fea_list[i]["desc"]+"）"
        if is_on(i):
            resp += "[已启用✅]\n"
        else:
            resp += "[已禁用❌]\n"
    return resp

def get(fea_name):
    """功能是否开启（布尔）。供无用户上下文的内部调用与不支持三级权限的子开关使用。"""
    info = fea_list[fea_name]
    if "perm" in info:
        return info["perm"] > PERM_DISABLED
    return bool(info.get("enable", False))

def is_on(fea_name):
    """同 get()，语义化别名：功能未被禁用（perm 为 1 或 2）。供管理员级命令判断使用。"""
    return get(fea_name)

def get_perm(fea_name):
    """返回三级权限级别；不支持三级权限的功能返回 None。"""
    info = fea_list.get(fea_name)
    if info is None or "perm" not in info:
        return None
    return info["perm"]

def can_use(fea_name, uid):
    """按当前功能权限级别判断用户是否可用：2=全员，1=管理员及以上，0=禁用。"""
    info = fea_list.get(fea_name)
    if info is None:
        return False
    if "perm" not in info:
        return bool(info.get("enable", False))
    level = info["perm"]
    if level == PERM_ALL:
        return True
    if level == PERM_ADMIN:
        return privilege_manager.checkuser(str(uid)) >= 1
    return False

def set_perm(fea_name, level):
    """设置三级权限，同时同步 enable 镜像字段。"""
    fea_list[fea_name]["perm"] = level
    fea_list[fea_name]["enable"] = level > PERM_DISABLED
    feature_config.update(fea_list)
    return "已将「"+fea_list[fea_name]["desc"]+"」的权限设为："+LEVEL_TEXT[level]+"。"

def enable(fea_name):
    # 支持三级权限的功能：启用=全员可用；其余功能：仅置 enable=True
    if "perm" in fea_list[fea_name]:
        return set_perm(fea_name, PERM_ALL)
    fea_list[fea_name]["enable"] = True
    feature_config.update(fea_list)
    return "已启用功能："+fea_name+"（"+fea_list[fea_name]["desc"]+"）"

def disable(fea_name):
    if "perm" in fea_list[fea_name]:
        return set_perm(fea_name, PERM_DISABLED)
    fea_list[fea_name]["enable"] = False
    feature_config.update(fea_list)
    return "已禁用功能："+fea_name+"（"+fea_list[fea_name]["desc"]+"）"

def import_fea_list(lis):
    global fea_list
    # 仅接受 JSON 格式，禁止执行任意代码
    try:
        parsed = json.loads(lis)
    except (json.JSONDecodeError, TypeError, ValueError):
        return "请提供有效的功能列表！"
    if not isinstance(parsed, dict):
        return "请提供有效的功能列表！"
    # 先完整校验（键必须存在、值必须为布尔/整数），再应用变更
    for key, value in parsed.items():
        if key not in fea_list or not isinstance(value, (bool, int)):
            return "请提供有效的功能列表！"
    for key, value in parsed.items():
        on = bool(value)
        if "perm" in fea_list[key]:
            # 预设导入：1=全员可用，0=禁用
            fea_list[key]["perm"] = PERM_ALL if on else PERM_DISABLED
        fea_list[key]["enable"] = on
    feature_config.update(fea_list)
    return "导入功能列表成功！"
