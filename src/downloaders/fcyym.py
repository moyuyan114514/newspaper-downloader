# -*- coding: UTF-8 -*-
"""
讽刺与幽默下载器（人民日报社漫画周刊，周五出版）
官方网站: https://paper.people.com.cn/fcyym/pc/layout/index.html

与人民日报同一站点模板，仅路径段不同，直接复用 PeopleDailyDownloader
"""
from .rmrb import PeopleDailyDownloader


class FengciyuyuDownloader(PeopleDailyDownloader):
    PAPER_PATH = "fcyym"

    def get_platform_name(self) -> str:
        return "讽刺与幽默"

    def get_platform_id(self) -> str:
        return "fcyym"
