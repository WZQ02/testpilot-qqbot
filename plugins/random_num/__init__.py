from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Event
import random
from nonebot.exception import FinishedException
import feature_manager

randn = on_command("随机数字", aliases={"random"}, priority=10, block=True)
@randn.handle()
async def handle_function(args: Message = CommandArg(), event: Event = Event):
    if not feature_manager.can_use("rand_num", event.get_user_id()):
        raise FinishedException
    ag = args.extract_plain_text()
    rd = random.randint(100,1000)
    if str.isdigit(ag) and int(ag) >= 1 and int(ag) <= 64:
        ag = int(ag)
        rd = random.randint(pow(10,ag-1),pow(10,ag))
    await randn.finish(str(rd))