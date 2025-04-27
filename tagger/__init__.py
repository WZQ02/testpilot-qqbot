import json

tl_file = open("json/tag_list.json","r",encoding="utf-8")
tag_list_raw = tl_file.read()
tl_file.close()
tag_list = json.loads(tag_list_raw)['tag_list']

def add_tag(qqid,tagname):
    if qqid in tag_list:
        lis = tag_list[qqid]
        if tagname in lis:
            return "此标签已被添加！"
        else:
            lis.append(tagname)
    else:
        tag_list[qqid] = []
        tag_list[qqid].append(tagname)
    writeback()
    return "已为"+qqid+"添加标签："+tagname

def rem_tag(qqid,tagname):
    if qqid in tag_list:
        lis = tag_list[qqid]
        if tagname in lis:
            lis.remove(tagname)
        else:
            return "还没有为"+qqid+"添加这个标签哦！"
    else:
        return qqid+"没有标签！"
    writeback()
    return "已为"+qqid+"删除标签："+tagname

def que_tag(qqid):
    if (qqid in tag_list) and (tag_list[qqid] != []):
        msg = qqid+"的标签有："
        for i in tag_list[qqid]:
            msg += i+" "
        return msg
    else:
        return qqid+"没有标签！"

def writeback():
    file = open("json/tag_list.json","w",encoding="utf-8")
    json.dump({'tag_list':tag_list},file,ensure_ascii=False,sort_keys=True)

# for nm_list.json

nm_file = open("json/nm_list.json","r",encoding="utf-8")
nm_list_raw = nm_file.read()
nm_file.close()
nm_list = json.loads(nm_list_raw)['nm_list']

def verify_nm(qqid,name):
    if qqid in nm_list and name == nm_list[qqid]:
        return 0
    else:
        nm_list[qqid] = name
        writeback2()
        return 1
    
def get_nm(qqid):
    if qqid in nm_list:
        return nm_list[qqid]
    else:
        return ""
    
def writeback2():
    file = open("json/nm_list.json","w",encoding="utf-8")
    json.dump({'nm_list':nm_list},file,ensure_ascii=False,sort_keys=True)