from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event, MessageEvent
from nonebot.exception import FinishedException
import feature_manager
import json
import re
import plugins.actual_deepseek
import misc_manager
import httpx
import privilege_manager

vibepilot_server = "http://127.0.0.1:8281/api/"
current_code = ""

async def getcode():
    # 与vibepilot通信，获取原有代码
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            vibepilot_server+"getcode",
            json = {"type": "0"}
        )
        global current_code
        current_code = json.loads(response.text)["code"]

async def vibeit(usrmsg):
    vibe_list = []
    await getcode()
    vibe_init = {"role": "system", "content": f"""你是一个资深的程序员，专注于基于nonebot2框架的QQ群聊机器人开发。你的任务是：根据用户提出的功能需求，修改现有项目中的代码文件。现有文件为 `plugins/main/__init__.py`，其初始内容如下：
                
                ```python
                {current_code}
                ```

                当用户提出功能需求时，你需要基于以上代码进行修改，例如添加新命令、调整现有命令逻辑、或改进代码结构等。用户需求可能以自然语言描述，请准确理解并实现，确保代码符合nonebot2框架规范、保持可读性和健壮性。如果需求不明确，你可以请求用户澄清。

                你的回复必须严格遵循以下格式：
                - 首先，输出 `# code` 标题，然后在后续行中提供一个代码块，使用 ` ```python` 和 ` ``` 包裹修改后的完整代码。
                - 接着，输出 `# description` 标题，然后在后续行中用自然语言简要描述你所做的修改，例如添加了哪些功能、修改了哪些部分、以及为什么这样改。

                注意：只返回格式化的代码和描述，不要添加额外解释或对话。"""}
    vibe_list.append(vibe_init)
    vibe_list.append({"role": "user", "content": usrmsg})
    config = plugins.actual_deepseek.config
    resp = await plugins.actual_deepseek.client.chat.completions.create(
        model = config[config["current_engine"]]["models"][0],
        messages = vibe_list,
        stream = False
    )
    remsg = resp.choices[0].message
    print(remsg.content)
    return remsg.content

async def extract_resp(resp):
    # 定义正则表达式模式
    code_pattern = r'# code\s*```python\s*(.*?)\s*```'
    description_pattern = r'# description\s*(.*?)(?=\s*$|\s*#)'
    
    # 提取代码部分
    code_match = re.search(code_pattern, resp, re.DOTALL)
    code = code_match.group(1).strip() if code_match else None
    
    # 提取描述部分
    description_match = re.search(description_pattern, resp, re.DOTALL)
    description = description_match.group(1).strip() if description_match else None

    if code != None:
        await writecode(code)
        return description
    else:
        return resp

async def writecode(code):
    # 与vibepilot通信，将得到的代码写回
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            vibepilot_server+"writecode",
            json = {"type": "1", "code": code}
        )
        return response

addfeature = on_command("addfeature", aliases={"添加功能"}, priority=10, block=True)
@addfeature.handle()
async def handle_function(args: Message = CommandArg(),event: MessageEvent = Event):
    #if not (feature_manager.get("deepseek") and privilege_manager.checkuser(event.get_user_id())):
    if not feature_manager.get("deepseek"):
        raise FinishedException
    misc_manager.tasks.append("vibepilot")
    # 获取args
    usrmsg = ""
    vibedata = ""
    if len(args) > 0:
        usrmsg = args.extract_plain_text()
        vibedata = await vibeit(usrmsg)
        text = await extract_resp(vibedata)
    await addfeature.send(text)
    misc_manager.tasks.remove("vibepilot")
    raise FinishedException