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
    lis = eval(lis)
    if isinstance(lis,dict):
        fl_copy = fea_list
        for key, value in lis.items():
            fl_copy[key]["enable"] = value and True or False
        if len(fl_copy) == len(fea_list):
            fea_list = fl_copy
            feature_config.update(fea_list)
            return "导入功能列表成功！"
        else:
            return "请提供有效的功能列表！"
    else:
        return "请提供有效的功能列表！"