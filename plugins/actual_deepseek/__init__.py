from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import feature_manager
import privilege_manager
import path_manager
import json
import math
import web, webss

akfile = open("json/oa_api_key.json","r",encoding="utf-8")
ak = json.loads(akfile.read())["key"]
akfile.close()

from openai import AsyncOpenAI
client = AsyncOpenAI(api_key=ak, base_url="https://api.deepseek.com")

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

dsb50_sysquo = "《舞萌DX》是一款街机音乐游戏，用户将会提供一份json格式的游玩数据，包含该玩家所有游戏记录中的50个最佳记录，其中包括35个旧有曲目的记录（数据charts中sd项），以及15个新版本，即《舞萌DX 2025》歌曲的记录（数据charts中dx项），**你需要根据这份数据做出一份详细的评价**（不超过1400字）。另外，总体评级（ra）是所有曲目单曲ra的总和，最高为16500左右，数值越高越难提升，15000以上可认为是高级玩家；单曲等级（level）最高为15；chart中的“sd”及“dx”（只表示旧曲目和新曲目）和单曲数据中的“sd”及“dx”（表示标准谱面和DX谱面）不是一个意思；additional_rating可以被随便设置，请忽略掉；单曲数据中的“fs”一项代表双人游玩同步评价，也可以忽略。"

async def ds_b50(json):
    b50msglist = [{"role": "system", "content": dsb50_sysquo},{"role": "user", "content": str(json)}]
    resp = await client.chat.completions.create(
        model = "deepseek-reasoner",
        messages = b50msglist,
        stream = False
    )
    remsg = resp.choices[0].message
    # 在控制台输出深度思考内容
    print(remsg.reasoning_content)
    return remsg.content

ads = on_command("ds", aliases={"深度求索","AI","actualdeepseek","deepseek","dick"}, priority=10, block=True)
@ads.handle()
async def handle_function(args: Message = CommandArg()):
    # 虽然没什么必要但有时发/dscount会同时触发ds，很奇怪，还是修补一下好了
    if (not feature_manager.get("deepseek")) or args.extract_plain_text() == "count" or args.extract_plain_text() == "md":
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
    await dsmd.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))