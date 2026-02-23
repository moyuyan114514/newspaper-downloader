# -*- coding: UTF-8 -*-
"""
光明日报、文摘报、中华读书报的公共基类
"""
from abc import ABC
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Optional, List, Tuple
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
    
    def _get_edition_by_date(self, date: str) -> Optional[EditionInfo]:
        """根据日期获取版面信息
        
        Args:
            date: 日期字符串，格式为 YYYY-MM-DD
            
        Returns:
            EditionInfo 包含版面信息和页面URL列表
        """
        date_str = date.replace('-', '')
        date_formatted = f"{date_str[:4]}{date_str[4:6]}/{date_str[6:8]}"
        
        try:
            resp = self._session.get(self._index_url, timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            html = resp.text
        except Exception as e:
            self._log_error(f"获取版面列表失败: {e}")
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        list_ul = soup.find('ul', id='list')
        page_urls = []
        page_names = []
        
        if list_ul:
            for li in list_ul.find_all('li'):
                a = li.find('a', href=True)
                if a and a.get('href'):
                    href = a.get('href')
                    if href.startswith('http'):
                        page_url = href
                    else:
                        page_url = f'{self.BASE_URL}/{self.PAPER_CODE}/html/layout/{href}'
                    page_urls.append(page_url)
                    
                    page_name = li.get_text(strip=True)
                    page_names.append(page_name)
        
        if not page_urls:
            for page in range(1, 20):
                page_url = f'{self.BASE_URL}/{self.PAPER_CODE}/html/layout/{date_formatted}/node_{page:02d}.html'
                page_urls.append(page_url)
                page_names.append(f"第{page}版")
        
        return self._fetch_all_page_images(page_urls, page_names, date_str, date)
    
    def _fetch_all_page_images(self, page_urls: List[str], page_names: List[str], date_str: str, date: str) -> Optional[EditionInfo]:
        """获取所有版面的图片URL"""
        image_urls = []
        for i, page_url in enumerate(page_urls):
            img_url = self._get_page_image_url(page_url)
            if img_url:
                image_urls.append(img_url)
        
        if not image_urls:
            return None
        
        return EditionInfo(
            url=image_urls[0] if len(image_urls) == 1 else "",
            filename=f"{self.PAPER_NAME}_{date_str}.pdf",
            date=date,
            page_urls=image_urls
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
