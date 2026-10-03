import asyncio
from playwright.async_api import async_playwright, TimeoutError
import logging
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

# 浏览器引擎设置（chromium / firefox），持久化到 json/webss_config.json
# 供 webss 和 web_agent 共用，可通过 /修改浏览器引擎 命令切换
engine_config = ConfigManager("json/webss_config.json")
current_engine = engine_config.get("engine", "chromium")
if current_engine not in ("chromium", "firefox"):
    current_engine = "chromium"

def set_engine(name: str) -> str:
    """设置浏览器引擎并持久化，返回旧引擎名。无效名称抛 ValueError。"""
    global current_engine
    name = name.lower()
    if name not in ("chromium", "firefox"):
        raise ValueError(f"不支持的引擎：{name}")
    old = current_engine
    current_engine = name
    engine_config.set("engine", name)
    logger.info(f"浏览器引擎已从 {old} 切换为 {name}")
    return old

async def take(url,sleep=3,filename="1",xres=1280,yres=1024):
    try:
        async with async_playwright() as p:
            browser = await getattr(p, current_engine).launch()
            page = await browser.new_page()
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await page.set_viewport_size({"width": xres, "height": yres})
            await page.wait_for_timeout(sleep*1000)
            await page.screenshot(path=f"webss/{filename}.png", full_page=True)
            await browser.close()
            logger.info(f"已将网页 {url} 截取为 webss/{filename}.png")
            return 0
    except Exception as e:
        logger.error(f"获取网页 {url} 截图失败: {e}")
        return 1

async def take2(url,dom_id,sleep=.5,filename="1"):
    try:
        async with async_playwright() as p:
            browser = await getattr(p, current_engine).launch()
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_timeout(sleep*1000)
            await page.locator("#"+dom_id).screenshot(path=f"webss/{filename}.png")
            await browser.close()
            logger.info(f"已将 {url} 的网页元素 #{dom_id} 截取为 webss/{filename}.png")
            return 0
    except Exception as e:
        logger.error(f"截取 {url} 的网页元素 #{dom_id} 失败: {e}")
        return 1
