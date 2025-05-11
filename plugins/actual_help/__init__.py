from nonebot import on_command
from nonebot.rule import to_me
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import Event
import feature_manager
import privilege_manager

help = on_command("actualhelp", rule=to_me(), aliases={"actual_help","真正的帮助","实际的帮助","真实的帮助"}, priority=10, block=True)
@help.handle()
async def handle_function(event: Event):
    if not feature_manager.get("actualhelp"):
        raise FinishedException
    helptext = "@testpilot /ping 测试bot是否在线\n/ccb [要被踩背的文本或图片] 给某个东西踩踩背\n/echo [要复读的文本] 复读一段文本\n/tag [昵称/QQ号/@群成员] [要添加的标签名] 为某个人添加标签\n/del [昵称/QQ号/@群成员] [要删除的标签名] 为某个人删除标签\n/que [要查看标签的昵称/QQ号/@群成员] 查看某个人拥有的标签\n/miku 随机发送 miratsu 的 miku 表情\n/fio 随机发送 fio 表情\n/mieru 随机发送美瑠表情\n/bocchi 随机发送波奇酱表情\n/karen 随机发送九条可怜表情\n/random [数字位数] 生成随机数，默认为3位数，最多64位\n/poem [格式名称] [关键词] 诗朗诵\n/explain [名词] 解释名词含义\n/admn [名词] [要添加的名词解释] 添加名词解释 [/override]\n/ds [对话内容] 向 AI 发起对话\n/qrcode [要转换为二维码的文本 或 要识别的二维码图片] 生成或识别二维码\n/repeat 复读上一句发言\n/bili [BV号/av号/B站视频链接] 发送B站视频到群聊\n/send [群号] [文本内容] 定向发送消息到bot所在的群聊\n/xkcd [图片号，不填写则为随机] 获取xkcd漫画\n/pix [pid] 获取pixiv插图"
    if privilege_manager.checkuser(event.get_user_id()):
        helptext += "\n\n以下为管理员限定功能：\n/echocq [要复读的CQ码] 复读CQ码\n/webss [网址] 生成一张网页截屏\n/fealist 查看功能列表\n/enable [功能名称] 启用某个功能\n/disable [功能名称] 禁用某个功能\n/import [功能列表json] 导入功能列表\n/preset [预设名] 启用功能预设\n/adminlist 查看管理员列表\n/reload 重载bot"
    await help.finish(helptext)

wzs = on_command("wzq", aliases={"wzs","小站导航","网站导航"}, priority=10, block=True)
@wzs.handle()
async def handle_function():
    if not feature_manager.get("wzs"):
        raise FinishedException
    await wzs.finish("https://wzq02.top/ WZQ'02 的小站\nhttps://s.wzq02.top/1drive WZQ'02 的网盘\nhttps://s.wzq02.top/ask WZQ'02 的提问箱\nhttps://wzq02.top/otomader-sites/ 音 MADer 网站收集\nhttps://wzq02.top/redirect/airasoft/ 艾拉软件库")