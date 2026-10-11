# -*- coding: UTF-8 -*-
from .base import PlatformDownloaderBase, EditionInfo, DownloadProgress
from .rmrb import PeopleDailyDownloader
from .xuexishibao import StudyTimesDownloader
from .guangming import GuangmingRibaoDownloader
from .xinhua_daily import XinhuaDailyDownloader
from .zhonghuadushu import ZhonghuadushuDownloader
from .wenzhai import WenzhaiDownloader
from .fcyym import FengciyuyuDownloader
from .jiefangjun import JiefangjunDailyDownloader
from .zqb import ZhongguoQingnianbaoDownloader
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
    "FengciyuyuDownloader",
    "JiefangjunDailyDownloader",
    "ZhongguoQingnianbaoDownloader",
]

DOWNLOADER_REGISTRY = {
    "rmrb": PeopleDailyDownloader,
    "xuexishibao": StudyTimesDownloader,
    "guangming": GuangmingRibaoDownloader,
    "xinhua_daily": XinhuaDailyDownloader,
    "zhonghuadushu": ZhonghuadushuDownloader,
    "wenzhai": WenzhaiDownloader,
    "fcyym": FengciyuyuDownloader,
    "jiefangjun": JiefangjunDailyDownloader,
    "zqb": ZhongguoQingnianbaoDownloader,
}

def get_downloader(platform_id: str, config):
    downloader_class = DOWNLOADER_REGISTRY.get(platform_id)
    if downloader_class:
        return downloader_class(config)
    return None

def get_available_platforms():
    return list(DOWNLOADER_REGISTRY.keys())

def check_available_dates(platform_id: str, config, days: int = 7) -> List[str]:
    """检查报纸在指定天数内哪些日期有更新（轻量探测，仅查各日期第一版）

    Args:
        platform_id: 报纸平台ID
        config: 配置对象
        days: 检查的天数

    Returns:
        有更新的日期列表 (格式: YYYY-MM-DD)
    """
    downloader = get_downloader(platform_id, config)
    if not downloader:
        return []

    available_dates = []

    for i in range(days):
        check_date = datetime.now() - timedelta(days=i)
        date_str = check_date.strftime('%Y-%m-%d')

        try:
            if downloader.has_edition(date_str):
                available_dates.append(date_str)
        except Exception:
            pass

    return available_dates
