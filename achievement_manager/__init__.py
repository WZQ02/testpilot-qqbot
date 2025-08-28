import json
import feature_manager

from nonebot_plugin_saa import MessageFactory, TargetQQGroup, Text, Mention
from nonebot_plugin_saa import enable_auto_select_bot
enable_auto_select_bot()

ach_file = open("json/achievement.json","r",encoding="utf-8")
ach_list_raw = ach_file.read()
ach_file.close()
ach_list = json.loads(ach_list_raw)['achievements']
user_list = json.loads(ach_list_raw)['users']

async def add(acid,event):
    qqid = str(event.get_user_id())
    groupid = str(event.get_session_id().split("_")[1])
    await do_add(acid,qqid,groupid)

async def add2(acid,qqid,groupid):
    qqid = str(qqid)
    groupid = str(groupid)
    await do_add(acid,qqid,groupid)

async def do_add(acid,qqid,groupid):
    acid = str(acid)
    if qqid in user_list:
        if acid in user_list[qqid]:
            return
        else:
            user_list[qqid].append(acid)
    else:
        user_list[qqid] = [acid]
    writeback()
    # 发送消息
    if feature_manager.get("achievement_display"):
        target = TargetQQGroup(group_id=int(groupid))
        ach_desc = ach_list[acid]["desc"]
        if ach_desc != "":
            ach_desc += "\n"
        await MessageFactory([Mention(qqid),Text("\n获得成就："+ach_list[acid]["name"]+"\n"+ach_desc+"条件："+ach_list[acid]["cond"])]).send_to(target=target)

async def list(event):
    qqid = str(event.get_user_id())
    groupid = str(event.get_session_id().split("_")[1])
    res = "\n"
    if qqid in user_list and len(user_list[qqid]) > 0:
        ac_list = user_list[qqid]
        res += "你获得的成就有："
        for i in ac_list:
            res += "\n"+ach_list[i]["name"]
    else:
        res += "你还没有取得任何成就！"
    target = TargetQQGroup(group_id=int(groupid))
    await MessageFactory([Mention(qqid),Text(res)]).send_to(target=target)

def writeback():
    file = open("json/achievement.json","w",encoding="utf-8")
    json.dump({'achievements':ach_list,'users':user_list},file,ensure_ascii=False,sort_keys=True)