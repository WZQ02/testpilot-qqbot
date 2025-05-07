from nonebot import on_command
from nonebot import on_keyword
from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message
import random
import asyncio
import httpx
from nonebot.exception import FinishedException
import feature_manager
import img_process

ping = on_command("ping", rule=to_me(), aliases={"喂","你好","hello","test","嗨"}, priority=10, block=True)
@ping.handle()
async def handle_function():
    if not feature_manager.get("ping"):
        raise FinishedException
    await ping.finish("嗨！")

mzsm = on_command("mzsm", aliases={"免责声明"}, priority=10, block=True)
@mzsm.handle()
async def handle_function():
    if not feature_manager.get("ping"):
        raise FinishedException
    await mzsm.finish("免责声明：本 bot 发表的所有言论均只代表我自己的意见，不代表 bot 作者的个人立场，望周知。")

ccb = on_command("ccb", aliases={"踩背","cb"}, priority=10, block=True)
@ccb.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("ccb"):
        raise FinishedException
    if args[0].type == 'image':
        img_process.download_img(args[0].data['url'],"images/img_ccb/temp/bcb.jpg")
        img_process.gen_ccb_img()
        await ccb.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/images/img_ccb/temp/result.png]'))
    else:
        await ccb.finish(f"{args.extract_plain_text()}，我给你踩背来咯！")

echo = on_command("echo", aliases={"复读"}, priority=10, block=True)
@echo.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("echo"):
        raise FinishedException
    await echo.finish(args)

yes = on_command("是", aliases={"yes"}, priority=10, block=True)
@yes.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = random.random()
    if rd < .5:
        await yes.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/images/xg_yes.png,sub_type=1]'))
    else:
        await yes.finish("是")

yes = on_command("不是", aliases={"no","否"}, priority=10, block=True)
@yes.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = random.random()
    if rd < .5:
        await yes.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/images/xg_no.png,sub_type=1]'))
    else:
        await yes.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/images/xg_no2.png,sub_type=1]'))

setu = on_keyword(["setu","色图","黄图","涩图","好涩","好色","🐍","打飞机","撸管","操逼","屄","操大逼","槽壁","草比"], priority=10, block=True)
@setu.handle()
async def handle_function():
    if not feature_manager.get("meme_resp_sex"):
        raise FinishedException
    rd = random.random()
    if rd < .5:
        await setu.finish("哈比下，我看到自己的兄弟，有时很ruan有时很应")
    else:
        await setu.finish("ccb")

mtf = on_keyword(["男娘","南梁","香香软软"], priority=10, block=True)
@mtf.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = random.random()
    if rd < .5:
        await mtf.finish("好香")
    else:
        await mtf.finish("嗯！香香软软的")

awmc = on_keyword(["maimai","打mai","舞萌","乌蒙","大力拍打或滑动","滴蜡熊","迪拉熊","拉兹","纱露朵","新的旅行伙伴","101.0000%"], priority=10, block=True)
@awmc.handle()
async def handle_function():
    if not feature_manager.get("meme_resp_mai"):
        raise FinishedException
    rd = random.random()
    if rd < .1:
        await awmc.finish("wmc！？")
    else:
        await awmc.finish("awmc")

mygo = on_keyword(["mygo","MyGO","春日影","crychic","Crychic","组一辈子乐队","你这个人，真是满脑子都","素世","长期素食","要乐奈","丰川祥子","椎名立希","千早爱音","为什么要演奏","高松灯"], priority=10, block=True)
@mygo.handle()
async def handle_function():
    if not feature_manager.get("meme_resp_mygo"):
        raise FinishedException
    await mygo.finish("还在go还在go")

choslif = on_keyword(["牯岭街","袁正","choose life","虚无主义","犬儒"], priority=10, block=True)
@choslif.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = random.random()
    if rd < .8:
        await choslif.finish("choose life？！")
    else:
        await choslif.finish("我选择不去choose life。我选择别的。至于理由呢？没什么理由。因为我是人机啊哈哈哈哈哈哈哈哈哈哈哈哈哈！！！！！！！")

yrhy = on_keyword(["犹如幻翳","教你看电影","机械唯物"], priority=10, block=True)
@yrhy.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    await yrhy.finish("在在在在在在在在在在在在")

zlkj = on_keyword(["粘连","网络油饼","网络油侠"], priority=10, block=True)
@zlkj.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    await zlkj.finish("😭😭😭😭😭😭😭😭😭😭")

aywdm = on_keyword(["哎呦我滴妈","哈基米","胖宝宝"], priority=10, block=True)
@aywdm.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = random.random()
    if rd < .5:
        await aywdm.finish("哎呦我滴妈哈哈哈哈哈哈")
    else:
        await aywdm.finish("叮咚鸡！叮咚鸡！胖宝宝！胖宝宝！哈基米！哈基米！")

sjdsw = on_keyword(["识人术","食人树"], priority=10, block=True)
@sjdsw.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    await asyncio.sleep(.5)
    await sjdsw.send("社交的手腕")
    await asyncio.sleep(1)
    await sjdsw.send("暗黑心理学")
    await asyncio.sleep(1)
    await sjdsw.finish("人性的秘密")

laicai = on_keyword(["来财"], priority=10, block=True)
@laicai.handle()
async def handle_function():
    if not feature_manager.get("meme_resp_laicai"):
        raise FinishedException
    await asyncio.sleep(.5)
    await laicai.send("来财")
    await asyncio.sleep(.5)
    await laicai.send("来财")
    await asyncio.sleep(.5)
    await laicai.send("来财")
    await asyncio.sleep(.5)
    await laicai.finish("来")

whosbot = on_keyword(["谁的bot","谁写的"], rule=to_me(), priority=10, block=True)
@whosbot.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    await whosbot.finish("妈妈生的")

yyz = on_keyword(["快乐","开心"], priority=10, block=True)
@yyz.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = random.random()
    if rd > 0.9:
        await yyz.finish(Message('[CQ:video,file=file:///W:/soft/web_svr/testpilot_qqbot/video/wyyyz/1.mp4]'))
    elif rd > 0.8:
        await yyz.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/images/wyyyz/1.webp,sub_type=1]'))
    elif rd > 0.7:
        await yyz.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/images/wyyyz/2.webp,sub_type=1]'))
    elif rd > 0.67:
        await yyz.finish("救我。")
    elif rd > 0.64:
        await yyz.finish("我好痛苦。")
    else:
        raise FinishedException

"""
test = on_message(priority=10, block=True)
@test.handle()
async def handle_function(args: Message = EventMessage()):
    for i in args:
        # if i.type == 'at':
            # print("用户"+i.data['qq']+"被at了，他的qq号是"+i.data['name'])
        print([i.type,i.data])
"""

help = on_command("help", rule=to_me(), aliases={"帮助"}, priority=10, block=True)
@help.handle()
async def handle_function():
    if not feature_manager.get("help"):
        if not feature_manager.get("actualhelp"):
            raise FinishedException
        else:
            await help.finish("请输入 /actualhelp 指令获取帮助哦！")
    rd = random.random()
    msg = ""
    if rd < .33:
        msg = "靠天靠地靠父母，不如靠自己！"
    elif rd < .66:
        msg = "你已经没救了，贫僧帮不了你了。"
    else:
        msg = "求人难，求己易，自立更生最实际。"
    await help.finish(msg)

"""
fds = on_command("deepseek", priority=10, block=True)
@fds.handle()
async def handle_function():
    if not feature_manager.get("fakedeepseek"):
        raise FinishedException
    await asyncio.sleep(3)
    await fds.finish("服务器繁忙，请稍后再试。")
"""

flipof = on_keyword(["你是","机器人","人机","谁啊","没素质","傻逼","sb","妈","赤石","谁家","杂鱼","低能","吃屎","弱智","操","草你","滚","去死","一边去"], rule=to_me(), priority=10, block=True)
@flipof.handle()
async def handle_function():
    if not feature_manager.get("flipoff"):
        raise FinishedException
    # await flipof.finish(MessageSegment.image(await get_image_data("https://img.wzq02.top/upl/1c3c2250c945fc7430c0d3a02ff3174e.jpg")))
    # await flipof.finish(Message('[CQ:at,qq=2975499623,name=test]'))
    await flipof.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/images/gbc_flip_off.webp,sub_type=1]'))

flipof2 = on_command("flipoff", aliases={"竖中指","比中指"}, priority=10, block=True)
@flipof2.handle()
async def handle_function():
    if not feature_manager.get("flipoff"):
        raise FinishedException
    await flipof2.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/images/gbc_flip_off.webp,sub_type=1]'))

flipof2 = on_keyword(["滴泪","地雷女","宝宝"], rule=to_me(), priority=10, block=True)
@flipof2.handle()
async def handle_function():
    if not feature_manager.get("flipoff"):
        raise FinishedException
    rd = random.random()
    if rd < .2:
        await flipof2.finish('捅死你！捅死你！捅死你！捅死你！捅死你！捅死你！')
    else:
        await flipof2.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/images/raincandy/cantflip.png]'))

async def get_image_data(url):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.text.strip()
    return data