from nonebot import on_command
from nonebot.params import CommandArg
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import feature_manager
import privilege_manager
import path_manager
import json
import math
import web, webss
import aiohttp
import achievement_manager
import shutil
import plugins.actual_deepseek

async def getb50data(info):
    if ("qq" in info and info["qq"] == "3978644480") or ("username" in info and info["username"] == "testpilot"):
        with open("web/templates/maimai_b50/example/df_exa.json","r",encoding="utf-8") as f:
            example = f.read()
            return json.loads(example)
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
            return int(data["rating"])
        # 直接获取json原始数据，不做进一步解析（AI锐评b50用）
        if qtype == "json":
            return data
        
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

def fakeap50():
    file = open("web/templates/maimai_b50/df_data.json","r",encoding="utf-8")
    list_raw = file.read()
    file.close()
    list = json.loads(list_raw)
    charts = list["charts"]
    newdxs = 0
    for i in charts["dx"]:
        i["achievements"] = 101.0000
        i["fc"] = "app"
        i["rate"] = "sssp"
        i["ra"] = int(float(i["ds"])*22.5)
        newdxs += i["ra"]
    charts["dx"].sort(key=lambda x:x["ra"],reverse = True)
    for i in charts["sd"]:
        i["achievements"] = 101.0000
        i["fc"] = "app"
        i["rate"] = "sssp"
        i["ra"] = int(float(i["ds"])*22.5)
        newdxs += i["ra"]
    charts["sd"].sort(key=lambda x:x["ra"],reverse = True)
    list["charts"] = charts
    list["rating"] = newdxs
    file2 = open("web/templates/maimai_b50/df_data.json","w",encoding="utf-8")
    json.dump(list,file2,ensure_ascii=False,sort_keys=True)

# 根据二人的 QQ 号查询b50重合度
async def getb50overlaplist(qqid_1,qqid_2):
    data1 = await getb50data({"qq": qqid_1,"b50": True})
    data2 = await getb50data({"qq": qqid_2,"b50": True})
    # 有数据查询不到
    if type(data1) != dict or type(data2) != dict:
        return -1
    data1_b35 = data1["charts"]["sd"]
    data1_b15 = data1["charts"]["dx"]
    data2_b35 = data2["charts"]["sd"]
    data2_b15 = data2["charts"]["dx"]
    b35_overlap = listoverlapquery(data1_b35,data2_b35)
    b15_overlap = listoverlapquery(data1_b15,data2_b15)
    # 统计重合铺面数量和平均达成率
    b35_ol_count = len(b35_overlap)
    b35_ol_rate_diff = 0
    b35_ol_song_list = []
    if (b35_ol_count > 0):
        for i in b35_overlap:
            b35_ol_rate_diff += i["achievements_1"] - i["achievements_2"]
            b35_ol_song_list.append({"title": i["title"], "type": i["type"], "level_label": i["level_label"]})
        b35_ol_rate_diff = round(b35_ol_rate_diff/b35_ol_count,2)
    b15_ol_count = len(b15_overlap)
    b15_ol_rate_diff = 0
    b15_ol_song_list = []
    if (b15_ol_count > 0):
        for i in b15_overlap:
            b15_ol_rate_diff += i["achievements_1"] - i["achievements_2"]
            b15_ol_song_list.append({"title": i["title"], "type": i["type"], "level_label": i["level_label"]})
        b15_ol_rate_diff = round(b15_ol_rate_diff/b15_ol_count,2)
    # 返回值：b35重合铺面数量，b35平均达成率差值，b15重合铺面数量，b15平均达成率差值，b35重合歌曲列表，b15重合歌曲列表
    return [b35_ol_count,b35_ol_rate_diff,b15_ol_count,b15_ol_rate_diff,b35_ol_song_list,b15_ol_song_list]

def listoverlapquery(list1,list2):
    overlap_list = []
    for i in list1:
        for j in list2:
            if j["song_id"] == i["song_id"] and j["level_index"] == i["level_index"]:
                overlap_list.append({"title": i["title"], "type": i["type"], "level_label": i["level_label"], "song_id": i["song_id"], "ds": i["ds"], "level_index": i["level_index"], "achievements_1": i["achievements"], "achievements_2": j["achievements"], "ra_1": i["ra"], "ra_2": j["ra"]})
    return overlap_list


b50 = on_command("b50", priority=10, block=True)
@b50.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("maimai"):
        raise FinishedException
    # await b50.finish("awmc！抱歉，阁下不能帮你查b50，请另请高明吧！")
    val = await qddata_pre(args,event,"list")
    if (isinstance(val,int)):
        file = open("web/templates/maimai_b50/index.html","r",encoding="utf-8")
        web.content = file.read()
        file.close()
        web.writehtml()
        await webss.take2("http://localhost:8104/","container")
        # 查自己并且底分大于1w
        if (len(args) == 0 and val > 10000):
            await achievement_manager.add(2,event)
        await b50.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))
    else:
        await b50.finish(val)

dxra = on_command("dxra", aliases={"rating"}, priority=10, block=True)
@dxra.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("maimai"):
        raise FinishedException
    #await achievement_manager.add(2,event)
    result = await qddata_pre(args,event,"dxra")
    await dxra.finish(result)

dxdv = on_command("dxdv", aliases={"锐评b50","cb50","b50dv","b50方差"}, priority=10, block=True)
@dxdv.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("maimai"):
        raise FinishedException
    result = await qddata_pre(args,event,"dxdv")
    await dxdv.finish(result)

ap50 = on_command("ap50", priority=10, block=True)
@ap50.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("maimai"):
        raise FinishedException
    val = await qddata_pre(args,event,"list")
    if (isinstance(val,int)):
        file = open("web/templates/maimai_b50/index.html","r",encoding="utf-8")
        web.content = file.read()
        file.close()
        web.writehtml()
        fakeap50()
        await webss.take2("http://localhost:8104/","container")
        await ap50.send(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))
        await ap50.finish("*本bot生成的ap50与其他bot的不同，是由b50所有成绩换成ap+重新计算得到。")
    else:
        await ap50.finish(val)

b50_styles = ["testpilot","prism"]

b50stysw = on_command("bstyle", aliases={"b50样式"}, priority=10, block=True)
@b50stysw.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("maimai"):
        raise FinishedException
    style = args.extract_plain_text()
    if style in b50_styles:
        shutil.copy("web/templates/maimai_b50/"+style+"/index.html","web/templates/maimai_b50/index.html")
        await b50stysw.finish("已将 b50 图表样式设置为："+style)
    else:
        await b50stysw.finish("参数错误。可用的 b50 图表样式有："+"、".join(b50_styles))

boverlap = on_command("boverlap", aliases={"b50重合"}, priority=10, block=True)
@boverlap.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("maimai"):
        raise FinishedException
    qqnum1 = 0
    qqnum2 = 0
    # 用户给定了参数
    if len(args) > 0:
        # 用户给定一个参数
        if len(args) == 1 and len(args.extract_plain_text().split()) == 1:
            # 第一个QQ号使用发起指令者的
            qqnum1 = event.get_user_id()
            # 第一个参数是@群员
            if args[0].type == 'at':
                qqnum2 = args[0].data['qq']
            # 第一个参数是QQ号
            elif str.isdigit(args.extract_plain_text().split()[0]):
                qqnum2 = args.extract_plain_text().split()[0]
            # 第一个参数不是@也不是数字（重合度不考虑用户名查询）
            # else:
        # 用户给定2个以上参数
        if len(args) > 1 or len(args.extract_plain_text().split()) > 1:
            # 前两个参数都是@群员
            print(args,len(args))
            if args[0].type == 'at' and args[1].type == 'at':
                qqnum1 = args[0].data['qq']
                qqnum2 = args[1].data['qq']
            # 两个@中间存在空格
            elif args[0].type == 'at' and args[2].type == 'at':
                qqnum1 = args[0].data['qq']
                qqnum2 = args[2].data['qq']
            # 前两个参数都是QQ号
            elif str.isdigit(args.extract_plain_text().split()[0]) and str.isdigit(args.extract_plain_text().split()[1]):
                qqnum1 = args.extract_plain_text().split()[0]
                qqnum2 = args.extract_plain_text().split()[1]
            # 不考虑其他情况
            # else:
    if qqnum1 != 0 and qqnum2 != 0:
        bot = get_bot()
        # 获取两人QQ昵称
        qqnam1 = dict(await bot.get_stranger_info(user_id=qqnum1))["nick"]
        qqnam2 = dict(await bot.get_stranger_info(user_id=qqnum2))["nick"]
        result = await getb50overlaplist(qqnum1,qqnum2)
        comment = ""
        # 查询失败
        if type(result) != list:
            await boverlap.finish("查询失败！你提供的至少其中一个QQ号无法查询到游戏数据！")
        # b35
        if (result[0] > 0):
            comment += qqnam1+" 和 "+qqnam2+" 的b35中，有 "+str(result[0])+" 张重合的谱面，\n在这些铺面中，"+qqnam1+" 的平均达成率比 "+qqnam2
            if (result[1] > 0):
                comment += " 高 "+str(result[1])+" %。"
            else:
                comment += " 低 "+str(-result[1])+" %。"
            comment += "\n重合的谱面有：\n"
            for i in result[4]:
                comment += ""+i["title"]+" ["+i["type"]+"] "" ["+i["level_label"]+"] \n"
        else:
            comment += qqnam1+" 和 "+qqnam2+" 的b35没有一张谱面重合！\n"
        # b15
        if (result[2] > 0):
            comment += "\n"+qqnam1+" 和 "+qqnam2+" 的b15中，有 "+str(result[2])+" 张重合的谱面，\n在这些铺面中，"+qqnam1+" 的平均达成率比 "+qqnam2
            if (result[3] > 0):
                comment += " 高 "+str(result[3])+" %。"
            else:
                comment += " 低 "+str(-result[3])+" %。"
            comment += "\n重合的谱面有："
            for i in result[5]:
                comment += "\n"+i["title"]+" ["+i["type"]+"] "" ["+i["level_label"]+"]"
        else:
            comment += "\n"+qqnam1+" 和 "+qqnam2+" 的b15没有一张谱面重合！"
        await boverlap.finish(comment)
    # 用户未给定参数或参数不正确（如果成功查询，则提前finish，不执行到这一步）。
    await boverlap.finish("参数错误。用法：/boverlap [要查询的QQ号/@群成员1] [要查询的QQ号/@群成员2]")
    
aib50 = on_command("aib50", aliases={"dsb50","ai锐评b50","AI锐评b50"}, priority=10, block=True)
@aib50.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if (not feature_manager.get("maimai")) or (not feature_manager.get("deepseek")):
        raise FinishedException
    result = await qddata_pre(args,event,"json")
    if type(result) != dict:
        await aib50.finish("没有查询到玩家数据！")
    web.content_md(await plugins.actual_deepseek.ds_b50(result))
    await webss.take2("http://localhost:8104","container")
    await aib50.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))