from nonebot import on_command
from nonebot import get_bot
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import feature_manager
import json
import path_manager

bot_qq_id = 3978644480
default_name = "testpilot"
default_pic = "images/headpic.jpg"

data = open("json/imbotate_data.json","r",encoding="utf-8")
faked = json.loads(data.read())['data']
data.close()

def writeback():
    file = open("json/imbotate_data.json","w",encoding="utf-8")
    json.dump({'data':faked},file,ensure_ascii=False,sort_keys=True)

fake = on_command("fake", aliases={"假扮","impersonate","imbotate","模仿"}, priority=10, block=True)
@fake.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
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
        else:
            await fake.finish("参数错误。用法：/fake [要假扮的@群员或群员QQ号]")
        # 如果提供的qq号就是bot自己
        if int(qqnum) == bot_qq_id:
            await fake.finish("你不能让我假扮自己哦！")
        # 获取该群员昵称
        qqnam = dict(await bot.get_stranger_info(user_id=qqnum))["nick"]
        # 获取该群员群昵称
        grnam = dict(await bot.get_group_member_info(user_id=qqnum,group_id=group_id))["card"]
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
            await bot.set_qq_avatar(file="https://q1.qlogo.cn/g?b=qq&nk="+qqnum+"&s=640")
        await fake.finish("大家好啊，我是"+setnam+"。")
    else:
        raise FinishedException
    
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