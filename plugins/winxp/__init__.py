from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
import asyncio
from nonebot.exception import FinishedException
import path_manager
from qemu.qmp import QMPClient
import feature_manager

vm_powerstatus = 0

async def run_winxp():
    await asyncio.create_subprocess_exec("C:\\Program Files\\qemu\\qemu-system-x86_64.exe", "-accel", "whpx,kernel-irqchip=off", "-m", "96m", "-qmp", "tcp:0.0.0.0:4444,server,nowait", "-drive", "file=D:\\vms\\qemu\\nanoxp.vhd,if=ide", "-display", "vnc=:0")
    global vm_powerstatus
    vm_powerstatus = 1
    return

async def connect_qemu():
    client = QMPClient('my-vm')
    await client.connect(('localhost', 4444))
    return client

async def xp_ss():
    client = await connect_qemu()
    await client.execute('screendump',{"filename": path_manager.nb_path()+"images/qemu/xp.png", "format": "png"})
    await client.disconnect()
    return (Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/qemu/xp.png]'))

async def xp_sendkey(key):
    client = await connect_qemu()
    await client.execute("human-monitor-command",{"command-line": "sendkey "+key})
    await client.disconnect()
    return

async def xp_sendtext(text):
    client = await connect_qemu()
    for i in text:
        keys: dict[str, str] = {" ": "spc","\n": "ret", ".": "dot", "/": "slash", "\\": "backslash", "-": "minus", "+": "plus"}
        thekey = keys.get(i)
        if thekey is None:
            thekey = i
        await client.execute("human-monitor-command",{"command-line": "sendkey "+thekey})
    await client.disconnect()
    return

async def xp_poweroff():
    client = await connect_qemu()
    await client.execute('quit')
    await client.disconnect()
    global vm_powerstatus
    vm_powerstatus = 0
    return

winxp = on_command("winxp", aliases={"启动xp","启动winxp","启动qemu"}, priority=10, block=True)
@winxp.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("qemu"):
        raise FinishedException
    if vm_powerstatus == 1:
        await xpsendkey.finish("虚拟机已经在运行！")
    await run_winxp()
    await asyncio.sleep(10)
    await xpsendkey.finish(await xp_ss())

sswinxp = on_command("sswinxp", aliases={"xp截图","vmss","虚拟机截图"}, priority=10, block=True)
@sswinxp.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("qemu"):
        raise FinishedException
    if not vm_powerstatus:
        await sswinxp.finish("虚拟机未启动！")
    await sswinxp.finish(await xp_ss())

xpsendkey = on_command("xpsendkey", aliases={"xp发送按键","vmsendkey","虚拟机发送按键"}, priority=10, block=True)
@xpsendkey.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("qemu"):
        raise FinishedException
    if not vm_powerstatus:
        await xpsendkey.finish("虚拟机未启动！")
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
    if not vm_powerstatus:
        await xptype.finish("虚拟机未启动！")
    text = args.extract_plain_text()
    await xp_sendtext(text)
    await asyncio.sleep(1)
    await xptype.finish(await xp_ss())

xpshut = on_command("xpshut", aliases={"xp关机","vmshut","虚拟机关机","poweroff"}, priority=10, block=True)
@xpshut.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("qemu"):
        raise FinishedException
    if not vm_powerstatus:
        await xpshut.finish("虚拟机已经关机或未启动！")
    await xp_poweroff()
    await xpshut.finish("已关闭xp系统。")