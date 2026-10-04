from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageEvent, GroupMessageEvent, PrivateMessageEvent, MessageSegment
from nonebot.exception import FinishedException
import feature_manager
import plugins.test1
import path_manager
import os
import json
import re
import asyncio
import requests

# 临时目录
TEMP_REL = "images/convert/"
TEMP_BF = path_manager.bf_path() + TEMP_REL  # QQ看到的路径
TEMP_NB = path_manager.nb_path() + TEMP_REL  # nonebot看到的路径

# 视频/音频后缀集合
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".flv", ".mkv", ".wmv", ".webm", ".m4v"}
AUDIO_EXTS = {".mp3", ".aac", ".wav", ".m4a", ".flac", ".ogg", ".wma", ".opus"}

# 小程序卡片无法识别时的提示
UNKNOWN_CARD_MSG = "这是哪来的小程序，没见过喵"


def to_message(rep) -> Message:
    """把 get_reply_content 返回值（dict 列表或字符串）统一转换为 Message。"""
    if isinstance(rep, str):
        return Message(rep)
    if isinstance(rep, list):
        segs = []
        for item in rep:
            if isinstance(item, dict):
                segs.append(MessageSegment(item.get("type", ""), item.get("data", {})))
            else:
                segs.append(item)
        return Message(segs)
    return Message(rep)


# CQ码转义
def escape_cq_value(value):
    return (value.replace('&', '&amp;')
                 .replace('[', '&#91;')
                 .replace(']', '&#93;')
                 .replace(',', '&#44;'))


async def get_file_url(bot: Bot, data: dict) -> str:
    """从 CQ:file 段获取本地可访问路径或 URL。
    优先调用 NapCat 的 get_file API 取 url；失败则回退到段自带 url/file。
    """
    file_id = data.get("file_id") or data.get("file")
    if file_id:
        try:
            info = await bot.call_api("get_file", file_id=file_id)
            if info:
                if info.get("file"):
                    return info["file"]
                if info.get("url"):
                    return info["url"]
        except Exception as e:
            print(f"convert: get_file 调用失败：{e}")
    return data.get("url") or data.get("file") or ""


def download_to_local(url: str, local_name: str) -> bool:
    """下载 URL 到本地临时目录，返回是否成功。"""
    try:
        os.makedirs(TEMP_NB, exist_ok=True)
        local_path = TEMP_NB + local_name
        # QQ 多媒体 URL 替换为内网域名，提高下载成功率
        resp = requests.get(url.replace("https://multimedia.nt.qq", "http://multimedia.nt.qq"),
                            stream=True, timeout=60)
        if resp.status_code != 200:
            return False
        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"convert: 下载失败 {url}：{e}")
        return False


async def run_ffmpeg(*args) -> int:
    """调用 ffmpeg，返回 returncode。"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", *args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            # stderr 包含 ffmpeg banner 和具体错误，输出完整内容便于诊断
            print(f"convert: ffmpeg 失败 (rc={proc.returncode})：\n{stderr.decode('utf-8', errors='ignore')}")
        return proc.returncode or 0
    except Exception as e:
        print(f"convert: 调用 ffmpeg 异常：{e}")
        return -1


async def parse_card_json(raw: str):
    """解析 JSON 卡片，返回 (title, desc, url) 或 None。"""
    try:
        obj = json.loads(raw) if isinstance(raw, str) else raw
        meta = obj.get("meta") or {}
        if not meta:
            return None
        # 取第一个子键（news/music/qq 等）
        sub = next(iter(meta.values())) if meta else {}
        if not isinstance(sub, dict):
            return None
        title = sub.get("title") or sub.get("name") or ""
        desc = sub.get("desc") or sub.get("summary") or ""
        url = (sub.get("qqdocurl") or sub.get("url")
               or sub.get("jumpUrl") or "")
        if not (title and url):
            return None
        return title, desc, url
    except Exception:
        return None


async def parse_card_xml(raw: str):
    """解析 XML/应用卡片，返回 (title, desc, url) 或 None。"""
    try:
        title_m = re.search(r'<title>(.*?)</title>', raw, re.S)
        summary_m = re.search(r'<summary>(.*?)</summary>', raw, re.S)
        # 尝试多种 url 形式：url='...'、url="..."、<url>...</url>
        url_m = (re.search(r"url='([^']+)'", raw)
                 or re.search(r'url="([^"]+)"', raw)
                 or re.search(r'<url>(.*?)</url>', raw, re.S))
        title = title_m.group(1).strip() if title_m else ""
        desc = summary_m.group(1).strip() if summary_m else ""
        url = url_m.group(1).strip() if url_m else ""
        if not (title and url):
            return None
        return title, desc, url
    except Exception:
        return None


convert = on_command("convert", aliases={"转换", "转"}, priority=10, block=True)


@convert.handle()
async def handle_function(bot: Bot = Bot, event: MessageEvent = Event):
    if not feature_manager.can_use("convert", event.get_user_id()):
        raise FinishedException

    rep_con = await plugins.test1.get_reply_content(event.original_message, bot)
    if not rep_con:
        await convert.finish("用法：[回复消息] /convert")
    if not isinstance(rep_con, list) or len(rep_con) == 0:
        await convert.finish(rep_con if isinstance(rep_con, str) else to_message(rep_con))

    seg = rep_con[0]
    seg_type = seg.get("type", "")
    data = seg.get("data", {})

    # ====== 1. CQ:file ======
    if seg_type == "file":
        # NapCat 字段不统一：file_name 缺失时 file 字段常含原始文件名
        file_name = (data.get("file_name") or data.get("name")
                     or data.get("file") or "file")
        ext = os.path.splitext(file_name)[1].lower()
        # 取本地路径或 URL
        src = await get_file_url(bot, data)

        # 视频后缀 → 以 CQ:video 发送
        if ext in VIDEO_EXTS:
            if not src:
                await convert.finish("无法获取该视频文件，可能已过期。")
            # 若是 URL 需下载到本地再发（NapCat CQ:video 需本地路径）
            if src.startswith("http"):
                local_name = f"video{ext}"
                if not download_to_local(src, local_name):
                    await convert.finish("视频下载失败，链接可能已过期。")
                await convert.finish(Message(f'[CQ:video,file={escape_cq_value(TEMP_BF + local_name)}]'))
            else:
                # 本地绝对路径，直接用
                await convert.finish(Message(f'[CQ:video,file={escape_cq_value(src)}]'))

        # 音频后缀 → 转 m4a 后以 CQ:record 发送
        if ext in AUDIO_EXTS:
            if not src:
                await convert.finish("无法获取该音频文件，可能已过期。")
            # 下载到本地
            local_in = f"audio_in{ext}"
            if src.startswith("http"):
                if not download_to_local(src, local_in):
                    await convert.finish("音频下载失败，链接可能已过期。")
                in_path = TEMP_NB + local_in
            else:
                in_path = src
            # 检查输入文件
            if not os.path.exists(in_path):
                await convert.finish(f"音频文件访问失败：{in_path}")
            in_size = os.path.getsize(in_path)
            if in_size == 0:
                await convert.finish("下载的音频文件为空，链接可能已失效。")
            print(f"convert: 音频转换输入 {in_path} ({in_size} bytes)")
            # 转 m4a（NapCat 接受作为 record）
            out_name = "audio_out.m4a"
            out_path = TEMP_NB + out_name
            rc = await run_ffmpeg("-i", in_path, "-ar", "44100", "-ac", "1",
                                  "-b:a", "64k", "-codec:a", "aac", "-vn", out_path)
            if rc != 0 or not os.path.exists(out_path):
                await convert.finish("音频转换失败，详情见控制台日志。")
            await convert.finish(Message(f'[CQ:record,file={escape_cq_value(TEMP_BF + out_name)}]'))

        # 其他文件后缀 → 原样返回
        await convert.finish(to_message(rep_con))

    # ====== 2. CQ:video → CQ:file ======
    if seg_type == "video":
        url = data.get("url") or ""
        file = data.get("file") or ""
        src = url or file
        if not src:
            await convert.finish("无法获取该视频，可能已过期。")
        # 下载到本地
        local_name = "video.mp4"
        if src.startswith("http"):
            if not download_to_local(src, local_name):
                await convert.finish("视频下载失败，链接可能已过期。")
        else:
            # 已经是本地路径，复制到临时目录统一处理
            try:
                import shutil
                os.makedirs(TEMP_NB, exist_ok=True)
                shutil.copy(src, TEMP_NB + local_name)
            except Exception as e:
                print(f"convert: 复制本地视频失败：{e}")
                await convert.finish("视频文件访问失败。")
        # 以 CQ:file 发送
        await convert.finish(Message(f'[CQ:file,file={escape_cq_value(TEMP_BF + local_name)}]'))

    # ====== 3. CQ:mface / CQ:face → 普通图片 ======
    if seg_type in ("mface", "face"):
        img_url = data.get("url") or ""
        if not img_url:
            await convert.finish("表情包图片不可用。")
        # 优先直接转发 url，失败再下载
        try:
            await convert.finish(Message(f'[CQ:image,file={escape_cq_value(img_url)}]'))
        except Exception:
            local_name = "emoji.jpg"
            if download_to_local(img_url, local_name):
                await convert.finish(Message(f'[CQ:image,file=file:///{escape_cq_value(TEMP_BF + local_name)}]'))
            await convert.finish("表情包图片下载失败。")

    # ====== 4. CQ:record → MP3 文件 ======
    if seg_type == "record":
        url = data.get("url") or ""
        file = data.get("file") or ""
        src = url or file
        if not src:
            await convert.finish("无法获取该语音，可能已过期。")
        # 下载到本地（源文件无扩展名，用 .amr 占位）
        local_in = "voice_in.amr"
        if src.startswith("http"):
            if not download_to_local(src, local_in):
                await convert.finish("语音下载失败，链接可能已过期。")
        else:
            try:
                import shutil
                os.makedirs(TEMP_NB, exist_ok=True)
                shutil.copy(src, TEMP_NB + local_in)
            except Exception as e:
                print(f"convert: 复制本地语音失败：{e}")
                await convert.finish("语音文件访问失败。")
        in_path = TEMP_NB + local_in
        # 检查输入文件
        if not os.path.exists(in_path):
            await convert.finish(f"语音文件访问失败：{in_path}")
        in_size = os.path.getsize(in_path)
        if in_size == 0:
            await convert.finish("下载的语音文件为空，链接可能已失效。")
        print(f"convert: 语音转换输入 {in_path} ({in_size} bytes)")
        out_name = "voice.mp3"
        out_path = TEMP_NB + out_name
        rc = await run_ffmpeg("-i", in_path, "-codec:a", "libmp3lame", "-q:a", "2", out_path)
        if rc != 0 or not os.path.exists(out_path):
            await convert.finish("语音转换失败，详情见控制台日志。")
        await convert.finish(Message(f'[CQ:file,file={escape_cq_value(TEMP_BF + out_name)}]'))

    # ====== 5. CQ:json / CQ:app 小程序卡片 ======
    if seg_type in ("json", "app"):
        raw = data.get("data") or data.get("content") or ""
        parsed = await parse_card_json(raw) if seg_type == "json" else await parse_card_xml(raw)
        if not parsed:
            await convert.finish(UNKNOWN_CARD_MSG)
        title, desc, url = parsed
        if desc:
            await convert.finish(f"{title}\n{desc}\n{url}")
        await convert.finish(f"{title}\n{url}")

    # ====== 6. 其他类型 → 原样返回 ======
    await convert.finish(to_message(rep_con))
