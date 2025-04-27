import json

fea_file = open("json/fea_list.json","r",encoding="utf-8")
fea_list_raw = fea_file.read()
fea_file.close()
fea_list = json.loads(fea_list_raw)['fea_list']

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
    writeback()
    return "已启用功能："+fea_name+"（"+fea_list[fea_name]["desc"]+"）"

def disable(fea_name):
    fea_list[fea_name]["enable"] = False
    writeback()
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
            writeback()
            return "导入功能列表成功！"
        else:
            return "请提供有效的功能列表！"
    else:
        return "请提供有效的功能列表！"

def writeback():
    file = open("json/fea_list.json","w",encoding="utf-8")
    json.dump({'fea_list':fea_list},file,ensure_ascii=False,sort_keys=True)