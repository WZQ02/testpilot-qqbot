import requests
from bs4 import BeautifulSoup
from io import BytesIO

from PIL import Image, ImageDraw
import json
import feature_manager
import path_manager
import misc_manager
import asyncio

from pixivpy3 import AppPixivAPI

import logging
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

tokens_config = ConfigManager("json/tokens.json")
pix_rt = tokens_config.get("pixiv_refresh_token")

def download_img(url,path):
    try:
        resp = requests.get(url.replace("https://multimedia.nt.qq","http://multimedia.nt.qq"))
        resp.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        with open(path,"wb") as f:
            f.write(resp.content)
        logger.info(f"下载图片 {url} 到 {path}。")
        return 0
    except requests.exceptions.RequestException as e:
        logger.error(f"从 {url} 下载图片出错: {e}")
        return 1
    except IOError as e:
        logger.error(f"写入图片到 {path} 出错: {e}")
        return 1

# 踩踩背


async def ccb_image(url):
    wpath = "images/img_ccb/"
    # Download the image to be processed
    temp_bcb_path = wpath + "temp/bcb.jpg"
    download_img(url, temp_bcb_path)

    # Load images
    bg = Image.open(wpath + "ccb_bg.png")
    bcb = Image.open(temp_bcb_path).resize((540, 240))
    ccb_overlay = Image.open(wpath + "ccb.png").resize((int(656 * .7), int(762 * .7)))

    # Create a blank image with the same size as the background
    # Convert all images to RGBA to handle transparency correctly
    bg = bg.convert("RGBA")
    bcb = bcb.convert("RGBA")
    ccb_overlay = ccb_overlay.convert("RGBA")

    # Paste the background
    composed_image = Image.new("RGBA", bg.size)
    composed_image.paste(bg, (0, 0), bg)

    # Paste the 'bcb' image (being trampled) at the bottom
    # The original tkinter code had it at (270, 540) centered, which means top-left is (270-540/2, 540-240/2) = (0, 420)
    composed_image.paste(bcb, (0, bg.height - bcb.height), bcb)

    # Paste the 'ccb' image (elephant) at (334, 280) centered
    # This means top-left is (334 - ccb_overlay.width/2, 280 - ccb_overlay.height/2)
    ccb_x = 334 - ccb_overlay.width // 2
    ccb_y = 280 - ccb_overlay.height // 2
    composed_image.paste(ccb_overlay, (ccb_x, ccb_y), ccb_overlay)

    result_path = path_manager.nb_path() + "images/img_ccb/temp/result.png"
    composed_image.save(result_path, "PNG")

    return result_path

def getrandomxkcdlink(num):
    url = "https://c.xkcd.com/random/comic/"
    if num:
        url = "https://xkcd.com/"+str(num)
    try:
        res = requests.get(url)
        res.raise_for_status()
        con = res.text
        soup = BeautifulSoup(con, "lxml")
        imgur = ""
        title = ""
        id = 0
        for i in soup.find_all("div"):
            if i.get("id") == "comic":
                imgur = i.find_all("img")[0].get("src")
                title = i.find_all("img")[0].get("title")
        for i in soup.find_all("meta"):
            if i.get("property") == "og:url":
                id = i.get("content").split("/")[-2]
        logger.info(f"xkcd 漫画: {id} - {title}")
        return {"url":imgur,"id":id,"title":title}
    except requests.exceptions.RequestException as e:
        logger.error(f"从 {url} 获取漫画失败: {e}")
        return None
        
def getpixivimg(pid):
    papi = AppPixivAPI()
    papi.requests.proxies = {
        "http": misc_manager.misc_data["http_proxy"],
        "https": misc_manager.misc_data["http_proxy"]
    }
    try:
        papi.auth(refresh_token=pix_rt)
        detail = papi.illust_detail(pid)
        # 没有获取到图片
        if detail.illust == None:
            logger.warning(f"无法获取 Pixiv 图片信息 {pid}: {detail}")
            return 1
        # r18
        if detail.illust.sanity_level > 5 and not feature_manager.get("pixiv-r18"):
            logger.info(f"Blocked R18 Pixiv illustration for PID {pid}.")
            return 2
        url = detail.illust.image_urls.large
        if detail.illust.meta_single_page != None and detail.illust.meta_single_page.original_image_url != None:
            url = detail.illust.meta_single_page.original_image_url
        # fmt = str.split(url,".")[-1]
        fnm = str.split(url,"/")[-1]
        papi.download(url, path="images/pix/temp/", fname=fnm)
        path = "images/pix/temp/"+fnm
        logger.info(f"获取到 Pixiv 图片 {pid}.")
        return path
    except Exception as e:
        logger.error(f"无法获取 Pixiv 图片 {pid}: {e}")
        return 1

# 图片放大（调用realesrgan）
async def img4x():
    # cmd = "W:/soft/av_tools/realesrgan-ncnn-vulkan-20220424-windows/realesrgan-ncnn-vulkan.exe -i "+path_manager.nb_path()+"images/upscale/source.jpg -o "+path_manager.nb_path()+"images/upscale/result.png"
    proc = await asyncio.create_subprocess_exec("W:/soft/av_tools/realesrgan-ncnn-vulkan-20220424-windows/realesrgan-ncnn-vulkan.exe", "-i", path_manager.nb_path()+"images/upscale/source.jpg", "-o", path_manager.nb_path()+"images/upscale/result.png")
    await proc.wait()
    return