from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.params import CommandArg
from nonebot import get_bot
from nonebot.exception import FinishedException
import msg_cache, feature_manager, path_manager
import re, json
import random
import plugins.poke_resp

start_character = ""
# 出现过的成语
noted_words = []

# 同步出现过的成语到misc.json
def sync():
    plugins.poke_resp.misc_data["jielong_noted_words"] = noted_words
    plugins.poke_resp.writeback()

autojielong = on_message(priority=10, block=True)
@autojielong.handle()
async def handle_function(event: Event = Event):
    if not feature_manager.get("autojie"):
        raise FinishedException
    # 检查消息是否由此方bot发起（如果是，则变更起始词语状态，并查找对于词语）
    if (int(event.get_user_id()) == 3928110595):
        # 检查消息格式
        msg = event.get_message().extract_plain_text()
        pattern = r"成语(.*)「([\u4e00-\u9fa5]+)」"
        match = re.search(pattern, msg)
        # 此方bot给出成语消息
        if match:
            global start_character
            start_character = match.group(2)[-1]
            print(f"起始字符为：{start_character}")
            # 开始搜索对应的成语
            avail_list = []
            for i in noted_words:
                if i[0] == start_character:
                    avail_list.append(i)
            # 如果存在匹配，随机抽取一个成语
            if len(avail_list) > 0:
                word = random.choice(avail_list)
                print(f"找到匹配词：{word}")
                # 一半的几率触发自动接龙（不是有匹配就一定会发）
                if random.random() < .5:
                    await autojielong.finish(word)
            else:
                print(f"未找到匹配的词语。")
        else:
            # 此方bot是否给出“接上了”提示
            pattern = r"接上了，(.*)"
            if re.search(pattern, msg):
                # 获取当前群聊id
                sid = event.get_session_id().split("_")
                if sid[0] == 'group':
                    groupid = sid[1]
                    # 从最近消息列表中寻找最后一个匹配的词语
                    cmlist = msg_cache.msglis[groupid]
                    word = ""
                    for i in cmlist:
                        if i.extract_plain_text()[0] == start_character:
                            word = i.extract_plain_text()
                    if len(word) > 0 and word not in noted_words:
                        noted_words.append(word)
                        sync()
                        print(f"记录接过的词语：{word}")
    raise FinishedException

clear_jielong_his = on_command("清空成语列表", priority=10, block=True)
@clear_jielong_his.handle()
async def handle_function():
    global noted_words
    noted_words = []
    sync()
    await clear_jielong_his.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/haoba.jpg,sub_type=1]'))