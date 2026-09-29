from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageEvent
from nonebot.exception import FinishedException
import feature_manager
import plugins.test1
import misc_manager
from config_manager import ConfigManager
import aiohttp
import asyncio
import os
import img_process
import path_manager

from importlib.metadata import version
from packaging.version import Version

# 两个大版本都提供顶层 SauceNao 类，可直接导入
from pysaucenao import SauceNao

# 兼容 pysaucenao 1.x / 2.x：
# 1.x 异常基类为 SauceNaoException，结果容器在 pysaucenao.containers，
# 构造函数原生支持 proxy 参数，from_file 可正常上传文件；
# 2.x 异常基类为 SauceNaoError，结果容器在 pysaucenao.results，
# 无代理支持且 from_file 存在不上传文件内容的 bug，需要子类重写。
PSN_V2 = Version(version("pysaucenao")) >= Version("2.0.0")

if PSN_V2:
    from pysaucenao.errors import SauceNaoError as SauceNaoBaseError
    from pysaucenao.results import SauceNaoResults
else:
    from pysaucenao.errors import SauceNaoException as SauceNaoBaseError

# 读取配置
tokens_config = ConfigManager("json/tokens.json")
saucenao_api_key = tokens_config.get("saucenao_api_key") or ""

# 相似度阈值（低于此值视为未匹配）
MIN_SIMILARITY = 60.0

# 临时图片路径（相对 nonebot 工作目录）
TEMP_IMG_REL = "images/saucenao/source.jpg"
TEMP_IMG_ABS = path_manager.nb_path() + TEMP_IMG_REL

# 未找到结果时的提示
NOT_FOUND_MSG = "你的图片真是小众又独特！没有找到匹配结果哦！"


if PSN_V2:
    class ProxiedSauceNao(SauceNao):
        """2.x 专用：走项目代理，并修复上游 from_file 不上传文件的 bug。"""

        def _session(self) -> aiohttp.ClientSession:
            proxy = misc_manager.misc_data.get("http_proxy", "")
            if not proxy:
                return super()._session()
            return aiohttp.ClientSession(
                cookies={"show_first": "0"},
                proxy=proxy,
            )

        async def from_file(self, path_or_fh) -> SauceNaoResults:
            """正确以 multipart/form-data 上传图片文件。"""
            params = self._build_params()
            form = aiohttp.FormData()
            # SauceNAO 接收的文件字段名为 file
            with open(path_or_fh, "rb") as fh:
                form.add_field(
                    "file", fh, filename="image.jpg", content_type="image/jpeg"
                )
                async with self._session() as session:
                    async with session.post(
                        self._endpoint, params=params, data=form
                    ) as response:
                        try:
                            status_code, data = (
                                response.status,
                                await response.json(),
                            )
                        except aiohttp.ContentTypeError:
                            raise SauceNaoBaseError(
                                "SauceNao returned a malformed json response."
                            )
            return self._process_response(status_code, data)


def make_sauce_client():
    """按 pysaucenao 版本构造客户端（1.x 用原生代理参数，2.x 用子类）。"""
    proxy = misc_manager.misc_data.get("http_proxy", "") or None
    if PSN_V2:
        return ProxiedSauceNao(api_key=saucenao_api_key, min_similarity=MIN_SIMILARITY)
    # 1.x 构造函数 api_key 为仅限关键字参数，且原生支持 proxy
    return SauceNao(api_key=saucenao_api_key, min_similarity=MIN_SIMILARITY, proxy=proxy)


async def search_image(url: str):
    """
    调用 SauceNAO API 溯源图片。
    返回 dict: {title, similarity, author, link} 或 None（无结果/失败）
    """
    if not saucenao_api_key:
        return None
    # 确保临时目录存在
    os.makedirs(os.path.dirname(TEMP_IMG_ABS), exist_ok=True)
    # 同步下载图片到本地（避免 SauceNAO 服务器无法访问本地 OneBot 缓存 URL）
    loop = asyncio.get_event_loop()
    ret = await loop.run_in_executor(None, img_process.download_img, url, TEMP_IMG_REL)
    if ret != 0:
        print(f"SauceNAO：下载图片失败：{url}")
        return None
    try:
        # 用本地文件上传给 SauceNAO
        sauce = make_sauce_client()
        results = await sauce.from_file(TEMP_IMG_ABS)
        if not results:
            return None
        best = results[0]
        similarity = float(best.similarity)
        if similarity < MIN_SIMILARITY:
            return None
        title = best.title or "未知"
        author = best.author_name or "未知"
        link = best.url or (best.urls[0] if best.urls else "")
        return {
            "title": title,
            "similarity": similarity,
            "author": author,
            "link": link,
        }
    except SauceNaoBaseError as e:
        print(f"SauceNAO API 错误：{e}")
        return None
    except Exception as e:
        print(f"SauceNAO 搜索出错：{e}")
        return None


searchpic = on_command("搜图", aliases={"saucenao", "searchpic"}, priority=10, block=True)


@searchpic.handle()
async def handle_function(args: Message = CommandArg(), bot: Bot = Bot, event: MessageEvent = Event):
    if not feature_manager.get("saucenao"):
        raise FinishedException

    img_url = ""
    # 优先从 args 中获取图片
    if len(args) > 0 and args[0].type == 'image':
        img_url = args[0].data['url']
    else:
        # 从回复消息中获取图片
        rep_con = await plugins.test1.get_reply_content(event.original_message, bot)
        if rep_con and rep_con[0]["type"] == 'image':
            img_url = rep_con[0]['data']['url']

    if not img_url:
        await searchpic.finish("请提供要搜索的图片！用法：/搜图 [图片] 或 [回复图片] /搜图")

    result = await search_image(img_url)
    if not result:
        await searchpic.finish(NOT_FOUND_MSG)

    # 构造回复消息：开头引用被搜索的图片所在消息
    reply_id = None
    for seg in event.original_message:
        if seg.type == "reply":
            reply_id = seg.data.get("id")
            break
    # 若没有回复段，则回复用户指令消息本身
    if reply_id is None:
        reply_id = event.message_id

    resp_text = f"{result['title']} ({result['similarity']:.2f}%)\n{result['author']}\n{result['link']}"
    await searchpic.finish(Message(f"[CQ:reply,id={reply_id}]{resp_text}"))
