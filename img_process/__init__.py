import requests
from io import BytesIO

import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk, ImageDraw

def download_img(url,path):
    resp = requests.get(url)
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
    image.save("w:/soft/web_svr/testpilot_qqbot/images/img_ccb/temp/result.png", "png")
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

