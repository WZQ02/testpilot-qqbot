from nonebot import on_command, on_message, get_driver
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, GroupMessageEvent, PrivateMessageEvent
from nonebot.params import CommandArg
from nonebot.exception import FinishedException
import feature_manager
import path_manager
import web
import webss
import jieba
import json
import os
import re
import random
import asyncio
import datetime
import logging
from collections import deque, Counter
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
async def handle_summary(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not feature_manager.can_use("group_summary", event.get_user_id()):
        raise FinishedException

    if isinstance(event, PrivateMessageEvent):
        # 私聊：需显式指定纯数字群号
        raw = args.extract_plain_text().strip()
        if not raw:
            await group_summary.finish("请在私聊使用 /群省流 [群号] 总结指定群。")
        if not (raw.isascii() and raw.isdigit()):
            await group_summary.finish("群号只能是纯数字哦！")
        group_id = raw
        # 校验调用者确为目标群成员，避免私聊越权查看自己不在的群聊内容
        try:
            await bot.get_group_member_info(group_id=int(group_id), user_id=int(event.get_user_id()), no_cache=True)
        except Exception:
            await group_summary.finish("bot或你不在该群，总结失败！")
    else:
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


# ====== /群词云 命令 ======
WORDCLOUD_TEMPLATE = "web/templates/wordcloud/index.html"
WORDCLOUD_MIN_WORDS = 10      # 有效词少于该数量则拒绝生成
WORDCLOUD_MAX_WORDS = 50      # 最多展示的词数
WORDCLOUD_MIN_SIZE = 18       # 最小字号（CSS 像素）
WORDCLOUD_MAX_SIZE = 96       # 最大字号（CSS 像素）
WORDCLOUD_RENDER_WAIT = 1.5   # 截图前等待字体与绘制的秒数

# 网页截图依赖全局单页 web/index.html，必须串行，避免与其他命令互相覆盖
_render_lock = asyncio.Lock()

CQ_CODE_RE = re.compile(r"\[CQ:[^\]]*\]")
URL_RE = re.compile(r"(?:https?://|www\.)[^\s]*", re.IGNORECASE)

# 高频虚词/口水词，命中直接丢弃，避免“就是”“什么”之类的词霸榜
WORDCLOUD_STOPWORDS = frozenset("""
的 了 是 在 我 你 他 她 它 们 这 那 就 都 也 又 还 和 与 及 或 把 被 给 对 向 从 到 为 以 于 之 其 着 过
很 太 更 最 不 没 有 会 能 可 要 说 想 做 让 吗 呢 吧 啊 呀 哦 嗯 哈 个 些 么 啥 嘛 呗 咯 哇 诶 欸
什么 怎么 这个 那个 这样 那样 这些 那些 这里 那里 我们 你们 他们 她们 咱们 自己 大家 别人 人家
就是 还是 也是 但是 可是 只是 因为 所以 如果 虽然 然后 而且 或者 不过 其实 居然 竟然 确实 反正
已经 现在 刚才 马上 一直 一起 一下 一点 一些 一样 一定 一般 可能 应该 可以 需要 觉得 感觉 知道
真的 好像 有点 有些 东西 时候 事情 问题 意思 而且 的话 这样 那种 这么 那么 多少 几个 怎样
哈哈 哈哈哈 哈哈哈哈 233 666 草 啊这 笑死 好家伙 离谱 牛 牛啊
""".split())

jieba.setLogLevel(logging.WARNING)


def _keep_word(word: str) -> bool:
    """过滤停用词、单字、标点、数字和纯符号，只保留有意义的中文词/英文词。"""
    if not word or word in WORDCLOUD_STOPWORDS:
        return False
    if word.isascii():
        # 英文只保留纯字母且长度 >= 3 的词
        return word.isalpha() and len(word) >= 3
    # 含中文：必须全部是汉字且长度 >= 2
    return len(word) >= 2 and all("\u4e00" <= ch <= "\u9fff" for ch in word)


def build_word_counter(group_id: str) -> Counter:
    """对群聊历史分词并统计词频。"""
    msgs = list(_load_history(group_id))
    counter = Counter()
    for m in msgs:
        text = CQ_CODE_RE.sub(" ", m.get("t", ""))
        text = URL_RE.sub(" ", text)
        if not text.strip():
            continue
        seen = set()
        for word in jieba.cut(text):
            word = word.strip().lower()
            # 同一条消息内同一个词只算一次，防止刷屏词霸榜
            if word in seen or not _keep_word(word):
                continue
            seen.add(word)
            counter[word] += 1
    return counter


def build_wordcloud_html(counter: Counter) -> str:
    """生成词云页面的 HTML。字号按词频开方映射到 18~96px，词序随机即位置随机。"""
    top = counter.most_common(WORDCLOUD_MAX_WORDS)
    random.shuffle(top)
    max_freq = max(f for _, f in top)
    min_freq = min(f for _, f in top)
    data = []
    for word, freq in top:
        ratio = 1.0 if max_freq == min_freq else (freq - min_freq) / (max_freq - min_freq)
        size = round(WORDCLOUD_MIN_SIZE + (ratio ** 0.6) * (WORDCLOUD_MAX_SIZE - WORDCLOUD_MIN_SIZE))
        data.append([word, size])
    with open(WORDCLOUD_TEMPLATE, "r", encoding="utf-8") as f:
        template = f.read()
    return template.replace("/*WORD_DATA*/ []", json.dumps(data, ensure_ascii=False))


group_wordcloud = on_command("群词云", aliases={"wordcloud"}, priority=10, block=True)


@group_wordcloud.handle()
async def handle_wordcloud(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not feature_manager.can_use("group_summary", event.get_user_id()):
        raise FinishedException

    if isinstance(event, PrivateMessageEvent):
        # 私聊：需显式指定纯数字群号
        raw = args.extract_plain_text().strip()
        if not raw:
            await group_wordcloud.finish("你还没有指定群号！")
        if not (raw.isascii() and raw.isdigit()):
            await group_wordcloud.finish("群号只能是纯数字哦！")
        group_id = raw
        # 校验调用者确为目标群成员，避免私聊越权查看自己不在的群聊内容
        try:
            await bot.get_group_member_info(group_id=int(group_id), user_id=int(event.get_user_id()), no_cache=True)
        except Exception:
            await group_wordcloud.finish("bot或你不在该群，词云生成失败！")
    else:
        group_id = str(event.group_id)

    # 落盘后再读取，保证词云包含最新内容
    if _dirty.get(group_id, 0) > 0:
        _flush_history(group_id)

    counter = await asyncio.to_thread(build_word_counter, group_id)
    if len(counter) < WORDCLOUD_MIN_WORDS:
        await group_wordcloud.finish("本群发言太少了，整理不了词云哦！")

    html = build_wordcloud_html(counter)
    #await group_wordcloud.send("正在绘制词云ing...")

    filename = f"wordcloud_{group_id}"
    async with _render_lock:
        web.change_content(html)
        code = await webss.take2("http://localhost:8104", "container",
                                 sleep=WORDCLOUD_RENDER_WAIT, filename=filename)
    if code != 0:
        await group_wordcloud.finish("词云渲染失败了，稍后再试吧！")

    await group_wordcloud.finish(
        Message(f'[CQ:image,file=file:///{path_manager.bf_path()}webss/{filename}.png]'))
