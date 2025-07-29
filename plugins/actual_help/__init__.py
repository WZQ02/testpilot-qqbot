from nonebot import on_command
from nonebot.rule import to_me
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import Event
import feature_manager
import random

helptext = "https://testpilot.wzq02.top/guide/"
wztext = "https://wzq02.top/ WZQ'02 的小站\nhttps://s.wzq02.top/1drive WZQ'02 的网盘\nhttps://s.wzq02.top/ask WZQ'02 的提问箱\nhttps://wzq02.top/otomader-sites/ 音 MADer 网站收集\nhttps://testpilot.wzq02.top/ Bot 介绍页"

ahelp = on_command("actualhelp", aliases={"actual_help","真正的帮助","实际的帮助","真实的帮助"}, priority=10, block=True)
@ahelp.handle()
async def handle_function():
    if not feature_manager.get("actualhelp"):
        raise FinishedException
    await ahelp.finish(helptext)

wzs = on_command("wzq", aliases={"wzs","小站导航","网站导航"}, priority=10, block=True)
@wzs.handle()
async def handle_function():
    if not feature_manager.get("wzs"):
        raise FinishedException
    await wzs.finish(wztext)

help = on_command("help", aliases={"帮助"}, priority=10, block=True)
@help.handle()
async def handle_function():
    if not feature_manager.get("help"):
        if not feature_manager.get("actualhelp"):
            raise FinishedException
        else:
            # await help.finish("请输入 /actualhelp 指令获取帮助哦！")
            await help.finish(helptext)
    rd = random.random()
    msg = ""
    if rd < .33:
        msg = "靠天靠地靠父母，不如靠自己！"
    elif rd < .66:
        msg = "你已经没救了，贫僧帮不了你了。"
    else:
        msg = "求人难，求己易，自立更生最实际。"
    await help.finish(msg)