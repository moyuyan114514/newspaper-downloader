# -*- coding: UTF-8 -*-
"""
存储管理器
"""
import os
import shutil
from typing import Optional

class StorageManager:
    def __init__(self, base_path: str):
        self.base_path = os.path.abspath(base_path)
    
    def ensure_output_dir(self, newspaper: str, date: str) -> str:
        date_str = date.replace('-', '')
        output_dir = os.path.join(self.base_path, newspaper, date_str)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def build_output_path(self, newspaper: str, date: str) -> str:
        output_dir = self.ensure_output_dir(newspaper, date)
        date_str = date.replace('-', '')
        filename = f"{newspaper}_{date_str}.pdf"
        return os.path.join(output_dir, filename)
    
    def get_temp_dir(self, newspaper: str, date: str) -> str:
        output_dir = self.ensure_output_dir(newspaper, date)
        temp_dir = os.path.join(output_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    def cleanup_temp_dir(self, newspaper: str, date: str):
        try:
            temp_dir = os.path.join(self.base_path, newspaper, date.replace('-', ''), 'temp')
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            pass
    
    def file_exists(self, newspaper: str, date: str) -> bool:
        output_path = self.build_output_path(newspaper, date)
        return os.path.exists(output_path)
    
    def get_file_size(self, filepath: str) -> int:
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0
    
    def format_size(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"
