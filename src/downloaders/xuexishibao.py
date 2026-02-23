# -*- coding: UTF-8 -*-
"""
学习时报下载器
"""
import re
import datetime
from typing import Optional, List
from .base import PlatformDownloaderBase, EditionInfo

class StudyTimesDownloader(PlatformDownloaderBase):
    BASE_URL = "https://paper.studytimes.cn"
    WEEKDAY_NAMES = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    
    def get_platform_name(self) -> str:
        return "学习时报"
    
    def get_platform_id(self) -> str:
        return "xuexishibao"
    
    def get_latest_edition(self, date: str = None) -> Optional[EditionInfo]:
        if date:
            return self._get_edition_by_date(date)
        else:
            return self._get_latest_from_main_page()
    
    def _get_latest_from_main_page(self) -> Optional[EditionInfo]:
        try:
            url = f"{self.BASE_URL}/cntheory/"
            response = self._session.get(url, timeout=30)
            response.encoding = 'utf-8'
            
            pattern = r'\./(\d{4}-\d{2}/\d{2})/node_1\.html'
            match = re.search(pattern, response.text)
            
            if not match:
                return None
            
            date_path = match.group(1)
            date_parts = date_path.split('/')
            date_str = f"{date_parts[0]}-{date_parts[1]}"
            
            return self._get_edition_by_date(date_str)
        except Exception:
            return None
    
    def _get_edition_by_date(self, date: str) -> Optional[EditionInfo]:
        date_parts = date.split('-')
        date_path = f"{date_parts[0]}-{date_parts[1]}/{date_parts[2]}"
        url = f"{self.BASE_URL}/cntheory/{date_path}/node_1.html"
        
        try:
            response = self._session.get(url, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code == 404:
                return None
            
            if 'window.location.href' in response.text and len(response.text) < 500:
                return None
            
            pattern = r'href="(https://paper\.studytimes\.cn/files/Resource/yt/cntheory/\d{4}-\d{2}-\d{2}/\d{2}/images/\d{2}-[a-f0-9-]+\.pdf)"'
            matches = re.findall(pattern, response.text)
            
            if not matches:
                pattern2 = r'href="(https://paper\.studytimes\.cn/files/Resource/yt/cntheory/\d{4}-\d{2}-\d{2}/\d{2}/images/[^\"]+\.pdf)"'
                matches = re.findall(pattern2, response.text)
            
            if not matches:
                return None
            
            unique_urls = []
            seen = set()
            for pdf_url in matches:
                if pdf_url not in seen:
                    seen.add(pdf_url)
                    unique_urls.append(pdf_url)
            
            date_str = date.replace('-', '')
            return EditionInfo(
                url="",
                filename=f"学习时报_{date_str}.pdf",
                date=date,
                page_urls=unique_urls
            )
        except Exception:
            return None
    
    def get_weekday_name(self, date: str) -> str:
        try:
            date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
            return self.WEEKDAY_NAMES[date_obj.weekday()]
        except Exception:
            return ""
