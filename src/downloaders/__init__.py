# -*- coding: UTF-8 -*-
from .base import PlatformDownloaderBase, EditionInfo, DownloadProgress
from .rmrb import PeopleDailyDownloader
from .xuexishibao import StudyTimesDownloader
from .guangming import GuangmingRibaoDownloader
from .xinhua_daily import XinhuaDailyDownloader
from .zhonghuadushu import ZhonghuadushuDownloader
from .wenzhai import WenzhaiDownloader
from datetime import datetime, timedelta
from typing import List

__all__ = [
    "PlatformDownloaderBase",
    "EditionInfo",
    "DownloadProgress",
    "PeopleDailyDownloader",
    "StudyTimesDownloader",
    "GuangmingRibaoDownloader",
    "XinhuaDailyDownloader",
    "ZhonghuadushuDownloader",
    "WenzhaiDownloader",
]

DOWNLOADER_REGISTRY = {
    "rmrb": PeopleDailyDownloader,
    "xuexishibao": StudyTimesDownloader,
    "guangming": GuangmingRibaoDownloader,
    "xinhua_daily": XinhuaDailyDownloader,
    "zhonghuadushu": ZhonghuadushuDownloader,
    "wenzhai": WenzhaiDownloader,
}

def get_downloader(platform_id: str, config):
    downloader_class = DOWNLOADER_REGISTRY.get(platform_id)
    if downloader_class:
        return downloader_class(config)
    return None

def get_available_platforms():
    return list(DOWNLOADER_REGISTRY.keys())

def check_available_dates(platform_id: str, config, days: int = 7) -> List[str]:
    downloader = get_downloader(platform_id, config)
    if not downloader:
        return []
    
    available_dates = []
    
    for i in range(days):
        check_date = datetime.now() - timedelta(days=i)
        date_str = check_date.strftime('%Y-%m-%d')
        
        try:
            edition = downloader.get_latest_edition(date_str)
            if edition and edition.page_urls and len(edition.page_urls) > 0:
                available_dates.append(date_str)
        except Exception:
            pass
    
    return available_dates
