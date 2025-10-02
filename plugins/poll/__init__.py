from nonebot import on_command
from nonebot import on_keyword
from nonebot import get_bot
from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
import random
import asyncio
import httpx
from nonebot.exception import FinishedException
import feature_manager
import path_manager
import img_process
import achievement_manager
import json
import time

poll_file = open("json/poll.json","r",encoding="utf-8")
poll_list_raw = poll_file.read()
poll_file.close()
poll_list = json.loads(poll_list_raw)['poll']

def writeback():
    file = open("json/poll.json","w",encoding="utf-8")
    json.dump({'poll':poll_list},file,ensure_ascii=False,sort_keys=True)

poll = on_command("poll", aliases={"发起投票","createpoll"}, priority=10, block=True)
@poll.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("poll"):
        raise FinishedException
    params = args.extract_plain_text().split()
    if (len(params) < 1):
        await poll.finish("参数错误。用法：/poll [投票标题] [选项1] [选项2]")
    elif (len(params) < 3):
        await poll.finish("请提供至少两个投票选项！")
    elif (len(params) < 12):
        title = params[0]
        params.remove(title)
        options = {}
        for i in params:
            options[params.index(i)] = i
        qqid = event.get_user_id()
        result = await createpoll(title,qqid,options)
        await poll.finish("已创建投票。回复 /viewpoll "+str(result)+" 查看该投票。")
    else:
        await poll.finish("投票选项太多了！请减少到10个选项以内。")

async def createpoll(title,qqid,options):
    polllength = len(poll_list)
    pollid = str(polllength)
    poll_create = int(time.time())
    poll_expiry = poll_create + 24*3600
    polljson = {"title":title,"qq":qqid,"create":poll_create,"expiry":poll_expiry,"options":options,"polldata":{}}
    poll_list[pollid] = polljson
    writeback()
    return pollid

def getpolldata(pollid_or_title):
    # 初始化“被指定的投票项目”
    thepoll = {}
    polnum = -1
    # 判断是ID还是标题
    if str.isdigit(pollid_or_title):
        if pollid_or_title in poll_list:
            thepoll = poll_list[pollid_or_title]
            polnum = pollid_or_title
        else:
            return [{},-1]
    else:
        for i in poll_list:
            if poll_list[i]["title"] == pollid_or_title:
                thepoll = poll_list[i]
                polnum = i
                break
        if polnum == -1:
            return [{},-1]
    return [thepoll,polnum]
    
viewpoll = on_command("viewpoll", aliases={"查看投票"}, priority=10, block=True)
@viewpoll.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("poll"):
        raise FinishedException
    params = args.extract_plain_text().split()
    if (len(params) < 1):
        await viewpoll.finish("请指定投票ID或标题！。用法：/viewpoll [投票ID/标题]")
    else:
        # 参数，投票ID或者标题
        # pollid_or_title = params[0]
        polldata = getpolldata(params[0])
        # 被指定的投票项目
        thepoll = polldata[0]
        polnum = polldata[1]
        if polnum == -1:
            await viewpoll.finish("该投票不存在！")
        # 检查投票是否已结束
        pollended = 0
        if time.time() > thepoll["expiry"]:
            pollended = 1
        # 回复内容
        reply = "投票："+thepoll["title"]+" [ID: "+str(polnum)+"]"
        # 如果投票已结束
        if pollended:
            for i in thepoll["options"]:
                reply += "\n"
                # 检查该选项是否有人投票
                if i in thepoll["polldata"]:
                    reply += "["+str(len(thepoll["polldata"][i]))+" 票]"
                else:
                    reply += "[0 票]"
                reply += " "+thepoll["options"][i]
            reply += "\n\n此投票已结束。"
        else:
            for i in thepoll["options"]:
                reply += "\n"
                reply += "- "+thepoll["options"][i]
            # reply += "\n\n小提示：向bot私聊发送 /viewpoll "+str(polnum)+" 可查看已投票数哦！"
            reply += "\n\n发送 /vote "+str(polnum)+" [选项文本] 即可参与投票！"
        await viewpoll.finish(reply)

async def pollvote(polnum,optionnum,qqnum):
    optiond = poll_list[polnum]["polldata"]
    if optionnum not in optiond:
        poll_list[polnum]["polldata"][optionnum] = []
    poll_list[polnum]["polldata"][optionnum].append(qqnum)
    writeback()
    return

vote = on_command("vote", aliases={"投票","参与投票"}, priority=10, block=True)
@vote.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("poll"):
        raise FinishedException
    params = args.extract_plain_text().split()
    if (len(params) < 2):
        await vote.finish("参数错误。用法：/vote [投票ID/标题] [选项文本]")
    else:
        polldata = getpolldata(params[0])
        # 被指定的投票项目
        thepoll = polldata[0]
        polnum = polldata[1]
        if polnum == -1:
            await viewpoll.finish("没有找到这个投票！")
        # thepolldata = thepoll["polldata"]
        # 查找对应的投票项
        optionnum = -1
        for i in thepoll["options"]:
            if params[1] == thepoll["options"][i]:
                optionnum = i
                break
        if optionnum == -1:
            reply = "此投票里面没有这一项！可用的选项有："
            for i in thepoll["options"]:
                reply += "\n"
                reply += "- "+thepoll["options"][i]
            await viewpoll.finish(reply)
        # 检查是否符合投票条件（该qq号是否已参与过投票、投票是否过期）
        if time.time() > thepoll["expiry"]:
            await viewpoll.finish("此投票已经结束！请发送 /viewpoll "+polnum+" 查看结果。")
        if str(event.get_user_id()) in str(thepoll["polldata"]):
            await viewpoll.finish("你已参与过此投票！请在投票结束后发送 /viewpoll "+polnum+" 查看结果。")
        # 写入项目
        await pollvote(polnum,optionnum,event.get_user_id())
        await viewpoll.finish("投票成功！你投给了 "+params[1])