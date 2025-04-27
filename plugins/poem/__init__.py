from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg
from nonebot.exception import FinishedException
import feature_manager
import asyncio

poem = on_command("poem", aliases={"诗朗诵","吟诗","recite"}, priority=10, block=True)
@poem.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("poem"):
        raise FinishedException
    ar = args.extract_plain_text().split()
    if len(ar) > 0 and ar[0] == '听我说':
        if len(ar) > 2:
            await poem.send(ar[1]+"你听我说")
            await asyncio.sleep(2)
            await poem.send("今天我来说说你")
            await asyncio.sleep(2)
            await poem.send("这个"+ar[2]+"是你制作的")
            await asyncio.sleep(2)
            await poem.finish("求求你把"+ar[2]+"关闭")
        else:
            await poem.finish("参数不够。用法：/poem 听我说 [关键词1] [关键词2]")
    if len(ar) > 0 and (ar[0] == '我要吃' or ar[0] == '贪吃小哥'):
        if len(ar) > 3:
            await poem.send("我要吃"+ar[1])
            await asyncio.sleep(.6)
            await poem.send("要吃"+ar[2])
            await asyncio.sleep(.6)
            await poem.send("要吃"+ar[3])
            await asyncio.sleep(1)
            await poem.send("就问你给不给我买")
            await asyncio.sleep(1)
            await poem.finish("你给不给我买")
        else:
            await poem.finish("参数不够。用法：/poem 我要吃 [关键词1] [关键词2] [关键词3]")
    if len(ar) > 0 and (ar[0] == '天雷' or ar[0] == '天雷滚滚'):
        if len(ar) > 4:
            await poem.send("天雷滚滚我"+ar[1])
            await asyncio.sleep(2)
            await poem.send("劈得我浑身"+ar[2])
            await asyncio.sleep(2)
            await poem.send("突破天劫我"+ar[3])
            await asyncio.sleep(2)
            await poem.finish("逆天改命我"+ar[4])
        else:
            await poem.finish("参数不够。用法：/poem 天雷滚滚 [关键词1] [关键词2] [关键词3] [关键词4]")
    else:
        await poem.finish("参数错误。用法：/poem [格式名称] [关键词]。可用的格式有：听我说、我要吃、天雷滚滚")