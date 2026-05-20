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
import misc_manager

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Union, Dict
from config_manager import ConfigManager

tokens_config = ConfigManager("json/tokens.json")
dfdev_tk = tokens_config.get("divinfish_dev_token")

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
    
async def getalldata(get_suffix):
    async def fetch(session, url, headers):
        async with session.get(url, headers=headers) as response:
            return await response.json()
    async with aiohttp.ClientSession() as session:
        url = f"https://www.diving-fish.com/api/maimaidxprober/dev/player/records{get_suffix}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json',
            'Developer-Token': dfdev_tk
        }
        data = await fetch(session, url, headers)
        print(data)
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
    if qtype != "all":
        if qqid != 0:
            data = await getb50data({"qq": qqid,"b50": True})
        else:
            data = await getb50data({"username": uname,"b50": True})
    else:
        if qqid != 0:
            data = await getalldata(f"?qq={qqid}")
        else:
            data = await getalldata(f"?username={uname}")
    callt = "此人"
    if iself:
        callt = "你"
    if type(data) != dict:
        return "无法查询到"+callt+"的乌蒙地艾克斯游戏数据！"
    else:
        if qtype == "dxra":
            return callt+"有 "+str(data["rating"])+" 底分"
        if qtype == "dxra_detailed":
            dxdt = getdxdt(data)
            return f"{callt}有 {dxdt[0]} ({dxdt[2]}+{dxdt[1]}) 底分"
        if qtype == "dxdv":
            calcd = dxdvcalc(data)
            return f'{callt}的b35方差：{str(calcd[0])}\n{callt}的b15方差：{str(calcd[1])}\n平均游玩等级：{calcd[4]}\n歌曲平均达成率：{calcd[2]}\n\n评价：{calcd[3].replace("你",callt)}'
        if qtype == "list":
            # 写入获取的json到文件
            file = open("web/templates/maimai_b50/df_data.json","w",encoding="utf-8")
            json.dump(data,file,ensure_ascii=False)
            return int(data["rating"])
        # 直接获取json原始数据，不做进一步解析（AI锐评b50用）
        if qtype == "json":
            return data
        # 获取全部游玩数据（写入文件并同时返回原始数据）
        if qtype == "all":
            # 写入获取的json到文件
            file = open("web/templates/maimai_b50/df_all.json","w",encoding="utf-8")
            json.dump(data,file,ensure_ascii=False)
            return data
        
def dxdvcalc(json):
    b15avg = 0
    b15dv = 0
    b35avg = 0
    b35dv = 0
    avgcomp = 0
    avglevel = 0
    b15data = json["charts"]["dx"]
    b35data = json["charts"]["sd"]
    b50data = b15data+b35data
    b15count = len(b15data)
    b35count = len(b35data)
    for i in b15data:
        b15avg += i["ra"]/b15count
    for i in b35data:
        b35avg += i["ra"]/b35count
    for i in b15data:
        b15dv += pow((i["ra"]-b15avg),2)/b15count
    for i in b35data:
        b35dv += pow((i["ra"]-b35avg),2)/b35count
    for i in b50data:
        avgcomp += i["achievements"]/len(b50data)
        avglevel += i["ds"]/len(b50data)
    comment = ""
    if (len(b35data) < 20):
        comment = "你好像总共就没打几首歌啊？多打一些歌再来找我评价吧，，，"
    else:
        if (b35dv < 30):
            comment = "你的b35太平淡了，每首歌的ra都差不多高，一看就是处于瓶颈期的拍拍机牢玩家了，真没意思呐~"
            if (len(b15data) < 2):
                comment += "\n等等，你的b15怎么是空的？看来你比较怀旧，不喜欢打新歌哦？"
            elif (b15dv < 50):
                comment += "\n你的b15也差不多，真让人提不起兴致呢。。。"
            else:
                comment += "\n但你的b15分数波动有点大，看来你新歌打的不是很多？"
        elif (b35dv < 120):
            comment = "你的b50高低分成绩相差不小，有一些波动，看起来像是一个处于稳步上升期的玩家，再接再励哦！"
        elif (b35dv < 400):
            comment = "你的b50成绩波动的简直像过山车！高的很高低的很低，上升空间还很大哦！"
        else:
            comment = "你的b50高低分相差的就nm离谱！请问你是刚入坑的新人玩家吗？"
        if (avgcomp > 100.6):
            comment += "\n你每首歌的达成率几乎都超过100.5，鸟加遍地，玩得好认真哦！好厉害！"
        elif (avgcomp > 99):
            comment += ""
        elif (avgcomp > 97):
            comment += "\n你的歌曲平均达成率不到99，可以考虑提升一下准度哦！"
        else:
            comment += "\n你的歌曲平均达成率不到97，哦？是连拍拍机都不会打的za~ ko~ 呐，杂鱼~杂鱼~"
    #b15avg = round(b15avg,1)
    b15dv = round(b15dv,2)
    #b35avg = round(b35avg,1)
    b35dv = round(b35dv,2)
    avgcomp = str(round(avgcomp,4))+"%"
    avglevel = round(avglevel,1)
    #return [b15avg,b15dv,b35avg,b35dv]
    return [b35dv,b15dv,avgcomp,comment,avglevel]

def getdxdt(json):
    b15add = 0
    b35add = 0
    b15data = json["charts"]["dx"]
    b35data = json["charts"]["sd"]
    for i in b15data:
        b15add += i["ra"]
    for i in b35data:
        b35add += i["ra"]
    return [b15add+b35add,b15add,b35add]

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
            b35_ol_song_list.append({"title": i["title"], "type": i["type"], "level_label": i["level_label"], "achievements": [i["achievements_1"],i["achievements_2"]]})
        b35_ol_rate_diff = round(b35_ol_rate_diff/b35_ol_count,2)
    b15_ol_count = len(b15_overlap)
    b15_ol_rate_diff = 0
    b15_ol_song_list = []
    if (b15_ol_count > 0):
        for i in b15_overlap:
            b15_ol_rate_diff += i["achievements_1"] - i["achievements_2"]
            b15_ol_song_list.append({"title": i["title"], "type": i["type"], "level_label": i["level_label"], "achievements": [i["achievements_1"],i["achievements_2"]]})
        b15_ol_rate_diff = round(b15_ol_rate_diff/b15_ol_count,2)
    # 返回值：b35重合铺面数量，b35平均达成率差值，b15重合铺面数量，b15平均达成率差值，b35重合歌曲列表，b15重合歌曲列表，玩家1数据，玩家2数据
    return [b35_ol_count,b35_ol_rate_diff,b15_ol_count,b15_ol_rate_diff,b35_ol_song_list,b15_ol_song_list,{"name": data1["nickname"], "rating": data1["rating"]},{"name": data2["nickname"], "rating": data2["rating"]}]

def listoverlapquery(list1,list2):
    overlap_list = []
    for i in list1:
        for j in list2:
            if j["song_id"] == i["song_id"] and j["level_index"] == i["level_index"]:
                overlap_list.append({"title": i["title"], "type": i["type"], "level_label": i["level_label"], "song_id": i["song_id"], "ds": i["ds"], "level_index": i["level_index"], "achievements_1": i["achievements"], "achievements_2": j["achievements"], "ra_1": i["ra"], "ra_2": j["ra"]})
    return overlap_list

# 生成散点图（代码AI写的）
class mai_sdt_gen:
    """
    全量程非线性缩放生成器。
    特性：全轴满足“数值越大，刻度越稀疏”，且自动对齐指定的中心点。
    """

    def __init__(self, data: Union[str, Dict]):
        # 基础参数设定
        self.ds_min, self.ds_max, self.ds_mid = 1.0, 15.0, 12.0
        self.ach_min, self.ach_max, self.ach_mid = 0.0, 101.0, 97.0
        
        # 自动计算指数 k，确保 mid 对应 0.5
        self.k_ds = np.log(0.5) / np.log((self.ds_mid - self.ds_min) / (self.ds_max - self.ds_min))
        self.k_ach = np.log(0.5) / np.log((self.ach_mid - self.ach_min) / (self.ach_max - self.ach_min))

        if isinstance(data, str):
            with open(data, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)
        else:
            self.raw_data = data
            
        self.df = self._prepare_dataframe()
        self.nickname = self.raw_data.get('nickname', 'Unknown')

    def _prepare_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(self.raw_data.get('records', []))
        
        # 颜色映射
        df['color'] = df.apply(self._get_color, axis=1)
        
        # 坐标映射
        df['plot_x'] = df['ds'].apply(
            lambda x: pow((x - self.ds_min) / (self.ds_max - self.ds_min), self.k_ds)
        )
        df['plot_y'] = df['achievements'].apply(
            lambda y: pow((y - self.ach_min) / (self.ach_max - self.ach_min), self.k_ach)
        )
        return df

    def _get_color(self, row) -> str:
        lv = row['level_index']
        if lv == 0 and row['level_label'] != "Utage": return "#00FF40"
        if lv == 1: return '#FFD700'
        if lv == 2: return "#FF0000"
        if lv == 3: return "#AE00FF"
        if lv == 4: return "#E6B0FF"
        return "#FF89B4"

    def generate_html(self, output_path: str = "maimai_global_scale.html"):
        fig = go.Figure()

        # 绘制散点
        fig.add_trace(go.Scatter(
            x=self.df['plot_x'],
            y=self.df['plot_y'],
            mode='markers',
            marker=dict(
                size=10,
                color=self.df['color'],
                line=dict(width=1, color='white'),
                opacity=0.8
            ),
            text=self.df.apply(lambda r: (
                f"<b>{r['title']}</b><br>"
                f"定数: {r['ds']} | 达成率: {r['achievements']:.4f}%<br>"
                f"Rating: {r['ra']}"
            ), axis=1),
            hoverinfo='text'
        ))

        # 刻度设置 (增加高值区的刻度密度以体现放大效果)
        ds_ticks = [1, 5, 7.6, 8, 8.6, 9, 9.6, 10, 10.6, 11, 11.6, 12, 12.6, 13, 13.6, 14, 14.6, 15]
        ach_ticks = [0, 50, 80, 90, 94, 97, 98, 99, 99.5, 100, 100.5, 101]

        def map_x(val): return pow((val - self.ds_min) / (self.ds_max - self.ds_min), self.k_ds)
        def map_y(val): return pow((val - self.ach_min) / (self.ach_max - self.ach_min), self.k_ach)
        
        def text_lv(number):
            if number%1 != 0:
                return str(int(number))+"+"
            else:
                return str(number)
            
        def text_rk(number):
            if number == 101:
                return "101% (AP+)"
            if number == 100.5:
                return "100.5% (SSS+)"
            if number == 100:
                return "100% (SSS)"
            if number == 99.5:
                return "99.5% (SS+)"
            if number == 99:
                return "99% (SS)"
            if number == 98:
                return "98% (S+)"
            if number == 97:
                return "97% (S)"
            else:
                return f"{number}%"

        fig.update_layout(
            title=dict(text=f"{self.nickname} 的舞萌 DX 等级 / 达成率散点图", x=0.5),
            xaxis=dict(
                title="谱面定数",
                tickvals=[map_x(t) for t in ds_ticks],
                ticktext=[text_lv(t) for t in ds_ticks],
                gridcolor='#F0F0F0',
                range=[-0.02, 1.02],
                zeroline=False
            ),
            yaxis=dict(
                title="达成率 (%)",
                tickvals=[map_y(t) for t in ach_ticks],
                ticktext=[text_rk(t) for t in ach_ticks],
                gridcolor='#F0F0F0',
                range=[-0.02, 1.02],
                zeroline=False
            ),
            plot_bgcolor='white',
            width=1200,
            height=850,
            showlegend=False
        )

        # 97% 处的中心参考线
        fig.add_shape(type="line", x0=0, y0=0.5, x1=1, y1=0.5, line=dict(color="#FF2A2A", width=1, dash="dot"))
        # 100.5% 处的中心参考线
        fig.add_shape(type="line", x0=0, y0=0.92, x1=1, y1=0.92, line=dict(color="#FF8A42", width=1, dash="dot"))

        fig.write_html(output_path)
        return output_path

b50 = on_command("b50", priority=10, block=True)
@b50.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("maimai"):
        raise FinishedException
    # await b50.finish("awmc！抱歉，阁下不能帮你查b50，请另请高明吧！")
    misc_manager.tasks.append("maimai_b50_query")
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
        misc_manager.tasks.remove("maimai_b50_query")
        await b50.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))
    else:
        misc_manager.tasks.remove("maimai_b50_query")
        await b50.finish(val)

dxra = on_command("dxra", aliases={"rating"}, priority=10, block=True)
@dxra.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("maimai"):
        raise FinishedException
    #await achievement_manager.add(2,event)
    result = await qddata_pre(args,event,"dxra_detailed")
    await dxra.finish(result)

dxdv = on_command("dxdv", aliases={"锐评b50","cb50","b50dv","b50方差"}, priority=10, block=True)
@dxdv.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("maimai"):
        raise FinishedException
    result = await qddata_pre(args,event,"dxdv")
    await dxdv.finish(result)    

b50_styles = ["testpilot","prism","circle"]

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
        """
        # 获取两人QQ昵称
        qqnam1 = ""
        qqnam2 = ""
        qqinfo1 = dict(await bot.get_stranger_info(user_id=qqnum1))
        qqinfo2 = dict(await bot.get_stranger_info(user_id=qqnum2))
        if "nick" in qqnam1:
            qqnam1 = qqinfo1["nick"]
        if "nick" in qqnam2:
            qqnam2 = qqinfo2["nick"]
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
        """
        result = await getb50overlaplist(qqnum1,qqnum2)
        # 查询失败
        if type(result) != list:
            await boverlap.finish("查询失败！你提供的至少其中一个QQ号无法查询到游戏数据！")
        # 写入json
        file1 = open("web/templates/maimai_boverlap/boverlap.json","w",encoding="utf-8")
        json.dump(result,file1,ensure_ascii=False)
        file1.close()
        # 写入html
        file2 = open("web/templates/maimai_boverlap/index.html","r",encoding="utf-8")
        web.content = file2.read()
        file2.close()
        web.writehtml()
        await webss.take2("http://localhost:8104/","container")
        await boverlap.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))
    # 用户未给定参数或参数不正确（如果成功查询，则提前finish，不执行到这一步）。
    await boverlap.finish("参数错误。用法：/boverlap [要查询的QQ号/@群成员1] [要查询的QQ号/@群成员2]")
    
aib50 = on_command("aib50", aliases={"dsb50","ai锐评b50","AI锐评b50"}, priority=10, block=True)
@aib50.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if (not feature_manager.get("maimai")) or (not feature_manager.get("deepseek")):
        raise FinishedException
    misc_manager.tasks.append("maimai_dsb50")
    result = await qddata_pre(args,event,"json")
    if type(result) != dict:
        misc_manager.tasks.remove("maimai_dsb50")
        await aib50.finish("没有查询到玩家数据！")
    web.content_md(await plugins.actual_deepseek.ds_b50(result))
    await webss.take2("http://localhost:8104","container")
    misc_manager.tasks.remove("maimai_dsb50")
    await aib50.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))

maisdt = on_command("maisdt", aliases={"舞萌散点图","舞萌成绩散点图","maimai散点图"}, priority=10, block=True)
@maisdt.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if not feature_manager.get("maimai"):
        raise FinishedException
    # 获取全曲成绩记录
    misc_manager.tasks.append("maimai_b50_query")
    # result = await qddata_pre(args,event,"json")
    result = await qddata_pre(args,event,"all")
    if type(result) != dict:
        misc_manager.tasks.remove("maimai_b50_query")
        await aib50.finish("没有查询到玩家数据！")
    gen = mai_sdt_gen(result)
    gen.generate_html(path_manager.nb_path()+"web/index.html")
    await webss.take("http://localhost:8104",1,filename="1",xres=1210,yres=825)
    misc_manager.tasks.remove("maimai_b50_query")
    await maisdt.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))