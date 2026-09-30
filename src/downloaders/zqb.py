# -*- coding: UTF-8 -*-
"""
中国青年报下载器
官方网站: https://zqb.cyol.com （方正模板，版面结构与光明网系同源）

版面页: /pc/layout/YYYYMM/DD/node_XX.html
整版图: /pic/YYYYMM/DD/xxx.jpg.2 （去 .2 后缀为高清图），下载后合并为 PDF
"""
from typing import Optional
from .base import EditionInfo
from .gmw_base import GMWDownloaderBase


class ZhongguoQingnianbaoDownloader(GMWDownloaderBase):
    BASE_URL = "https://zqb.cyol.com"
    PAPER_CODE = ""  # URL 中无报代码段
    PAPER_NAME = "中国青年报"

    def __init__(self, config):
        super().__init__(config)
        self._index_url = f'{self.BASE_URL}/pc/layout/index.html'

    def get_platform_name(self) -> str:
        return self.PAPER_NAME

    def get_platform_id(self) -> str:
        return "zqb"

    def get_latest_edition(self, date: str = None) -> Optional[EditionInfo]:
        try:
            if date:
                return self._get_edition_by_date(date)
            else:
                return self._get_latest_edition()
        except Exception as e:
            self._log_error(f"获取{self.PAPER_NAME}版面信息失败: {e}")
            return None

    def _page_node_url(self, date_formatted: str, page_num: int) -> str:
        return f'{self.BASE_URL}/pc/layout/{date_formatted}/node_{page_num:02d}.html'

    def _get_page_image_url(self, page_url: str) -> Optional[str]:
        img_url, _ = self._extract_image_from_page_gmrb(page_url)
        return img_url
