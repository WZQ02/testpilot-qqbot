from nonebot import on_command
from nonebot import on_keyword
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Message
import random
import math
from nonebot.exception import FinishedException
import feature_manager
import path_manager

miku = on_command("随机miku", aliases={"随机miratsu","miratsu","miku"}, priority=10, block=True)
@miku.handle()
async def handle_function():
    if not feature_manager.get("rand_pic"):
        raise FinishedException
    rd = math.ceil(random.random()*21)
    sfx = ""
    if rd <= 7:
        sfx = ".gif"
    else:
        sfx = ".jpg"
    await miku.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/miku_miratsu/'+str(rd)+sfx+',sub_type=1,summary=&#91;miku&#93;]'))

thwy = on_command("随机fio", aliases={"fio","thwy","璐璐"}, priority=10, block=True)
@thwy.handle()
async def handle_function():
    if not feature_manager.get("rand_pic"):
        raise FinishedException
    rd = str(math.ceil(random.random()*10))
    await thwy.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/fio/'+rd+'.jpg,sub_type=1,summary=&#91;fio&#93;]'))

mieru = on_command("随机美瑠", aliases={"随机mieru","mieru","loulou","楼楼"}, priority=10, block=True)
@mieru.handle()
async def handle_function():
    if not feature_manager.get("rand_pic"):
        raise FinishedException
    rd = str(math.ceil(random.random()*15))
    await mieru.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/mieru/'+rd+'.jpg,sub_type=1,summary=&#91;美瑠&#93;]'))

bocchi = on_command("随机bocchi", aliases={"bocchi","随机波奇","波奇","孤独摇滚","ぼっち"}, priority=10, block=True)
@bocchi.handle()
async def handle_function():
    if not feature_manager.get("rand_pic"):
        raise FinishedException
    rd = str(math.ceil(random.random()*15))
    await bocchi.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/bocchi/'+rd+'.gif,sub_type=1,summary=&#91;波奇酱&#93;]'))

karen = on_command("随机可怜", aliases={"karen","九条可怜","随机金发"}, priority=10, block=True)
@karen.handle()
async def handle_function():
    if not feature_manager.get("rand_pic"):
        raise FinishedException
    rd = str(math.ceil(random.random()*20))
    await karen.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/karen/'+rd+'.jpg,sub_type=1,summary=&#91;可怜&#93;]'))

wxhn = on_keyword(["我喜欢你","我爱你"], rule=to_me(), priority=10, block=True)
@wxhn.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = math.ceil(random.random()*7)
    path = "file:///"+path_manager.bf_path()+"images/wxhn/"
    if 2 <= rd <= 4:
        await wxhn.finish(Message('[CQ:image,file='+path+str(rd)+'.jpg,sub_type=1]'))
    else:
        await wxhn.finish(Message('[CQ:image,file='+path+str(rd)+'.gif,sub_type=1]'))