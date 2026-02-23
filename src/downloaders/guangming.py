# -*- coding: UTF-8 -*-
"""
光明日报下载器
官方网站: https://epaper.gmw.cn/gmrb/

下载方式: 从HTML解析版面图片，去除 .2 后缀后下载
"""
import re
from datetime import datetime
from typing import Optional, List
from .base import PlatformDownloaderBase, EditionInfo
from .gmw_base import GMWDownloaderBase


class GuangmingRibaoDownloader(GMWDownloaderBase):
    """光明日报下载器
    
    下载方式: 从HTML解析版面图片，去除 .2 后缀后下载
    """
    
    BASE_URL = "https://epaper.gmw.cn"
    PAPER_CODE = "gmrb"
    PAPER_NAME = "光明日报"
    
    def get_platform_name(self) -> str:
        return self.PAPER_NAME
    
    def get_platform_id(self) -> str:
        return "guangming"
    
    def get_latest_edition(self, date: str = None) -> Optional[EditionInfo]:
        try:
            if date:
                return self._get_edition_by_date(date)
            else:
                return self._get_latest_edition()
        except Exception as e:
            self._log_error(f"获取{self.PAPER_NAME}版面信息失败: {e}")
            return None
    
    def _get_latest_edition(self) -> Optional[EditionInfo]:
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        return self._get_edition_by_date(date_str)
    
    def _get_page_image_url(self, page_url: str) -> tuple:
        """从版面页面获取图片URL和版名
        
        Args:
            page_url: 版面页面URL
            
        Returns:
            (图片URL, 版名) 的元组
        """
        return self._extract_image_from_page_gmrb(page_url)
