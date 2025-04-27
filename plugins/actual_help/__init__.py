from nonebot import on_command
from nonebot.rule import to_me
from nonebot.exception import FinishedException
import feature_manager

help = on_command("actualhelp", rule=to_me(), aliases={"actual_help","真正的帮助","实际的帮助","真实的帮助"}, priority=10, block=True)
@help.handle()
async def handle_function():
    if not feature_manager.get("actualhelp"):
        raise FinishedException
    await help.finish("@testpilot /ping 测试bot是否在线\n/ccb [要被踩背的文本或图片] 给某个东西踩踩背\n/echo [要复读的文本] 复读一段文本\n/tag [昵称/QQ号/@群成员] [要添加的标签名] 为某个人添加标签\n/del [昵称/QQ号/@群成员] [要删除的标签名] 为某个人删除标签\n/que [要查看标签的昵称/QQ号/@群成员] 查看某个人拥有的标签\n/miku 随机发送 miratsu 的 miku 表情\n/fio 随机发送 fio 表情\n/mieru 随机发送 mieru 表情\n/bocchi 随机发送波奇酱表情\n/random [数字位数] 生成随机数，默认为3位数，最多64位\n/poem [格式名称] [关键词] 诗朗诵\n/explain [名词] 解释名词含义\n/admn [名词] [要添加的名词解释] 添加名词解释 [/override]\n/ds [对话内容] 向 AI 发起对话\n/qrcode [要转换为二维码的文本 或 要识别的二维码图片] 生成或识别二维码\n/repeat 复读上一句发言\n/bili [BV号/av号/B站视频链接] 发送B站视频到群聊")

wzs = on_command("wzq", aliases={"wzs","小站导航","网站导航"}, priority=10, block=True)
@wzs.handle()
async def handle_function():
    if not feature_manager.get("wzs"):
        raise FinishedException
    await wzs.finish("https://wzq02.top/ WZQ'02 的小站\nhttps://s.wzq02.top/1drive WZQ'02 的网盘\nhttps://s.wzq02.top/ask WZQ'02 的提问箱\nhttps://wzq02.top/otomader-sites/ 音 MADer 网站收集\nhttps://wzq02.top/redirect/airasoft/ 艾拉软件库")