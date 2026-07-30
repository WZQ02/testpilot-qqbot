from nonebot import on_command, on_message, get_bot
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Message, MessageEvent, Event
from nonebot.exception import FinishedException
import path_manager
import webss
import json
import base64
import requests
import asyncio
import Levenshtein
import privilege_manager

api = "https://api.wzq02.top/namecard2026/nc_update"

facts = []
with open("json/fun_facts.json","r",encoding="utf-8") as f:
    facts = json.loads(f.read())["facts"]

def str_to_base64(text: str, encoding="utf-8") -> str:
    return base64.b64encode(text.encode(encoding)).decode(encoding)

def base64_to_str(b64_str: str, encoding="utf-8") -> str:
    return base64.b64decode(b64_str).decode(encoding)

encoded = []
for i in facts:
    encoded.append(str_to_base64(i))

"""
code for generating passmap
temp = {}
count = 0
for i in encoded:
    count+=1
    temp.update({i:count})
print(temp)
"""

main = on_message(priority=10, block=True, rule=to_me())
@main.handle()
async def handle_function(event: MessageEvent):
    message = event.get_message().extract_plain_text()
    passphrase = ""
    pp_count = 0
    for i in encoded:
        pp_count += 1
        if abs(len(i) - len(message)) <= 2 and Levenshtein.distance(i, message) < 4:
            passphrase = i
            break
    # if len(message) > 10 and message in encoded:
    if len(passphrase) > 10:
        bot = get_bot()
        sender_id = event.get_user_id()
        uinfo = dict(await bot.get_stranger_info(user_id=sender_id))
        sender_nick = "thetestnickname"
        if "nick" in uinfo:
            sender_nick = uinfo["nick"]
        form = {"type": 1,"data": {"passphrase": passphrase,"name": sender_nick,"id": sender_id}}
        resp = requests.post(api,json=form)
        result = resp.json()
        if int(result["type"]) == 11:
            await main.finish("你的点位已经被抢占了哦！")
        await asyncio.sleep(2)
        await webss.take("https://namecard2026.wzq02.top/?highlight="+sender_id,3,filename="1",xres=1280,yres=800)
        await main.finish(Message(f'[CQ:image,file=file:///{path_manager.bf_path()}webss/1.png]fun fact #{pp_count}: {base64_to_str(passphrase)}\nhttps://namecard2026.wzq02.top/'))
    else:
        raise FinishedException

nc26rm = on_command("nc26rm", aliases={"nc26remove"}, priority=10, block=True)
@nc26rm.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    # 限定超管可用
    if privilege_manager.checkuser(event.get_user_id()) == 2:
        num = args.extract_plain_text()
        if (str.isdigit(num)):
            form = {"type": 0,"data": {"id": num}}
            resp = requests.post(api,json=form)
            result = resp.json()
            if int(result["type"]) == 1:
                await nc26rm.finish("已删除点位。")
            else:
                await nc26rm.finish("点位删除失败。错误代码："+result["type"])
    else:
        raise FinishedException 