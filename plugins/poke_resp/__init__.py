from nonebot import on_notice, on_command
from nonebot.adapters.onebot.v11 import NoticeEvent, PokeNotifyEvent, Message, Event
import random, math, json
from nonebot.exception import FinishedException
import feature_manager
import path_manager
import achievement_manager
import plugins.member_stuff

#specd = open("json/spec_qq_list.json","r",encoding="utf-8")
#plugins.member_stuff.spec_list = json.loads(specd.read())

miscd = open("json/misc.json","r",encoding="utf-8")
misc_data = json.loads(miscd.read())

def writeback():
    file = open("json/misc.json","w",encoding="utf-8")
    json.dump(misc_data,file,ensure_ascii=False,sort_keys=True)

pokeresp = on_notice()
emojiresp = on_notice()

poke_user_history = []

@pokeresp.handle()
async def handle_function(event: NoticeEvent):
    if not feature_manager.get("poke"):
        raise FinishedException
    if isinstance(event, PokeNotifyEvent):
        # print(str(event.get_user_id()))
        if event.target_id == event.self_id:
            # group_id = event.group_id
            # user_id = event.user_id
            rd = math.ceil(random.random()*(13+4*2))
            msg = ""
            if rd <= 10:
                msg = Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/poke/poke_'+str(rd)+'.jpg,sub_type=1]')
            elif 10 < rd < 14: # 11、12、13
                msg = Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/poke/poke_'+str(rd)+'.gif,sub_type=1]')
            elif 13 < rd < 16: # 14、15
                msg = "干嘛！"
            elif 15 < rd < 18:
                msg = "不可以戳我哟！"
            elif 17 < rd < 20:
                msg = "诶呦！"
            elif 19 < rd < 22:
                msg = "喵"
            await poke_user_chk(event)
            await pokeresp.send(msg)
        elif int(event.target_id) == plugins.member_stuff.spec_list["special_users"][1]:
            misc_data["aira_poke_count"] += 1
            writeback()
        raise FinishedException

@emojiresp.handle()
async def handle_function(event: NoticeEvent):
    if event.notice_type == 'group_msg_emoji_like':
        if event.likes and event.likes[0]["emoji_id"] == "38":
            await achievement_manager.add2(15,event.user_id,event.group_id)
    raise FinishedException

# 最近5次poke中，有user触发3次poke，授予该用户“戳你戳你戳戳你”成就
async def poke_user_chk(event):
    id = event.user_id
    poke_user_history.append(id)
    if len(poke_user_history) > 5:
        poke_user_history.remove(poke_user_history[0])
    user_pc = 0
    for i in poke_user_history:
        if i == id:
            user_pc += 1
    if user_pc >= 3:
        await achievement_manager.add(3,event)

a_poke_count = on_command("airapokecount", priority=10, block=True)
@a_poke_count.handle()
async def handle_function(event: Event = Event):
    group_id = event.get_session_id().split("_")[1]
    if int(group_id) == plugins.member_stuff.spec_list["special_groups"][1]:
        await a_poke_count.finish(f"艾拉的白丝被捏了 {misc_data["aira_poke_count"]} 次。")
    else:
        raise FinishedException