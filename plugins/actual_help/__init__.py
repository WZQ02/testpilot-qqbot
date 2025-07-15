from nonebot import on_command
from nonebot.rule import to_me
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import Event
import feature_manager

help = on_command("actualhelp", rule=to_me(), aliases={"actual_help","真正的帮助","实际的帮助","真实的帮助"}, priority=10, block=True)
@help.handle()
async def handle_function():
    if not feature_manager.get("actualhelp"):
        raise FinishedException
    helptext = "https://testpilot.wzq02.top/guide/"
    await help.finish(helptext)

wzs = on_command("wzq", aliases={"wzs","小站导航","网站导航"}, priority=10, block=True)
@wzs.handle()
async def handle_function():
    if not feature_manager.get("wzs"):
        raise FinishedException
    await wzs.finish("https://wzq02.top/ WZQ'02 的小站\nhttps://s.wzq02.top/1drive WZQ'02 的网盘\nhttps://s.wzq02.top/ask WZQ'02 的提问箱\nhttps://wzq02.top/otomader-sites/ 音 MADer 网站收集\nhttps://testpilot.wzq02.top/ Bot 介绍页")