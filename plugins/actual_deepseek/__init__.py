from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageEvent
from nonebot.exception import FinishedException
import feature_manager
import privilege_manager
import path_manager
import json
import math
import web, webss
import base64, mimetypes
import plugins.test1, img_process
import misc_manager

config_f = open("json/oa_data.json","r",encoding="utf-8")
config = json.loads(config_f.read())["configs"]
config_f.close()

from openai import AsyncOpenAI
client = AsyncOpenAI(api_key=config[config["current_engine"]]["key"], base_url=config[config["current_engine"]]["base_url"])

# 初始化语句和全局变量
msg_init = {"role": "system", "content": "你是一个名叫testpilot的群聊机器人，致力于帮群友解决问题。"}
msg_list = []
msg_limit = config["chat_msg_limit"]
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

def cfg_writeback():
    file = open("json/oa_data.json","w",encoding="utf-8")
    json.dump({"configs":config},file,ensure_ascii=False,sort_keys=True)

async def chat(dialogue):
    msg_list.append({"role": "user", "content": dialogue})
    # print(msg_list)
    resp = await client.chat.completions.create(
        model = config[config["current_engine"]]["models"][0],
        messages = msg_list,
        stream = False
    )
    remsg = resp.choices[0].message
    # msg_list.append(remsg)
    response = remsg.content
    msg_list.append({"role": "assistant", "content": response})
    global msg_count
    msg_count += 1
    if (msg_count > msg_limit):
        response = f"***对话轮数已超过上限（{msg_limit}轮）。这轮对话后，AI 的记忆将被清除。***\n"+response
        ds_reinit()
    writeback()
    return response

dsb50_sysquo = "《舞萌DX》是一款街机音乐游戏，用户将会提供一份json格式的游玩数据，包含该玩家所有游戏记录中的50个最佳记录，其中包括35个旧有曲目的记录（数据charts中sd项），以及15个新版本，即《舞萌DX 2025》歌曲的记录（数据charts中dx项），**你需要根据这份数据做出一份详细的评价**（不超过1400字）。另外，总体评级（ra）是所有曲目单曲ra的总和，最高为16500左右，数值越高越难提升，15000以上可认为是高级玩家；单曲等级（level）最高为15；chart中的“sd”及“dx”（只表示旧曲目和新曲目）和单曲数据中的“sd”及“dx”（表示标准谱面和DX谱面）不是一个意思；additional_rating可以被随便设置，请忽略掉；单曲数据中的“fs”一项代表双人游玩同步评价，也可以忽略。"

async def ds_b50(json):
    b50msglist = [{"role": "system", "content": dsb50_sysquo},{"role": "user", "content": str(json)}]
    resp = await client.chat.completions.create(
        model = config[config["current_engine"]]["models"][1],
        messages = b50msglist,
        stream = False
    )
    remsg = resp.choices[0].message
    # 在控制台输出深度思考内容（当深度思考内容存在时）
    if hasattr(remsg, 'reasoning_content'):
        print(remsg.reasoning_content)
    return remsg.content

async def analyze_image(url,prompt):
    path = "images/analyze/1.jpg"
    img_process.download_img(url, path)
    # 编码图片
    b64 = encode_image(path)
    if not prompt:
        prompt = "图片里面有什么？"
    resp = await client.chat.completions.create(
        # model = config[config["current_engine"]]["models"][1],
        # 始终使用gemini分析图片
        model = config["gemini"]["models"][1],
        messages = [
            {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": prompt,
                    },
                    {
                    "type": "image_url",
                    "image_url": {
                        "url":  f"data:image/jpeg;base64,{b64}"
                    },
                    },
                ],
            }
        ],
        stream = False
    )
    print(resp)
    remsg = resp.choices[0].message
    return remsg.content

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def reload_client(engine):
    global client
    client = AsyncOpenAI(api_key=config[engine]["key"], base_url=config[engine]["base_url"])

ads = on_command("ds", aliases={"深度求索","AI","actualdeepseek","deepseek","dick"}, priority=10, block=True)
@ads.handle()
async def handle_function(args: Message = CommandArg()):
    # 虽然没什么必要但有时发/dscount会同时触发ds，很奇怪，还是修补一下好了
    if (not feature_manager.get("deepseek")) or args.extract_plain_text() == "count" or args.extract_plain_text() == "md":
        raise FinishedException
    misc_manager.tasks.append("ds_chat")
    text = await chat(args.extract_plain_text())
    # 输出内容每3000字分段，避免长消息发不出
    segs = split_str_by_length(text, 3000)
    for i in segs:
        await ads.send(i)
    misc_manager.tasks.remove("ds_chat")
    raise FinishedException

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
    misc_manager.tasks.append("ds_chat")
    web.content_md(await chat(args.extract_plain_text()))
    await webss.take2("http://localhost:8104","container")
    misc_manager.tasks.remove("ds_chat")
    await dsmd.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))

switchengine = on_command("switchai", aliases={"更换AI引擎","切换AI"}, priority=10, block=True)
@switchengine.handle()
async def handle_function():
    if not feature_manager.get("deepseek"):
        raise FinishedException
    current = config["current_engine"]
    list = config["available_engine_list"]
    next = list[(list.index(current)+1) % len(list)]
    config["current_engine"] = next
    cfg_writeback()
    reload_client(next)
    if "desc" in config[next]:
        next = config[next]["desc"]
    await switchengine.finish(f"已切换 AI 引擎为 {next}。")

anaimg = on_command("anaimg", aliases={"fxtp","分析图片","AI分析图片"}, priority=10, block=True)
@anaimg.handle()
async def handle_function(args: Message = CommandArg(),bot: Bot = Bot, event: MessageEvent = Event):
    if not feature_manager.get("deepseek"):
        raise FinishedException
    #if config["current_engine"] != "gemini":
        #await anaimg.finish("当前 AI 引擎不支持图片分析！请用 /switchai 切换引擎再试哦！")
    misc_manager.tasks.append("ds_anaimg")
    rep_con = await plugins.test1.get_reply_content(event.original_message,bot)
    # 优先从args附带的图片获取
    if len(args) > 0 and args[0].type == 'image':
        text = await analyze_image(args[0].data['url'])
        misc_manager.tasks.remove("ds_anaimg")
        await anaimg.finish(text)
    # 检查回复的消息内容
    elif rep_con and rep_con[0]["type"] == 'image':
        # 如果存在文本参数，则作为自定义prompt传入
        custom_prompt = None
        if len(args) > 0 and args[0].type == 'text':
            custom_prompt = args.extract_plain_text()
        text = await analyze_image(rep_con[0]["data"]['url'],custom_prompt)
        misc_manager.tasks.remove("ds_anaimg")
        await anaimg.finish(text)
    else:
        misc_manager.tasks.remove("ds_anaimg")
        await anaimg.finish("请提供要分析的图片！")

checkengine = on_command("checkai", aliases={"查看AI引擎","当前AI引擎"}, priority=10, block=True)
@checkengine.handle()
async def handle_function():
    if not feature_manager.get("deepseek"):
        raise FinishedException
    current = config["current_engine"]
    if "desc" in config[current]:
        current = config[current]["desc"]
    await checkengine.finish(f"当前 AI 引擎为 {current}。")

# 按固定长度切分字符串
def split_str_by_length(s, chunk_size):
    return [s[i:i + chunk_size] for i in range(0, len(s), chunk_size)]

changedslimit = on_command("setdscount", priority=10, block=True)
@changedslimit.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) and feature_manager.get("deepseek"):
        aaa = args.extract_plain_text()
        if str.isdigit(aaa):
            global msg_limit
            msg_limit = config["chat_msg_limit"] = int(aaa)
            cfg_writeback()
        await changedslimit.finish(f"已将 AI 对话次数上限设置为 {msg_limit} 次。")
    else:
        raise FinishedException