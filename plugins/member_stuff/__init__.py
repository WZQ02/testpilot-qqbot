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
        group_id = event.get_session_id().split("_")[1]
        print(await bot.get_group_member_list(group_id=group_id))
    raise FinishedException
"""
bot_qq_id = 3978644480
lvstr_list = ["我喜欢你","我！爱！你！","！suki！拉布！嗨嗨！","齁哦哦哦哦哦哦哦","约吗？"]
lvstr_list2 = ["我喜欢你","爱你喵","我爱你","贴贴","你是一个小蛋糕","亲","宝宝","宝贝","宝宝你是一个甜甜糯糯的小蛋糕","揉你小肚肚~","摸摸头","摸摸","么么"]

randomcs = on_command("rdcs", aliases={"随机赤石","randomchishi","randomcs","随机吃屎","随机扔粑粑"}, priority=10, block=True)
@randomcs.handle()
async def handle_function(event: Event = Event):
    if feature_manager.get("randomcs"):
        bot = get_bot()
        group_id = event.get_session_id().split("_")[1]
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
    if feature_manager.get("randomcs"):
        bot = get_bot()
        group_id = event.get_session_id().split("_")[1]
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
    if feature_manager.get("randomcs"):
        bot = get_bot()
        group_id = event.get_session_id().split("_")[1]
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
async def handle_function():
    if not feature_manager.get("changesex"):
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
    if not feature_manager.get("meme_resp"):
        raise FinishedException
    bot = get_bot()
    group_id = event.get_session_id().split("_")[1]
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
    resp = "===== 群戳戳排行榜 ====="
    thesorted = dict(sorted(misc_manager.misc_data["group_poke_count"].items(), key=lambda x: x[1], reverse=True))
    first_10 = dict(tuple(thesorted.items())[:10])
    for i in first_10:
        info = await bot.get_group_info(group_id=i)
        name = info.get("group_name")
        """
        if get_display_width(name) > 12:
            name = name[0:11]+"..."
        """
        name = truncate_text(name, 24, ellipsis="…")
        resp += f"\n{name}      {str(first_10[i])}"
    await group_poke_rank.finish(resp)

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