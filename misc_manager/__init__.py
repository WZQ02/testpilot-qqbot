import json

miscd = open("json/misc.json","r",encoding="utf-8")
misc_data = json.loads(miscd.read())

def writeback():
    file = open("json/misc.json","w",encoding="utf-8")
    json.dump(misc_data,file,ensure_ascii=False,sort_keys=True)

tasks = []