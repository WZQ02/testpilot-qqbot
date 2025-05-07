from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message
from nonebot.exception import FinishedException
import feature_manager
import img_process

xkcd = on_command("xkcd", aliases={"随机xkcd"}, priority=10, block=True)
@xkcd.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("xkcd"):
        raise FinishedException
    num = None
    ag = args.extract_plain_text()
    if str.isdigit(ag) and int(ag) >= 1:
        num = int(ag)
    img_process.download_img("https:"+img_process.getrandomxkcdlink(num),"images/xkcd/1.png")
    await xkcd.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/images/xkcd/1.png]'))

pix = on_command("pix", aliases={"p站图片","p站插图"}, priority=10, block=True)
@pix.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("pixiv"):
        raise FinishedException
    ag = args.extract_plain_text()
    if str.isdigit(ag) and int(ag) >= 1:
        pix_res = img_process.getpixivimg(int(ag))
        if pix_res == 1:
            await pix.finish("获取插图失败！")
        elif pix_res == 2:
            await pix.finish("你要的图片太色了，哈哈，我私吞了！")
        else:
            await pix.finish(Message('[CQ:image,file=file:///W:/soft/web_svr/testpilot_qqbot/'+pix_res+']'))
    else:
        await pix.finish("参数错误。用法：/pix [你要获取的图片pid]")