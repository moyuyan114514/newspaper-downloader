# -*- coding: UTF-8 -*-
"""
光明日报、文摘报、中华读书报的公共基类
"""
import re
from abc import ABC
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Optional, Tuple
from .base import PlatformDownloaderBase, EditionInfo
from ..utils.logger import logger


class GMWDownloaderBase(PlatformDownloaderBase):
    """光明日报、文摘报、中华读书报的公共基类
    
    这三个报纸都使用光明网(epaper.gmw.cn)的相同模板
    """
    
    BASE_URL = "https://epaper.gmw.cn"
    PAPER_CODE = ""
    PAPER_NAME = ""
    
    def __init__(self, config):
        super().__init__(config)
        self._index_url = f'{self.BASE_URL}/{self.PAPER_CODE}/html/layout/index.html'
    
    def _log_error(self, message: str):
        logger.error(message)
    
    def _log_warning(self, message: str):
        logger.warning(message)
    
    def _get_latest_date(self) -> Optional[str]:
        """从 index 页解析最新一期的真实日期

        Returns:
            日期字符串 (YYYY-MM-DD)，解析失败返回 None
        """
        try:
            resp = self._session.get(self._index_url, timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
        except Exception as e:
            self._log_error(f"获取{self.PAPER_NAME}最新期号失败: {e}")
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')
        list_ul = soup.find('ul', id='list')
        if not list_ul:
            return None

        a = list_ul.find('a', href=True)
        if not a:
            return None

        m = re.search(r'(\d{6})/(\d{2})/node_\d+\.html', a.get('href', ''))
        if not m:
            return None

        ym = m.group(1)
        return f"{ym[:4]}-{ym[4:6]}-{m.group(2)}"

    def _get_latest_edition(self) -> Optional[EditionInfo]:
        latest_date = self._get_latest_date()
        if not latest_date:
            self._log_error(f"{self.PAPER_NAME} 无法确定最新期号")
            return None
        return self._get_edition_by_date(latest_date)

    def _page_node_url(self, date_formatted: str, page_num: int) -> str:
        """构造版面页 URL，子类可覆盖以适配不同路径结构"""
        return f'{self.BASE_URL}/{self.PAPER_CODE}/html/layout/{date_formatted}/node_{page_num:02d}.html'

    def has_edition(self, date: str) -> bool:
        """轻量探测：仅请求第一版页面判断当日是否有报"""
        date_str = date.replace('-', '')
        date_formatted = f"{date_str[:4]}{date_str[4:6]}/{date_str[6:8]}"
        return self._get_page_image_url(self._page_node_url(date_formatted, 1)) is not None

    def _get_edition_by_date(self, date: str) -> Optional[EditionInfo]:
        """根据日期获取版面信息

        版面页按日期存放，版号可能有跳号，逐个请求直到连续取不到图片为止。

        Args:
            date: 日期字符串，格式为 YYYY-MM-DD

        Returns:
            EditionInfo 包含版面信息和页面URL列表
        """
        date_str = date.replace('-', '')
        date_formatted = f"{date_str[:4]}{date_str[4:6]}/{date_str[6:8]}"

        page_urls = []
        page_num = 1
        consecutive_misses = 0
        while page_num <= 40 and consecutive_misses < 3:
            page_url = self._page_node_url(date_formatted, page_num)
            img_url = self._get_page_image_url(page_url)
            if not img_url:
                consecutive_misses += 1
            else:
                consecutive_misses = 0
                page_urls.append(img_url)
            page_num += 1

        if not page_urls:
            self._log_warning(f"{self.PAPER_NAME} {date} 未找到任何版面")
            return None

        return EditionInfo(
            url=page_urls[0] if len(page_urls) == 1 else "",
            filename=f"{self.PAPER_NAME}_{date_str}.pdf",
            date=date,
            page_urls=page_urls
        )
    
    def _get_page_image_url(self, page_url: str) -> Optional[str]:
        """从版面页面获取图片URL
        
        子类可以重写此方法以实现特定的图片提取逻辑
        """
        return None
    
    def _extract_image_from_page_gmrb(self, page_url: str) -> Tuple[Optional[str], str]:
        """光明日报的图片提取逻辑"""
        try:
            resp = self._session.get(page_url, timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            html = resp.text
        except Exception as e:
            return None, "未知版"
        
        soup = BeautifulSoup(html, 'html.parser')
        
        version_div = soup.find('div', class_='m-paper-version')
        page_name = "未知版"
        if version_div:
            span = version_div.find('span', class_='mob-version')
            if span:
                page_name = span.get_text(strip=True)
        
        img = soup.find('img', id='map')
        if img and img.get('src'):
            src = img.get('src')
            if src:
                abs_url = urljoin(page_url, src)
                jpg_url = abs_url.replace('.jpg.2', '.jpg')
                return jpg_url, page_name

        # 兜底：部分站点的整版图不带 id="map"，但有 USEMAP 或 pic/ 路径
        # （如中国青年报: <img src="../../../pic/.../xxx.jpg.2" USEMAP=#PagePicMap>）
        for img in soup.find_all('img'):
            src = img.get('src') or ''
            if '.jpg' in src and (img.get('usemap') or '/pic/' in src):
                abs_url = urljoin(page_url, src)
                jpg_url = abs_url.replace('.jpg.2', '.jpg')
                return jpg_url, page_name

        return None, page_name
    
    def _extract_image_from_page_wenzhai(self, page_url: str) -> Tuple[Optional[str], str]:
        """文摘报的备用图片提取逻辑"""
        img_url, page_name = self._extract_image_from_page_gmrb(page_url)
        if img_url:
            return img_url, page_name
        
        try:
            resp = self._session.get(page_url, timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            html = resp.text
        except Exception as e:
            return None, "未知版"
        
        soup = BeautifulSoup(html, 'html.parser')
        
        version_div = soup.find('div', class_='m-paper-version')
        page_name = "未知版"
        if version_div:
            span = version_div.find('span', class_='mob-version')
            if span:
                page_name = span.get_text(strip=True)
        
        all_imgs = soup.find_all('img')
        for img in all_imgs:
            src = img.get('src')
            if src and 'page' in src and ('.jpg' in src or 'images' in src):
                abs_url = urljoin(page_url, src)
                jpg_url = abs_url.replace('.jpg.2', '.jpg').replace('../../../', 'https://img.gmw.cn/')
                return jpg_url, page_name
        
        return None, page_name
