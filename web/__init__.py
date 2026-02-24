import logging

logger = logging.getLogger(__name__)

content = ""
def content_init():
    try:
        with open("web/templates/wel/index.html","r",encoding="utf-8") as file:
            global content
            content = file.read()
        writehtml()
        logger.info("已初始化网页截图初始页面。")
    except IOError as e:
        logger.error(f"网页截图初始页面初始化失败: {e}")

def change_content(con):
    global content
    content = con
    writehtml()
    logger.info("网页内容发生变更。")

def writehtml():
    try:
        with open("web/index.html","w",encoding="utf-8") as file:
            file.write(content)
        logger.info("已将内容写入网页 web/index.html")
    except IOError as e:
        logger.error(f"写入内容到 web/index.html 失败: {e}")

def content_md(md):
    try:
        with open("web/templates/markdown/index.html","r",encoding="utf-8") as file:
            page = file.read()
        global content
        content = page
        with open("web/templates/markdown/md.md","w",encoding="utf-8") as mdf:
            mdf.write(md)
        writehtml()
        logger.info("已渲染 markdown 内容。")
    except IOError as e:
        logger.error(f"渲染 markdown 内容失败: {e}")

def content_text(con):
    try:
        with open("web/templates/text/index.html","r",encoding="utf-8") as file:
            page = file.read()
        global content
        content = page.replace("<!-- Text Content -->",con)
        writehtml()
        logger.info("已渲染文本内容。")
    except IOError as e:
        logger.error(f"文本渲染失败: {e}")