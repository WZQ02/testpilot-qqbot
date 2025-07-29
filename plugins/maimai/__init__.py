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
import aiohttp

async def getb50data(info):
    async with aiohttp.request("POST", "https://www.diving-fish.com/api/maimaidxprober/query/player", json=info) as resp:
        if resp.status == 400:
            return 400
        if resp.status == 403:
            return 403
        data = await resp.json()
        return data

async def qddata_pre(args,event,type):
    qqnum = 0
    uname = ""
    result = ""
    self_flag = True
    # 用户给定了参数
    if len(args) > 0:
        # 第一个参数是@群员
        if args[0].type == 'at':
            qqnum = args[0].data['qq']
        # 第一个参数是QQ号
        elif str.isdigit(args.extract_plain_text().split()[0]):
            qqnum = args.extract_plain_text().split()[0]
        # 第一个参数不是数字而是username
        else:
            uname = args.extract_plain_text().split()[0]
        self_flag = False
    # 用户未给定参数，使用发起指令者QQ号查询
    else:
        qqnum = event.get_user_id()
    result = await quedfdata(qqnum,type,uname,self_flag)
    return result

async def quedfdata(qqid,qtype,uname,iself):
    # 发起查询
    data = ""
    if qqid != 0:
        data = await getb50data({"qq": qqid,"b50": True})
    else:
        data = await getb50data({"username": uname,"b50": True})
    callt = "此人"
    if iself:
        callt = "你"
    if type(data) != dict:
        return "无法查询到"+callt+"的乌蒙地艾克斯游戏数据！"
    else:
        if qtype == "dxra":
            return callt+"有 "+str(data["rating"])+" 底分"
        if qtype == "dxdv":
            calcd = dxdvcalc(data)
            #return callt+"有 "+str(data["rating"])+" 哥度。\n其中，在「抓小哥DX」新增猎场，"+callt+"抓到过最好的 15 个小哥平均为"+callt+"贡献了 "+str(calcd[0])+" 哥度，方差为 "+str(calcd[1])+"；在「抓小哥DX」旧有猎场，"+callt+"抓到过最好的 35 个小哥平均为"+callt+"贡献了 "+str(calcd[2])+" 哥度，方差为 "+str(calcd[3])+"。"
            return callt+"的b35方差："+str(calcd[0])+"\n"+callt+"的b15方差："+str(calcd[1])+"\n歌曲平均达成率："+calcd[2]+"\n\n评价："+calcd[3].replace("你",callt)
        if qtype == "list":
            # 写入获取的json到文件
            file = open("web/templates/maimai_b50/df_data.json","w",encoding="utf-8")
            json.dump(data,file,ensure_ascii=False)
            return 0
        
def dxdvcalc(json):
    b15avg = 0
    b15dv = 0
    b35avg = 0
    b35dv = 0
    avgcomp = 0
    b15data = json["charts"]["dx"]
    b35data = json["charts"]["sd"]
    b50data = b15data+b35data
    for i in b15data:
        b15avg += i["ra"]/15
    for i in b35data:
        b35avg += i["ra"]/35
    for i in b15data:
        b15dv += pow((i["ra"]-b15avg),2)/15
    for i in b35data:
        b35dv += pow((i["ra"]-b35avg),2)/15
    for i in b50data:
        avgcomp += i["achievements"]/len(b50data)
    comment = ""
    if (len(b35data) < 20):
        comment = "你好像总共就没打几首歌啊？多打一些歌再来找我评价吧。。。"
    else:
        if (b35dv < 50):
            comment = "你的b35太平淡了，像一滩死水，每首歌的ra都差不多高，就跟大多数玩拍拍机的牢玩家一样，没意思！"
            if (len(b15data) < 2):
                comment += "\n等等，你的b15怎么是空的？看来你比较怀旧，不喜欢打新歌哦？"
            elif (b15dv < 80):
                comment += "\n你的b15也差不多，每首歌都很均衡，无聊无聊无聊，下一位！"
            else:
                comment += "\n但你的b15分数波动有点大，看来你新歌打的不是很多？"
        elif (b35dv < 150):
            comment = "你的b50高低分成绩相差不小，有一些波动，看起来像是一个处于稳步上升期的玩家，再接再励哦！"
        elif (b35dv < 500):
            comment = "你的b50成绩波动的简直像过山车！高的很高低的很低，上升空间还很大哦！"
        else:
            comment = "你的b50高低分相差的就nm离谱！请问你是刚入坑的新人玩家吗？"
        if (avgcomp > 100.25):
            comment += "\n而且，你每首歌的达成率几乎都超过100，玩的太认真了吧！偶尔试着越点级也行的哦？"
        elif (avgcomp < 97):
            comment += "\n你的歌曲平均达成率不到97，可以！哥就喜欢你这样勇猛上前越大级的玩家，不要在意机厅里别人的目光！"
    #b15avg = round(b15avg,1)
    b15dv = round(b15dv,2)
    #b35avg = round(b35avg,1)
    b35dv = round(b35dv,2)
    avgcomp = str(round(avgcomp,4))+"%"
    #return [b15avg,b15dv,b35avg,b35dv]
    return [b35dv,b15dv,avgcomp,comment]

b50 = on_command("b50", priority=10, block=True)
@b50.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("maimai"):
        raise FinishedException
    # await b50.finish("awmc！抱歉，阁下不能帮你查b50，请另请高明吧！")
    val = await qddata_pre(args,event,"list")
    if (val == 0):
        file = open("web/templates/maimai_b50/index.html","r",encoding="utf-8")
        web.content = file.read()
        file.close()
        web.writehtml()
        webss.take2("http://localhost:8104/","container")
        await dxra.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))
    else:
        await dxra.finish(val)

dxra = on_command("dxra", aliases={"rating"}, priority=10, block=True)
@dxra.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("maimai"):
        raise FinishedException
    result = await qddata_pre(args,event,"dxra")
    await dxra.finish(result)

dxdv = on_command("dxdv", aliases={"锐评b50","cb50","b50dv","b50方差"}, priority=10, block=True)
@dxdv.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("maimai"):
        raise FinishedException
    result = await qddata_pre(args,event,"dxdv")
    await dxdv.finish(result)
    