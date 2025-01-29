import os
from enum import Enum
import asyncio
import argparse
from copy import deepcopy
import logging

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from playwright.async_api import Page
from playwright.async_api import async_playwright

from config import *


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

class Order(Enum):
    NAME = 0
    TYPE = 2
    TIME_ASC = 4
    TIME_DESC = 5 # default
    SIZE_ASC = 6
    SIZE_DESC = 7

ORDER_BAR_SELECTOR = "//div[contains(@class, 'tab_line')]//div[contains(@class, 'selectBar')]"

ORDER_SELECTOR = {i:f"{ORDER_BAR_SELECTOR}//li[@value='{i.value}']" for i in list(Order)}

ORDER_CMD_CHOICES = {
    "name": Order.NAME,
    "type": Order.TYPE,
    "time_asc": Order.TIME_ASC,
    "time_desc": Order.TIME_DESC,
    "size_asc": Order.SIZE_ASC,
    "size_desc": Order.SIZE_DESC
}


### logger ###

logging.basicConfig(level=LOG_LEVEL, format = '%(asctime)s %(name)s: [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


### argparse ###

parser = argparse.ArgumentParser(prog="EasyShare(互传)_Web_Downloader", description="This script simulates the browser request to realize the function of **quick** batch file download. 本脚本通过模拟浏览器请求，实现了互传网页版**快速**批量下载文件的功能")
parser.add_argument("menu_type", choices=["home", "img", "video", "music", "app", "doc"], help="选择下载的文件类型")
parser.add_argument("-o", "--order", choices=ORDER_CMD_CHOICES.keys(), help="选择排序方式，默认time_desc")
parser.add_argument("-n", "--number", type=int, help="选择下载的文件数量")
parser.add_argument("-r", "--override", action="store_true", help="是否覆盖同名文件")
parser.add_argument("-D", "--debug", action="store_true", help="开启调试模式")
parser.add_argument("-U", "--base-url", help="设置互传网页版地址")
parser.add_argument("-S", "--save-dir", help="设置下载保存目录")
parser.add_argument("-B", "--batch-size", type=int, help="设置每次下载的文件数量")
parser.add_argument("-T", "--contents-timeout", type=int, help="等待内容加载的时间，单位ms")
parser.add_argument("-d", "--tmp-save-dir", help="设置临时保存目录")


### functions ###

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


async def batch_download(page, menu_type, save_dir, num=None, batch_size=None, override=False, _downloaded_list=None):
    # type: (Page, str, str, int|None, int|None, bool, list|None) -> tuple[int, list[str]]
    """批量下载
    
    Args:
        page: Page
        menu_type: str - Menu.value
        save_dir: str
        num: int - 最多下载的文件数量，默认为None，即下载所有“可见”(html中有的)文件
        batch_size: int - 一批次并行下载的文件数量，默认为None，即一次性下载所有“可见”(html中有的)文件
        override: bool - 是否覆盖已存在的文件，默认为False
        _downloaded_list: list[str] - 已下载的文件名列表，默认为None。注：由`srcoll_all_download`调用，且是deepcopy。
    """
    existed_list = os.listdir(save_dir)
    
    # the item selector: used to be hovered
    selector = ITEMS_SELECTOR[menu_type]
    # the download selector: used to be clicked
    download_selector = DOWNLOAD_SELECTOR[menu_type]

    await page.wait_for_selector(selector)
    elements = await page.query_selector_all(selector)

    num = min(num, len(elements)) if num else len(elements)
    batch_size = min(batch_size, len(elements)) if batch_size else len(elements)
    downloaded_list = deepcopy(_downloaded_list) if _downloaded_list else []
    downloaded_list_lock = asyncio.Lock()

    batch_count = 0
    count = 0

    while count < num:
        async with asyncio.TaskGroup() as tg:
            for element in elements[batch_count * batch_size:(batch_count + 1) * batch_size]:
                # title is the file name
                title = await element.get_attribute("title")
                # do not download if the file already exists or is downloaded
                if not override and (title in existed_list or title in downloaded_list):
                    continue

                async with page.expect_download() as download_info:
                    await element.hover()
                    await element.eval_on_selector(download_selector, "el => el.click()")

                    # this enables parallel downloading!
                    async def save():
                        download = await download_info.value
                        file_path = os.path.join(save_dir, download.suggested_filename)
                        await download.save_as(file_path)
                        logger.info(f"Downloaded '{title}' to {file_path}")
                        async with downloaded_list_lock:
                            downloaded_list.append(title)
                    tg.create_task(save())
                    
                    count += 1
                    if count >= num:
                        break

        batch_count += 1
    
    return count, downloaded_list


async def scroll_all_download(page, menu_type, save_dir, num=None, batch_size=None, override=False):
    # type: (Page, str, str, int|None, int|None, bool) -> list[str]
    """滚动页面，批量下载
    
    Args:
        page: Page
        menu_type: str - Menu.value
        save_dir: str
        num: int - 最多下载的文件数量，默认为None，即下载所有“可见”(html中有的)文件
        batch_size: int - 一批次并行下载的文件数量，默认为None，即一次性下载所有“可见”(html中有的)文件
        override: bool - 是否覆盖已存在的文件，默认为False
    """
    selector = ITEMS_SELECTOR[menu_type]
    await page.wait_for_selector(selector)

    count = 0
    downloaded_list = []
    existed_list = os.listdir(save_dir)

    while not num or count < num:
        tmp_count, downloaded_list = await batch_download(page, menu_type, save_dir, num - count if num else None, batch_size, override, downloaded_list)    
        count += tmp_count

        original_elements = await page.query_selector_all(selector)    
        original_list = [el.get_attribute("title") for el in original_elements]

        last_element = (original_elements)[-1]
        await last_element.scroll_into_view_if_needed()
        # better wait a bit to let elements be fully loaded
        page.wait_for_timeout(500)

        new_elements = await page.query_selector_all(selector)    
        new_list = [el.get_attribute("title") for el in new_elements]

        # no more elements: end
        if original_list == new_list:
            break
        
    return downloaded_list


async def select_order(page, menu_type, order_type, timeout=3000):
    # type: (Page, str, Order, int) -> None
    """选择排序方式"""
    order_bar_selector = f"{CONTENTS_SELECTOR[menu_type]}{ORDER_BAR_SELECTOR}"
    order_selector = f"{CONTENTS_SELECTOR[menu_type]}{ORDER_SELECTOR[order_type]}"

    await page.wait_for_selector(order_bar_selector)
    await page.hover(order_bar_selector)

    await page.wait_for_selector(order_selector)
    await page.click(order_selector)
    # wait for content to be loaded
    await page.wait_for_timeout(timeout)


async def main(menu_type, order_type=None, num=None, override=False, *, debug=None, base_url=None, save_dir=None, batch_size=None, contents_timeout=None, tmp_save_dir=None):
    # type: (str, Order|None, int|None, bool, Any, bool, str|None, str|None, int|None, int|None, str|None) -> None
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

        if order_type:
            await select_order(page, menu_type, order_type, CONTENTS_TIMEOUT)

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
    asyncio.run(main(args.menu_type, ORDER_CMD_CHOICES[args.order], args.number, args.override, debug=args.debug, base_url=args.base_url, save_dir=args.save_dir, batch_size=args.batch_size, contents_timeout=args.contents_timeout, tmp_save_dir=args.tmp_save_dir))
