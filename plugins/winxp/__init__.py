from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
import asyncio
from nonebot.exception import FinishedException
import path_manager
from qemu.qmp import QMPClient
import feature_manager

async def run_winxp():
    await asyncio.create_subprocess_exec("C:\\Program Files\\qemu\\qemu-system-x86_64.exe", "-accel", "whpx,kernel-irqchip=off", "-m", "96m", "-qmp", "tcp:0.0.0.0:4444,server,nowait", "-drive", "file=D:\\vms\\qemu\\nanoxp.vhd,if=ide", "-display", "vnc=:0")
    return

async def connect_qemu():
    client = QMPClient('my-vm')
    await client.connect(('localhost', 4444))
    return client

async def xp_ss():
    client = await connect_qemu()
    await client.execute('screendump',{"filename": path_manager.nb_path()+"images/qemu/xp.ppm"})
    await client.disconnect()
    proc = await asyncio.create_subprocess_exec("ffmpeg.exe", "-y", "-i", path_manager.nb_path()+"images/qemu/xp.ppm", path_manager.nb_path()+"images/qemu/xp.png")
    await proc.wait()
    return (Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/qemu/xp.png]'))

async def xp_sendkey(key):
    client = await connect_qemu()
    await client.execute("human-monitor-command",{"command-line": "sendkey "+key})
    await client.disconnect()
    return

async def xp_sendtext(text):
    client = await connect_qemu()
    for i in text:
        await client.execute("human-monitor-command",{"command-line": "sendkey "+i})
    await client.disconnect()
    return

winxp = on_command("winxp", priority=10, block=True)
@winxp.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("qemu"):
        raise FinishedException
    await run_winxp()
    await asyncio.sleep(10)
    await xpsendkey.finish(await xp_ss())

sswinxp = on_command("sswinxp", aliases={"xp截图","vmss","虚拟机截图"}, priority=10, block=True)
@sswinxp.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("qemu"):
        raise FinishedException
    await sswinxp.finish(await xp_ss())

xpsendkey = on_command("xpsendkey", aliases={"xp发送按键","vmsendkey","虚拟机发送按键"}, priority=10, block=True)
@xpsendkey.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("qemu"):
        raise FinishedException
    text = args.extract_plain_text()
    key = text.split(" ")[0]
    await xp_sendkey(key)
    await asyncio.sleep(1)
    await xpsendkey.finish(await xp_ss())

xptype = on_command("xptype", aliases={"xp发送文本","vmtype","虚拟机发送文本"}, priority=10, block=True)
@xptype.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("qemu"):
        raise FinishedException
    text = args.extract_plain_text()
    await xp_sendtext(text)
    await asyncio.sleep(1)
    await xptype.finish(await xp_ss())