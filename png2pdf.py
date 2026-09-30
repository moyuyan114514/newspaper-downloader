# -*- coding: UTF-8 -*-
"""
png2pdf - 把已保存的报纸图片（PNG/JPG）合并转换为 PDF

用法:
    python png2pdf.py 报纸图片文件夹
    python png2pdf.py 第1版.png 第2版.png 第3版.png -o 人民日报_20260930.pdf
    python png2pdf.py ./downloads/人民日报/2026-09-30 -o 人民日报_20260930.pdf

说明:
    - 文件夹模式: 收集文件夹内的 .png/.jpg/.jpeg（按文件名自然排序）合并为一个 PDF
    - 原始图片不会被修改或删除
"""
import argparse
import os
import re
import sys
import tempfile

from PIL import Image

try:
    from pypdf import PdfWriter
except ImportError:
    from PyPDF2 import PdfMerger as PdfWriter  # 旧版兜底


def natural_key(path):
    """按文件名自然排序: page_2.png 排在 page_10.png 之前"""
    name = os.path.basename(path)
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r'(\d+)', name)]


def collect_images(inputs):
    """把输入参数(文件夹或文件)展开为图片路径列表"""
    exts = {'.png', '.jpg', '.jpeg'}
    files = []
    for inp in inputs:
        if os.path.isdir(inp):
            for name in os.listdir(inp):
                p = os.path.join(inp, name)
                if os.path.isfile(p) and os.path.splitext(name)[1].lower() in exts:
                    files.append(p)
        elif os.path.isfile(inp):
            files.append(inp)
        else:
            print(f"[警告] 跳过不存在的路径: {inp}")
    return sorted(files, key=natural_key)


def convert(images, output_path):
    if not images:
        print("[错误] 没有找到任何图片文件")
        return False

    writer = PdfWriter()
    temp_pdfs = []
    try:
        for img_path in images:
            img = Image.open(img_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # 先写成临时 PDF，避免覆盖原始图片
            tmp = os.path.join(tempfile.mkdtemp(prefix='png2pdf_'),
                               os.path.basename(img_path) + '.pdf')
            img.save(tmp, 'PDF', resolution=100.0)
            temp_pdfs.append(tmp)
            writer.append(tmp)
            print(f"  已加入: {os.path.basename(img_path)}")

        writer.write(output_path)
        print(f"[完成] {output_path} ({os.path.getsize(output_path)} bytes, "
              f"{len(images)} 页)")
        return True
    except Exception as e:
        print(f"[错误] 转换失败: {e}")
        return False
    finally:
        try:
            writer.close()
        except Exception:
            pass
        for tmp in temp_pdfs:
            try:
                os.remove(tmp)
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(description="把 PNG/JPG 报纸图片合并为 PDF")
    parser.add_argument('inputs', nargs='+', help='图片文件夹或图片文件（可多个）')
    parser.add_argument('-o', '--output', help='输出 PDF 路径（默认与第一个输入同目录）')
    args = parser.parse_args()

    images = collect_images(args.inputs)
    if not images:
        sys.exit(1)

    if args.output:
        output = args.output
    elif os.path.isdir(args.inputs[0]):
        output = os.path.join(os.path.dirname(args.inputs[0].rstrip('/\\')) or '.',
                              os.path.basename(args.inputs[0].rstrip('/\\')) + '.pdf')
    else:
        root, _ = os.path.splitext(images[0])
        output = root + '.pdf'

    ok = convert(images, output)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
