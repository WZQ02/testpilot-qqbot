from nonebot import on_command, on_message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event, MessageEvent, MessageSegment
from nonebot.exception import FinishedException
import asyncio
import feature_manager
import privilege_manager
import path_manager
import os
import random
import time
import yt_dlp
import json
import requests
import re

# 获取特殊qq号列表
specd = open("json/spec_qq_list.json","r",encoding="utf-8")
spec_list = json.loads(specd.read())

# vid_path = "W:/soft/web_svr/testpilot_qqbot/video/temp/video.mp4"
vid_path1 = path_manager.bf_path()+"video/temp/video.mp4" # QQ看到的path
vid_path2 = path_manager.nb_path()+"video/temp/video.mp4" # nonebot看到的path
vid_ongoing_state = 0
last_get_vid_time = 0

bilivid = on_command("bili", aliases={"bilibili","视频","b站视频","video","sp"}, priority=10, block=True)
@bilivid.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("video_web"):
        global vid_ongoing_state,last_get_vid_time
        if vid_ongoing_state != 0:
            await bilivid.finish("且慢！正在为上一个人获取视频……")
        if os.path.exists(vid_path2):
            os.remove(vid_path2)
        str = args.extract_plain_text()
        if str == "":
            await bilivid.finish("参数不够。用法 /bili [视频链接/BV号/av号]")
        last_get_itvl = time.time() - last_get_vid_time
        vid_ongoing_state = 1
        last_get_vid_time = time.time()
        link = ""
        if str.startswith("BV") or str.startswith("av"):
            link = "https://www.bilibili.com/video/"+str
        elif str.startswith("sm"):
            link = "https://www.nicovideo.jp/watch/"+str
        else:
            link = str
        """
        cmd = ""
        
        if "x.com" in link or "twitter.com" in link or "tumblr.com" in link or "youtube.com" in link or "douyin.com" in link:
            cmd = "ytdlp -P video/temp/ -o video.mp4 --merge-output-format mp4 "+link
        else:
            cmd = "lux -O video -o video/temp/ "+link
        
        # if "bilibili.com" in link:
            # cmd = "lux -O video -o video/temp/ "+link
        # else:
        cmd = "ytdlp -P video/temp/ -o video.mp4 --merge-output-format mp4 "+link
        proc = await asyncio.create_subprocess_exec('cmd', '/c', cmd)
        await proc.wait()
        """
        result = await download_video(link)
        vid_ongoing_state = 0
        if (result == 10):
            await bilivid.finish("你要的视频太大太长了啊啊啊！请另请高明吧！")
        if os.path.exists(vid_path2):
            await bilivid.finish(Message('[CQ:video,file='+vid_path1+']'))
        else:
            if (last_get_itvl < 15*60):
                await bilivid.finish("视频获取失败，你过会再试试吧！")
            else:
                await bilivid.finish("视频获取失败！")
    else:
        raise FinishedException
    
bill = on_command("bill", priority=10, block=True)
@bill.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("video_web"):
        rd = random.random()
        if rd < .6:
            await bill.finish("请问你刚才发的是“bill”（比尔）吗？")
        else:
            await bill.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/bill/bill.jpg]'))
    else:
        raise FinishedException
    
async def download_video(url,path="video/temp/video.mp4"):
    # 配置选项
    ydl_opts = {
        # 'outtmpl': f'{path}/%(title)s.%(ext)s',
        'outtmpl': path,
        # 强制转换为MP4格式
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',  # 合并音视频时输出MP4
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 获取视频信息（可选）
            info = ydl.extract_info(url, download=False)
            # print(f"准备下载: {info.get('title', '未知标题')}")
            # 检查视频文件体积
            filesz = info.get('filesize', 0) or info.get('filesize_approx', 0)
            file_mb = filesz / 1048576
            # 控制台输出视频信息
            print(f"视频标题：{info.get('title')}\n文件体积：{file_mb:.2f} MB")
            if (file_mb > 100):
                # 大于100m，拒绝下载
                return 10
            # 实际下载
            ydl.download([url])
            # print("下载完成！")
            return 0
    except Exception as e:
        # print(f"下载失败: {e}")
        return -1

# b23解析
async def resolve_b23(url):
    try:
        # 发送HTTP请求到短链URL
        response = requests.get(url, allow_redirects=True)
        # 获取最终URL
        furl = response.url
        # 提取av/BV号
        avidmatch = re.search(r'av(\d+)', furl)
        bvidmatch = re.search(r'BV[A-Za-z0-9]+', furl)
        bvid = ""
        if avidmatch:
            bvid = avidmatch.group(0)
        elif bvidmatch:
            bvid = bvidmatch.group(0)
        else:
            bvid = url
        return bvid
    except requests.RequestException as e:
        # print(f"Error fetching the URL: {e}")
        return None

xcxrepl_lastnotitime = 0

# b站小程序解析
bilixcx = on_message(priority=10, block=True)
@bilixcx.handle()
async def handle_function(event: MessageEvent):
    if feature_manager.get("bilixcx"):
        # 检查是否在黑名单群聊（存在其他解析b站小程序bot的群聊）
        group_id = event.get_session_id().split("_")[1]
        if int(group_id) in spec_list["bilixcx_blacklist_groups"]:
            raise FinishedException
        # 获取原始消息
        message = event.get_message()
        for segment in message:
            if segment.type == "json":
                # 这是 JSON 消息，可能是小程序
                json_data = segment.data["data"]
                # print(json_data)
                data = json.loads(json_data)
                # 检查json格式（是否存在特定项目）
                if ("meta" in data and "qqdocurl" in data["meta"]["detail_1"] and data["meta"]["detail_1"]["title"] == "哔哩哔哩"):
                    # 解析b23
                    url = data["meta"]["detail_1"]["qqdocurl"]
                    bvid = await resolve_b23(url)
                    url = "https://www.bilibili.com/video/"+bvid+"/"
                    # 提取视频标题
                    title = data["meta"]["detail_1"]["desc"]
                    # 获取消息id
                    reply_id = event.message_id
                    # 发出的消息
                    replcont = title+"\n"+url
                    # 判断是否需要添加小提示
                    global xcxrepl_lastnotitime
                    if (time.time() - xcxrepl_lastnotitime) > 3600*5 and feature_manager.get("video_web"):
                        xcxrepl_lastnotitime = time.time()
                        replcont += "\n小提示：发送 /bili "+bvid+" 即可在群聊预览该视频！"
                    await bilixcx.send(MessageSegment.reply(reply_id)+replcont)
                # 格式不符合则直接退出
    raise FinishedException

