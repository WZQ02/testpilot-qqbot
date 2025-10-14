from nonebot import on_command
from nonebot import get_bot
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import privilege_manager
import feature_manager
import random
import achievement_manager
import json

# 获取特殊qq号列表
specd = open("json/spec_qq_list.json","r",encoding="utf-8")
spec_list = json.loads(specd.read())

# 获取群员列表
"""
getmbl = on_command("gmbl", priority=10, block=True)
@getmbl.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) == 2:
        bot = get_bot()
        group_id = event.get_session_id().split("_")[1]
        print(await bot.get_group_member_list(group_id=group_id))
    raise FinishedException
"""
bot_qq_id = 3978644480
lvstr_list = ["我喜欢你","爱你喵","我爱你","贴贴","！suki！拉布！嗨嗨！","你是一个小蛋糕","亲","宝宝","宝贝","宝宝你是一个甜甜糯糯的小蛋糕"]

randomcs = on_command("rdcs", aliases={"随机赤石","suiji","随机吃屎","随机扔粑粑"}, priority=10, block=True)
@randomcs.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("randomcs"):
        bot = get_bot()
        group_id = event.get_session_id().split("_")[1]
        if int(group_id) in spec_list["randomcs_whitelist_groups"]:
            mbl = await bot.get_group_member_list(group_id=group_id)
            mbllen = len(mbl)
            rd = random.randint(0,mbllen-1)
            chqq = str(mbl[rd]['user_id'])
            if int(chqq) == bot_qq_id:
                await achievement_manager.add(6,event)
            # event.get_user_id()获取到的是str而不是int
            if chqq == event.get_user_id():
                await achievement_manager.add(11,event)
            await randomcs.finish(Message("[CQ:at,qq="+chqq+"] 赤石"))
        else:
            await randomcs.finish("请在“抓小哥”相关群聊使用这个命令哦！")
    else:
        raise FinishedException
    
randombb = on_command("rdbb", aliases={"随机表白"}, priority=10, block=True)
@randombb.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("randomcs"):
        bot = get_bot()
        group_id = event.get_session_id().split("_")[1]
        mbl = await bot.get_group_member_list(group_id=group_id)
        mbllen = len(mbl)
        rd = random.randint(0,mbllen-1)
        lvstr = lvstr_list[random.randint(0,9)]
        chqq = str(mbl[rd]['user_id'])
        if int(chqq) == bot_qq_id:
            await achievement_manager.add(6,event)
        if chqq == event.get_user_id():
            await achievement_manager.add(11,event)
        await randombb.finish(Message("[CQ:at,qq="+chqq+"] "+lvstr))
    else:
        raise FinishedException

"""
randombb = on_command("rdcp", aliases={"随机凑CP","随机结婚证"}, priority=10, block=True)
@randombb.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("randomcs"):
        bot = get_bot()
        group_id = event.get_session_id().split("_")[1]
        mbl = await bot.get_group_member_list(group_id=group_id)
        mbllen = len(mbl)
        rd1 = random.randint(0,mbllen-1)
        rd2 = random.randint(0,mbllen-1)
        await randombb.finish(Message("[CQ:at,qq="+str(mbl[rd1]['user_id'])+"] 结[CQ:at,qq="+str(mbl[rd2]['user_id'])+"]"))
    else:
        raise FinishedException
"""