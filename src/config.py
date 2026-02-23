# -*- coding: UTF-8 -*-
"""
报纸下载器配置管理
"""
import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional, List

DEFAULT_CONFIG = {
    "app_name": "报纸下载器",
    "version": "0.5.1",
    "default_output_dir": "./downloads",
    "newspapers": {
        "rmrb": {
            "name": "人民日报",
            "enabled": True,
            "update_days": [0, 1, 2, 3, 4, 5, 6]
        },
        "xuexishibao": {
            "name": "学习时报",
            "enabled": True,
            "update_days": [0, 2, 4]
        },
        "guangming": {
            "name": "光明日报",
            "enabled": True,
            "update_days": [0, 1, 2, 3, 4, 5, 6]
        },
        "xinhua_daily": {
            "name": "新华每日电讯",
            "enabled": True,
            "update_days": [0, 1, 2, 3, 4, 5, 6]
        },
        "zhonghuadushu": {
            "name": "中华读书报",
            "enabled": True,
            "update_days": [0, 1, 2, 3, 4, 5, 6]
        },
        "wenzhai": {
            "name": "文摘报",
            "enabled": True,
            "update_days": [0, 1, 2, 3, 4, 5, 6]
        }
    },
    "download": {
        "max_retries": 3,
        "timeout": 60,
        "chunk_size": 8192
    },
    "ui": {
        "theme": "default",
        "language": "zh_CN"
    }
}

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = DEFAULT_CONFIG.copy()
            cls._instance._config_path = None
        return cls._instance
    
    def load(self, config_path: str) -> bool:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._merge_config(loaded)
                self._config_path = config_path
                return True
            except Exception:
                pass
        return False
    
    def save(self, config_path: str = None) -> bool:
        path = config_path or self._config_path
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, ensure_ascii=False, indent=4)
                return True
            except Exception:
                pass
        return False
    
    def _merge_config(self, loaded: dict):
        for key, value in loaded.items():
            if key in self._config and isinstance(self._config[key], dict) and isinstance(value, dict):
                self._config[key].update(value)
            else:
                self._config[key] = value
    
    @property
    def app_name(self) -> str:
        return self._config.get("app_name", "报纸下载器")
    
    @property
    def version(self) -> str:
        return self._config.get("version", "0.5.1")
    
    @property
    def default_output_dir(self) -> str:
        return self._config.get("default_output_dir", "./downloads")
    
    @default_output_dir.setter
    def default_output_dir(self, value: str):
        self._config["default_output_dir"] = value
    
    @property
    def newspapers(self) -> dict:
        return self._config.get("newspapers", {})
    
    @property
    def max_retries(self) -> int:
        return self._config.get("download", {}).get("max_retries", 3)
    
    @property
    def timeout(self) -> int:
        return self._config.get("download", {}).get("timeout", 60)
    
    @property
    def chunk_size(self) -> int:
        return self._config.get("download", {}).get("chunk_size", 8192)
    
    def get_newspaper(self, paper_id: str) -> Optional[dict]:
        return self.newspapers.get(paper_id)
    
    def get_enabled_newspapers(self) -> dict:
        return {k: v for k, v in self.newspapers.items() if v.get("enabled", True)}
    
    def get_cached_dates(self, platform_id: str) -> List[str]:
        cache = self._config.get("available_dates_cache", {})
        platform_cache = cache.get(platform_id, {})
        cached_dates = platform_cache.get("dates", [])
        cached_time = platform_cache.get("timestamp", 0)
        
        if cached_time and (time.time() - cached_time) < 86400:
            return cached_dates
        return []
    
    def set_cached_dates(self, platform_id: str, dates: List[str]):
        cache = self._config.get("available_dates_cache", {})
        cache[platform_id] = {
            "dates": dates,
            "timestamp": time.time()
        }
        self._config["available_dates_cache"] = cache

config = Config()
