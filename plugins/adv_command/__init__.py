# 高级指令（只能被 wzq2002 [2975499623] 触发）
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import asyncio
import chardet
import feature_manager
import webss
import web
import privilege_manager
import os

from nonebot_plugin_saa import MessageFactory, TargetQQGroup
from nonebot_plugin_saa import enable_auto_select_bot
enable_auto_select_bot()

echocq = on_command("echocq", aliases={"复读CQ","cq"}, priority=10, block=True)
@echocq.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) and feature_manager.get("echocq"):
        await echocq.finish(Message(args.extract_plain_text()))
    else:
        raise FinishedException

# 定向发送（至群聊）
tar_send = on_command("send", aliases={"targetsend","定向发送","snd","sendcq"}, priority=10, block=True)
@tar_send.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    # 改为所有人可用
    if feature_manager.get("targetsend"):
        data = args.extract_plain_text().split()
        if len(data) > 1 and str.isdigit(data[0]):
            grnum = data[0]
            data.remove(data[0])
            target = TargetQQGroup(group_id=int(grnum))
            await MessageFactory(data).send_to(target=target)
            raise FinishedException
        else:
            await tar_send.finish("参数错误。使用方法：/send [群号] [文本内容]")
    else:
        raise FinishedException

cmd = on_command("cmd", aliases={"shell","exec"}, priority=10, block=True)
@cmd.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    # 限定超管可用
    if privilege_manager.checkuser(event.get_user_id()) == 2 and feature_manager.get("cmd"):
        # res = subprocess.run(['cmd', '/c', args.extract_plain_text()], capture_output=True, text=True)
        proc = await asyncio.create_subprocess_exec('cmd', '/c', args.extract_plain_text(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        await proc.wait()
        out_d = stdout.decode(chardet.detect(stdout)['encoding'] or 'utf-8')
        err_d = stderr.decode(chardet.detect(stderr)['encoding'] or 'utf-8')
        resp = out_d + err_d
        # print(type(stdout),type(resp))
        if resp != "":
            await cmd.finish(resp)
        else:
            raise FinishedException
    else:
        raise FinishedException

# 网页截图（实验性功能）
webscrnshot = on_command("webss", aliases={"网页截图"}, priority=10, block=True)
@webscrnshot.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) and feature_manager.get("webss"):
        webss.take(args.extract_plain_text())
        await webscrnshot.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/webss/1.png]'))
    else:
        raise FinishedException

fea1 = on_command("fealist", aliases={"功能列表","features"}, priority=10, block=True)
@fea1.handle()
async def handle_function(event: Event):
    if privilege_manager.checkuser(event.get_user_id()):
        await fea1.finish(feature_manager.get_all_features())
        #web.content_text(feature_manager.get_all_features())
        #webss.take2("http://localhost:8104","container")
        #await fea1.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/webss/1.png]'))
    else:
        raise FinishedException
    
fea2 = on_command("feaenable", aliases={"启用功能","enable"}, priority=10, block=True)
@fea2.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()):
        resp = feature_manager.enable(args.extract_plain_text())
        await fea2.finish(resp)
    else:
        raise FinishedException
    
fea3 = on_command("feadisable", aliases={"禁用功能","disable"}, priority=10, block=True)
@fea3.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()):
        resp = feature_manager.disable(args.extract_plain_text())
        await fea3.finish(resp)
    else:
        raise FinishedException
    
fea4 = on_command("importfea", aliases={"导入功能列表","import"}, priority=10, block=True)
@fea4.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()):
        resp = feature_manager.import_fea_list(args.extract_plain_text())
        await fea4.finish(resp)
    else:
        raise FinishedException

addadmin = on_command("addadmin", aliases={"添加管理员","admin","adduser"}, priority=10, block=True)
@addadmin.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    # if event.get_user_id() == w_qqid:
    if privilege_manager.checkuser(event.get_user_id()) == 2:
        valu = args.extract_plain_text()
        if str.isdigit(valu):
            await addadmin.finish(privilege_manager.add_admin(valu))
        else:
            await addadmin.finish("参数错误。用法：/admin [要添加为管理员的QQ号]")
    else:
        raise FinishedException
    
remadmin = on_command("remadmin", aliases={"移除管理员","noadmin","remuser"}, priority=10, block=True)
@remadmin.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) == 2:
        valu = args.extract_plain_text()
        if str.isdigit(valu):
            await remadmin.finish(privilege_manager.rem_admin(valu))
        else:
            await remadmin.finish("参数错误。用法：/admin [要添加为管理员的QQ号]")
    else:
        raise FinishedException
    
admlis = on_command("adminlist", aliases={"管理员列表","userlist","用户列表"}, priority=10, block=True)
@admlis.handle()
async def handle_function(event: Event):
    if privilege_manager.checkuser(event.get_user_id()):
        await remadmin.finish(privilege_manager.get_admin_list())
    else:
        raise FinishedException    

# 重载bot
reload = on_command("reload", aliases={"重载bot","reboot"}, priority=10, block=True)
@reload.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()):
        await reload.send("我重生啦！")
        #e = open("reload_triggered","w")
        #e.write(event.get_session_id())
        f = open("plugins/placeholder/__init__.py","w")
        f.write(" ")
    else:
        raise FinishedException

"""
# 触发重载后，下次 bot 启动时动作
if os.path.exists("reload_triggered"):
    f = open("reload_triggered","r")
    fr = f.read()
    f.close()
    if fr.startswith("group"):
        # 获取群id
        grnum = fr.split("_")[1]
        target = TargetQQGroup(group_id=int(grnum))
"""

# bot调试
b_debug = on_command("debug", aliases={"调试","测试"}, priority=10, block=True)
@b_debug.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    # 限定超管可用
    if privilege_manager.checkuser(event.get_user_id()) == 2:
        eval(args.extract_plain_text())
    raise FinishedException