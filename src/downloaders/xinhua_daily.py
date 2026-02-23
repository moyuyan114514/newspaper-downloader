# -*- coding: UTF-8 -*-
"""
新华每日电讯下载器
官方网站: http://mrdx.cn/
"""
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Optional, List
from .base import PlatformDownloaderBase, EditionInfo


class XinhuaDailyDownloader(PlatformDownloaderBase):
    BASE_URL = "http://mrdx.cn"
    
    def get_platform_name(self) -> str:
        return "新华每日电讯"
    
    def get_platform_id(self) -> str:
        return "xinhua_daily"
    
    def get_latest_edition(self, date: str = None) -> Optional[EditionInfo]:
        try:
            if date:
                return self._get_edition_by_date(date)
            else:
                return self._get_latest_edition()
        except Exception as e:
            print(f"获取新华每日电讯版面信息失败: {e}")
            return None
    
    def _get_latest_edition(self) -> Optional[EditionInfo]:
        today = datetime.now()
        date_str = today.strftime('%Y%m%d')
        return self._get_edition_by_date(date_str)
    
    def _get_edition_by_date(self, date: str) -> Optional[EditionInfo]:
        date_str = date.replace('-', '')
        
        try:
            first_page_url = f'http://mrdx.cn/content/{date_str}/Page01BC.htm'
            resp = self._session.get(first_page_url, timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            html = resp.text
        except Exception as e:
            print(f"新华每日电讯暂时无法连接: {e}")
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        page_urls = self._get_image_urls_from_page(soup, date_str)
        
        if not page_urls:
            return None
        
        return EditionInfo(
            url=page_urls[0] if len(page_urls) == 1 else "",
            filename=f"新华每日电讯_{date_str}.pdf",
            date=date,
            page_urls=page_urls
        )
    
    def _get_image_urls_from_page(self, soup, date_str: str) -> List[str]:
        urls = []
        
        all_imgs = soup.find_all('img')
        
        for img in all_imgs:
            src = img.get('src')
            if src and 'Page' in src and '.jpg' in src:
                if src.startswith('http'):
                    img_url = src
                elif src.startswith('../../'):
                    img_url = f'http://mrdx.cn/{src.replace("../../", "")}'
                else:
                    img_url = urljoin(f'http://mrdx.cn/content/{date_str}/', src)
                
                if img_url not in urls:
                    urls.append(img_url)
        
        urls.sort()
        return urls
