from nonebot import on_command
from nonebot import on_keyword
from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageEvent
import random, math
import asyncio
import httpx
from nonebot.exception import FinishedException
import feature_manager
import path_manager
import img_process
import achievement_manager
import plugins.member_stuff

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
async def handle_function(args: Message = CommandArg(),bot: Bot = Bot, event: MessageEvent = Event):
    if not feature_manager.get("ccb"):
        raise FinishedException
    # 优先获取args
    if len(args) > 0:
        if args[0].type == 'image':
            await ccb.finish(await ccb_image(args[0].data['url']))
        else:
            await ccb.finish(f"{args.extract_plain_text()}，我给你踩背来咯！")
    # 获取回复内容
    else:
        rep_con = await get_reply_content(event.original_message,bot)
        if rep_con and rep_con[0]["type"] == 'image':
            await ccb.finish(await ccb_image(rep_con[0]['data']['url']))
    raise FinishedException


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
        await yes.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/xg_yes.png,sub_type=1,summary=是]'))
    else:
        await yes.finish("是")

yes = on_command("不是", aliases={"no","否"}, priority=10, block=True)
@yes.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = random.random()
    if rd < .5:
        await yes.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/xg_no.png,sub_type=1,summary=不是]'))
    else:
        await yes.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/xg_no2.png,sub_type=1,summary=不是]'))

setu = on_keyword(["setu","色图","黄图","涩图","好涩","好色","🐍","打飞机","撸管","操逼","屄","操大逼","槽壁","草比"], priority=10, block=True)
@setu.handle()
async def handle_function():
    if not feature_manager.get("meme_resp_sex"):
        raise FinishedException
    rd = random.random()
    if rd < .5 and plugins.member_stuff.bot_sex == 1:
        await setu.finish("哈比下，我看到自己的兄弟，有时很ruan有时很应")
    elif plugins.member_stuff.bot_sex == 2:
        await setu.finish("不可以涩涩喵")
    else:
        await setu.finish("群友又在涩涩哦")

mtf = on_keyword(["男娘","南梁","香香软软"], priority=10, block=True)
@mtf.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = random.random()
    if rd < .5:
        await mtf.finish("哪里有？")
    else:
        await mtf.finish("嗯！")

awmc = on_keyword(["maimai","打mai","舞萌","乌蒙","大力拍打或滑动","滴蜡熊","迪拉熊","拉兹","纱露朵","新的旅行伙伴","101.0000%"], priority=10, block=True)
@awmc.handle()
async def handle_function():
    if not feature_manager.get("meme_resp_mai"):
        raise FinishedException
    rd = random.random()
    if rd < .1:
        await awmc.finish("wmc！？")
    elif rd < .15:
        await awmc.finish("你们wmc真的是")
    elif rd < .4:
        await awmc.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/awmc.jpg,sub_type=1]'))
    elif rd < .7:
        await awmc.finish("awmc")

mygo = on_keyword(["mygo","MyGO","春日影","crychic","Crychic","组一辈子乐队","你这个人，真是满脑子都","素世","长期素食","要乐奈","丰川祥子","椎名立希","千早爱音","为什么要演奏","高松灯"], priority=10, block=True)
@mygo.handle()
async def handle_function():
    if not feature_manager.get("meme_resp_mygo"):
        raise FinishedException
    await mygo.finish("gop！？")

choslif = on_keyword(["牯岭街","袁正","choose life","虚无主义","犬儒","选择生活"], priority=10, block=True)
@choslif.handle()
async def handle_function(event: Event = Event):
    if ("choose life" in event.get_plaintext()):
        await achievement_manager.add(10,event)
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = random.random()
    if rd < .6:
        await choslif.finish("choose life？！")
    elif rd < .8:
        await choslif.finish("初四来福？！")
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
    await zlkj.finish("😭😭😭😭😭")

aywdm = on_keyword(["哎呦我滴妈","哈基米","胖宝宝"], priority=10, block=True)
@aywdm.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = random.random()
    if plugins.member_stuff.bot_sex == 2:
        await aywdm.finish("喵喵？")
    else:
        if rd < .3:
            await aywdm.finish("哎呦我滴妈哈哈哈哈哈哈")
        elif rd < .6:
            await aywdm.finish("哈基米南北绿豆~")
        else:
            await aywdm.finish("曼波~")

whocallme = on_keyword(["w机","testpilot","wzq人机","wzqbot"], priority=10, block=True)
@whocallme.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = random.random()
    if rd < .6:
        await whocallme.finish("谁在叫我？")
    elif plugins.member_stuff.bot_sex == 2:
        await whocallme.finish("喵")
    else:
        await whocallme.finish("在")

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
    await laicai.send("来")
    rd = random.random()
    if rd < .1:
        await laicai.finish("你不给点表示吗？")
    else:
        raise FinishedException

whosbot = on_keyword(["谁的bot","谁写的"], rule=to_me(), priority=10, block=True)
@whosbot.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    await whosbot.finish("妈妈生的")

jiahao = on_keyword(["嘉豪","佳豪","alan walker","艾伦沃克","faded","走路人"], priority=10, block=True)
@jiahao.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    await jiahao.finish("哎呦我去艾露迪克")

yyz = on_keyword(["快乐","开心"], priority=10, block=True)
@yyz.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    rd = random.random()
    if rd > 0.8:
        await yyz.finish("qwq")
    elif rd > 0.6:
        await yyz.finish("呜呜")
    else:
        raise FinishedException

haosharen1 = on_keyword(["你这人就好杀人"], priority=10, block=True)
@haosharen1.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    await haosharen1.finish("对！")

haosharen2 = on_keyword(["就说不听你话就全杀呗","就说不听你话全杀"], priority=10, block=True)
@haosharen2.handle()
async def handle_function():
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    await haosharen2.finish("全杀！")

flipof = on_keyword(["你是","机器人","人机","谁啊","没素质","傻逼","sb","妈","赤石","谁家","杂鱼","低能","吃屎","弱智","操","草你","滚","去死","一边去","idiot","douchebag","bitch","脑残","asshole"], rule=to_me(), priority=10, block=True)
@flipof.handle()
async def handle_function():
    if not feature_manager.get("flipoff"):
        raise FinishedException
    await flipof.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/gbc_flip_off.webp,sub_type=1]'))

flipof2 = on_command("flipoff", aliases={"竖中指","比中指"}, priority=10, block=True)
@flipof2.handle()
async def handle_function():
    if not feature_manager.get("flipoff"):
        raise FinishedException
    await flipof2.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/gbc_flip_off.webp,sub_type=1]'))

flipof3 = on_keyword(["滴泪","地雷女","宝宝"], rule=to_me(), priority=10, block=True)
@flipof3.handle()
async def handle_function():
    if not feature_manager.get("flipoff"):
        raise FinishedException
    rd = random.random()
    if rd < .2:
        await flipof3.finish('捅死你喵！捅死你喵！捅死你喵！捅死你喵！捅死你喵！捅死你喵！')
    else:
        await flipof3.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/raincandy/cantflip.png]'))

async def get_image_data(url):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.text.strip()
    return data

getachi = on_command("achievements", aliases={"成就","cj","我的成就","成就列表"}, priority=10, block=True)
@getachi.handle()
async def handle_function(event: Event = Event):
    await achievement_manager.list(event)
    raise FinishedException

upscale = on_command("upscale", aliases={"放大","zoom"}, priority=10, block=True)
@upscale.handle()
async def handle_function(args: Message = CommandArg(),bot: Bot = Bot, event: MessageEvent = Event):
    if not feature_manager.get("upscale"):
        raise FinishedException
    rep_con = await get_reply_content(event.original_message,bot)
    # 优先从args附带的图片获取
    if len(args) > 0 and args[0].type == 'image':
        await upscale.finish(await zoom_image(args[0].data['url']))
    # 检查回复的消息内容
    elif rep_con and rep_con[0]["type"] == 'image':
        await upscale.finish(await zoom_image(rep_con[0]["data"]['url']))
    else:
        await upscale.finish("请提供要放大的图片！")

# 消息转换为cq码，以文本发出
parsecq = on_command("parsecq", priority=10, block=True)
@parsecq.handle()
async def handle_function(bot: Bot = Bot, event: MessageEvent = Event):
    rep_con = await get_reply_content(event.original_message,bot,1)
    if rep_con:
        await parsecq.finish(rep_con)
    else:
        raise FinishedException

async def get_reply_data(message,bot):
    reply_segment = None
    for segment in message:
        if segment.type == "reply":
            reply_segment = segment
            break
    if reply_segment:
        reply_id = reply_segment.data.get("id")
        message_info = await bot.get_msg(message_id=int(reply_id))
        return message_info
    else:
        return {}
    
async def get_reply_content(message,bot,cq=0):
    message_info = await get_reply_data(message,bot)
    if message_info:
        if cq:
            return message_info.get("raw_message")
        else:
            return message_info.get("message")
    else:
        return 0
    
async def zoom_image(url):
    img_process.download_img(url,"images/upscale/source.jpg")
    await img_process.img4x()
    return Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/upscale/result.png]')

async def ccb_image(url):
    img_process.download_img(url,"images/img_ccb/temp/bcb.jpg")
    await img_process.ccb_image(url)
    return Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/img_ccb/temp/result.png]')
