# -*- coding: UTF-8 -*-
"""
中华读书报下载器
官方网站: https://epaper.gmw.cn/zhdsb/

下载方式: 从HTML解析版面图片，下载后合并为PDF
"""
from typing import Optional
from .base import EditionInfo
from .gmw_base import GMWDownloaderBase


class ZhonghuadushuDownloader(GMWDownloaderBase):
    """中华读书报下载器
    
    下载方式: 从HTML解析版面图片，下载后合并为PDF
    """
    
    BASE_URL = "https://epaper.gmw.cn"
    PAPER_CODE = "zhdsb"
    PAPER_NAME = "中华读书报"
    
    def get_platform_name(self) -> str:
        return self.PAPER_NAME
    
    def get_platform_id(self) -> str:
        return "zhonghuadushu"
    
    def get_latest_edition(self, date: str = None) -> Optional[EditionInfo]:
        try:
            if date:
                return self._get_edition_by_date(date)
            else:
                return self._get_latest_edition()
        except Exception as e:
            self._log_error(f"获取{self.PAPER_NAME}版面信息失败: {e}")
            return None
    
    def _get_latest_edition(self):
        from datetime import datetime
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        return self._get_edition_by_date(date_str)
    
    def _get_page_image_url(self, page_url: str) -> Optional[str]:
        img_url, _ = self._extract_image_from_page_gmrb(page_url)
        return img_url
