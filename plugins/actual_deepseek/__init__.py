from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import feature_manager
import privilege_manager
import json
import math
import web, webss

from openai import AsyncOpenAI
client = AsyncOpenAI(api_key="sk-0fc94c15a3fe40ae9244396045d9ff17", base_url="https://api.deepseek.com")

# 初始化语句和全局变量
msg_init = {"role": "system", "content": "你是一个名叫testpilot的群聊机器人，致力于帮群友解决问题。"}
msg_list = []
msg_limit = 25
msg_count = 0

# 加载json
msg_file = open("json/ds_quotes.json","r",encoding="utf-8")
msj_list_raw = msg_file.read()
msg_file.close()
msg_list = json.loads(msj_list_raw)
msg_count = math.floor(len(msg_list)/2)

def ds_reinit():
    global msg_list,msg_count #操作全局变量msg_list、msg_count
    msg_list = []
    msg_list.append(msg_init)
    msg_count = 0
    writeback()

# json写入
def writeback():
    file = open("json/ds_quotes.json","w",encoding="utf-8")
    json.dump(msg_list,file,ensure_ascii=False,sort_keys=True)

async def chat(dialogue):
    msg_list.append({"role": "user", "content": dialogue})
    # print(msg_list)
    resp = await client.chat.completions.create(
        model = "deepseek-chat",
        messages = msg_list,
        stream = False
    )
    remsg = resp.choices[0].message
    # msg_list.append(remsg)
    msg_list.append({"role": "assistant", "content": remsg.content})
    global msg_count
    msg_count += 1
    writeback()
    return remsg.content

ads = on_command("ds", aliases={"深度求索","AI","actualdeepseek","真正的deepseek"}, priority=10, block=True)
@ads.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("deepseek"):
        raise FinishedException
    await ads.finish(await chat(args.extract_plain_text()))

dscount = on_command("dscount", aliases={"AI对话轮数","deepseek对话轮数","对话轮数"}, priority=10, block=True)
@dscount.handle()
async def handle_function(event: Event):
    if privilege_manager.checkuser(event.get_user_id()) and feature_manager.get("deepseek"):
        await dscount.finish("已与 AI 进行了 "+str(msg_count)+" 轮对话。")
    else:
        raise FinishedException

dssetup = on_command("dssetup", aliases={"deepseek初始化"}, priority=10, block=True)
@dssetup.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) and feature_manager.get("deepseek"):
        global msg_init
        rid = args.extract_plain_text()
        msg_init = {"role": "system", "content": rid}
        await dssetup.finish("已将 AI 初始化设定调整为：“"+rid+"”。请清除对话记忆以使更改生效。")
    else:
        raise FinishedException

reds = on_command("reds", aliases={"重置deepseek","重置AI","resetdeepseek"}, priority=10, block=True)
@reds.handle()
async def handle_function(event: Event):
    if privilege_manager.checkuser(event.get_user_id()) and feature_manager.get("deepseek"):
        ds_reinit()
        await reds.finish("已清除 AI 的对话记忆。")
    else:
        raise FinishedException
    
dsmd = on_command("dsmd", aliases={"deepseekmarkdown"}, priority=10, block=True)
@dsmd.handle()
async def handle_function(args: Message = CommandArg()):
    if not (feature_manager.get("deepseek") and feature_manager.get("rendermd")):
        raise FinishedException
    web.content_md(await chat(args.extract_plain_text()))
    webss.take2("http://localhost:8104","container")
    await dsmd.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/webss/1.png]'))