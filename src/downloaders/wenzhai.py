# -*- coding: UTF-8 -*-
"""
文摘报下载器
官方网站: https://epaper.gmw.cn/wzb/
"""
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Optional, List
from .base import PlatformDownloaderBase, EditionInfo


class WenzhaiDownloader(PlatformDownloaderBase):
    BASE_URL = "https://epaper.gmw.cn"
    PAPER_CODE = "wzb"
    
    def get_platform_name(self) -> str:
        return "文摘报"
    
    def get_platform_id(self) -> str:
        return "wenzhai"
    
    def get_latest_edition(self, date: str = None) -> Optional[EditionInfo]:
        try:
            if date:
                return self._get_edition_by_date(date)
            else:
                return self._get_latest_edition()
        except Exception as e:
            print(f"获取文摘报版面信息失败: {e}")
            return None
    
    def _get_latest_edition(self) -> Optional[EditionInfo]:
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        return self._get_edition_by_date(date_str)
    
    def _get_edition_by_date(self, date: str) -> Optional[EditionInfo]:
        try:
            url = f'https://epaper.gmw.cn/{self.PAPER_CODE}/html/layout/index.html'
            resp = self._session.get(url, timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            html = resp.text
        except Exception as e:
            print(f"获取版面列表失败: {e}")
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        page_urls = []
        page_names = []
        
        list_ul = soup.find('ul', id='list')
        
        if list_ul:
            for li in list_ul.find_all('li'):
                a = li.find('a', href=True)
                if a and a.get('href'):
                    href = a.get('href')
                    if href.startswith('http'):
                        page_url = href
                    else:
                        page_url = f'https://epaper.gmw.cn/{self.PAPER_CODE}/html/layout/{href}'
                    page_urls.append(page_url)
                    
                    page_name = li.get_text(strip=True)
                    page_names.append(page_name)
        
        if not page_urls:
            return None
        
        image_urls = []
        for i, page_url in enumerate(page_urls):
            img_url, page_name = self._get_page_image_url(page_url)
            if img_url:
                image_urls.append(img_url)
                page_names[i] = page_name or page_names[i]
        
        if not image_urls:
            return None
        
        date_str = date.replace('-', '')
        return EditionInfo(
            url=image_urls[0] if len(image_urls) == 1 else "",
            filename=f"文摘报_{date_str}.pdf",
            date=date,
            page_urls=image_urls
        )
    
    def _get_page_image_url(self, page_url: str) -> tuple:
        try:
            resp = self._session.get(page_url, timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            html = resp.text
        except Exception as e:
            return None, None
        
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
        
        all_imgs = soup.find_all('img')
        for img in all_imgs:
            src = img.get('src')
            if src and 'page' in src and ('.jpg' in src or 'images' in src):
                abs_url = urljoin(page_url, src)
                jpg_url = abs_url.replace('.jpg.2', '.jpg').replace('../../../', 'https://img.gmw.cn/')
                return jpg_url, page_name
        
        return None, page_name
