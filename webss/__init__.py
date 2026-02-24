import asyncio
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)



async def take(url,sleep=3,filename="1"):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            await page.set_viewport_size({"width": 1280, "height": 1024})
            await page.screenshot(path=f"webss/{filename}.png")
            await asyncio.sleep(sleep)
            await browser.close()
            logger.info(f"已将网页 {url} 截取为 webss/{filename}.png")
            return 0
    except Exception as e:
        logger.error(f"获取网页 {url} 截图失败: {e}")
        return 1

async def take2(url,dom_id,sleep=.5,filename="1"):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            await page.locator("#"+dom_id).screenshot(path=f"webss/{filename}.png")
            await asyncio.sleep(sleep)
            await browser.close()
            logger.info(f"已将 {url} 的网页元素 #{dom_id} 截取为 webss/{filename}.png")
            return 0
    except Exception as e:
        logger.error(f"截取 {url} 的网页元素 #{dom_id} 失败: {e}")
        return 1