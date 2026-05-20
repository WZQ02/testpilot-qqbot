from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg
from nonebot.exception import FinishedException
import feature_manager
import asyncio
import re
from config_manager import ConfigManager

poem_config = ConfigManager("json/poem.json")
templates = poem_config.all()

def get_required_keywords_count(template_lines):
    max_arg_num = 0
    for line_data in template_lines:
        text = line_data["text"]
        matches = re.findall(r"\{(\d+)\}", text)
        if matches:
            current_max = max(int(m) for m in matches)
            max_arg_num = max(max_arg_num, current_max)
    return max_arg_num

async def send_poem_lines(matcher, template_lines, keywords):
    for i, line_data in enumerate(template_lines):
        line_text = line_data["text"]
        # Replace placeholders {1}, {2}, etc.
        for j, keyword in enumerate(keywords):
            line_text = line_text.replace(f"{{{j+1}}}", keyword)
        await matcher.send(line_text)
        if "delay" in line_data:
            await asyncio.sleep(line_data["delay"])

poem = on_command("poem", aliases={"诗朗诵","吟诗","recite"}, priority=10, block=True)
@poem.handle()
async def handle_poem(args: Message = CommandArg()):
    if not feature_manager.get("poem"):
        raise FinishedException
    
    parsed_args = args.extract_plain_text().split()
    if not parsed_args:
        await poem.finish("参数错误，请指定要朗诵的模板名称和关键词。用法：/poem [格式名称] [关键词1] [关键词2] ...")
    
    template_name = parsed_args[0]
    keywords = parsed_args[1:]

    if template_name not in templates:
        available_templates = ', '.join(templates.keys()) if templates else '无'
        await poem.finish(f"未找到模板！可用的模板有：{available_templates}。")
    
    template_data = templates[template_name]
    required_keywords_count = get_required_keywords_count(template_data["lines"])

    if len(keywords) < required_keywords_count:
        keywords_hint = ' '.join([f'[关键词{i+1}]' for i in range(required_keywords_count)])
        await poem.finish(f"参数不够。用法：/poem {template_name} {keywords_hint}")

    await send_poem_lines(poem, template_data["lines"], keywords)
    await poem.finish()

list_poem = on_command("listpoem", aliases={"列出诗模板"}, priority=10, block=True)
@list_poem.handle()
async def handle_list_poem():
    if not feature_manager.get("poem"):
        raise FinishedException
    
    if not templates:
        await list_poem.finish("诗朗诵模板为空！")
    
    response = "可用的诗朗诵模板：\n"
    for name in templates.keys():
        response += f"- {name}\n"
    await list_poem.finish(response)

add_poem = on_command("addpoem", aliases={"添加诗模板"}, priority=10, block=True)
@add_poem.handle()
async def handle_add_poem(args: Message = CommandArg()):
    if not feature_manager.get("poem"):
        raise FinishedException

    parsed_args_str = args.extract_plain_text()
    parts = parsed_args_str.split(' ', 1)
    
    if len(parts) < 2:
        await add_poem.finish("参数错误。用法：/addpoem <模板名称> <模板内容>。模板内容中每句话用空格分隔，关键词用{1},{2}...表示。")
    
    template_name = parts[0]
    template_content_str = parts[1]
    
    if template_name in templates:
        await add_poem.finish(f"模板 {template_name} 已存在！换个名称吧。")

    lines_str = template_content_str.split(' ')
    new_lines = []
    description_parts = []
    for line_idx, line in enumerate(lines_str):
        new_lines.append({"text": line, "delay": 1})
        # For description, replace {N} with [关键词N]
        desc_line = line
        for i in range(1, 10): # Assuming max 9 keywords for description
            desc_line = desc_line.replace(f"{{{i}}}", f"[关键词{i}]")
        description_parts.append(desc_line)
    
    templates[template_name] = {
        "description": " ".join(description_parts),
        "lines": new_lines
    }
    poem_config.update(templates)
    
    await add_poem.finish(f"已添加诗朗诵模板：{template_name}")

del_poem = on_command("delpoem", aliases={"删除诗模板"}, priority=10, block=True)
@del_poem.handle()
async def handle_del_poem(args: Message = CommandArg()):
    if not feature_manager.get("poem"):
        raise FinishedException

    template_name = args.extract_plain_text().strip()
    if not template_name:
        await del_poem.finish("参数错误。用法：/delpoem <模板名称>")
    
    if template_name not in templates:
        await del_poem.finish(f"未找到诗朗诵模板：{template_name}。")
    
    del templates[template_name]
    poem_config.update(templates)
    
    await del_poem.finish(f"已删除诗朗诵模板：{template_name}")