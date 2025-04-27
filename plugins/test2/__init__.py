from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message
from nonebot.exception import FinishedException
import feature_manager
import web
import webss

web.content_init()

"""
cwc = on_command("cwc", aliases={"更改网页内容"}, priority=10, block=True)
@cwc.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("webss"):
        raise FinishedException
    else:
        # await cwc.finish(f"{args.extract_plain_text()}，我给你踩背来咯！")
        web.change_content(args.extract_plain_text())
        raise FinishedException
"""
    
rendermd = on_command("rendermd", aliases={"md渲染","mdrender"}, priority=10, block=True)
@rendermd.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("rendermd"):
        raise FinishedException
    else:
        # await test2.finish(f"{args.extract_plain_text()}，我给你踩背来咯！")
        web.content_md(args.extract_plain_text())
        webss.take2("http://localhost:8104","container")
        await rendermd.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/webss/1.png]'))