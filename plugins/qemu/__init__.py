from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageEvent
import asyncio
from nonebot.exception import FinishedException
from nonebot.log import logger
import path_manager
from qemu.qmp import QMPClient
import feature_manager
import bridge
import asyncvnc
import asyncssh
import aiohttp
import cv2
import numpy as np
import json
import base64
import io
import os
import misc_manager
import plugins.actual_deepseek as ds
from PIL import Image

vm_powerstatus = 0
vm_address = ""
# 当前运行的虚拟机名称；bot 启动前就已运行的虚拟机无法判断，记为 None
vm_current_name = None
# 虚拟机屏幕尺寸（宽, 高），由 AI 截图工具更新，用于鼠标绝对坐标换算
vm_screen_size = [0, 0]
qemu_command_presets = {"winxp": ["-accel", "whpx", "-m", "96m", "-qmp", "tcp:0.0.0.0:4444,server,nowait", "-drive", "file=D:/vms/qemu/nanoxp.vhd,if=ide", "-display", "vnc=:0", "-device", "usb-ehci", "-device", "usb-tablet"], "win7": ["-accel", "whpx", "-m", "1024m", "-qmp", "tcp:0.0.0.0:4444,server,nowait", "-drive", "file=D:/vms/qemu/thinpc.vhd,if=ide", "-smp", "2", "-display", "vnc=:0", "-device", "usb-ehci", "-device", "usb-tablet"]}
ssh_presets = misc_manager.misc_data["vm_ssh_data"]
environment_prompt = {"winxp": "32 位 Windows XP 系统，用户名 Administrator。没有网络。", "win7": "32 位 Windows 7 系统，用户名 sometroublemaker（显示名称 testpilot），有网络连接、安装有 PowerShell 5.1、7-zip、curl、scoop、Python 3.8、Supermium 等软件。"}

def get_vnc_address():
    """根据虚拟机运行位置返回 VNC 地址。本机 5900，bridge 5900。"""
    if vm_address == "localhost":
        return "127.0.0.1", 5900
    return bridge.bridge_host_ip, 5900

async def probe_vm_alive():
    """并发探测 bridge 上虚拟机的 VNC(5900) 与 QMP(4444) 端口，任一连通即认为在运行。"""
    host = bridge.bridge_host_ip

    async def tcp_probe(port):
        try:
            _, w = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=3)
            w.close()
            return True
        except Exception:
            return False

    results = await asyncio.gather(tcp_probe(5900), tcp_probe(4444))
    return any(results)

async def ensure_vm_status():
    """bot 重启后 vm_powerstatus 归零，但 bridge 上的虚拟机可能仍在运行。
    非本机部署时先探测一次，能连上就恢复运行状态并补全 vm_address。"""
    global vm_powerstatus, vm_address
    if vm_powerstatus == 1:
        return
    # localhost 部署时 QEMU 由 bot 进程拉起，重启后必然没跑，无需探测
    if path_manager.pat_list["sys_env"] == "linux":
        if await probe_vm_alive():
            vm_powerstatus = 1
            vm_address = bridge.bridge_host_ip
            logger.info("探测到 bridge 虚拟机仍在运行，已恢复 vm_powerstatus=1")

async def run_vm(name):
    """按名称启动 qemu_command_presets 中配置的虚拟机。成功返回 True。"""
    global vm_address, vm_powerstatus, vm_current_name
    if path_manager.pat_list["sys_env"] != "linux":
        await asyncio.create_subprocess_exec("C:\\Program Files\\qemu\\qemu-system-x86_64.exe", *qemu_command_presets[name])
        vm_address = 'localhost'
    else:
        result = bridge.start_vm(name)
        if not result:
            return False
        vm_address = bridge.bridge_host_ip
    vm_powerstatus = 1
    vm_current_name = name
    return True

async def connect_qemu():
    client = QMPClient('my-vm')
    await client.connect((vm_address, 4444))
    return client

async def vm_ss():
    host, port = get_vnc_address()
    async with asyncvnc.connect(host, port) as client:
        # 截全屏，返回 RGBA 的 numpy 数组 (height, width, 4)
        rgba = await client.screenshot()
        # RGBA -> BGR，供 OpenCV 保存
        bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
        cv2.imwrite(path_manager.nb_path()+"images/qemu/xp.png", bgr)
    return (Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/qemu/xp.png]'))

async def vm_sendkey(key):
    client = await connect_qemu()
    try:
        await client.execute("human-monitor-command",{"command-line": "sendkey "+key})
    finally:
        await client.disconnect()
    return

async def vm_sendtext(text):
    client = await connect_qemu()
    try:
        for i in text:
            keys: dict[str, str] = {" ": "spc","\n": "ret", ".": "dot", "/": "slash", "\\": "backslash", "-": "minus", "+": "plus"}
            thekey = keys.get(i)
            if thekey is None:
                thekey = i
            await client.execute("human-monitor-command",{"command-line": "sendkey "+thekey})
    finally:
        await client.disconnect()
    return

async def vm_poweroff():
    client = await connect_qemu()
    try:
        await client.execute('quit')
    finally:
        await client.disconnect()
    global vm_powerstatus, vm_current_name
    vm_powerstatus = 0
    vm_current_name = None
    return

startvm = on_command("startvm", aliases={"启动虚拟机","开机","启动qemu"}, priority=10, block=True)
@startvm.handle()
async def handle_function(args: Message = CommandArg(), event: Event = Event):
    if not feature_manager.can_use("qemu", event.get_user_id()):
        raise FinishedException
    name = args.extract_plain_text().strip()
    available = "、".join(qemu_command_presets.keys())
    if not name:
        await startvm.finish(f"用法：/startvm [虚拟机名称]\n可用虚拟机：{available}")
    if name not in qemu_command_presets:
        await startvm.finish(f"没有找到这个虚拟机！可用虚拟机：{available}")
    await ensure_vm_status()
    if vm_powerstatus == 1:
        await startvm.finish("虚拟机已经在运行！")
    if not await run_vm(name):
        await startvm.finish(f"虚拟机 {name} 启动失败！")
    await asyncio.sleep(10)
    await startvm.finish(await vm_ss())

vmss = on_command("vmss", aliases={"截图","screenshot","虚拟机截图"}, priority=10, block=True)
@vmss.handle()
async def handle_function(args: Message = CommandArg(), event: Event = Event):
    if not feature_manager.can_use("qemu", event.get_user_id()):
        raise FinishedException
    await ensure_vm_status()
    if not vm_powerstatus:
        await vmss.finish("虚拟机未启动！")
    await vmss.finish(await vm_ss())

sendkey = on_command("sendkey", aliases={"发送按键","vmsendkey","虚拟机发送按键","键入"}, priority=10, block=True)
@sendkey.handle()
async def handle_function(args: Message = CommandArg(), event: Event = Event):
    if not feature_manager.can_use("qemu", event.get_user_id()):
        raise FinishedException
    await ensure_vm_status()
    if not vm_powerstatus:
        await sendkey.finish("虚拟机未启动！")
    text = args.extract_plain_text()
    key = text.split(" ")[0]
    await vm_sendkey(key)
    await asyncio.sleep(1)
    await sendkey.finish(await vm_ss())

type = on_command("type", aliases={"打字","发送文本","vmtype","虚拟机发送文本"}, priority=10, block=True)
@type.handle()
async def handle_function(args: Message = CommandArg(), event: Event = Event):
    if not feature_manager.can_use("qemu", event.get_user_id()):
        raise FinishedException
    await ensure_vm_status()
    if not vm_powerstatus:
        await type.finish("虚拟机未启动！")
    text = args.extract_plain_text()
    await vm_sendtext(text)
    await asyncio.sleep(1)
    await type.finish(await vm_ss())

shut = on_command("shut", aliases={"关机","vmshut","虚拟机关机","poweroff","关虚拟机","关闭虚拟机"}, priority=10, block=True)
@shut.handle()
async def handle_function(args: Message = CommandArg(), event: Event = Event):
    if not feature_manager.can_use("qemu", event.get_user_id()):
        raise FinishedException
    await ensure_vm_status()
    if not vm_powerstatus:
        await shut.finish("虚拟机已经关机或未启动！")
    await vm_poweroff()
    await shut.finish("已关闭虚拟机。")

vmcmd = on_command("vmcmd", aliases={"qemucmd","虚拟机cmd","虚拟机命令"}, priority=10, block=True)
@vmcmd.handle()
async def handle_function(args: Message = CommandArg(), event: Event = Event):
    if not feature_manager.can_use("qemu", event.get_user_id()):
        raise FinishedException
    await ensure_vm_status()
    if not vm_powerstatus:
        await vmcmd.finish("虚拟机未启动！")
    command = args.extract_plain_text().strip()
    if not command:
        await vmcmd.finish("用法：/vmcmd [要在虚拟机里执行的命令]")
    result = await tool_vm_ssh_run(command)
    await vmcmd.finish(result)

# ===== AI 虚拟机操作 =====

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

async def tool_vm_get_screenshot(step: int = 0):
    """截取虚拟机当前画面，返回 base64 图片数据。step 用于区分过程截图文件。"""
    global vm_screen_size
    host, port = get_vnc_address()
    async with asyncvnc.connect(host, port) as client:
        rgba = await client.screenshot()
        vm_screen_size = [rgba.shape[1], rgba.shape[0]]
        bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
        img_path = path_manager.nb_path() + f"images/qemu/xp_ai_{step}.png"
        cv2.imwrite(img_path, bgr)
    return encode_image(img_path), img_path

VM_MOUSE_BUTTONS = ("left", "right", "middle", "wheel-up", "wheel-down")

async def tool_vm_send_mouse(x: int, y: int, button: str = None):
    """按截图像素坐标移动虚拟机鼠标，可选左/右/中键点击或滚轮。"""
    if vm_screen_size[0] == 0:
        return "失败：尚不知道屏幕尺寸，请先调用 vm_get_screenshot"
    # 移动事件：像素坐标换算为 QMP 绝对坐标（0~0x7FFF）
    move_events = [
        {"type": "abs", "data": {"axis": "x", "value": int(x * 32767 / vm_screen_size[0])}},
        {"type": "abs", "data": {"axis": "y", "value": int(y * 32767 / vm_screen_size[1])}},
    ]
    # 点击事件：button 参数校验，未知值直接报错让 AI 重试，不再静默忽略
    click_events = []
    if button is not None:
        if button not in VM_MOUSE_BUTTONS:
            return f"失败：未知的按键 '{button}'，button 只能是 left/right/middle/wheel-up/wheel-down 之一，或不填表示仅移动"
        if button in ("left", "right", "middle"):
            click_events = [
                {"type": "btn", "data": {"down": True, "button": button}},
                {"type": "btn", "data": {"down": False, "button": button}},
            ]
        else:
            click_events = [{"type": "btn", "data": {"down": True, "button": button}}]
    logger.info(f"dsqemu 鼠标操作: button={button}, 像素=({x},{y}), 屏幕={vm_screen_size[0]}x{vm_screen_size[1]}")
    client = await connect_qemu()
    try:
        # 移动与点击分两次发送，中间留间隔，避免 guest 未消化完移动增量就收到点击
        await client.execute("input-send-event", {"events": move_events})
        if click_events:
            await asyncio.sleep(0.05)
            await client.execute("input-send-event", {"events": click_events})
    finally:
        await client.disconnect()
    await asyncio.sleep(0.3)
    return "鼠标操作已发送"

async def tool_vm_send_key(key: str):
    """向虚拟机发送单个按键。"""
    await vm_sendkey(key)
    await asyncio.sleep(0.3)
    return "按键已发送"

async def tool_vm_send_text(text: str):
    """向虚拟机发送一段文本。"""
    await vm_sendtext(text)
    await asyncio.sleep(0.5)
    return "文本已发送"

def parse_ssh_target(vm_name):
    """从 ssh_presets 解析目标，返回 (username, host, port, password) 或 None。"""
    entry = ssh_presets.get(vm_name)
    if not entry:
        return None
    ssh_cfg = entry.get("ssh")
    if not isinstance(ssh_cfg, dict):
        return None
    ssh_str = ssh_cfg.get("cmd", "").strip()
    password = ssh_cfg.get("password")
    if not ssh_str:
        return None
    parts = ssh_str.split()
    user_host = parts[0]
    port = 22
    if len(parts) >= 3 and parts[1] == "-p":
        try:
            port = int(parts[2])
        except ValueError:
            pass
    if "@" in user_host:
        username, host = user_host.split("@", 1)
    else:
        username, host = "root", user_host
    return username, host, port, password

def decode_output(data: bytes) -> str:
    """命令输出可能是非 UTF-8 编码（如 Windows cmd 的 GBK），按链式回退解码。"""
    if not data:
        return ""
    for enc in ("utf-8", "gb18030", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")

async def tool_vm_ssh_run(command: str):
    """通过 SSH 在当前运行的虚拟机上执行命令，返回 stdout/stderr。"""
    if vm_current_name is None:
        return "失败：无法确定当前运行的是哪台虚拟机（可能在 bot 启动前就已运行），无法使用 SSH"
    target = parse_ssh_target(vm_current_name)
    if target is None:
        return f"失败：虚拟机 {vm_current_name} 未配置 SSH 连接方式"
    username, host, port, password = target
    try:
        # encoding=None 让 asyncssh 返回原始字节，编码在本地解码，避免服务器输出非 UTF-8 时解析出错
        async with asyncssh.connect(host, port=port, username=username, password=password, known_hosts=None) as conn:
            result = await asyncio.wait_for(conn.run(command, encoding=None), timeout=15)
            out = decode_output(result.stdout or b"").strip()
            err = decode_output(result.stderr or b"").strip()
            rc = result.exit_status
            if rc is None:
                # 服务器未返回退出码（如通过信号终止，或服务器不支持 exit-status）
                signal = getattr(result, "exit_signal", None)
                rc_text = f"signal {signal.get('name', '未知')}" if isinstance(signal, dict) else "未知"
            else:
                rc_text = str(rc)
            parts = [f"[exit {rc_text}]"]
            if out:
                parts.append(out)
            if err:
                parts.append(f"[stderr] {err}")
            if len(parts) == 1:
                parts.append("(命令执行完成，无输出)")
            text = "\n".join(parts)
            # 控制返回长度，避免爆 token
            return text[:2000] if len(text) > 2000 else text
    except Exception as e:
        return f"失败：SSH 执行出错 {type(e).__name__}: {e}"

def build_remote_path(username: str, filename: str, vm_name: str) -> str:
    """根据虚拟机名称推断远程路径。winxp/win7 → Windows 用户桌面，其他 → Linux home。"""
    safe_name = os.path.basename(filename)
    if vm_name in ("winxp", "win7"):
        return f"/C:/Users/{username}/Desktop/{safe_name}"
    return f"/home/{username}/{safe_name}"

async def vm_send_file(file_data: bytes, filename: str, vm_name: str) -> str:
    """通过 SFTP 将内存中的文件上传到虚拟机，返回远程路径或错误消息。"""
    target = parse_ssh_target(vm_name)
    if target is None:
        return f"失败：虚拟机 {vm_name} 未配置 SSH 连接方式"
    username, host, port, password = target
    remote_path = build_remote_path(username, filename, vm_name)
    try:
        async with asyncssh.connect(host, port=port, username=username,
                                    password=password, known_hosts=None) as conn:
            sftp = await conn.start_sftp_client()
            # 确保远程目录存在
            remote_dir = os.path.dirname(remote_path)
            try:
                if not await sftp.exists(remote_dir):
                    await sftp.makedirs(remote_dir)
            except Exception:
                pass
            # encoding=None 以二进制模式打开，write() 直接接受 bytes
            async with sftp.open(remote_path, 'w', encoding=None) as f:
                await f.write(file_data)
            return remote_path
    except Exception as e:
        return f"失败：SFTP 传输出错 {type(e).__name__}: {str(e)}"

async def download_to_memory(url: str, max_size: int = 1024 ** 3) -> bytes:
    """用 aiohttp 异步下载到内存，流式检查不超过 max_size（默认 1GB）。"""
    proxy = misc_manager.misc_data.get("http_proxy") or None
    chunk_size = 65536
    buf = io.BytesIO()
    downloaded = 0
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            if resp.status != 200:
                raise RuntimeError(f"下载失败，HTTP {resp.status}")
            content_length = resp.headers.get("Content-Length")
            if content_length:
                try:
                    if int(content_length) > max_size:
                        raise RuntimeError(f"文件大小 {content_length} 超过限制 {max_size}")
                except ValueError:
                    pass
            async for chunk in resp.content.iter_chunked(chunk_size):
                downloaded += len(chunk)
                if downloaded > max_size:
                    raise RuntimeError(f"文件大小超过 {max_size} 字节限制")
                buf.write(chunk)
    return buf.getvalue()

async def fetch_file_data(bot: Bot, seg_data: dict) -> bytes:
    """从 CQ:file 段下载文件到内存。优先本地路径读取，否则调用 get_file API 取 URL 下载。"""
    # 先尝试本地路径直接读取
    local_path = seg_data.get("file")
    if local_path and os.path.exists(local_path):
        with open(local_path, "rb") as f:
            return f.read()
    # 调用 OneBot get_file API 获取可访问 URL 或本地路径
    file_id = seg_data.get("file_id") or seg_data.get("file")
    if file_id:
        try:
            info = await bot.call_api("get_file", file_id=file_id)
            if info:
                api_path = info.get("file")
                api_url = info.get("url")
                if api_path and os.path.exists(api_path):
                    with open(api_path, "rb") as f:
                        return f.read()
                if api_url:
                    return await download_to_memory(api_url)
        except Exception as e:
            logger.warning(f"vmsend: get_file API 调用失败：{e}")
    # 回退：段自带的 url 字段
    seg_url = seg_data.get("url")
    if seg_url:
        return await download_to_memory(seg_url)
    raise RuntimeError("无法获取该文件，可能已过期")

# ===== /vmsend 指令 =====
vmsend = on_command("vmsend", aliases={"vmfile", "发送文件"}, priority=10, block=True)
@vmsend.handle()
async def handle_vm_send(bot: Bot = Bot, event: MessageEvent = Event):
    if not feature_manager.can_use("qemu", event.get_user_id()):
        raise FinishedException
    await ensure_vm_status()
    if not vm_powerstatus:
        await vmsend.finish("虚拟机未启动！")
    if vm_current_name is None:
        await vmsend.finish("无法确定当前运行的是哪台虚拟机，无法使用文件传输！")

    # 获取被回复消息
    import plugins.test1
    rep_con = await plugins.test1.get_reply_content(event.original_message, bot)
    if not rep_con or not isinstance(rep_con, list):
        await vmsend.finish("用法：[回复一个文件] /vmsend")

    # 查找 CQ:file 段
    file_seg = None
    for seg in rep_con:
        if isinstance(seg, dict) and seg.get("type") == "file":
            file_seg = seg
            break
    if file_seg is None:
        await vmsend.finish("请回复一个文件！用法：[回复一个文件] /vmsend")

    seg_data = file_seg.get("data", {})
    file_name = (seg_data.get("file_name") or seg_data.get("name")
                 or seg_data.get("file") or "file")
    # 只取文件名，避免路径穿越
    file_name = os.path.basename(str(file_name))
    if not file_name or file_name in (".", ".."):
        await vmsend.finish("文件名无效")

    # 下载到内存
    try:
        await vmsend.send(f"正在下载文件 {file_name} ...")
        file_bytes = await fetch_file_data(bot, seg_data)
    except RuntimeError as e:
        await vmsend.finish(str(e))
    except Exception as e:
        logger.error(f"vmsend: 下载文件异常：{e}")
        await vmsend.finish(f"文件下载失败：{e}")

    size_mb = len(file_bytes) / (1024 ** 2)
    await vmsend.send(f"文件下载完成（{size_mb:.1f} MB），正在通过 SSH 传输到虚拟机 ...")

    # SFTP 上传
    result = await vm_send_file(file_bytes, file_name, vm_current_name)
    if result.startswith("失败"):
        await vmsend.finish(result)

    await vmsend.finish(f"文件已上传到虚拟机：{result}")

# 工具 JSON Schema
vm_tools = [
    {
        "type": "function",
        "function": {
            "name": "vm_get_screenshot",
            "description": "获取虚拟机当前屏幕画面。在每一步操作前都必须先调用此工具查看屏幕状态。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vm_send_key",
            "description": "向虚拟机发送单个按键，如 ret（回车）、spc（空格）、esc、tab、up/down/left/right 等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "按键名称"},
                },
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vm_send_mouse",
            "description": "移动虚拟机鼠标到指定位置，可选点击或滚动。坐标为截图中目标的像素位置（左上角为原点，与 vm_get_screenshot 返回的画面一一对应）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "横坐标（像素，与截图对应）"},
                    "y": {"type": "integer", "description": "纵坐标（像素，与截图对应）"},
                    "button": {"type": "string", "enum": ["left", "right", "middle", "wheel-up", "wheel-down"], "description": "可选：点击的按键或滚轮方向，不填则仅移动鼠标"},
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vm_send_text",
            "description": "向虚拟机发送一段文本字符串。",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要输入的文本"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vm_ssh_run",
            "description": "通过 SSH 在当前虚拟机上直接执行一条 shell 命令，返回命令输出。适用于执行系统级操作、查看进程/文件、安装软件等，比逐个按键更高效。仅当当前虚拟机已配置 SSH 时可用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要在虚拟机内执行的 shell 命令"},
                },
                "required": ["command"],
            },
        },
    },
]

VM_SYSTEM_PROMPT = (
    "你是一个虚拟机操作助手。你正在控制一台运行 Windows 的 QEMU 虚拟机。"
    "你可以通过工具查看屏幕、移动/点击鼠标、发送按键、输入文本，以及通过 SSH 在虚拟机内直接执行 shell 命令。"
    "规则："
    "1. 每一步操作前必须先调用 vm_get_screenshot 查看当前屏幕。"
    "2. 需要点击界面元素时，用 vm_send_mouse，坐标以截图中目标的像素位置为准；点击后应再截图确认效果。"
    "3. 输入文字用 vm_send_text，配合 vm_send_key 发送回车等按键。"
    "4. 需要执行系统级操作（查看文件/进程、运行程序、修改配置等）时，优先用 vm_ssh_run 直接执行命令，比模拟按键更高效。"
    "5. 如果任务可以完全通过 SSH 命令完成、无需查看屏幕画面，就只用 vm_ssh_run，不要调用 vm_get_screenshot。"
    "6. 你最多只能连续操作 10 轮工具，之后必须总结。"
    "7. 当任务完成或你认为无法继续时，直接文字回复，不要调用工具。"
    "8. 回复要简洁，说明当前状态或结果。"
)

async def run_ds_qemu(prompt: str, stop_flag: list = None):
    """执行 AI 虚拟机操作，返回 (AI回复文本, 过程GIF路径或None, 过程截图路径列表)。
    stop_flag 为可变列表，若外部置 stop_flag[0] = True，则下一步循环强制总结并停止。"""
    ds.reload_client(ds.config["current_engine"])
    client = ds.client
    # 截图分析需要视觉模型，按 analyze_image 的逻辑为各引擎切换到支持图片的模型
    model_index = ds.config["model_index_prio"]
    if ds.config["current_engine"] == "kimi":
        model_index = 1
    if ds.config["current_engine"] == "zhipu":
        model_index = 1
    if ds.config["current_engine"] == "deepseek":
        model_index = 0
    model = ds.config[ds.config["current_engine"]]["models"][model_index]

    messages = [
        {"role": "system", "content": VM_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    max_steps = 10
    process_images = []
    final_reply = ""
    # 本轮是否用到 GUI（截图/鼠标/键盘/打字）；纯 SSH 后台操作为 False
    gui_used = False
    GUI_TOOLS = ("vm_get_screenshot", "vm_send_mouse", "vm_send_key", "vm_send_text")
    # 收到 /stopdsqemu 时由 handler 置位，AI 循环在下一步开始前检测并转入总结
    stop_requested = False
    if stop_flag is None:
        stop_flag = [False]

    def _build_summary_request(reason: str) -> str:
        return (
            f"【操作结束：{reason}】"
            "请总结本次操作：1) 你依次执行了哪些操作及结果；2) 任务完成度。"
            "若任务未完成，请说明下一步该如何继续，以及用户应如何用新的 /dsqemu 指令让你接着完成剩余工作。"
        )

    for step in range(max_steps):
        stop_requested = stop_flag[0]
        current_tools = vm_tools
        current_tool_choice = "auto"
        force_summary = False
        # 用户请求停止或到达最后一步时，强制 AI 直接回复总结
        if stop_requested:
            force_summary = True
            current_tools = None
            current_tool_choice = None
            messages.append({"role": "user", "content": _build_summary_request("用户要求停止")})
        elif step == max_steps - 1:
            force_summary = True
            current_tools = None
            current_tool_choice = None

        try:
            resp = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=current_tools,
                tool_choice=current_tool_choice,
                stream=False,
            )
        except Exception as e:
            logger.error(f"dsqemu API 调用失败: {e}")
            return f"AI 操作虚拟机失败：{str(e)}", None, process_images
        remsg = resp.choices[0].message

        if remsg.tool_calls:
            # 记录 AI 的 tool_call 消息
            messages.append(remsg)
            tool_outputs = []
            screenshot_b64s = []
            for tool_call in remsg.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                if func_name in GUI_TOOLS:
                    gui_used = True
                try:
                    if func_name == "vm_get_screenshot":
                        b64, img_path = await tool_vm_get_screenshot(step)
                        # 兼容层的 tool 消息只支持文本，截图以 user 消息形式补发
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": func_name,
                            "content": "截图已获取，当前屏幕画面见随后的图片消息。",
                        })
                        # 记录关键截图（截图工具调用）
                        process_images.append(img_path)
                        screenshot_b64s.append(b64)
                    elif func_name == "vm_send_key":
                        result = await tool_vm_send_key(func_args.get("key", ""))
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": func_name,
                            "content": result,
                        })
                    elif func_name == "vm_send_mouse":
                        result = await tool_vm_send_mouse(
                            int(func_args.get("x", 0)),
                            int(func_args.get("y", 0)),
                            func_args.get("button"),
                        )
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": func_name,
                            "content": result,
                        })
                    elif func_name == "vm_send_text":
                        result = await tool_vm_send_text(func_args.get("text", ""))
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": func_name,
                            "content": result,
                        })
                    elif func_name == "vm_ssh_run":
                        result = await tool_vm_ssh_run(func_args.get("command", ""))
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": func_name,
                            "content": result,
                        })
                    else:
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": func_name,
                            "content": f"[未知工具：{func_name}]",
                        })
                except Exception as e:
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": func_name,
                        "content": f"[工具执行失败：{str(e)}]",
                    })
            messages.extend(tool_outputs)
            # Gemini 等 OpenAI 兼容层的 tool 消息不支持图片，截图以 user 消息形式补发给 AI
            if screenshot_b64s:
                image_content = [{"type": "text", "text": "以下是本次截取的虚拟机屏幕画面："}]
                for b64 in screenshot_b64s:
                    image_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    })
                messages.append({"role": "user", "content": image_content})
        else:
            # AI 直接回复，结束循环
            final_reply = remsg.content or "AI 未给出回复。"
            break

    if not final_reply:
        if stop_requested:
            final_reply = "已收到停止指令，但 AI 未能生成总结。"
        else:
            final_reply = f"已达到最大操作步数（{str(max_steps)}步），AI 未能生成总结。"

    # 达到最大步数且 AI 未主动结束时，追加一次总结请求，让 AI 报告已做操作和下一步建议
    if not stop_requested and step == max_steps - 1 and remsg.tool_calls:
        try:
            messages.append({"role": "user", "content": _build_summary_request("已达到最大操作步数")})
            resp = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=None,
                tool_choice=None,
                stream=False,
            )
            summary_msg = resp.choices[0].message
            if summary_msg.content:
                final_reply = summary_msg.content
        except Exception as e:
            logger.error(f"dsqemu 总结请求失败: {e}")

    # 仅当本轮用到了 GUI 操作时才截取最终画面并合成 GIF；
    # 纯 SSH 后台操作不涉及画面，跳过，不发送截图
    if gui_used:
        # 操作结束后补一张最终画面截图
        try:
            final_img_path = path_manager.nb_path() + "images/qemu/xp_final.png"
            host, port = get_vnc_address()
            async with asyncvnc.connect(host, port) as client:
                rgba = await client.screenshot()
                bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
                cv2.imwrite(final_img_path, bgr)
            process_images.append(final_img_path)
        except Exception:
            pass

    # 将全部过程截图（含最终画面）合成 1fps GIF
    gif_path = None
    if process_images:
        try:
            frames = []
            for p in process_images:
                img = Image.open(p).convert("RGB")
                # 控制体积：宽度超过 1024 时等比缩小
                if img.width > 1024:
                    ratio = 1024 / img.width
                    img = img.resize((1024, int(img.height * ratio)))
                frames.append(img)
            gif_path = path_manager.nb_path() + "images/qemu/xp_process.gif"
            frames[0].save(gif_path, save_all=True, append_images=frames[1:],
                           duration=1000, loop=0, optimize=True)
        except Exception as e:
            logger.error(f"dsqemu GIF 合成失败: {e}")
            gif_path = None

    return final_reply, gif_path, process_images

# 全局 stop flag，用于 /stopdsqemu 停止 AI 虚拟机操作
_dsqemu_stop_flag = [False]

dsqemu = on_command("dsqemu", aliases={"deepseekqemu", "AI操作虚拟机"}, priority=10, block=True)
@dsqemu.handle()
async def handle_ds_qemu(args: Message = CommandArg(), event: Event = Event):
    # 同时检查 deepseek 和 qemu 两个开关
    if not feature_manager.can_use("deepseek", event.get_user_id()):
        raise FinishedException
    if not feature_manager.can_use("qemu", event.get_user_id()):
        raise FinishedException

    if "dsqemu" in misc_manager.tasks:
        await dsqemu.finish("AI 正在操作虚拟机，请稍后再试！")
    await ensure_vm_status()
    if not vm_powerstatus:
        await dsqemu.finish("虚拟机未启动！请先使用 /startvm [虚拟机名称] 启动。")

    prompt = args.extract_plain_text().strip()
    if not prompt:
        await dsqemu.finish("用法：/dsqemu [你想让 AI 在虚拟机里做的事]")

    _dsqemu_stop_flag[0] = False
    misc_manager.tasks.append("dsqemu")
    try:
        await dsqemu.send("AI 开始操作，请稍候...")
        reply, gif_path, images = await run_ds_qemu(prompt, _dsqemu_stop_flag)

        # 发送 AI 回复
        await dsqemu.send(reply)

        # 发送过程动图；合成失败时回退为逐张发送；无截图（纯后台操作）则跳过
        if gif_path:
            await dsqemu.send(Message("[CQ:image,file=file:///" + path_manager.bf_path() + "images/qemu/xp_process.gif]"))
        elif images:
            for img_path in images:
                await dsqemu.send(Message(f"[CQ:image,file=file:///{path_manager.bf_path()}images/qemu/{img_path.split('/')[-1]}]"))
    finally:
        misc_manager.tasks.remove("dsqemu")
        _dsqemu_stop_flag[0] = True
    raise FinishedException

stopdsqemu = on_command("stopdsqemu", aliases={"停止AI操控"}, priority=10, block=True)
@stopdsqemu.handle()
async def handle_stop_ds_qemu(args: Message = CommandArg(), event: Event = Event):
    if not feature_manager.can_use("qemu", event.get_user_id()):
        raise FinishedException
    if "dsqemu" not in misc_manager.tasks:
        await stopdsqemu.finish("当前没有 AI 正在操作虚拟机！")
    _dsqemu_stop_flag[0] = True
    await stopdsqemu.finish("已收到停止指令，AI 将在完成当前步骤后总结并停止。")
