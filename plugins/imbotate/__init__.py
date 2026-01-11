from nonebot import on_command
from nonebot import get_bot
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import feature_manager
import json
import path_manager
import time
import achievement_manager
import random
import plugins.member_stuff

bot_qq_id = 3978644480
default_name = "testpilot"
default_pic = "images/headpic.jpg"

data = open("json/imbotate_data.json","r",encoding="utf-8")
datar = json.loads(data.read())
faked = datar['data']
hist = datar['history']
data.close()

fake_presets_data = open("json/fake_presets.json","r",encoding="utf-8")
fake_presets = json.loads(fake_presets_data.read())['fake_presets']
fake_presets_data.close()

#specd = open("json/spec_qq_list.json","r",encoding="utf-8")
#plugins.member_stuff.spec_list = json.loads(specd.read())

def howlong1(unixtime):
    hl = time.time() - float(unixtime)
    if (hl) < 60:
        return str(int(hl))+"秒"
    elif (hl) < 3600:
        return str(int(hl/60))+"分钟"
    elif (hl) < 86400:
        return str(int(hl/3600))+"小时"
    else:
        return str(int(hl/86400))+"天"

def add_history(time,fakeid,fakenm,fromid,fromnm,groupid):
    # 如果历史记录超过5条，删去最旧的一条
    if len(hist) >= 5:
        hist.remove(hist[0])
    hist.append({"time":time,"fakeid":fakeid,"fakenm":fakenm,"fromid":fromid,"fromnm":fromnm,"group":groupid})
    # 写回数据
    writeback()

def writeback():
    file = open("json/imbotate_data.json","w",encoding="utf-8")
    json.dump({'data':faked,'history':hist},file,ensure_ascii=False,sort_keys=True)

fake = on_command("fake", aliases={"假扮","impersonate","imbotate","模仿","fuck"}, priority=10, block=True)
@fake.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if event.get_plaintext().startswith("/fuck"):
        await achievement_manager.add(14,event)
    if feature_manager.get("fake"):
        bot = get_bot()
        qqnum = 0
        # 发起假扮指令人所在群聊
        group_id = event.get_session_id().split("_")[1]
        # 第一个参数是@群员
        if len(args) > 0 and args[0].type == 'at':
            qqnum = args[0].data['qq']
        # 第一个参数是群员QQ号
        elif len(args) > 0 and str.isdigit(args.extract_plain_text().split()[0]):
            qqnum = args.extract_plain_text().split()[0]
        # 第一个参数是非数字、非at，查找是否存在于fake_presets
        else:
            for i in fake_presets:
                if fake_presets[i]["name"] == args.extract_plain_text():
                    qqnum = "-"+i
                    break
            if qqnum == 0:
                await fake.finish("参数错误。用法：/fake [要假扮的@群员或群员QQ号]")
        # 如果提供的qq号就是bot自己
        if int(qqnum) == bot_qq_id:
            await achievement_manager.add(1,event)
            await fake.finish("你不能让我假扮自己哦！")
        setnam = await do_fake(bot,event,qqnum,group_id)
        await fake.finish("大家好啊，我是"+setnam+"。")
    else:
        raise FinishedException
    
randomfake = on_command("rdfake", aliases={"随机假扮","随机模仿","randomfake","randomimbotate"}, priority=10, block=True)
@randomfake.handle()
async def handle_function(event: Event = Event):
    if feature_manager.get("fake"):
        bot = get_bot()
        group_id = event.get_session_id().split("_")[1]
        mbl = await bot.get_group_member_list(group_id=group_id)
        mbllen = len(mbl)
        qqnum = 0
        # 随机一个群员，并确保不随机到bot自己
        while 1:
            rd = random.randint(0,mbllen-1)
            qqnum = str(mbl[rd]['user_id'])
            if int(qqnum) != bot_qq_id:
                break
        # 发起假扮指令人所在群聊
        group_id = event.get_session_id().split("_")[1]
        setnam = await do_fake(bot,event,qqnum,group_id)
        await randomfake.finish("大家好啊，我是"+setnam+"。")
    else:
        raise FinishedException

# 拆分一部分fake代码以复用
async def do_fake(bot,event,qqnum,group_id):
    # 判断fake的是qq用户还是preset
    if int(qqnum) >= 0:   
        # 获取该群员昵称
        qqnam = dict(await bot.get_stranger_info(user_id=qqnum))["nick"]
        # 获取该群员群昵称
        grnam = dict(await bot.get_group_member_info(user_id=qqnum,group_id=group_id))["card"]
    else:
        qqnam = fake_presets[str(-int(qqnum))]["name"]
        grnam = qqnam
    # 获取bot先前群昵称
    btnam = dict(await bot.get_group_member_info(user_id=bot_qq_id,group_id=group_id))["card"]
    # 刷新部分json数据
    faked["imp_enabled"] = 1
    faked["imp_qq"] = qqnum
    faked["imp_qqname"] = qqnam
    faked["imp_group_nick"] = grnam
    # 检查是否来自上次发起假扮指令的群聊（如果是，则不修改imp_from_group和ori_group_nick）
    if group_id != faked["imp_from_group"]:
        if faked["imp_from_group"] != 0:
            # 先在上一个群聊还原群昵称
            await bot.set_group_card(group_id=faked["imp_from_group"],user_id=bot_qq_id,card=faked["ori_group_nick"])
        faked["imp_from_group"] = group_id
        faked["ori_group_nick"] = btnam
    # json回写
    writeback()
    # 获取fake发起人QQ号和名称
    fak_fromid = event.get_user_id()
    fak_fromnm = dict(await bot.get_stranger_info(user_id=fak_fromid))["nick"]
    # 写入fake历史记录
    add_history(time.time(),qqnum,qqnam,fak_fromid,fak_fromnm,group_id)
    # 修改bot群昵称
    setnam = ""
    if (grnam == ""):
        setnam=qqnam
    else:
        setnam=grnam
    await bot.set_group_card(group_id=group_id,user_id=bot_qq_id,card=setnam)
    # 修改botQQ昵称和头像
    await bot.set_qq_profile(nickname=qqnam)
    if feature_manager.get("fake_headpic"):
        if int(qqnum) >= 0:
            await bot.set_qq_avatar(file="https://q1.qlogo.cn/g?b=qq&nk="+qqnum+"&s=640")
        else:
            await bot.set_qq_avatar(file=path_manager.bf_path()+"images/fake_presets/"+fake_presets[str(-int(qqnum))]["hpic"])
    # 成就(除了“试图让bot假扮自己”以外的)
    try:
        # 让bot假扮fake发起人自己
        if int(qqnum) == int(fak_fromid):
            await achievement_manager.add(13,event)
        # 让bot假扮别的bot
        if int(qqnum) in plugins.member_stuff.spec_list["bots"]:
            await achievement_manager.add(7,event)
        # 让bot假扮。。。
        if int(qqnum) == plugins.member_stuff.spec_list["special_users"][0]:
            await achievement_manager.add(12,event)
        if int(qqnum) == plugins.member_stuff.spec_list["special_users"][1]:
            await achievement_manager.add(8,event)
        if int(qqnum) == plugins.member_stuff.spec_list["special_users"][2]:
            await achievement_manager.add(9,event)
    except:
        print("")  
    return setnam  
    
defake = on_command("defake", aliases={"变回","noimpersonate","noimbotate"}, priority=10, block=True)
@defake.handle()
async def handle_function():
    # 读取fake状态（为0则不回应）
    if faked["imp_enabled"] == 1:
        bot = get_bot()
        # 改回bot群昵称
        await bot.set_group_card(group_id=faked["imp_from_group"],user_id=bot_qq_id,card=faked["ori_group_nick"])
        # 改回botQQ名
        await bot.set_qq_profile(nickname=default_name)
        # 改回bot头像
        if feature_manager.get("fake_headpic"):
            await bot.set_qq_avatar(file=path_manager.bf_path()+"images/headpic.jpg")
        # 重置并写回json数据
        faked["imp_enabled"] = 0
        faked["imp_qq"] = 0
        faked["imp_qqname"] = ""
        faked["imp_from_group"] = 0
        faked["imp_group_nick"] = ""
        faked["ori_group_nick"] = ""
        writeback()
        await defake.finish("我变回来啦！")
    else:
        raise FinishedException
    
sethead = on_command("sethead", aliases={"设置头像","头像","headpic"}, priority=10, block=True)
@sethead.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("fake_headpic"):
        bot = get_bot()
        url = args.extract_plain_text()
        try:
            await bot.set_qq_avatar(file=url)
            await sethead.send("已设置头像。")
        except:
            await sethead.finish("设置头像失败！")
        raise FinishedException

gfhistory = on_command("fakehistory", aliases={"getfakehistory","假扮记录","假扮历史记录"}, priority=10, block=True)
@gfhistory.handle()
async def handle_function(event: Event = Event):
    if feature_manager.get("fake"):
        res = "变身记录："
        for i in hist:
            res += ("\n- "+howlong1(i["time"])+"前 "+i["fromnm"]+"("+i["fromid"]+") 把bot变成了 "+i["fakenm"]+"("+i["fakeid"]+")")
        await gfhistory.finish(res)