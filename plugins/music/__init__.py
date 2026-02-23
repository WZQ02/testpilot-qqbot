from nonebot import on_command, on_message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event, MessageEvent, MessageSegment
from nonebot.exception import FinishedException
import asyncio
import feature_manager
import path_manager
import os
import json
import requests
import re

"""
from musicdl import musicdl
init_music_clients_cfg = dict()
init_music_clients_cfg['NeteaseMusicClient'] = {'work_dir': path_manager.nb_path()+"music/temp"}
client = musicdl.MusicClient(music_sources=['NeteaseMusicClient'])
"""
mus_path1 = path_manager.bf_path()+"music/temp/" # QQ看到的path
mus_path2 = path_manager.nb_path()+"music/temp/" # nonebot看到的path
mus_ongoing_state = 0
http_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Referer': 'https://music.163.com/'
}

current_song_name = ""

# 从URL解析网易云歌曲ID
def parse_music_id(param):
    # 给定的是ID
    if param.isdigit():
        return int(param)
    # 给定的是链接
    else:
        song_id_match = re.search(r'song\?id=(\d+)', param)
        if not song_id_match:
            return -1
        return int(song_id_match.group(1))

async def get_metadata(id):
    loop = asyncio.get_event_loop()
    def get_metadata():
        global current_song_name
        current_song_name = ""
        url = f"http://music.163.com/api/song/detail/?id={id}&ids=[{id}]"
        try:
            response = requests.get(url, headers=http_headers)
            data = response.json()
            if data['songs'] and len(data['songs']) > 0:
                song = data['songs'][0]
                song_name = song['name']
                artists = '、'.join([artist['name'] for artist in song['artists']])

                # 更改当前标题
                current_song_name = f"{artists} - {song_name}[{id}]"

                # 返回元数据（小程序解析用）
                meta = {
                    'id': id,
                    'title': song_name,
                    'artist': artists,
                    'album': song['album']['name'] if 'album' in song else None,
                    'cover_url': song['album']['blurPicUrl'] if 'blurPicUrl' in song['album'] else None
                }
                return meta
            else:
                return None
        except Exception as e:
            print(f"解析音乐元数据出错：{e}")
            return None
    return await loop.run_in_executor(None, get_metadata)

async def download_music(id):
    loop = asyncio.get_event_loop()
    """
    def search_and_download():
        song_infos = client.search(id)
        print()
        client.
        client.download(song_infos=song_infos)
    """
    def download():
        if os.path.exists(f"{mus_path1}{current_song_name}.mp3"):
            return f"{current_song_name}.mp3"
        url = f"http://music.163.com/song/media/outer/url?id={id}.mp3"
        response = requests.get(url, headers=http_headers, stream=True)
        if response.status_code == 200 and "audio" in response.headers.get('Content-Type'):
            song_name = f"{current_song_name}.mp3"
            file_path = f"{mus_path1}{song_name}"
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return song_name
        else:
            return str(response.status_code)
    return await loop.run_in_executor(None, download)

# CQ码转义
def escape_cq_value(value):
    return (value.replace('&', '&amp;')
                 .replace('[', '&#91;')
                 .replace(']', '&#93;')
                 .replace(',', '&#44;'))

wyy = on_command("wyy", aliases={"wyyyl","网易云","网易云预览"}, priority=10, block=True)
@wyy.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("music_web"):
        str = args.extract_plain_text()
        id = parse_music_id(str)
        if id == -1:
            await wyy.finish("参数错误。用法 /wyy [网易云音乐链接/歌曲ID]\n目前暂不支持获取专辑/歌单。")
        await get_metadata(id)
        name = await download_music(id)
        if os.path.exists(mus_path1+name):
            await wyy.send(current_song_name)
            await wyy.finish(Message(f'[CQ:record,url={escape_cq_value(mus_path2+name)}]'))
        else:
            await wyy.finish("音乐获取失败！")
    else:
        raise FinishedException
    
wyydl = on_command("wyydl", aliases={"网易云下载","下歌","下载歌曲"}, priority=10, block=True)
@wyydl.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("music_web"):
        str = args.extract_plain_text()
        id = parse_music_id(str)
        if id == -1:
            await wyy.finish("参数错误。用法 /wyydl [网易云音乐链接/歌曲ID]\n目前暂不支持获取专辑/歌单。")
        await get_metadata(id)
        name = await download_music(id)
        if os.path.exists(mus_path1+name):
            await wyy.finish(Message(f'[CQ:file,url={escape_cq_value(mus_path2+name)}]'))
        else:
            await wyy.finish("音乐获取失败！")
    else:
        raise FinishedException

"""
wyysg = on_command("wyysg", aliases={"网易云搜歌","搜歌","搜索歌曲"}, priority=10, block=True)
@wyysg.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if feature_manager.get("music_web"):
        print()
    else:
        raise FinishedException
"""