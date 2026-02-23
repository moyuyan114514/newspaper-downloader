# -*- coding: UTF-8 -*-
"""
日志模块 - 只持久化错误和警告日志
"""
import json
import os
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

LOG_FILE = "error_log.json"

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class LogEntry:
    timestamp: str
    level: str
    message: str
    details: dict = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

class Logger:
    def __init__(self, name: str = "NewspaperDownloader"):
        self.name = name
        self._entries: list[LogEntry] = []
        self._callbacks: list[Callable[[LogEntry], None]] = []
        self._json_export_path: Optional[str] = None
    
    def add_callback(self, callback: Callable[[LogEntry], None]):
        self._callbacks.append(callback)
    
    def _log(self, level: LogLevel, message: str, details: dict = None):
        entry = LogEntry(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            level=level.value,
            message=message,
            details=details
        )
        self._entries.append(entry)
        
        for callback in self._callbacks:
            try:
                callback(entry)
            except Exception:
                pass
        
        if level in (LogLevel.ERROR, LogLevel.WARNING):
            self._persist_error_log(entry)
    
    def _persist_error_log(self, entry: LogEntry):
        try:
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), LOG_FILE)
            
            existing_logs = []
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        existing_logs = json.load(f)
                except:
                    pass
            
            existing_logs.append(asdict(entry))
            
            if len(existing_logs) > 1000:
                existing_logs = existing_logs[-1000:]
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(existing_logs, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def debug(self, message: str, details: dict = None):
        self._log(LogLevel.DEBUG, message, details)
    
    def info(self, message: str, details: dict = None):
        self._log(LogLevel.INFO, message, details)
    
    def warning(self, message: str, details: dict = None):
        self._log(LogLevel.WARNING, message, details)
    
    def error(self, message: str, details: dict = None):
        self._log(LogLevel.ERROR, message, details)
    
    def export_json(self, filepath: str = None) -> str:
        path = filepath or self._json_export_path
        if path is None:
            path = f"download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "app": self.name,
            "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "entries": [asdict(e) for e in self._entries]
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return path
    
    def get_entries(self) -> list[LogEntry]:
        return self._entries.copy()
    
    def clear(self):
        self._entries.clear()

logger = Logger()
