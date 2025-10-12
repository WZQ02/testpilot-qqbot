import requests
from bs4 import BeautifulSoup
from io import BytesIO

import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk, ImageDraw
import json
import feature_manager
import path_manager
import asyncio

from pixivpy3 import AppPixivAPI

tkfile = open("json/tokens.json","r",encoding="utf-8")
pix_rt = json.loads(tkfile.read())["pixiv_refresh_token"]
tkfile.close()

def download_img(url,path):
    resp = requests.get(url.replace("https://multimedia.nt.qq","http://multimedia.nt.qq")) # bim获取QQ的图片时避免SSLv3报错
    with open(path,"wb") as f:
        f.write(resp.content)
    return 0

# 踩踩背
def gen_ccb_img():
    wpath = "images/img_ccb/"
    root = tk.Tk()
    canvas = Canvas(root, width=540, height=640)
    canvas.pack()
    # background
    bg = Image.open(wpath+"ccb_bg.png")
    bg2 = ImageTk.PhotoImage(bg)
    bgimg = canvas.create_image(270, 320, image=bg2, anchor='center')
    # img being caod
    bcb = Image.open(wpath+"temp/bcb.jpg")
    bcb = bcb.resize((540,240),1)
    bcb2 = ImageTk.PhotoImage(bcb)
    bcbimg = canvas.create_image(270, 540, image=bcb2, anchor='center')
    # elephant
    ccb = Image.open(wpath+"ccb.png")
    ccb = ccb.resize((int(656*.7),int(762*.7)),1)
    ccb2 = ImageTk.PhotoImage(ccb)
    ccbimg = canvas.create_image(334, 280, image=ccb2, anchor='center')
    canvas.update()
    image = canvas_to_image(canvas)
    image.save(path_manager.nb_path()+"images/img_ccb/temp/result.png", "png")
    root.destroy()

def canvas_to_image(canvas):
    """
    width = canvas.winfo_width()
    height = canvas.winfo_height()
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    canvas.postscript(file="temp.eps")
    image = Image.open("temp.eps")
    """
    eps = canvas.postscript(colormode='color')
    image = Image.open(BytesIO(bytes(eps,'ascii')))
    return image

def getrandomxkcdlink(num):
    url = "https://c.xkcd.com/random/comic/"
    if num:
        url = "https://xkcd.com/"+str(num)
    res = requests.get(url)
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
    return {"url":imgur,"id":id,"title":title}
        
def getpixivimg(pid):
    papi = AppPixivAPI()
    papi.auth(refresh_token=pix_rt)
    detail = papi.illust_detail(pid)
    # 没有获取到图片
    if detail.illust == None:
        print(detail)
        return 1
    # r18
    if detail.illust.sanity_level > 5 and not feature_manager.get("pixiv-r18"):
        return 2
    url = detail.illust.image_urls.large
    if detail.illust.meta_single_page != None and detail.illust.meta_single_page.original_image_url != None:
        url = detail.illust.meta_single_page.original_image_url
    # fmt = str.split(url,".")[-1]
    fnm = str.split(url,"/")[-1]
    papi.download(url, path="images/pix/temp/", fname=fnm)
    path = "images/pix/temp/"+fnm
    return path

# 图片放大（调用realesrgan）
async def img4x():
    # cmd = "W:/soft/av_tools/realesrgan-ncnn-vulkan-20220424-windows/realesrgan-ncnn-vulkan.exe -i "+path_manager.nb_path()+"images/upscale/source.jpg -o "+path_manager.nb_path()+"images/upscale/result.png"
    proc = await asyncio.create_subprocess_exec("W:/soft/av_tools/realesrgan-ncnn-vulkan-20220424-windows/realesrgan-ncnn-vulkan.exe", "-i", path_manager.nb_path()+"images/upscale/source.jpg", "-o", path_manager.nb_path()+"images/upscale/result.png")
    await proc.wait()
    return