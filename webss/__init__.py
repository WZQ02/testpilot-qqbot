import asyncio
from playwright.async_api import async_playwright

"""
import time
import io
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-extensions')
options.add_argument('--disable-plugins')

def take(url,sleep=5):
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    # driver.set_window_size(1280+16, 1024+147) 100%缩放下的设置
    driver.set_window_size(1280+22, 1024+150)
    time.sleep(sleep)
    driver.save_screenshot("webss/1.png")
    driver.quit()

def take2(url,dom_id,sleep=.5):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(.5)
    el = driver.find_element(By.ID, dom_id)
    # driver.set_window_size(el.size['width']+16, el.size['height']+148)
    driver.set_window_size(el.size['width']+40, el.size['height']+160)
    time.sleep(sleep)
    cdp_method = 'Page.captureScreenshot'
    params = {'clip': {'x': el.location['x'], 'y': el.location['y'], 'width': el.size['width'], 'height': el.size['height'], 'scale': 1}}
    data = driver.execute_cdp_cmd(cdp_method, params)
    screenshot = base64.b64decode(data['data'])
    with open('webss/1.png', 'wb') as f:
        f.write(screenshot)
    driver.quit()
"""

async def take(url,sleep=3,filename="1"):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.set_viewport_size({"width": 1280, "height": 1024})
        await page.screenshot(path=f"webss/{filename}.png")
        await asyncio.sleep(sleep)
        await browser.close()
        return 0

async def take2(url,dom_id,sleep=.5,filename="1"):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.locator("#"+dom_id).screenshot(path=f"webss/{filename}.png")
        await asyncio.sleep(sleep)
        await browser.close()
        return 0