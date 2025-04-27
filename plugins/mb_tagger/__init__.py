import tagger
import json

from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot import get_bot
from nonebot.exception import FinishedException
import feature_manager

tagger1 = on_command("添加标签", aliases={"tag","add"}, priority=10, block=True)
@tagger1.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("tag_1"):
        raise FinishedException
    bot = get_bot()
    tg_cm = args.extract_plain_text().split()
    res_msg = ""
    # 第一个参数是@群员
    if len(tg_cm) > 0 and args[0].type == 'at':
        res_msg = tagger.add_tag(args[0].data['qq'],tg_cm[0])
        rm_uname = tagger.get_nm(args[0].data['qq'])
        # 如果没有缓存的群员昵称
        if (rm_uname == ""):
            infos = dict(await bot.get_stranger_info(user_id=args[0].data['qq']))
            rm_uname = infos['nick']
            tagger.verify_nm(args[0].data['qq'],rm_uname)
        res_msg = res_msg.replace(args[0].data['qq'],rm_uname)
    # 第一个参数是昵称或数字
    elif len(tg_cm) > 1:
        tgw = tg_cm[0]
        if (tg_cm[0] == "你"):
            tgw = "我"
        if (tg_cm[0] == "我"):
            tgw = "你"
        res_msg = tagger.add_tag(tgw,tg_cm[1])
        # 如果第一个参数是数字，检查是否存在缓存的群员昵称
        if (str.isdigit(tgw)):
            potential_nam = tagger.get_nm(tgw)
            if potential_nam != "":
                res_msg = res_msg.replace(tgw,potential_nam)
    else:
        res_msg = "参数不够。使用方法：/tag [昵称/QQ号/@群成员] [要添加的标签名]"
    await tagger1.finish(res_msg)

tagger2 = on_command("删除标签", aliases={"del","rem"}, priority=10, block=True)
@tagger2.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("tag_1"):
        raise FinishedException
    bot = get_bot()
    tg_cm = args.extract_plain_text().split()
    res_msg = ""
    # 第一个参数是@群员
    if len(tg_cm) > 0 and args[0].type == 'at':
        res_msg = tagger.rem_tag(args[0].data['qq'],tg_cm[0])
        rm_uname = tagger.get_nm(args[0].data['qq'])
        # 如果没有缓存的群员昵称
        if (rm_uname == ""):
            infos = dict(await bot.get_stranger_info(user_id=args[0].data['qq']))
            rm_uname = infos['nick']
            tagger.verify_nm(args[0].data['qq'],rm_uname)
        res_msg = res_msg.replace(args[0].data['qq'],rm_uname)
    # 第一个参数是昵称或数字
    elif len(tg_cm) > 1:
        tgw = tg_cm[0]
        if (tg_cm[0] == "你"):
            tgw = "我"
        if (tg_cm[0] == "我"):
            tgw = "你"
        res_msg = tagger.rem_tag(tgw,tg_cm[1])
        # 如果第一个参数是数字，检查是否存在缓存的群员昵称
        if (str.isdigit(tgw)):
            potential_nam = tagger.get_nm(tgw)
            if potential_nam != "":
                res_msg = res_msg.replace(tgw,potential_nam)
    else:
        res_msg = "参数不够。使用方法：/del [昵称/QQ号/@群成员] [要删除的标签名]"
    await tagger2.finish(res_msg)

tagger3 = on_command("查看标签", aliases={"que","查看","look","lookup","展示标签"}, priority=10, block=True)
@tagger3.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("tag_2"):
        raise FinishedException
    bot = get_bot()
    # 第一个参数是@群员
    if len(args) > 0 and args[0].type == 'at':
        res_msg = tagger.que_tag(args[0].data['qq'])
        # res_msg = res_msg.replace(args[0].data['qq'],args[0].data['name'])
        # res_msg = res_msg.replace(args[0].data['qq'],"[CQ:at,qq="+args[0].data['qq']+"]")
        rm_uname = tagger.get_nm(args[0].data['qq'])
        # 如果没有缓存的群员昵称
        if (rm_uname == ""):
            infos = dict(await bot.get_stranger_info(user_id=args[0].data['qq']))
            rm_uname = infos['nick']
            tagger.verify_nm(args[0].data['qq'],rm_uname)
        res_msg = res_msg.replace(args[0].data['qq'],rm_uname)
    # 第一个参数是昵称或数字
    elif len(args) > 0:
        tg_cm = args.extract_plain_text().split()
        tgw = tg_cm[0]
        if (tg_cm[0] == "你"):
            tgw = "我"
        if (tg_cm[0] == "我"):
            tgw = "你"
        res_msg = tagger.que_tag(tgw)
        # 如果第一个参数是数字
        if (str.isdigit(tgw)):
            # 如果指定了 /getname 参数（强制重新获取群员昵称）
            if len(tg_cm) > 1 and tg_cm[1] == '/getname':
                infos = dict(await bot.get_stranger_info(user_id=tgw))
                uname = infos['nick']
                tagger.verify_nm(tgw,uname)
                res_msg = res_msg.replace(tgw,uname)
            # 未指定 /getname，则检查是否存在缓存的群员昵称
            else:
                potential_nam = tagger.get_nm(tgw)
                if potential_nam != "":
                    res_msg = res_msg.replace(tgw,potential_nam)
    else:
        res_msg = "参数不够。使用方法：/que [要查看标签的昵称/QQ号/@群成员]"
    await tagger3.finish(res_msg)