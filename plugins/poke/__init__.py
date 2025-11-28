from nonebot import on_command
from nonebot import get_bot
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import feature_manager
import asyncio
import random
import privilege_manager

bot_qq_id = 3978644480

poke = on_command("poke", aliases={"戳","戳一戳"}, priority=10, block=True)
@poke.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("poke"):
        bot = get_bot()
        qqnum = 0
        times = 1
        # 发起指令所在群聊
        groupid = event.get_session_id().split("_")[1]
        splitex = args.extract_plain_text().split()
        # 第一个参数是@群员
        if len(args) > 0 and args[0].type == 'at':
            qqnum = args[0].data['qq']
            # 存在第二个参数，且是数字
            if len(splitex) > 0 and str.isdigit(splitex[0]):
                times = int(splitex[0])
        # 第一个参数是群员QQ号
        elif len(args) > 0 and str.isdigit(splitex[0]):
            qqnum = splitex[0]
            # 存在第二个参数，且是数字
            if len(splitex) > 1 and str.isdigit(splitex[1]):
                times = int(splitex[1])
        else:
            await poke.finish("参数错误。用法：/poke [要戳的@群员或群员QQ号] [次数]")
        if int(qqnum) == bot_qq_id:
            await poke.finish("嘛~人家不想戳自己喵~")
        # 对于非管理员，times超过10次减为10
        if (not privilege_manager.checkuser(event.get_user_id()) and times > 10):
            times = 10
        for i in range(times):
            sltim = pow(random.random(),3)*5
            await asyncio.sleep(sltim)
            await bot.group_poke(group_id=groupid, user_id=qqnum)
    raise FinishedException
    
rdpoke = on_command("rdpoke", aliases={"randompoke","随机戳戳","随机戳一戳"}, priority=10, block=True)
@rdpoke.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("randomcs") and feature_manager.get("poke"):
        bot = get_bot()
        group_id = event.get_session_id().split("_")[1]
        mbl = await bot.get_group_member_list(group_id=group_id)
        mbllen = len(mbl)
        # 存在arg且是数字（解析为次数，每次戳不同的群友）
        times = 1
        splitex = args.extract_plain_text().split()
        if len(splitex) > 0 and str.isdigit(splitex[0]):
            times = int(splitex[0])
        # 对于非管理员，times超过10次减为10
        if (not privilege_manager.checkuser(event.get_user_id()) and times > 10):
            times = 10
        for i in range(times):
            sltim = pow(random.random(),3)*5
            await asyncio.sleep(sltim)
            rd = random.randint(0,mbllen-1)
            chqq = str(mbl[rd]['user_id'])
            await bot.group_poke(group_id=group_id, user_id=chqq)
    raise FinishedException