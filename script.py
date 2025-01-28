import os
from enum import Enum
import asyncio
import argparse
import logging

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from playwright.async_api import Page
from playwright.async_api import async_playwright


### argparse ###

parser = argparse.ArgumentParser(prog="EasyShare(互传)_Web_Downloader", description="This script simulates the browser request to realize the function of **quick** batch file download. 本脚本通过模拟浏览器请求，实现了互传网页版**快速**批量下载文件的功能")
parser.add_argument("menu_type", choices=["home", "img", "video", "music", "app", "doc"], help="选择下载的文件类型")
parser.add_argument("-n", "--number", type=int, help="选择下载的文件数量")
parser.add_argument("-o", "--override", action="store_true", help="是否覆盖同名文件")
parser.add_argument("-D", "--debug", action="store_true", help="开启调试模式")
parser.add_argument("-B", "--base-url", help="设置互传网页版地址")
parser.add_argument("-A", "--save-dir", help="设置下载保存目录")
parser.add_argument("-S", "--batch-size", type=int, help="设置每次下载的文件数量")
parser.add_argument("-T", "--contents-timeout", type=int, help="等待内容加载的时间，单位ms")
parser.add_argument("-d", "--tmp-save-dir", help="设置临时保存目录")


### 配置参数 ###

DEBUG = False
# do not use "http://as.vivo.com/"; use the url which has already established connection
BASE_URL = "http://192.168.1.57:55666/"
# 下载保存目录
SAVE_DIR = "G:\\phoneT\\互传-网页传文件\\ScriptDownloads"  
# no cookies
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
}
BATCH_SIZE = 6
CONTENTS_TIMEOUT = 3000 # ms
# 日志配置
LOG_LEVEL = logging.INFO


### 常量 ###

class Menu(Enum):
    HOME = "home"
    IMG = "img"
    VIDEO = "video"
    MUSIC = "music"
    APP = "app"
    DOC = "doc"
    FILE = "file"

MENU_SELECTOR = {
    Menu.HOME.value: f"//li[@id='{Menu.HOME.value}_Module']//div",
    Menu.IMG.value: f"//li[@id='{Menu.IMG.value}_Module']//div",
    Menu.VIDEO.value: f"//li[@id='{Menu.VIDEO.value}_Module']//div",
    Menu.MUSIC.value: f"//li[@id='{Menu.MUSIC.value}_Module']//div",
    Menu.APP.value: f"//li[@id='{Menu.APP.value}_Module']//div",
    Menu.DOC.value: f"//li[@id='{Menu.DOC.value}_Module']//div",
    Menu.FILE.value: f"//li[@id='{Menu.FILE.value}_Module']//div",
}

CONTENTS_SELECTOR = {
    Menu.HOME.value: f"//div[contains(@class, 'module_container')][1]//div",
    Menu.IMG.value: f"//div[contains(@class, '{Menu.IMG.value}Page_contents')]",
    Menu.VIDEO.value: f"//div[contains(@class, '{Menu.VIDEO.value}Page_contents')]",
    Menu.MUSIC.value: f"//div[contains(@class, 'module_container')][4]//div",
    Menu.APP.value: f"//div[contains(@class, 'module_container')][5]//div",
    Menu.DOC.value: f"//div[contains(@class, 'module_container')][6]//div",
    Menu.FILE.value: f"//div[contains(@class, 'module_container')][7]//div",
}

ITEMS_SELECTOR = {
    Menu.HOME.value: f"{CONTENTS_SELECTOR[Menu.HOME.value]}//div[contains(@class, 'icon_list_item')]",
    Menu.IMG.value: f"{CONTENTS_SELECTOR[Menu.IMG.value]}//div[contains(@class, 'image_list_item')]",
    Menu.VIDEO.value: f"{CONTENTS_SELECTOR[Menu.VIDEO.value]}//div[contains(@class, 'video_list_item')]",
    Menu.MUSIC.value: f"{CONTENTS_SELECTOR[Menu.MUSIC.value]}//li[contains(@class, 'musicName')]",
    Menu.APP.value: f"{CONTENTS_SELECTOR[Menu.APP.value]}//div[contains(@class, 'app_list_item')]",
    Menu.DOC.value: f"{CONTENTS_SELECTOR[Menu.DOC.value]}//li[contains(@class, 'docName')]",
}

# relative to `ITEMS_SELECTOR`
DOWNLOAD_SELECTOR = {
    Menu.HOME.value: f"//dd[contains(@class, 'downloadItem')]",
    Menu.IMG.value: f"//dd[contains(@class, 'downloadItem')]",
    Menu.VIDEO.value: f"//dd[contains(@class, 'downloadItem')]",
    Menu.MUSIC.value: f"..//span[contains(@class, 'op_download')]//b",
    Menu.APP.value: f"//dd[contains(@class, 'downloadItem')]",
    Menu.DOC.value: f"..//span[contains(@class, 'op_download')]//b"
}

DIR_NAMES = {
    Menu.HOME.value: "主页",
    Menu.IMG.value: "图片",
    Menu.VIDEO.value: "视频",
    Menu.MUSIC.value: "音乐",
    Menu.APP.value: "应用",
    Menu.DOC.value: "文档",
    Menu.FILE.value: "文件",
}


### 其他 ###

logging.basicConfig(level=LOG_LEVEL, format = '%(asctime)s %(name)s: [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def create_dir(path):
    # type: (str) -> bool
    """判断目录是否存在，不存在则递归创建"""
    if not os.path.exists(path):  # 先检查路径是否存在
        os.makedirs(path)         # 创建目录（包含所有中间目录）
        return True
    else:
        return False


# async def is_element_visible(page, selector):
#     # type: (Page, str) -> bool
#     """判断元素的display样式是否不为none"""
#     # 检查元素的display属性
#     display_value = await page.eval_on_selector(selector, "el => window.getComputedStyle(el).display")
#     # 返回判断结果
#     return display_value != "none"


def create_wait_fn(selector, timeout=3000):
    # type: (str, int) -> callable
    """创建等待函数"""
    async def wait_fn(page):
        # type: (Page) -> None

        # while not await is_element_visible(page, selector):
        #     await page.wait_for_timeout(500)
        await page.wait_for_selector(selector)
        # wait for the content to be loaded
        await page.wait_for_timeout(timeout)

    return wait_fn


async def click_wait(page, click_selector, wait_selector=None, wait_fn=None):
    # type: (Page, str, str|None, callable|None) -> str
    """动态模拟点击，获取页面内容"""
    await page.wait_for_selector(click_selector)
    await page.click(click_selector)

    # 处理动态内容
    if wait_selector:
        await page.wait_for_selector(wait_selector)
    if wait_fn:
        await wait_fn(page)

    # 获取内容
    return await page.content()


async def batch_download(page, menu_type, save_dir, num=None, batch_size=None, override=False, name_list=None):
    # type: (Page, str, str, int|None, int|None, bool, list|None) -> tuple[int, list[str]]
    """批量下载"""
    selector = ITEMS_SELECTOR[menu_type]
    download_selector = DOWNLOAD_SELECTOR[menu_type]

    await page.wait_for_selector(selector)
    elements = await page.query_selector_all(selector)

    if not num:
        num = len(elements)
    if not batch_size:
        batch_size = len(elements)
    if not name_list:
        name_list = []

    num = min(num, len(elements))
    batch_size = min(batch_size, len(elements))
    name_list_lock = asyncio.Lock()

    batch_count = 0
    count = 0

    while count < num:
        async with asyncio.TaskGroup() as tg:
            for element in elements[batch_count * batch_size:(batch_count + 1) * batch_size]:
                async with page.expect_download() as download_info:
                    title = await element.get_attribute("title")
                    if title not in name_list:
                        await element.hover()
                        await element.eval_on_selector(download_selector, "el => el.click()")

                        # if this enables batch? No!
                        # download = await download_info.value
                        # await download.save_as(os.path.join(save_dir, download.suggested_filename))

                        # this enables batch!!!
                        async def save():
                            download = await download_info.value
                            file_path = os.path.join(save_dir, download.suggested_filename)
                            if override or not os.path.isfile(file_path):
                                await download.save_as(file_path)
                                logger.info(f"Downloaded '{title}' to {file_path}")
                                async with name_list_lock:
                                    name_list.append(title)
                        tg.create_task(save())
                        
                        count += 1
                        if count >= num:
                            break

        batch_count += 1
    
    return count, name_list


async def scroll_all_download(page, menu_type, save_dir, num=None, batch_size=None, override=False):
    # type: (Page, str, str, int|None, int|None, bool) -> list[str]
    """滚动页面，批量下载"""
    count = 0
    name_list = []
    selector = ITEMS_SELECTOR[menu_type]

    while not num or count < num:
        tmp_count, name_list = await batch_download(page, menu_type, save_dir, num - count if num else None, batch_size, override, name_list)    
        if tmp_count == 0 or count == len(name_list):
            break
        count += tmp_count

        await page.wait_for_selector(selector)
        element = (await page.query_selector_all(selector))[-1]

        await element.scroll_into_view_if_needed()
        
    return name_list

    # # for test
    # await page.wait_for_selector(selector)
    # elements = await page.query_selector_all(selector)
    # logger.debug(f"Initially found {len(elements)} elements")
    # print(elements)
    # element = (await page.query_selector_all(selector))[-1]

    # await element.scroll_into_view_if_needed()
    # await element.click()

    # elements = await page.query_selector_all(selector)
    # logger.debug(f"Found {len(elements)} elements")


async def main(menu_type, num=None, override=False, *, debug=None, base_url=None, save_dir=None, batch_size=None, contents_timeout=None, tmp_save_dir=None):
    # type: (str, int|None, bool, Any, bool, str|None, str|None, int|None, int|None, str|None) -> None
    global DEBUG, BASE_URL, SAVE_DIR, BATCH_SIZE, CONTENTS_TIMEOUT
    DEBUG = debug if debug else DEBUG
    BASE_URL = base_url if base_url else BASE_URL
    SAVE_DIR = save_dir if save_dir else SAVE_DIR
    BATCH_SIZE = batch_size if batch_size else BATCH_SIZE
    CONTENTS_TIMEOUT = contents_timeout if contents_timeout else CONTENTS_TIMEOUT

    tmp_save_dir = os.path.join(SAVE_DIR, ".tmp") if not tmp_save_dir else tmp_save_dir
    save_dir = os.path.join(SAVE_DIR, DIR_NAMES[menu_type])
    create_dir(tmp_save_dir)
    create_dir(save_dir)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not DEBUG, downloads_path=tmp_save_dir)
        page = await browser.new_page()
        await page.goto(BASE_URL)

        contents_wait_fn = create_wait_fn(f"{CONTENTS_SELECTOR[menu_type]}/..", CONTENTS_TIMEOUT)
        await click_wait(page, MENU_SELECTOR[menu_type], wait_fn=contents_wait_fn)

        name_list = await scroll_all_download(page, menu_type, save_dir, 4 if DEBUG and not num else num, 2 if DEBUG and not batch_size else BATCH_SIZE, override)

        output = "Download sum:\n"
        for i, name in enumerate(name_list):
            output += f"\t{i}: {name}\n"
        logger.info(output)

        while DEBUG:
            pass
        await browser.close()


async def test():
    tmp_save_dir = os.path.join(SAVE_DIR, ".tmp")
    save_dir = os.path.join(SAVE_DIR, DIR_NAMES[Menu.VIDEO.value])
    create_dir(tmp_save_dir)
    create_dir(save_dir)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not DEBUG, downloads_path=tmp_save_dir)
        page = await browser.new_page()

        await page.goto(BASE_URL)

        contents_wait_fn = create_wait_fn(f"{CONTENTS_SELECTOR[Menu.VIDEO.value]}/..")
        await click_wait(page, MENU_SELECTOR[Menu.VIDEO.value], wait_fn=contents_wait_fn)

        # await batch_download(page, Menu.VIDEO.value, save_dir, 2 if DEBUG else None, BATCH_SIZE)
        await scroll_all_download(page, Menu.VIDEO.value, save_dir, 4 if DEBUG else None, BATCH_SIZE)

        while DEBUG:
            pass
        await browser.close()


if __name__ == "__main__":
    args = parser.parse_args()
    asyncio.run(main(args.menu_type, args.number, args.override, debug=args.debug, base_url=args.base_url, save_dir=args.save_dir, batch_size=args.batch_size, contents_timeout=args.contents_timeout, tmp_save_dir=args.tmp_save_dir))
