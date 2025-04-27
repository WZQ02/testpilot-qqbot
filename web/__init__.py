content = ""
def content_init():
    file = open("web/templates/wel/index.html","r",encoding="utf-8")
    global content
    content = file.read()
    file.close()
    writehtml()

def change_content(con):
    global content
    content = con
    writehtml()

def writehtml():
    file = open("web/index.html","w",encoding="utf-8")
    file.write(content)

# markdown
def content_md(md):
    file = open("web/templates/markdown/index.html","r",encoding="utf-8")
    page = file.read()
    global content
    content = page.replace("<!-- Markdown Content -->",md)
    file.close()
    writehtml()

# HTML / plain text screenshot
def content_text(con):
    file = open("web/templates/text/index.html","r",encoding="utf-8")
    page = file.read()
    global content
    content = page.replace("<!-- Text Content -->",con)
    file.close()
    writehtml()