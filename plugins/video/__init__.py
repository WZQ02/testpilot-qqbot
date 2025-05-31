from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import asyncio
import feature_manager
import privilege_manager
import path_manager
import os
import random

# vid_path = "W:/soft/web_svr/testpilot_qqbot/video/temp/video.mp4"
vid_path1 = path_manager.bf_path()+"video/temp/video.mp4" # QQ看到的path
vid_path2 = path_manager.nb_path()+"video/temp/video.mp4" # nonebot看到的path
vid_ongoing_state = 0

bilivid = on_command("bili", aliases={"bilibili","视频","b站视频","video","sp"}, priority=10, block=True)
@bilivid.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("video_web"):
        global vid_ongoing_state
        if vid_ongoing_state != 0:
            await bilivid.finish("且慢！正在为上一个人获取视频……")
        if os.path.exists(vid_path2):
            os.remove(vid_path2)
        str = args.extract_plain_text()
        if str == "":
            await bilivid.finish("参数不够。用法 /bili [视频链接/BV号/av号]")
        vid_ongoing_state = 1
        link = ""
        if str.startswith("BV") or str.startswith("av"):
            link = "https://www.bilibili.com/video/"+str
        elif str.startswith("sm"):
            link = "https://www.nicovideo.jp/watch/"+str
        else:
            link = str
        cmd = ""
        """
        if "x.com" in link or "twitter.com" in link or "tumblr.com" in link or "youtube.com" in link or "douyin.com" in link:
            cmd = "ytdlp -P video/temp/ -o video.mp4 --merge-output-format mp4 "+link
        else:
            cmd = "lux -O video -o video/temp/ "+link
        """
        # if "bilibili.com" in link:
            # cmd = "lux -O video -o video/temp/ "+link
        # else:
        cmd = "ytdlp -P video/temp/ -o video.mp4 --merge-output-format mp4 "+link
        proc = await asyncio.create_subprocess_exec('cmd', '/c', cmd)
        await proc.wait()
        vid_ongoing_state = 0
        if os.path.exists(vid_path2):
            await bilivid.finish(Message('[CQ:video,file='+vid_path1+']'))
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