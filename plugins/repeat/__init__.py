from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.params import CommandArg
from nonebot.exception import FinishedException
import feature_manager
import msg_cache
import asyncio
import random

from nonebot_plugin_saa import MessageFactory, TargetQQGroup
from nonebot_plugin_saa import enable_auto_select_bot
enable_auto_select_bot()

rep = on_command("repeat", aliases={"重复","复读上一句"}, priority=10, block=True)
@rep.handle()
async def handle_function(event: Event):
    if not feature_manager.get("repeat"):
        raise FinishedException
    else:
        sid = event.get_session_id().split("_")
        if sid[0] == 'group':
            groupid = sid[1]
            # await rep.finish(Message(msglis[groupid]))
            await rep.finish(Message(msg_cache.get_cached_msg(groupid,0)))
        else:
            raise FinishedException

# 存储每个群聊的最后一条消息（/repeat 除外）
rep_record = on_message(priority=10, block=True)
@rep_record.handle()
async def handle_function(event: Event):
    sid = event.get_session_id().split("_")
    if sid[0] == 'group':
        groupid = sid[1]
        msg = event.get_message()
        if "/repeat" not in msg.extract_plain_text() and "/复读上一句" not in msg.extract_plain_text() and "/重复" not in msg.extract_plain_text():
            # msglis[groupid] = msg
            msg_cache.cache_msg(groupid,msg)
        # 如果最近三条消息重复，则复读
        if feature_manager.get("autorepeat") and check_3rep(groupid):
            await asyncio.sleep(2+random.randint(0,5))
            if check_3rep(groupid):
                await rep_record.send(msg_cache.get_cached_msg(groupid,0))
                # 触发复读后，删去前两条重复的消息
                msg_cache.rem_cached_msg(groupid,1)
                # 重复一次（删去一条后列表顺序变更）
                msg_cache.rem_cached_msg(groupid,1)
        """
        # 如果有人在非抓小哥群发送kz / zhua / 狂抓
        if (msg.extract_plain_text() == "kz" or msg.extract_plain_text() == "zhua" or msg.extract_plain_text() == "狂抓") and (groupid != '982438201' and groupid != '913376542'):
            await kz_transfer(msg,groupid)
        # 在有人触发以上条件后，转发小镜bot的回复到原群聊
        global kztransfer_label
        if (kztransfer_label != 0 and groupid == '913376542' and sid[2] == '3687050325'):
            await Message(msg).send_to(TargetQQGroup(group_id=int(kztransfer_label)))
            kztransfer_label = 0
        """
    raise FinishedException

def check_3rep(groupid):
    if msg_cache.get_cached_msg_count(groupid) >= 3:
        if msg_cache.get_cached_msg(groupid,0) == msg_cache.get_cached_msg(groupid,1) == msg_cache.get_cached_msg(groupid,2):
            return True
        else:
            return False
    else:
        return False

"""
kztransfer_label = 0

async def kz_transfer(msg,groupid):
    await Message(msg).send_to(TargetQQGroup(group_id=913376542))
    global kztransfer_label
    kztransfer_label = groupid
"""