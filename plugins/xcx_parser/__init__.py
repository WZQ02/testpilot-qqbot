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
import misc_manager
import plugins.member_stuff

import plugins.video
import plugins.music

# 获取特殊qq号列表
specd = open("json/spec_qq_list.json","r",encoding="utf-8")
spec_list = json.loads(specd.read())

xcxrepl_lastnotitime = 0

# b站小程序解析
xcx = on_message(priority=10, block=True)
@xcx.handle()
async def handle_function(event: MessageEvent):
    global xcxrepl_lastnotitime
    if feature_manager.get("bilixcx"):
        # 获取原始消息
        message = event.get_message()
        for segment in message:
            if segment.type == "json":
                # 这是 JSON 消息，可能是小程序
                json_data = segment.data["data"]
                # print(json_data)
                data = json.loads(json_data)
                # 检查json格式（是否存在特定项目）
                if ("meta" in data and "detail_1" in data["meta"] and "qqdocurl" in data["meta"]["detail_1"] and data["meta"]["detail_1"]["title"] == "哔哩哔哩"):
                    # 检查是否在黑名单群聊（存在其他解析b站小程序bot的群聊）
                    group_id = plugins.member_stuff.get_group_id(event)
                    if int(group_id) in spec_list["bilixcx_blacklist_groups"]:
                        raise FinishedException
                    # 解析b23
                    url = data["meta"]["detail_1"]["qqdocurl"]
                    bvid = await plugins.video.resolve_b23(url)
                    url = "https://www.bilibili.com/video/"+bvid+"/"
                    # 提取视频标题
                    title = data["meta"]["detail_1"]["desc"]
                    # 获取消息id
                    reply_id = event.message_id
                    # 发出的消息
                    replcont = title+"\n"+url
                    # 判断是否需要添加小提示
                    if (time.time() - xcxrepl_lastnotitime) > 3600*5 and feature_manager.get("video_web"):
                        xcxrepl_lastnotitime = time.time()
                        replcont += "\n小提示：发送 /bili "+bvid+" 即可在群聊预览该视频！"
                    await xcx.send(MessageSegment.reply(reply_id)+replcont)
                if ("meta" in data and "music" in data["meta"] and "musicUrl" in data["meta"]["music"]):
                    music_url = data["meta"]["music"]["jumpUrl"]
                    # 解析id并获取元数据
                    id = plugins.music.parse_music_id(music_url)
                    meta = await plugins.music.get_metadata(id)
                    """
                    msg = ""
                    if meta["cover_url"]:
                        msg += f'[CQ:image,url={meta["cover_url"]}]\n'
                    """
                    url = f"https://music.163.com/song?id={id}"
                    # 构造消息内容
                    msg = f'{meta["title"]}\n{url}\n艺术家：{meta["artist"]}'
                    if meta["album"]:
                        msg += f'\n专辑：{meta["album"]}'
                    # 判断是否需要添加小提示
                    if (time.time() - xcxrepl_lastnotitime) > 3600*5 and feature_manager.get("music_web"):
                        xcxrepl_lastnotitime = time.time()
                        msg += f"\n小提示：发送 /wyydl {id} 即可下载这首歌！"
                    # 获取消息id
                    reply_id = event.message_id
                    await xcx.send(MessageSegment.reply(reply_id)+MessageSegment.image(meta["cover_url"])+msg)
                # 格式不符合则直接退出
    raise FinishedException