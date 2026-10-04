from nonebot import on_command
from nonebot import get_bot
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import privilege_manager
import feature_manager
import random
import achievement_manager
import json
import plugins.imbotate
import misc_manager
import plugins.member_stuff
import path_manager
import asyncio, math
import unicodedata
import web
import webss

# 获取特殊qq号列表
specd = open("json/spec_qq_list.json","r",encoding="utf-8")
spec_list = json.loads(specd.read())

# 获取群员列表
"""
getmbl = on_command("gmbl", priority=10, block=True)
@getmbl.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) == 2:
        bot = get_bot()
        group_id = get_group_id(event)
        print(await bot.get_group_member_list(group_id=group_id))
    raise FinishedException
"""
bot_qq_id = 3978644480
lvstr_list = ["我喜欢你","我！爱！你！","！suki！拉布！嗨嗨！","齁哦哦哦哦哦哦哦","约吗？","妈妈","麻麻"]
lvstr_list2 = ["我喜欢你","爱你喵","我爱你","贴贴","你是一个小蛋糕","亲","宝宝","宝贝","宝宝你是一个甜甜糯糯的小蛋糕","揉你小肚肚~","摸摸头","摸摸","么么"]

randomcs = on_command("rdcs", aliases={"随机赤石","randomchishi","randomcs","随机吃屎","随机扔粑粑"}, priority=10, block=True)
@randomcs.handle()
async def handle_function(event: Event = Event):
    if feature_manager.can_use("randomcs", event.get_user_id()):
        bot = get_bot()
        group_id = get_group_id(event)
        if int(group_id) in spec_list["randomcs_whitelist_groups"]:
            mbl = await bot.get_group_member_list(group_id=group_id)
            mbllen = len(mbl)
            rd = random.randint(0,mbllen-1)
            chqq = str(mbl[rd]['user_id'])
            if int(chqq) == bot_qq_id:
                await achievement_manager.add(6,event)
            # event.get_user_id()获取到的是str而不是int
            if chqq == event.get_user_id():
                await achievement_manager.add(11,event)
            if plugins.member_stuff.bot_sex == 2:
                await randomcs.finish(Message("[CQ:at,qq="+chqq+"] 给你丢粑粑喵"))
            else:
                await randomcs.finish(Message("[CQ:at,qq="+chqq+"] 赤石"))
        else:
            await randomcs.finish("请在“抓小哥”相关群聊使用这个命令哦！")
    else:
        raise FinishedException
    
randombb = on_command("rdbb", aliases={"randomlove","随机表白"}, priority=10, block=True)
@randombb.handle()
async def handle_function(event: Event = Event):
    if feature_manager.can_use("randomcs", event.get_user_id()):
        bot = get_bot()
        group_id = get_group_id(event)
        mbl = await bot.get_group_member_list(group_id=group_id)
        mbllen = len(mbl)
        rd = random.randint(0,mbllen-1)
        lvstr = ""
        if plugins.member_stuff.bot_sex == 2:
            lvstr = lvstr_list2[random.randint(0,len(lvstr_list2)-1)]
        else:
            lvstr = lvstr_list[random.randint(0,len(lvstr_list)-1)]
        chqq = str(mbl[rd]['user_id'])
        # 在特定群聊更改行为
        if int(group_id) == spec_list["special_groups"][0]:
            chqq = str(spec_list["special_users"][0])
        if int(group_id) == spec_list["special_groups"][1]:
            chqq = str(spec_list["special_users"][1])
        if int(chqq) == bot_qq_id:
            await achievement_manager.add(6,event)
        if chqq == event.get_user_id():
            await achievement_manager.add(11,event)
        await randombb.finish(Message("[CQ:at,qq="+chqq+"] "+lvstr))
    else:
        raise FinishedException

"""
randombb = on_command("rdcp", aliases={"随机凑CP","随机结婚证"}, priority=10, block=True)
@randombb.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.can_use("randomcs", event.get_user_id()):
        bot = get_bot()
        group_id = get_group_id(event)
        mbl = await bot.get_group_member_list(group_id=group_id)
        mbllen = len(mbl)
        rd1 = random.randint(0,mbllen-1)
        rd2 = random.randint(0,mbllen-1)
        await randombb.finish(Message("[CQ:at,qq="+str(mbl[rd1]['user_id'])+"] 结[CQ:at,qq="+str(mbl[rd2]['user_id'])+"]"))
    else:
        raise FinishedException
"""

bot_sex = 0
def sync_bot_sex():
    misc_manager.misc_data["bot_sex"] = bot_sex
    misc_manager.writeback()
bot_sex = misc_manager.misc_data["bot_sex"]

changesex = on_command("changesex", aliases={"变性","更改性别"}, priority=10, block=True)
@changesex.handle()
async def handle_function(event: Event = Event):
    if not feature_manager.can_use("changesex", event.get_user_id()):
        raise FinishedException
    global bot_sex
    bot = get_bot()
    cases = {0:1,1:2,2:1}
    sex = cases.get(bot_sex)
    # 获取当前qq昵称
    nick = ""
    fake_status = plugins.imbotate.faked["imp_enabled"]
    if fake_status:
        nick = plugins.imbotate.faked["imp_qqname"]
    else:
        nick = plugins.imbotate.default_name
    await bot.set_qq_profile(nickname=nick,sex=sex)
    bot_sex = sex
    sync_bot_sex()
    quotes = {0:"",1:"男",2:"女"}
    await changesex.finish("大家好啊，我是"+quotes.get(sex)+nick+"。")

xxhq_id = 3889784836
cf_id = 3928110595

acexplode = on_command("炸空调", priority=10, block=True)
@acexplode.handle()
async def handle_function(event: Event = Event):
    if not feature_manager.can_use("meme_resp", event.get_user_id()):
        raise FinishedException
    bot = get_bot()
    group_id = get_group_id(event)
    mbl = await bot.get_group_member_list(group_id=group_id)
    target_id = 0
    for i in mbl:
        if int(i['user_id']) == xxhq_id:
            target_id = xxhq_id
    for i in mbl:
        if int(i['user_id']) == cf_id:
            target_id = cf_id
    if target_id != 0:
        await acexplode.send(Message(f"[CQ:at,qq={str(target_id)}] 开空调"))
        await asyncio.sleep(.5)
        await acexplode.finish(Message(f"[CQ:at,qq={str(target_id)}] 空调升温 {str(math.ceil((random.random()+.111)*900))}"))
    else:
        await acexplode.finish("此地无空调可炸，请不要再试了！")

group_poke_rank = on_command("grouppokerank", aliases={"戳戳排行榜","群戳戳排行榜"}, priority=10, block=True)
@group_poke_rank.handle()
async def handle_function():
    bot = get_bot()
    thesorted = dict(sorted(misc_manager.misc_data["group_poke_count"].items(), key=lambda x: x[1], reverse=True))
    first_10 = dict(tuple(thesorted.items())[:10])
    if not first_10:
        await group_poke_rank.finish("还没有戳戳数据呢！")
    # 收集群信息（名称 + 头像 URL）
    rank_data = []
    for gid, cnt in first_10.items():
        try:
            info = await bot.get_group_info(group_id=int(gid))
            name = info.get("group_name") or str(gid)
        except Exception:
            name = str(gid)
        name = truncate_text(name, 24, ellipsis="…")
        avatar_url = f"http://p.qlogo.cn/gh/{gid}/{gid}/100/"
        rank_data.append({"name": name, "count": cnt, "avatar": avatar_url})
    # 渲染图片
    await render_group_poke_rank(rank_data)
    await group_poke_rank.finish(Message(f'[CQ:image,file=file:///{path_manager.bf_path()}webss/1.png]'))


def _escape_html(text: str) -> str:
    if not text:
        return ""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


async def render_group_poke_rank(rank_data: list):
    """渲染群戳戳排行榜为图片。"""
    import os
    template_path = "web/templates/group_poke_rank/index.html"
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"模板文件不存在：{template_path}")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # 前三名：按 2-1-3 顺序排列（第1名居中且最大）
    top3_order = [1, 0, 2]  # 对应 rank_data 索引：第2、第1、第3
    top3_html = ""
    for idx_in_top3, data_idx in enumerate(top3_order):
        if data_idx >= len(rank_data):
            continue
        item = rank_data[data_idx]
        rank = data_idx + 1
        name = _escape_html(item["name"])
        count = item["count"]
        avatar = item["avatar"]
        top3_html += (
            f'<div class="podium-item">'
            f'<div class="avatar-wrap">'
            f'<span class="rank-badge">{rank}</span>'
            f'<img class="avatar avatar-{rank}" src="{avatar}" alt="" />'
            f'</div>'
            f'<div class="podium-name">{name}</div>'
            f'<div class="podium-count">{count}</div>'
            f'</div>'
        )

    # 第4名及以下：白色圆角卡片
    list_html = ""
    for i, item in enumerate(rank_data[3:], start=4):
        name = _escape_html(item["name"])
        count = item["count"]
        list_html += (
            f'<div class="row">'
            f'<div class="row-rank">{i}</div>'
            f'<div class="row-name">{name}</div>'
            f'<div class="row-count">{count}</div>'
            f'</div>'
        )

    html = template.replace(
        '<!-- TOP2 -->\n    <!-- TOP1 -->\n    <!-- TOP3 -->',
        top3_html
    ).replace("<!-- LIST_ROWS -->", list_html)
    web.change_content(html)
    await webss.take2("http://localhost:8104", "container")

# 文字截断代码（DeepSeek生成）
def get_display_width(text):
    """
    获取字符串的显示宽度（考虑中英文字符宽度差异）
    :param text: 输入字符串
    :return: 显示宽度
    """
    width = 0
    for char in text:
        # 根据Unicode字符宽度计算
        if unicodedata.east_asian_width(char) in ('F', 'W', 'A'):
            width += 2  # 全角字符占2个位置
        else:
            width += 1  # 半角字符占1个位置
    return width

def truncate_text(text, max_width, ellipsis="…"):
    """
    智能截断文本，考虑中英文字符宽度
    :param text: 原始文本
    :param max_width: 最大显示宽度
    :param ellipsis: 省略号字符
    :return: 截断后的文本
    """
    if get_display_width(text) <= max_width:
        return text
    
    result = ""
    current_width = 0
    ellipsis_width = get_display_width(ellipsis)
    
    for char in text:
        char_width = 2 if unicodedata.east_asian_width(char) in ('F', 'W', 'A') else 1
        
        # 检查是否还能放下这个字符+省略号
        if current_width + char_width + ellipsis_width > max_width:
            result += ellipsis
            break
        
        result += char
        current_width += char_width
    
    return result

def get_group_id(event):
    session = event.get_session_id().split("_")
    if session[0] == "group":
        return session[1]
    else:
        return "0"