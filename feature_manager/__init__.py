import json
from config_manager import ConfigManager

feature_config = ConfigManager("json/fea_list.json", default_key="fea_list")
fea_list = feature_config.all()

def get_all_features():
    resp = ""
    for i in fea_list:
        resp += i+"（"+fea_list[i]["desc"]+"）"
        if fea_list[i]["enable"]:
            resp += "[已启用✅]\n"
        else:
            resp += "[已禁用❌]\n"
    return resp

def get(fea_name):
    return fea_list[fea_name]["enable"]

def enable(fea_name):
    fea_list[fea_name]["enable"] = True
    feature_config.update(fea_list)
    return "已启用功能："+fea_name+"（"+fea_list[fea_name]["desc"]+"）"

def disable(fea_name):
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
        fea_list[key]["enable"] = bool(value)
    feature_config.update(fea_list)
    return "导入功能列表成功！"