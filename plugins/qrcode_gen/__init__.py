import qrcode
from pyzbar.pyzbar import decode
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg
from nonebot.exception import FinishedException
import feature_manager
import img_process
import path_manager
from PIL import Image

def genqr(data):
    qr = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=8,border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save("images/qrcode/1.png")

def recqr(url):
    im_path = "images/qrcode/2.jpg"
    img_process.download_img(url,im_path)
    img = Image.open(im_path)
    decoded_objects = decode(img)
    data = ""
    for obj in decoded_objects:
        data += obj.data.decode('utf-8')
    return data

gqrc = on_command("qr", aliases={"qrcode","二维码","生成二维码","识别二维码"}, priority=10, block=True)
@gqrc.handle()
async def handle_function(args: Message = CommandArg()):
    if not feature_manager.get("qrcode"):
        raise FinishedException
    # 二维码识别
    if args[0].type == 'image':
        data = recqr(args[0].data['url'])
        if data == "":
            raise FinishedException
        else:
            await gqrc.finish(recqr(args[0].data['url']))
    # 二维码生成
    else:
        genqr(args.extract_plain_text())
        await gqrc.finish(Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/qrcode/1.png]'))