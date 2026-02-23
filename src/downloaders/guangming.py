# -*- coding: UTF-8 -*-
"""
光明日报下载器
官方网站: https://epaper.gmw.cn/gmrb/
"""
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Optional, List
from .base import PlatformDownloaderBase, EditionInfo


class GuangmingRibaoDownloader(PlatformDownloaderBase):
    BASE_URL = "https://epaper.gmw.cn"
    
    def get_platform_name(self) -> str:
        return "光明日报"
    
    def get_platform_id(self) -> str:
        return "guangming"
    
    def get_latest_edition(self, date: str = None) -> Optional[EditionInfo]:
        try:
            if date:
                return self._get_edition_by_date(date)
            else:
                return self._get_latest_edition()
        except Exception as e:
            print(f"获取光明日报版面信息失败: {e}")
            return None
    
    def _get_latest_edition(self) -> Optional[EditionInfo]:
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        return self._get_edition_by_date(date_str)
    
    def _get_edition_by_date(self, date: str) -> Optional[EditionInfo]:
        date_str = date.replace('-', '')
        date_formatted = f"{date_str[:4]}{date_str[4:6]}/{date_str[6:8]}"
        
        try:
            resp = self._session.get('https://epaper.gmw.cn/gmrb/html/layout/index.html', timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            html = resp.text
        except Exception as e:
            print(f"获取版面列表失败: {e}")
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
                    page_url = f'https://epaper.gmw.cn/gmrb/html/layout/{href}'
                    page_urls.append(page_url)
                    
                    page_name = li.get_text(strip=True)
                    page_names.append(page_name)
        
        if not page_urls:
            for page in range(1, 20):
                page_url = f'https://epaper.gmw.cn/gmrb/html/layout/{date_formatted}/node_{page:02d}.html'
                page_urls.append(page_url)
                page_names.append(f"第{page}版")
        
        image_urls = []
        for i, page_url in enumerate(page_urls):
            img_url, page_name = self._get_page_image_url(page_url)
            if img_url:
                image_urls.append(img_url)
                page_names[i] = page_name or page_names[i]
        
        if not image_urls:
            return None
        
        return EditionInfo(
            url=image_urls[0] if len(image_urls) == 1 else "",
            filename=f"光明日报_{date_str}.pdf",
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
            abs_url = urljoin(page_url, src)
            jpg_url = abs_url.replace('.jpg.2', '.jpg')
            return jpg_url, page_name
        
        return None, page_name
