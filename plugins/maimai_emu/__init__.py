from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import feature_manager
import path_manager
import asyncio
import plugins.maimai
import misc_manager
import random

bot_mai_status = 0 # -1死机，-2爆炸
current_difficulty = 0 # 大于0
track_count = 0

async def get_rating(qq):
    ra = await plugins.maimai.quedfdata(qq,"list","",0)
    if (not isinstance(ra,int) or ra < 4000):
        ra = 4000
    return ra

def parse_difficulty(str):
    plus = 0
    if str[-1] == "+":
        str = str[0:-1]
        plus = 0.8
    if str.isdigit():
        return float(str)+plus
    else:
        return -1
    
def getrank(ac):
    if ac < 50:
        return "D"
    elif ac < 60:
        return "C"
    elif ac < 70:
        return "B"
    elif ac < 75:
        return "BB"
    elif ac < 80:
        return "BBB"
    elif ac < 90:
        return "A"
    elif ac < 94:
        return "AA"
    elif ac < 97:
        return "AAA"
    elif ac < 98:
        return "S"
    elif ac < 99:
        return "S+"
    elif ac < 99.5:
        return "SS"
    elif ac < 100:
        return "SS+"
    elif ac < 100.5:
        return "SSS"
    else:
        return "SSS+"

def getfc(ac):
    if ac < 100:
        return ""
    elif ac < 100.5:
        return "full combo！"
    elif ac < 100.9:
        return "full combo+！"
    else:
        return "all perfect！"
    
async def calc_achievement(qq):
    ra = await get_rating(qq)
    global bot_mai_status
    if current_difficulty > 100:
        bot_mai_status = -2
        return -100
    min = (2+current_difficulty/10)**(current_difficulty-(ra/1000)+1)
    max = (3+current_difficulty/10)**(current_difficulty-(ra/1000)+1)
    ac = 101-random.uniform(min,max)
    if ac <= 0:
        bot_mai_status = -2
    elif ac < 80:
        mai_explos_poss = 1-0.98**(80-ac)
        if random.random() < mai_explos_poss:
            bot_mai_status = -2
    return ac

def stress():
    mai_bsod_poss = 1-0.8**(current_difficulty-15)
    global bot_mai_status
    if random.random() < mai_bsod_poss:
        bot_mai_status = -1

play_mai1 = on_command("出勤", aliases={"打舞萌","我要打舞萌","我要打乌蒙","我要打mai"}, priority=10, block=True)
@play_mai1.handle()
async def handle_function(event: Event = Event):
    if not feature_manager.get("maimai_emu"):
        raise FinishedException
    global bot_mai_status
    if (bot_mai_status >= 0):
        bot_mai_status = 1
        qqid = event.get_user_id()
        if qqid in misc_manager.misc_data["bot_mai_noti_list"]:
            expl_count = misc_manager.misc_data["mai_expl_count"][qqid]
            if expl_count >= 20:
                await play_mai1.send(Message(f"[CQ:at,qq={qqid}] 你已经炸掉了本市{str(expl_count)}个机厅的舞萌dx。\n因为造成的经济损失过多，你已经被全市通缉。\n你随时可能在下一次出勤时候被就地伏法。\n祝你好运！"))
            elif expl_count >= 10:
                await play_mai1.send(Message(f"[CQ:at,qq={qqid}] 你已经炸掉了本市{str(expl_count)}个机厅的舞萌dx。\n现在，你除了被越来越多的机厅老板盯上，一些原本在你去过的机厅打舞萌的玩家，因为你把机台搞炸玩不成了！现在，有一群地雷女玩家开始调查你的行踪，并准备在你去的下一家机厅对你改花刀。\n一定要保护好自己哦！"))
            elif expl_count >= 5:
                await play_mai1.send(Message(f"[CQ:at,qq={qqid}] 你已经炸掉了本市{str(expl_count)}个机厅的舞萌dx。\n每次你玩炸机器后，你没有向机厅老板赔偿损失，而是逃离到下一家，继续游戏。\n现在，这几家机厅的老板已经打听到了你的身份，要在你可能前往的下一个机厅对你围堵追截，把你暗杀掉。\n为了防止被追杀，以后请不要在同一个机厅出勤太多次哦！"))
            misc_manager.misc_data["bot_mai_noti_list"].remove(qqid)
            misc_manager.writeback()
        await play_mai1.send(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/bot_mai/cab_start.webp,sub_type=1]'))
        await play_mai1.send("要开始了哟！")
        await asyncio.sleep(.5)
        await play_mai1.finish("请选择难度！")
    else:
        imgname = "cab_exploded"
        if bot_mai_status == -1:
            imgname = "cab_bsod"
        await play_mai1.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/bot_mai/'+imgname+'.webp,sub_type=1]'))

play_mai2 = on_command("选择难度", priority=10, block=True)
@play_mai2.handle()
async def handle_function(args: Message = CommandArg()):
    global bot_mai_status, current_difficulty
    if not feature_manager.get("maimai_emu") or bot_mai_status < 1:
        raise FinishedException
    current_difficulty = parse_difficulty(args.extract_plain_text())
    if current_difficulty > 0:
        bot_mai_status = 2
        await play_mai2.finish("准备好的话就开始吧！")
    else:
        await play_mai2.finish("没有这个难度哦！请重新选择")
    
play_mai3 = on_command("开始游戏", priority=10, block=True)
@play_mai3.handle()
async def handle_function(event: Event = Event):
    global bot_mai_status, current_difficulty, track_count
    if not feature_manager.get("maimai_emu") or bot_mai_status < 1:
        raise FinishedException
    if bot_mai_status == 1:
        await play_mai3.finish("你还没选择难度！")
    qqid = event.get_user_id()
    stress()
    ac = await calc_achievement(qqid)
    rank = getrank(ac)
    fc = getfc(ac)
    ac = round(ac,4)
    current_difficulty = 0
    if bot_mai_status == -2:
        if (qqid in misc_manager.misc_data["mai_expl_count"]):
            misc_manager.misc_data["mai_expl_count"][qqid] += 1
        else:
            misc_manager.misc_data["mai_expl_count"][qqid] = 1
        misc_manager.writeback()
        await play_mai2.send(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/bot_mai/explosion.gif,sub_type=1]'))
        await play_mai2.finish(Message(f"[CQ:at,qq={qqid}] 谱子太难了！你越级拆机，把机台拆炸了！"))
    elif bot_mai_status == -1:
        await play_mai2.send(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/bot_mai/cab_bsod.webp,sub_type=1]'))
        await play_mai2.finish(Message(f"[CQ:at,qq={qqid}] 你选择的难度太高，机台承受不住死机了！"))
    else:
        track_count += 1
        if ac <= 80:
            await play_mai3.send(Message(f"[CQ:at,qq={qqid}] 你没有通关！rank {rank} ，达成率 {ac}%"))
        else:
            await play_mai3.send(Message(f"[CQ:at,qq={qqid}] rank {rank} clear！达成率 {ac}%！{fc}通关啦！"))
        if (track_count >= 4):
            bot_mai_status = 0
            await asyncio.sleep(5)
            track_count = 0
            await play_mai3.finish(f"游戏结束！下次再见！")
        else:
            bot_mai_status = 1
            await asyncio.sleep(5)
            await play_mai3.finish(f"下一首！请选择难度！")

call_help = on_command("召唤机修", priority=10, block=True)
@call_help.handle()
async def handle_function():
    if not feature_manager.get("maimai_emu"):
        raise FinishedException
    global bot_mai_status
    if bot_mai_status >= 0:
        await call_help.finish(f"你把机修叫来了，机台没问题，机修不知所措。。。")
    elif bot_mai_status == -1:
        bot_mai_status = 0
        await call_help.send(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/bot_mai/cab_home.webp,sub_type=1]'))
        await call_help.finish(f"你把机修叫来了，机修帮你重启了机器，机台恢复啦！")
    elif bot_mai_status == -2:
        await call_help.send(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/bot_mai/cab_exploded.webp,sub_type=1]'))
        await call_help.finish(f"你把机修叫来了，机修看到机台惨状，被吓跑了！")

runaway = on_command("更换机厅", priority=10, block=True)
@runaway.handle()
async def handle_function():
    if not feature_manager.get("maimai_emu"):
        raise FinishedException
    global bot_mai_status
    bot_mai_status = 1
    await runaway.send(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/bot_mai/cab_home.webp,sub_type=1]'))
    await runaway.finish(f"你来到了新的机厅！发送 /出勤 开始游戏吧！")

explos_his = on_command("炸机记录", aliases={"舞萌炸炸记录"}, priority=10, block=True)
@explos_his.handle()
async def handle_function(event: Event = Event):
    if not feature_manager.get("maimai_emu"):
        raise FinishedException
    qqid = event.get_user_id()
    if (qqid in misc_manager.misc_data["mai_expl_count"]):
        count = misc_manager.misc_data["mai_expl_count"][qqid]
        if count == 5 or count == 10 or count == 20:
            misc_manager.misc_data["bot_mai_noti_list"].append(qqid)
            misc_manager.writeback()
        await explos_his.finish(Message(f"[CQ:at,qq={qqid}] 你玩炸了{str(count)}个舞萌机台，累计经济损失{str(count*8)}万元！"))
    else:
        await explos_his.finish(Message(f"[CQ:at,qq={qqid}] 你没有炸掉任何一台舞萌dx！是不拆机的好孩子哦？"))