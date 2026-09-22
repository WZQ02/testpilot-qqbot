import path_manager
import os
import requests

bridge_api = path_manager.pat_list["bridge_api"]
bridge_host_ip = path_manager.pat_list["bridge_ip"]
sign = "[testpilot bridge] "

def upload(file_path):
    if not os.path.exists(file_path):
        print(f"{sign}文件不存在: {file_path}")
        return None
    
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f)}
        response = requests.post(bridge_api+"/upload", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"{sign}上传成功！")
        return result
    else:
        print(f"{sign}上传失败: {response.text}")
        return None

def upscale_image():
    upl_result = upload("./images/upscale/source.jpg")
    if upl_result:
        response = requests.get(bridge_api+"/img_upscale/source.jpg")
        if response.status_code == 200:
            with open("./images/upscale/result.png","wb") as f:
                f.write(response.content)
            return 1
    return None

def start_vm(name):
    response = requests.get(bridge_api+"/qemu/"+name)
    if response.status_code == 200:
        return 1
    else:
        return 0

def move_qmss():
    response = requests.get(bridge_api+"/move_qmss")
    if response.status_code == 200:
        return 1
    else:
        return 0

def get_file(name, dest):
    response = requests.get(bridge_api+"/files/"+name)
    if response.status_code == 200:
        with open(dest+"/"+name,"wb") as f:
            f.write(response.content)
        return 1
    return None