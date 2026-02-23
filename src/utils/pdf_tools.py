# -*- coding: UTF-8 -*-
"""
PDF 合并工具
"""
import os
from typing import List, Tuple
from PIL import Image

try:
    from pypdf import PdfWriter
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False
    from PyPDF2 import PdfMerger as _PdfMergerLegacy
    class PdfWriter:
        def __init__(self):
            self._merger = _PdfMergerLegacy()
        def append(self, pdf_path):
            self._merger.append(pdf_path)
        def write(self, output_path):
            self._merger.write(output_path)
        def close(self):
            self._merger.close()


def merge_pdfs(pdf_files: List[str], output_path: str) -> bool:
    if not pdf_files:
        return False
    
    merger = PdfWriter()
    try:
        for pdf_file in pdf_files:
            if pdf_file and pdf_file.strip():
                merger.append(pdf_file)
        merger.write(output_path)
        merger.close()
        return True
    except Exception as e:
        try:
            merger.close()
        except:
            pass
        raise e


def merge_pdfs_sorted(pdf_files: List[Tuple[int, str]], output_path: str) -> bool:
    sorted_files = sorted(pdf_files, key=lambda x: x[0])
    file_paths = [f[1] for f in sorted_files]
    return merge_pdfs(file_paths, output_path)


def merge_images_to_pdf(image_files: List[Tuple[int, str]], output_path: str) -> bool:
    """将JPG图片合并为PDF
    
    Args:
        image_files: 图片文件列表 [(页码, 文件路径), ...]
        output_path: 输出PDF路径
        
    Returns:
        bool: 是否成功
    """
    if not image_files:
        return False
    
    sorted_files = sorted(image_files, key=lambda x: x[0])
    
    merger = PdfWriter()
    temp_pdfs = []
    
    try:
        for page_num, img_path in sorted_files:
            if not img_path or not os.path.exists(img_path):
                continue
            
            img = Image.open(img_path)
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            pdf_path = img_path.replace('.jpg', '.pdf').replace('.jpeg', '.pdf')
            img.save(pdf_path, 'PDF', resolution=100.0)
            temp_pdfs.append(pdf_path)
        
        if not temp_pdfs:
            return False
        
        for pdf_path in temp_pdfs:
            merger.append(pdf_path)
        
        merger.write(output_path)
        merger.close()
        
        for pdf_path in temp_pdfs:
            try:
                os.remove(pdf_path)
            except:
                pass
        
        return True
    except Exception as e:
        try:
            merger.close()
        except:
            pass
        for pdf_path in temp_pdfs:
            try:
                os.remove(pdf_path)
            except:
                pass
        raise e
