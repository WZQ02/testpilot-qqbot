# 高级指令（只能被 wzq2002 [2975499623] 触发）
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.exception import FinishedException
import asyncio
import chardet
import feature_manager
import webss
import web
import privilege_manager
import os
import path_manager
import achievement_manager
import misc_manager
import re

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
tar_send = on_command("send", aliases={"targetsend","定向发送","snd","sendcq","隔空传话"}, priority=10, block=True)
@tar_send.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    # 改为所有人可用
    if feature_manager.get("targetsend"):
        data = args.extract_plain_text().split()
        if len(data) > 1 and str.isdigit(data[0]):
            grnum = data[0]
            data.remove(data[0])
            target = TargetQQGroup(group_id=int(grnum))
            await MessageFactory(" ".join(data)).send_to(target=target)
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
        cmd_pa1 = "cmd"
        cmd_pa2 = "/c"
        if path_manager.pat_list["sys_env"] == "linux":
            cmd_pa1 = "bash"
            cmd_pa2 = "-c"
        proc = await asyncio.create_subprocess_exec(cmd_pa1, cmd_pa2, args.extract_plain_text(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        await proc.wait()
        out_e = chardet.detect(stdout)['encoding']
        err_e = chardet.detect(stderr)['encoding']
        out_d = stdout.decode(out_e or 'utf-8')
        err_d = stderr.decode(err_e or 'utf-8')
        resp = out_d + err_d
        # print(type(stdout),type(resp))
        # print("命令输出编码为 "+out_e+"、"+err_e+"。")
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
        await webss.take(args.extract_plain_text())
        await webscrnshot.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))
    else:
        raise FinishedException

fea1 = on_command("fealist", aliases={"功能列表","features"}, priority=10, block=True)
@fea1.handle()
async def handle_function(event: Event):
    if privilege_manager.checkuser(event.get_user_id()):
        await fea1.finish(feature_manager.get_all_features())
        #web.content_text(feature_manager.get_all_features())
        #await webss.take2("http://localhost:8104","container")
        #await fea1.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))
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
    
fea5 = on_command("preset", aliases={"功能预设"}, priority=10, block=True)
@fea5.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()):
        ps_name = args.extract_plain_text()
        res = "已启用预设："+ps_name
        if ps_name == "enableall":
            feature_manager.import_fea_list("{\"actualhelp\":1,\"autorepeat\":1,\"ccb\":1,\"cmd\":1,\"deepseek\":1,\"echo\":1,\"echocq\":1,\"explain\":1,\"flipoff\":1,\"help\":1,\"meme_resp\":1,\"meme_resp_laicai\":1,\"meme_resp_mai\":1,\"meme_resp_mygo\":1,\"meme_resp_sex\":1,\"ping\":1,\"poem\":1,\"poke\":1,\"qrcode\":1,\"rand_num\":1,\"rand_pic\":1,\"randomcs\":1,\"rendermd\":1,\"repeat\":1,\"revoke\":1,\"tag_1\":1,\"tag_2\":1,\"targetsend\":1,\"video_web\":1,\"webss\":1,\"wzs\":1}")
        elif ps_name == "disableall":
            feature_manager.import_fea_list("{\"actualhelp\":0,\"autorepeat\":0,\"ccb\":0,\"cmd\":0,\"deepseek\":0,\"echo\":0,\"echocq\":0,\"explain\":0,\"flipoff\":0,\"help\":0,\"meme_resp\":0,\"meme_resp_laicai\":0,\"meme_resp_mai\":0,\"meme_resp_mygo\":0,\"meme_resp_sex\":0,\"ping\":0,\"poem\":0,\"poke\":0,\"qrcode\":0,\"rand_num\":0,\"rand_pic\":0,\"randomcs\":0,\"rendermd\":0,\"repeat\":0,\"revoke\":0,\"tag_1\":0,\"tag_2\":0,\"targetsend\":0,\"video_web\":0,\"webss\":0,\"wzs\":0}")
        elif ps_name == "allmeme":
            feature_manager.import_fea_list("{\"meme_resp\":1,\"meme_resp_laicai\":1,\"meme_resp_mai\":1,\"meme_resp_mygo\":1,\"meme_resp_sex\":1}")
        elif ps_name == "nomeme":
            feature_manager.import_fea_list("{\"meme_resp\":0,\"meme_resp_laicai\":0,\"meme_resp_mai\":0,\"meme_resp_mygo\":0,\"meme_resp_sex\":0}")
        elif ps_name == "passive":
            feature_manager.import_fea_list("{\"actualhelp\":1,\"autorepeat\":0,\"ccb\":1,\"cmd\":1,\"deepseek\":1,\"echo\":1,\"echocq\":1,\"explain\":1,\"flipoff\":1,\"help\":1,\"meme_resp\":0,\"meme_resp_laicai\":0,\"meme_resp_mai\":0,\"meme_resp_mygo\":0,\"meme_resp_sex\":0,\"ping\":1,\"poem\":1,\"poke\":1,\"qrcode\":1,\"rand_num\":1,\"rand_pic\":1,\"randomcs\":1,\"rendermd\":1,\"repeat\":1,\"revoke\":1,\"tag_1\":1,\"tag_2\":1,\"targetsend\":1,\"video_web\":1,\"webss\":1,\"wzs\":1}")
        elif ps_name == "justtool":
            feature_manager.import_fea_list("{\"actualhelp\":1,\"autorepeat\":0,\"ccb\":0,\"cmd\":1,\"deepseek\":1,\"echo\":1,\"echocq\":1,\"explain\":1,\"flipoff\":0,\"help\":0,\"meme_resp\":0,\"meme_resp_laicai\":0,\"meme_resp_mai\":0,\"meme_resp_mygo\":0,\"meme_resp_sex\":0,\"ping\":1,\"poem\":0,\"poke\":0,\"qrcode\":1,\"rand_num\":1,\"rand_pic\":0,\"randomcs\":0,\"rendermd\":1,\"repeat\":0,\"revoke\":1,\"tag_1\":1,\"tag_2\":1,\"targetsend\":1,\"video_web\":1,\"webss\":1,\"wzs\":1}")
        else:
            res = "未找到指定的预设。可用的预设有：enableall（启用全部功能）、disableall（禁用全部功能）、allmeme（关键词回应全启用）、nomeme（关键词不回应）、passive（被动模式）、justtool（工具模式）"
        await fea5.finish(res)
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
async def handle_function(event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()):
        if len(misc_manager.tasks) < 1:
            await reload.send("收到！重启中。。。")
            #e = open("reload_triggered","w")
            #e.write(event.get_session_id())
            f = open("plugins/placeholder/__init__.py","w")
            f.write(" ")
        else:
            await reload.send("当前有任务正在进行，稍后再试吧！\n正在进行的任务有："+str(misc_manager.tasks))
    else:
        raise FinishedException
    
# 强制重载
forcereload = on_command("forcereload", aliases={"强制重载"}, priority=10, block=True)
@forcereload.handle()
async def handle_function(event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()):
        await reload.send("注意，我要重启了，谁都别拦着我！")
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

# bot调试（同步函数）
b_debug = on_command("debug", aliases={"调试","测试","botdbg"}, priority=10, block=True)
@b_debug.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    # 限定超管可用
    if privilege_manager.checkuser(event.get_user_id()) == 2:
        bot = get_bot()
        exec(args.extract_plain_text())
    raise FinishedException

"""
# bot调试（异步函数）
b_debug2 = on_command("debug2", aliases={"adebug","异步调试","botdbg2"}, priority=10, block=True)
@b_debug2.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    # 限定超管可用
    if privilege_manager.checkuser(event.get_user_id()) == 2:
        bot = get_bot()
        await asyncio.eval(args.extract_plain_text())
    raise FinishedException
"""

# 广播（发送至bot所在所有群聊）
broad = on_command("sendall", aliases={"broadcast","广播"}, priority=10, block=True)
@broad.handle()
async def handle_function(args: Message = CommandArg(),event: Event = Event):
    if (privilege_manager.checkuser(event.get_user_id()) and feature_manager.get("targetsend")) or misc_manager.april_fools_flag():
        bot = get_bot()
        gr_list = await bot.get_group_list()
        if len(args) > 0:
            for i in gr_list:
                target = TargetQQGroup(group_id=int(i["group_id"]))
                try:
                    await MessageFactory(args.extract_plain_text()).send_to(target=target)
                except Exception as e:
                    print(e)
                # asyncio.sleep(.2)
        raise FinishedException
    else:
        raise FinishedException

# 切换path环境
switch_sys_env = on_command("switchsys", priority=10, block=True)
@switch_sys_env.handle()
async def handle_function(event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) == 2:
        await switch_sys_env.finish(path_manager.switch_sys_env())
    else:
        raise FinishedException

# 询问path环境
ask_sys_env = on_command("asksys", priority=10, block=True)
@ask_sys_env.handle()
async def handle_function(event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) == 2:
        await ask_sys_env.finish(path_manager.ask_sys())
    else:
        raise FinishedException
    
# 查看成就获得人数
achi_ask = on_command("askachi", priority=10, block=True)
@achi_ask.handle()
async def handle_function(event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()):
        list = achievement_manager.getachicountlist()
        resp = "成就系统记录："
        for i in list:
            resp += "\n"+list[i]["name"]+" - 触发次数："+str(list[i]["usecount"])
        await achi_ask.finish(resp)
    else:
        raise FinishedException

# 查看bot运行日志（markdown，linux only）
viewlog = on_command("viewlog", aliases={"日志","查看日志"}, priority=10, block=True)
@viewlog.handle()
async def handle_function(event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) and feature_manager.get("rendermd"):
        if os.path.exists('nohup.out'):
            with open('nohup.out', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_lines = lines[-100:]
                log = (''.join(last_lines))
                log = re.sub(r'\r\n|\r|\n', '<br>', log)
            web.content_md(log)
            await webss.take2("http://localhost:8104","container")
            await viewlog.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'webss/1.png]'))
        else:
            await viewlog.finish("没有找到nohup输出！（此命令仅在bot以nohup方式运行时适用）")
    else:
        raise FinishedException

# ==================== 录播姬管理（仅超管） ====================
import httpx

RECORDER_BASE = "http://192.168.2.5:2356"
RECORDER_TIMEOUT = 10.0

async def rec_api(method: str, path: str, json_body=None):
    """调用录播姬 REST API。
    返回 (status_code, data)：成功时 data 为解析后的 JSON（或 None），
    失败时 data 为错误文本。
    """
    url = RECORDER_BASE + path
    try:
        async with httpx.AsyncClient(timeout=RECORDER_TIMEOUT) as client:
            resp = await client.request(method, url, json=json_body)
            if resp.status_code == 200:
                try:
                    return resp.status_code, resp.json()
                except Exception:
                    return resp.status_code, None
            return resp.status_code, resp.text
    except httpx.RequestError as e:
        return -1, str(e)
    except Exception as e:
        return -2, str(e)

async def get_room_name(room_id: int) -> str:
    """操作完成后重新获取房间信息，返回播主名称（取不到则返回"未知"）。"""
    status, data = await rec_api("GET", f"/api/room/{room_id}")
    if status == 200 and isinstance(data, dict):
        return data.get("name") or "未知"
    return "未知"

def _escape_html(text: str) -> str:
    """转义 HTML 特殊字符，防止注入破坏模板结构。"""
    if not text:
        return ""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

async def render_room_list(rooms: list, mode: str = "all"):
    """渲染房间列表为图片并写入 webss/1.png。
    mode='all' 渲染全部房间；mode='live' 只渲染正在直播的房间。
    """
    import os
    template_path = "web/templates/room_list/index.html"
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"模板文件不存在：{template_path}")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    total_all = len(rooms)
    streaming_all = sum(1 for r in rooms if r.get("streaming"))
    recording_all = sum(1 for r in rooms if r.get("recording"))

    if mode == "live":
        display_rooms = [r for r in rooms if r.get("streaming")]
    else:
        display_rooms = rooms

    # 生成 header 文本
    if mode == "all":
        header_text = f"当前已添加 {total_all} 个直播间，{streaming_all} 个正在直播，{recording_all} 个正在录制："
    else:
        recording_live = sum(1 for r in display_rooms if r.get("recording"))
        header_text = f"当前有 {len(display_rooms)} 人正在直播，{recording_live} 个正在录制："

    # 生成卡片 HTML
    cards_html = ""
    for r in display_rooms:
        connected = r.get("danmakuConnected")
        dot_color = "#7CB342" if connected else "#E53935"
        name = _escape_html(r.get("name") or "未知")
        room_id = r.get("roomId") or r.get("shortId") or 0
        badges_html = ""
        if r.get("streaming"):
            title = _escape_html(r.get("title") or "")
            badges_html += f'<span class="badge badge-live">正在直播：{title}</span>'
        if r.get("recording"):
            badges_html += '<span class="badge badge-rec">正在录制</span>'
        cards_html += (
            f'<div class="card">'
            f'<span class="dot" style="background:{dot_color}"></span>'
            f'<span class="name">{name}</span>'
            f'<span class="sep">·</span>'
            f'<span class="roomid">{room_id}</span>'
            f'<div class="badges">{badges_html}</div>'
            f'</div>'
        )

    html = template.replace("<!-- HEADER -->", header_text).replace("<!-- ROOM_CARDS -->", cards_html)
    web.change_content(html)
    await webss.take2("http://localhost:8104", "container")

# 房间列表
room_list = on_command("房间列表", aliases={"roomlist","rooms"}, priority=10, block=True)
@room_list.handle()
async def handle_function(event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) != 2:
        raise FinishedException
    status, data = await rec_api("GET", "/api/room")
    if status != 200 or not isinstance(data, list):
        await room_list.finish(f"获取房间列表失败：{data}")
    if not data:
        await room_list.finish("当前没有添加任何直播间。")
    await render_room_list(data, mode="all")
    await room_list.finish(Message(f'[CQ:image,file=file:///{path_manager.bf_path()}webss/1.png]'))

# 正在直播
living_list = on_command("正在直播", aliases={"living","live"}, priority=10, block=True)
@living_list.handle()
async def handle_function(event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) != 2:
        raise FinishedException
    status, data = await rec_api("GET", "/api/room")
    if status != 200 or not isinstance(data, list):
        await living_list.finish(f"获取房间列表失败：{data}")
    living = [r for r in data if r.get("streaming")]
    if not living:
        await living_list.finish("当前没有人在直播哦。")
    await render_room_list(data, mode="live")
    await living_list.finish(Message(f'[CQ:image,file=file:///{path_manager.bf_path()}webss/1.png]'))

# 添加房间
add_room = on_command("添加房间", aliases={"addroom","addroomid"}, priority=10, block=True)
@add_room.handle()
async def handle_function(args: Message = CommandArg(), event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) != 2:
        raise FinishedException
    room_id_str = args.extract_plain_text().strip()
    if not room_id_str.isdigit():
        await add_room.finish("请提供有效的房间号，例如：/添加房间 4947891")
    room_id = int(room_id_str)
    status, data = await rec_api("POST", "/api/room", json_body={"roomId": room_id, "autoRecord": True})
    if status == 200:
        name = await get_room_name(room_id)
        await add_room.finish(f"已添加房间 {room_id}（{name}）并开启自动录制。")
    elif status == 400:
        await add_room.finish(f"添加失败，房间号 {room_id} 可能无效或已存在。")
    else:
        await add_room.finish(f"添加失败：{data}")

# 停止录制
stop_rec = on_command("停止录制", aliases={"stoprec","stoprecord"}, priority=10, block=True)
@stop_rec.handle()
async def handle_function(args: Message = CommandArg(), event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) != 2:
        raise FinishedException
    room_id_str = args.extract_plain_text().strip()
    if not room_id_str.isdigit():
        await stop_rec.finish("请提供有效的房间号，例如：/停止录制 4947891")
    room_id = int(room_id_str)
    status, data = await rec_api("POST", f"/api/room/{room_id}/stop")
    if status == 200:
        name = await get_room_name(room_id)
        await stop_rec.finish(f"已停止录制房间 {room_id}（{name}）。")
    elif status == 404:
        await stop_rec.finish(f"未找到房间 {room_id}，请检查房间号是否正确。")
    else:
        await stop_rec.finish(f"停止录制失败：{data}")

# 开始录制
start_rec = on_command("开始录制", aliases={"startrec","startrecord"}, priority=10, block=True)
@start_rec.handle()
async def handle_function(args: Message = CommandArg(), event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) != 2:
        raise FinishedException
    room_id_str = args.extract_plain_text().strip()
    if not room_id_str.isdigit():
        await start_rec.finish("请提供有效的房间号，例如：/开始录制 4947891")
    room_id = int(room_id_str)
    status, data = await rec_api("POST", f"/api/room/{room_id}/start")
    if status == 200:
        name = await get_room_name(room_id)
        await start_rec.finish(f"已开始录制房间 {room_id}（{name}）。")
    elif status == 404:
        await start_rec.finish(f"未找到房间 {room_id}，请检查房间号是否正确。")
    else:
        await start_rec.finish(f"开始录制失败：{data}")

# 删除房间
del_room = on_command("删除房间", aliases={"delroom","delroomid","removeroom"}, priority=10, block=True)
@del_room.handle()
async def handle_function(args: Message = CommandArg(), event: Event = Event):
    if privilege_manager.checkuser(event.get_user_id()) != 2:
        raise FinishedException
    room_id_str = args.extract_plain_text().strip()
    if not room_id_str.isdigit():
        await del_room.finish("请提供有效的房间号，例如：/删除房间 4947891")
    room_id = int(room_id_str)
    # 先取播主名称用于回复（删除后就取不到了）
    name = await get_room_name(room_id)
    status, data = await rec_api("DELETE", f"/api/room/{room_id}")
    if status == 200:
        await del_room.finish(f"已删除房间 {room_id}（{name}）。")
    elif status == 404:
        await del_room.finish(f"未找到房间 {room_id}，请检查房间号是否正确。")
    else:
        await del_room.finish(f"删除失败：{data}")