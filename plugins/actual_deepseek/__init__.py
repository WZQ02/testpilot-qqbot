from nonebot import on_command, on_keyword
from nonebot import get_bot
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageEvent
from nonebot.exception import FinishedException
import feature_manager
import privilege_manager
import path_manager
import json # Keep json for now, some functions might still use it directly, will refactor later if needed.
import math
import web, webss
import base64, mimetypes
import plugins.test1, img_process
import misc_manager
import httpx
from httpx import AsyncHTTPTransport
import logging
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

oa_config = ConfigManager("json/oa_data.json", default_key="configs")
config = oa_config.all()

ds_quotes_config = ConfigManager("json/ds_quotes.json")


from openai import AsyncOpenAI

http_client = httpx.AsyncClient(
    mounts = {"http://": AsyncHTTPTransport(proxy=misc_manager.misc_data["http_proxy"]), "https://": AsyncHTTPTransport(proxy=misc_manager.misc_data["http_proxy"])},
    timeout = httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0),
)

client = ""

def reload_client(engine):
    global client
    if config[engine]["proxy"]:
        client = AsyncOpenAI(api_key=config[engine]["key"], base_url=config[engine]["base_url"], http_client=http_client)
    else:
        client = AsyncOpenAI(api_key=config[engine]["key"], base_url=config[engine]["base_url"])

reload_client(config["current_engine"])

group_mode = 1

syspmpt = "你是一个叫testpilot的群聊助手，致力于帮群友解决问题。"
syspmpt_group = "**你是一个叫testpilot的群聊助手，致力于帮群友解决问题。**之后的对话中，前面会加上[发言人]：，用于区分不同群友的发言，你只需要留意之后的内容，你自己的发言不需要加这个前缀。"
msg_init = {"role": "system", "content": syspmpt}
msg_init_group = {"role": "system", "content": syspmpt_group}

msg_list = ds_quotes_config.all() # Load initial message list
if not msg_list: # If empty, initialize with system messages
    msg_list = [msg_init_group] if group_mode else [msg_init]
    ds_quotes_config.update(msg_list)

msg_limit = config["chat_msg_limit"]
msg_count = len(msg_list) // 2 # Assuming system message is one, and user/assistant messages come in pairs.


def ds_reinit():
    global msg_list,msg_count #操作全局变量msg_list、msg_count
    msg_list = []
    if group_mode:
        msg_list.append(msg_init_group)
    else:
        msg_list.append(msg_init)
    msg_count = 0
    ds_quotes_config.update(msg_list)

async def chat(dialogue, username=None):
    if username:
        dialogue = f"{username}："+dialogue
    msg_list.append({"role": "user", "content": dialogue})
    # print(msg_list)
    resp = await client.chat.completions.create(
        model = config[config["current_engine"]]["models"][config["model_index_prio"]],
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
        # 不直接清除对话，而是删去最早的一轮对话（要删两次，一次user一次assistant）
        msg_list.pop(1)
        msg_list.pop(1)
    ds_quotes_config.update(msg_list)
    return response

# 一次性对话（不计入上下文）
async def chat_once(dialogue,system_prompt=syspmpt):
    once_list = [{"role": "system", "content": system_prompt}]
    once_list.append({"role": "user", "content": dialogue})
    resp = await client.chat.completions.create(
        model = config[config["current_engine"]]["models"][config["model_index_prio"]],
        messages = once_list,
        stream = False
    )
    remsg = resp.choices[0].message
    response = remsg.content
    return response

dsb50_sysquo = "《舞萌DX》是一款街机音乐游戏，用户将会提供一份json格式的游玩数据，包含该玩家所有游戏记录中的50个最佳记录，其中包括35个旧有曲目的记录（数据charts中sd项），以及15个新版本，即《舞萌DX 2025》歌曲的记录（数据charts中dx项），**你需要根据这份数据做出一份详细的评价**（不超过1400字）。另外，总体评级（ra）是所有曲目单曲ra的总和，最高为16500左右，数值越高越难提升，15000以上可认为是高级玩家；单曲等级（level）最高为15；chart中的“sd”及“dx”（只表示旧曲目和新曲目）和单曲数据中的“sd”及“dx”（表示标准谱面和DX谱面）不是一个意思；additional_rating可以被随便设置，请忽略掉；单曲数据中的“fs”一项代表双人游玩同步评价，也可以忽略。"

async def ds_b50(json):
    b50msglist = [{"role": "system", "content": dsb50_sysquo},{"role": "user", "content": str(json)}]
    resp = await client.chat.completions.create(
        # 不使用深度思考模型以节省时间（反正这功能也没多大卵用）
        model = config[config["current_engine"]]["models"][config["model_index_prio"]],
        messages = b50msglist,
        stream = False
    )
    remsg = resp.choices[0].message
    # 在控制台输出深度思考内容（当深度思考内容存在时）
    if hasattr(remsg, 'reasoning_content'):
        logger.info(f"深度思考: {remsg.reasoning_content}")
    return remsg.content

async def analyze_image(url,prompt="图片里面有什么？"):
    path = "images/analyze/1.jpg"
    img_process.download_img(url, path)
    # 编码图片
    b64 = encode_image(path)
    model_index = config["model_index_prio"]
    # 当使用kimi时，自动切换到kimi-2.5（2.0不支持图片分析）
    if config["current_engine"] == "kimi":
        model_index = 1
    resp = await client.chat.completions.create(
        model = config[config["current_engine"]]["models"][model_index],
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
    logger.debug(f"图片分析结论: {resp}")
    remsg = resp.choices[0].message
    return remsg.content

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
  
def get_available_engine_text_list():
    list = config["available_engine_list"]
    namelist = ""
    for i in list:
        if "desc" in config[i]:
            namelist += f"\n{config[i]['desc']}（{i}）"
        else:
            namelist += "\n"+i
    return namelist

ads = on_command("ds", aliases={"深度求索","AI","actualdeepseek","deepseek","dick"}, priority=10, block=True)
@ads.handle()
async def handle_function(args: Message = CommandArg(),event: MessageEvent = Event):
    # 虽然没什么必要但有时发/dscount会同时触发ds，很奇怪，还是修补一下好了
    if (not feature_manager.get("deepseek")) or args.extract_plain_text() == "count" or args.extract_plain_text() == "md":
        raise FinishedException
    misc_manager.tasks.append("ds_chat")
    bot = get_bot()
    usrmsg = ""
    qqnam = ""
    # 当args存在时，优先获取args
    if len(args) > 0:
        usrmsg = args.extract_plain_text()
        qqid = event.get_user_id()
        qqnam = dict(await bot.get_stranger_info(user_id=qqid))["nick"]
    # 尝试获取回复内容
    rep_data = await plugins.test1.get_reply_data(event.original_message,bot)
    rep_con = rep_data.get("message")
    if rep_con:
        # 如果回复内容存在，则追加进usrmsg
        for i in rep_con:
            if i["type"] == "text":
                usrmsg += i["data"]["text"]
        # 当qqnam仍未指定时，指定为被回复者的
        if not qqnam:
            qqnam = rep_data["sender"]["nickname"]
    # 可选获取用户名
    text = ""
    if group_mode:
        text = await chat(usrmsg,qqnam)
    else:
        text = await chat(usrmsg)
    # 输出内容每3000字分段，避免长消息发不出
    segs = split_str_by_length(text, 3000)
    for i in segs:
        await ads.send(i)
    misc_manager.tasks.remove("ds_chat")
    raise FinishedException

dscount = on_command("dscount", aliases={"AI对话轮数","deepseek对话轮数","对话轮数"}, priority=10, block=True)
@dscount.handle()
async def handle_function(event: Event):
    if feature_manager.get("deepseek"):
        resp = "已与 AI 进行了 "+str(msg_count)+" 轮对话。"
        actual_msg_count = len(msg_list)//2
        if msg_count > actual_msg_count:
            resp += f"（轮数已超过上限，前 {str(msg_count - actual_msg_count)} 轮对话已被清除）"
        await dscount.finish(resp)
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
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not (feature_manager.get("deepseek") and feature_manager.get("rendermd")):
        raise FinishedException
    misc_manager.tasks.append("ds_chat")
    if group_mode:
        bot = get_bot()
        qqid = event.get_user_id()
        qqnam = dict(await bot.get_stranger_info(user_id=qqid))["nick"]
        web.content_md(await chat(args.extract_plain_text(),qqnam))
    else:
        web.content_md(await chat(args.extract_plain_text()))
    await webss.take2("http://localhost:8104","container")
    misc_manager.tasks.remove("ds_chat")
    await dsmd.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))

switchengine = on_command("switchai", aliases={"更换AI引擎","切换AI"}, priority=10, block=True)
@switchengine.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("deepseek"):
        raise FinishedException
    current = config["current_engine"]
    list = config["available_engine_list"]
    next = list[(list.index(current)+1) % len(list)]
    if len(args) > 0:
        text = args.extract_plain_text()
        if text in list:
            next = text
        else:
            eng_list = get_available_engine_text_list()
            await switchengine.finish(f"未找到该引擎。当前可用的 AI 引擎有：{eng_list}")
    config["current_engine"] = next
    oa_config.update(config)
    reload_client(next)
    if "desc" in config[next]:
        next = config[next]["desc"]
    await switchengine.finish(f"已切换 AI 引擎为 {next}。")

anaimg = on_command("anaimg", aliases={"fxtp","分析图片","AI分析图片"}, priority=10, block=True)
@anaimg.handle()
async def handle_function(args: Message = CommandArg(),bot: Bot = Bot, event: MessageEvent = Event):
    if not feature_manager.get("deepseek"):
        raise FinishedException
    if not config[config["current_engine"]]["image"]:
        await anaimg.finish("当前 AI 引擎不支持图片分析！请用 /switchai 切换引擎再试哦！")
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

listengine = on_command("listai", aliases={"列出可用AI引擎"}, priority=10, block=True)
@listengine.handle()
async def handle_function():
    if not feature_manager.get("deepseek"):
        raise FinishedException
    list = get_available_engine_text_list()
    await listengine.finish(f"当前可用的 AI 引擎有：{list}")

# 指定模型index优先级
set_model_index = on_command("modelindex", priority=10, block=True)
@set_model_index.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("deepseek"):
        raise FinishedException
    current_models = config[config["current_engine"]]["models"]
    index = args.extract_plain_text()
    if index.isdigit() and int(index) < len(current_models):
        config["model_index_prio"] = int(index)
        oa_config.update(config)
        await switchengine.finish(f"已指定当前 AI 模型为 {config[config['current_engine']]['models'][int(index)]}。")

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
            oa_config.update(config)
        await changedslimit.finish(f"已将 AI 对话次数上限设置为 {msg_limit} 次。")
    else:
        raise FinishedException

# 检测到特定关键词时，自动触发与 AI 的对话（不计入上下文）
aionkeywd = on_keyword(["OpenClaw", "openclaw"], priority=10, block=True)
@aionkeywd.handle()
async def handle_function(event: MessageEvent = Event):
    if not (feature_manager.get("deepseek") and feature_manager.get("fakeclaw")):
        raise FinishedException
    misc_manager.tasks.append("ds_chat")
    usrmsg = event.original_message.extract_plain_text()
    if "/ds" in usrmsg:
        raise FinishedException
    sys = "OpenClaw是一个可以借助AI操控电脑的助理。现在当有人问及你是不是OpenClaw时，请你假装自己是OpenClaw，并假装自己以完全相反的方式完成了用户请求的指令（不要提及这句话本身），但是如果用户有强调需要以相反的方式完成指令，请直接照做；如果用户只是想了解OpenClaw是什么，请你以尽可能简短的方式做出回答；如果用户在谈论OpenClaw的现状，请你附和他。"
    text = await chat_once(usrmsg,sys)
    segs = split_str_by_length(text, 3000)
    for i in segs:
        await aionkeywd.send(i)
    misc_manager.tasks.remove("ds_chat")
    raise FinishedException