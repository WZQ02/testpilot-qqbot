from nonebot import on_command, on_message, get_driver
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, PrivateMessageEvent
from nonebot.exception import FinishedException
import feature_manager
import json
import os
import asyncio
import datetime
from collections import deque
from config_manager import ConfigManager

# 直接复用 actual_deepseek 的 openai client 与模型配置，最省 token（不走搜索工具循环）
import plugins.actual_deepseek as ds

HISTORY_DIR = "json/chat_history"
MAX_HISTORY = 1000          # 每群最多保留的消息条数
FLUSH_EVERY = 20            # 每群每记录多少条后落盘一次
MAX_TEXT_LEN = 200          # 单条消息文本截断长度（防超长消息撑爆 token）
MAX_NICK_LEN = 10           # 昵称截断长度
DAILY_LIMIT = 5             # 每群每日总结次数上限
MAX_PROMPT_CHARS = 30000    # 发给 AI 的聊天记录字符上限（超出则均匀抽样）

SUMMARY_SYSTEM_PROMPT = (
    "你是一个群聊总结助手。用户会提供一个 QQ 群最近的聊天记录，每行格式为“昵称:内容”。"
    "请用 1000 字左右总结，群聊中哪些用户从前往后都讨论了哪些主要话题。"
    "输出格式简洁，尽量不要复述原文。"
)

os.makedirs(HISTORY_DIR, exist_ok=True)

# 内存中的消息缓存：{group_id: deque([{"n": 昵称, "t": 文本}, ...])}
_history = {}
# 每群自上次落盘以来的新增条数
_dirty = {}
# 每日调用次数配额
quota_config = ConfigManager("json/summary_quota.json")
# 限制同时调用 AI 的数量
_ai_semaphore = asyncio.Semaphore(3)


def _history_path(group_id: str) -> str:
    return os.path.join(HISTORY_DIR, f"{group_id}.json")


def _load_history(group_id: str) -> deque:
    """从文件加载某群的历史到内存（只加载一次）。"""
    if group_id in _history:
        return _history[group_id]
    msgs = deque(maxlen=MAX_HISTORY)
    path = _history_path(group_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("msgs", []):
                msgs.append({"n": item.get("n", ""), "t": item.get("t", "")})
        except Exception as e:
            print(f"group_summary: 加载群 {group_id} 历史失败：{e}")
    _history[group_id] = msgs
    _dirty[group_id] = 0
    return msgs


def _flush_history(group_id: str):
    """把某群的内存历史落盘。"""
    msgs = _history.get(group_id)
    if msgs is None:
        return
    try:
        with open(_history_path(group_id), "w", encoding="utf-8") as f:
            json.dump({"msgs": list(msgs)}, f, ensure_ascii=False)
        _dirty[group_id] = 0
    except Exception as e:
        print(f"group_summary: 群 {group_id} 历史落盘失败：{e}")


def record_msg(group_id: str, speaker: str, text: str):
    """记录一条群消息到内存，达到阈值后落盘。"""
    msgs = _load_history(group_id)
    msgs.append({"n": speaker, "t": text})
    _dirty[group_id] = _dirty.get(group_id, 0) + 1
    if _dirty[group_id] >= FLUSH_EVERY:
        _flush_history(group_id)


# bot 退出时把所有脏数据落盘
driver = get_driver()


@driver.on_shutdown
async def flush_all():
    for gid in list(_dirty.keys()):
        if _dirty.get(gid, 0) > 0:
            _flush_history(gid)


def build_prompt(group_id: str) -> str:
    """拼接聊天记录，超出字符上限时按时间均匀抽样以覆盖全程。"""
    msgs = list(_load_history(group_id))
    lines = [f"{m['n']}:{m['t']}" for m in msgs]
    full = "\n".join(lines)
    if len(full) <= MAX_PROMPT_CHARS:
        return full
    # 估算可放入的行数，均匀抽样
    avg_len = max(len(full) / max(len(lines), 1), 1)
    keep = max(int(MAX_PROMPT_CHARS / avg_len), 1)
    step = len(lines) / keep
    sampled = [lines[int(i * step)] for i in range(keep)]
    return "\n".join(sampled)


async def summarize(prompt: str) -> str:
    """直接调用 openai 接口做总结（不经过 chat_once 的搜索工具循环，省 token）。"""
    msglist = [
        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    async with _ai_semaphore:
        resp = await ds.client.chat.completions.create(
            model=ds.config[ds.config["current_engine"]]["models"][ds.config["model_index_prio"]],
            messages=msglist,
            stream=False,
        )
    return resp.choices[0].message.content


def check_quota(group_id: str):
    """返回 (是否可用, 剩余次数)。不消耗次数。"""
    today = datetime.date.today().isoformat()
    entry = quota_config.get(group_id) or {}
    if entry.get("date") != today:
        return True, DAILY_LIMIT
    used = entry.get("used", 0)
    return used < DAILY_LIMIT, DAILY_LIMIT - used


def consume_quota(group_id: str):
    today = datetime.date.today().isoformat()
    entry = quota_config.get(group_id) or {}
    if entry.get("date") != today:
        entry = {"date": today, "used": 0}
    entry["used"] = entry.get("used", 0) + 1
    quota_config.set(group_id, entry)


# ====== 消息记录监听器 ======
# 注意：repeat/cast 等插件在 priority=10 且 block=True，会阻断数字更大优先级的 matcher，
# 因此这里必须用更小的 priority（5）确保能收到所有群消息；block=False 不影响其他 matcher
chat_record = on_message(priority=5, block=False)


@chat_record.handle()
async def handle_record(event: MessageEvent):
    if not feature_manager.can_use("group_summary", event.get_user_id()):
        return
    if not isinstance(event, GroupMessageEvent):
        return
    # 不记录 bot 自己的发言（避免总结内容被再次喂回，浪费 token）
    if event.user_id == event.self_id:
        return
    text = event.get_message().extract_plain_text().strip()
    # 跳过空消息（纯图片/表情）和命令
    if not text or text.startswith("/"):
        return
    if len(text) > MAX_TEXT_LEN:
        text = text[:MAX_TEXT_LEN]
    speaker = event.sender.card or event.sender.nickname or str(event.user_id)
    if len(speaker) > MAX_NICK_LEN:
        speaker = speaker[:MAX_NICK_LEN]
    record_msg(str(event.group_id), speaker, text)


# ====== /群省流 命令 ======
group_summary = on_command("群省流", aliases={"群总结", "qsl"}, priority=10, block=True)


@group_summary.handle()
async def handle_summary(event: MessageEvent):
    if not feature_manager.can_use("group_summary", event.get_user_id()):
        raise FinishedException

    # 私聊兜底
    if isinstance(event, PrivateMessageEvent):
        await group_summary.finish("喂，你是baka吗？让我在私聊里面群总结？！")

    group_id = str(event.group_id)

    # 配额检查（先查后扣，失败不扣）
    allowed, remaining = check_quota(group_id)
    if not allowed:
        await group_summary.finish("ding~pong~bang~pong~！今天的总结次数用完了哦，明天再试吧！")

    # 落盘后再读取，保证总结包含最新内容
    if _dirty.get(group_id, 0) > 0:
        _flush_history(group_id)

    prompt = build_prompt(group_id)
    if not prompt:
        await group_summary.finish("群里还没什么人说过话呢，稍后再试吧！")

    await group_summary.send("整理群聊内容ing...")

    try:
        result = await summarize(prompt)
    except Exception as e:
        print(f"group_summary: AI 总结失败：{e}")
        await group_summary.finish("群省流出了点故障，稍后再试吧！")

    # 成功后才消耗配额
    consume_quota(group_id)
    await group_summary.finish(f"{result}\n\n（今日还剩 {remaining - 1} 次）")
