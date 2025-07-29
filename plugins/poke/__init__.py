from nonebot import on_command
from nonebot import get_bot
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import feature_manager
import asyncio
import random

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
        # times超过10次减为10
        if (times > 10):
            times = 10
        for i in range(times):
            sltim = pow(random.random(),3)*5
            await asyncio.sleep(sltim)
            await bot.group_poke(group_id=groupid, user_id=qqnum)
    else:
        raise FinishedException