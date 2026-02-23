# -*- coding: UTF-8 -*-
"""
人民日报下载器
"""
import re
import datetime
from typing import Optional, List
from .base import PlatformDownloaderBase, EditionInfo

class PeopleDailyDownloader(PlatformDownloaderBase):
    BASE_URL = "https://paper.people.com.cn"
    
    def get_platform_name(self) -> str:
        return "人民日报"
    
    def get_platform_id(self) -> str:
        return "rmrb"
    
    def get_latest_edition(self, date: str = None) -> Optional[EditionInfo]:
        try:
            if date:
                return self._get_edition_by_date(date)
            else:
                return self._get_latest_from_main_page()
        except Exception:
            return None
    
    def _get_latest_from_main_page(self) -> Optional[EditionInfo]:
        url = f"{self.BASE_URL}/rmrb/pc/layout/index.html"
        response = self._session.get(url, timeout=30)
        response.encoding = 'utf-8'
        
        pattern = r'href="(\d{6}/\d{2}/node_\d+\.html)"'
        matches = re.findall(pattern, response.text)
        
        if not matches:
            return None
        
        first_match = matches[0]
        parts = first_match.split('/')
        date = f"{parts[0][:4]}-{parts[0][4:6]}-{parts[1]}"
        date_str = date.replace('-', '')
        date_path = parts[0] + '/' + parts[1]
        
        pattern = rf'href="({date_path}/node_(\d+)\.html)"'
        matches = re.findall(pattern, response.text)
        
        pages = [(int(m[1]), f"{self.BASE_URL}/rmrb/pc/layout/{m[0]}") for m in matches]
        page_urls = []
        
        for page_num, page_url in pages:
            pdf_url = self._get_pdf_url(page_url)
            if pdf_url:
                page_urls.append(pdf_url)
        
        if not page_urls:
            return None
        
        return EditionInfo(
            url=page_urls[0] if len(page_urls) == 1 else "",
            filename=f"人民日报_{date_str}.pdf",
            date=date,
            page_urls=page_urls
        )
    
    def _get_edition_by_date(self, date: str) -> Optional[EditionInfo]:
        date_str = date.replace('-', '')
        date_path = date_str[0:6] + '/' + date_str[6:8]
        
        page_urls = []
        page_num = 1
        
        while page_num <= 30:
            url = f"{self.BASE_URL}/rmrb/pc/layout/{date_path}/node_{page_num:02d}.html"
            pdf_url = self._get_pdf_url(url)
            if pdf_url:
                page_urls.append(pdf_url)
                page_num += 1
            else:
                if page_num == 1:
                    return None
                break
        
        if not page_urls:
            return None
        
        return EditionInfo(
            url=page_urls[0] if len(page_urls) == 1 else "",
            filename=f"人民日报_{date_str}.pdf",
            date=date,
            page_urls=page_urls
        )
    
    def _get_pdf_url(self, page_url: str) -> Optional[str]:
        try:
            response = self._session.get(page_url, timeout=30)
            response.encoding = 'utf-8'
            match = re.search(r'href="\.\./\.\./\.\./attachement/(\d{6}/\d{2}/[a-f0-9-]+\.pdf)"', response.text)
            if match:
                return f"https://paper.people.com.cn/rmrb/pc/attachement/{match.group(1)}"
        except Exception:
            pass
        return None
