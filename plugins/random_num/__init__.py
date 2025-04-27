from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters import Message
import random
from nonebot.exception import FinishedException
import feature_manager

randn = on_command("随机数字", aliases={"random"}, priority=10, block=True)
@randn.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("rand_num"):
        raise FinishedException
    ag = args.extract_plain_text()
    rd = random.randint(100,1000)
    if str.isdigit(ag) and int(ag) >= 1 and int(ag) <= 64:
        ag = int(ag)
        rd = random.randint(pow(10,ag-1),pow(10,ag))
    await randn.finish(str(rd))