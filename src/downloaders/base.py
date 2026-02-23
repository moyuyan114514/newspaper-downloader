# -*- coding: UTF-8 -*-
"""
下载器基类和数据结构
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional, List
import requests
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

@dataclass
class EditionInfo:
    url: str
    filename: str
    mime_type: str = "application/pdf"
    size_bytes: int = 0
    date: str = ""
    page_urls: List[str] = None
    
    def __post_init__(self):
        if self.page_urls is None:
            self.page_urls = []

@dataclass
class DownloadProgress:
    current: int
    total: int
    filename: str
    status: str = "downloading"

class PlatformDownloaderBase(ABC):
    def __init__(self, config):
        self.config = config
        self._progress_callback: Optional[Callable[[DownloadProgress], None]] = None
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
    
    @abstractmethod
    def get_latest_edition(self, date: str = None) -> Optional[EditionInfo]:
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        pass
    
    @abstractmethod
    def get_platform_id(self) -> str:
        pass
    
    def set_progress_callback(self, callback: Callable[[DownloadProgress], None]):
        self._progress_callback = callback
    
    def _report_progress(self, progress: DownloadProgress):
        if self._progress_callback:
            self._progress_callback(progress)
    
    def download_file(self, url: str, dest_path: str) -> bool:
        max_retries = self.config.max_retries
        timeout = self.config.timeout
        chunk_size = self.config.chunk_size
        
        for attempt in range(max_retries):
            try:
                response = self._session.get(url, timeout=timeout, stream=True)
                if response.status_code == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    filename = os.path.basename(dest_path)
                    
                    self._report_progress(DownloadProgress(
                        current=0,
                        total=total_size,
                        filename=filename,
                        status="starting"
                    ))
                    
                    downloaded = 0
                    with open(dest_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                self._report_progress(DownloadProgress(
                                    current=downloaded,
                                    total=total_size,
                                    filename=filename,
                                    status="downloading"
                                ))
                    
                    self._report_progress(DownloadProgress(
                        current=downloaded,
                        total=total_size,
                        filename=filename,
                        status="completed"
                    ))
                    return True
            except Exception as e:
                if attempt < max_retries - 1:
                    continue
        return False
    
    def close(self):
        self._session.close()
