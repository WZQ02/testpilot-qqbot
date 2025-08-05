from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.params import CommandArg
from nonebot.exception import FinishedException
import feature_manager
import json
import achievement_manager

expl = on_command("expl", aliases={"名词解释","explain","meaning","什么意思"}, priority=10, block=True)
@expl.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("explain"):
        raise FinishedException
    await expl.finish(explain_word(args.extract_plain_text()))

admn = on_command("admn", aliases={"添加名词解释","添加含义","addmean"}, priority=10, block=True)
@admn.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("explain"):
        tg_cm = args.extract_plain_text().split()
        if len(tg_cm) > 1:
            if tg_cm[-1] == '/override':
                await achievement_manager.add(5,event)
                await admn.finish(add_explain(tg_cm[0],args.extract_plain_text().replace(tg_cm[0]+" ","",1).replace(" /override","",1),True))
            else:
                await admn.finish(add_explain(tg_cm[0],args.extract_plain_text().replace(tg_cm[0]+" ","",1),False))
        else:
            await admn.finish("参数不够。用法：/admn [名词] [要添加的名词解释]")
    else:
        raise FinishedException

expl_file = open("json/expl_list.json","r",encoding="utf-8")
expl_list_raw = expl_file.read()
expl_file.close()
expl_list = json.loads(expl_list_raw)['expl_list']

def explain_word(word):
    if word in expl_list:
        return expl_list[word]
    else:
        return "没有找到这个词的含义哦！"
    
def add_explain(word,meaning,override):
    if word in expl_list and not override:
        return "已为"+word+"添加名词解释。内容为“"+expl_list[word]+"”\n如需更改解释内容，请在末尾添加 /override 参数。"
    elif meaning:
        expl_list[word] = meaning
        writeback()
        return "为"+word+"添加了名词解释。内容为“"+meaning+"”"
    
def writeback():
    file = open("json/expl_list.json","w",encoding="utf-8")
    json.dump({'expl_list':expl_list},file,ensure_ascii=False,sort_keys=True)