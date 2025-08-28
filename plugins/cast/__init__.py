from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.params import CommandArg
from nonebot import get_bot
from nonebot.exception import FinishedException
import feature_manager
import privilege_manager
import json
import requests

# cast参数
#cast_url = "http://localhost:8120/cast"//测试服务器
cast_url = "https://api.wzq02.top/testpilot/cast"#线上主服务
group = 0

cast = on_command("cast", aliases={"投放"}, priority=10, block=True)
@cast.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("cast"):
        raise FinishedException
    bot = get_bot()
    uid = event.get_user_id()
    uname = dict(await bot.get_stranger_info(user_id=uid))["nick"]
    msg = args.extract_plain_text()
    picurl = ""
    if args[0].type == 'image':
        picurl = args[0].data['url']
    castit(uname,msg,picurl,"")
    raise FinishedException

anocast = on_command("anocast", aliases={"匿名投放"}, priority=10, block=True)
@anocast.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("cast"):
        raise FinishedException
    bot = get_bot()
    #uid = event.get_user_id()
    #uname = dict(await bot.get_stranger_info(user_id=uid))["nick"]
    msg = args.extract_plain_text()
    picurl = ""
    if args[0].type == 'image':
        picurl = args[0].data['url']
    castit("",msg,picurl,"")
    raise FinishedException

castgroup = on_command("castgroup", aliases={"投放群聊"}, priority=10, block=True)
@castgroup.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) and feature_manager.get("cast"):
        msg = args.extract_plain_text()
        if (str.isdigit(msg) and int(msg) >= 0):
            global group
            group = int(msg)
            if group == 0:
                await castgroup.send("已停用群聊投放。")
            else:
                await castgroup.send("投放群聊："+str(group))
        elif (msg == "all"):
            group = -1
            await castgroup.send("将投放 bot 接收到的所有群聊消息！")
        else:
            await castgroup.send("参数错误。用法：/castgroup [需要投放消息的群号]")
        raise FinishedException
    else:
        raise FinishedException
    
autocast = on_message(priority=10, block=True)
@autocast.handle()
async def handle_function(event: Event):
    sid = event.get_session_id().split("_")
    if sid[0] == 'group' and (int(sid[1]) == group or group == -1):
        bot = get_bot()
        uid = event.get_user_id()
        uname = dict(await bot.get_stranger_info(user_id=uid))["nick"]
        gname = dict(await bot.get_group_info(group_id=int(sid[1])))["group_name"]
        evmsg = event.get_message()
        msg = evmsg.extract_plain_text() or ""
        picurl = ""
        for item in evmsg:
            if item.type == 'image':
                picurl = item.data['url']
                break
        if (len(msg) == 0 or (len(msg) > 0 and msg[0] != "/")):
            castit(uname,msg,picurl,"群聊："+gname)
    raise FinishedException

def castit(uname,msg,picurl,desc):
    data = {"castcontent":{"version":1,"casttype":"message","username":uname,"textcontent":msg,"picurl":picurl,"desc":desc}}
    resp = requests.post(cast_url,json=data)