# -*- coding: UTF-8 -*-
"""
解放军报下载器
官方网站: http://www.81.mil.cn （旧域名 81.cn 已迁移）

下载方式: 每日数字报 index.json 直接给出全部版面的直连 PDF，逐版下载后合并
"""
from datetime import datetime, timedelta
from typing import Optional
from .base import PlatformDownloaderBase, EditionInfo
from ..utils.logger import logger


class JiefangjunDailyDownloader(PlatformDownloaderBase):
    BASE_URL = "http://www.81.mil.cn"
    PAPER_CODE = "jfjb"
    # 当天未出报时最多向前回溯的天数
    MAX_LOOKBACK_DAYS = 7

    def get_platform_name(self) -> str:
        return "解放军报"

    def get_platform_id(self) -> str:
        return "jiefangjun"

    def get_latest_edition(self, date: str = None) -> Optional[EditionInfo]:
        try:
            if date:
                return self._get_edition_by_date(date)
            else:
                return self._get_latest_edition()
        except Exception as e:
            logger.error(f"获取解放军报版面信息失败: {e}")
            return None

    def _get_latest_edition(self) -> Optional[EditionInfo]:
        for i in range(self.MAX_LOOKBACK_DAYS):
            day = datetime.now() - timedelta(days=i)
            edition = self._get_edition_by_date(day.strftime('%Y-%m-%d'))
            if edition:
                return edition
        return None

    def _get_edition_by_date(self, date: str) -> Optional[EditionInfo]:
        date_str = date.replace('-', '')
        day = datetime.strptime(date_str, '%Y%m%d')
        url = (f"{self.BASE_URL}/_szb/{self.PAPER_CODE}/"
               f"{day.year}/{day.month:02d}/{day.day:02d}/index.json")

        try:
            resp = self._session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"解放军报 {date} 数字报数据获取失败: {e}")
            return None

        pages = []
        for item in data.get('paperInfo') or []:
            pdf_url = item.get('paperPDF')
            if not pdf_url:
                continue
            try:
                page_no = int(item.get('paperNumber'))
            except (TypeError, ValueError):
                page_no = len(pages) + 1
            pages.append((page_no, pdf_url))

        if not pages:
            return None

        pages.sort(key=lambda x: x[0])
        page_urls = [p[1] for p in pages]

        return EditionInfo(
            url=page_urls[0] if len(page_urls) == 1 else "",
            filename=f"解放军报_{date_str}.pdf",
            date=date,
            page_urls=page_urls
        )
