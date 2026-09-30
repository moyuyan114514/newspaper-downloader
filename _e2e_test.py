# -*- coding: UTF-8 -*-
"""端到端管线测试：直接调用 GUI 背后的 DownloadWorker，验证从点击到出文件的全链路"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_e2e_out")

from src.config import config
config.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json'))

from src.gui.controller import DownloadWorker, BatchDownloadWorker, DownloadController

def run_case(name, worker):
    print(f"\n=== {name} ===")
    logs = []
    worker.log_signal.connect(lambda m: logs.append(m))
    try:
        success, message = worker._do_download()
        for m in logs:
            print(f"  {m}")
        print(f"  → success={success}, msg={message}")
        return success, message
    except Exception as e:
        print(f"  异常: {e}")
        import traceback; traceback.print_exc()
        return False, str(e)

# 1. 人民日报 指定历史日期 (PDF 路线)
w1 = DownloadWorker("rmrb", "2026-09-15", OUT)
ok1, msg1 = run_case("人民日报 2026-09-15（单日下载）", w1)

# 2. 同一天再下一次 → 应命中"文件已存在，跳过"
w2 = DownloadWorker("rmrb", "2026-09-15", OUT)
ok2, msg2 = run_case("人民日报 2026-09-15（重复下载→应跳过）", w2)

# 3. 新华每日电讯 历史日期 (JPG→合并PDF 路线)
w3 = DownloadWorker("xinhua_daily", "2026-09-15", OUT)
ok3, msg3 = run_case("新华每日电讯 2026-09-15（JPG合并路线）", w3)

# 4. 光明日报 最新一期 (date=None，验证 tuple 修复走完整管线)
w4 = DownloadWorker("guangming", None, OUT)
ok4, msg4 = run_case("光明日报 最新一期（date=None）", w4)

# 5. 批量下载：学习时报 近7天（应只挑出版日）
ctrl = DownloadController()
dates = ctrl.get_dates_for_range("xuexishibao", 7)
print(f"\n=== 学习时报 批量近7天 → 候选日期: {dates} ===")
w5 = BatchDownloadWorker("xuexishibao", dates, OUT)
logs5 = []
w5.log_signal.connect(lambda m: logs5.append(m))
w5.run()
for m in logs5:
    print(f"  {m}")

# 6. 产物校验
print("\n=== 产物校验 ===")
from pypdf import PdfReader
count = 0
for root, dirs, files in os.walk(OUT):
    for f in files:
        if f.endswith('.pdf'):
            p = os.path.join(root, f)
            try:
                pages = len(PdfReader(p).pages)
                size = os.path.getsize(p)
                head = open(p, 'rb').read(5)
                print(f"  ✅ {os.path.relpath(p, OUT)}: {pages}页, {size/1024/1024:.1f}MB, 头={head.decode('ascii', 'ignore')}")
                count += 1
            except Exception as e:
                print(f"  ❌ {p}: 损坏 {e}")
print(f"共 {count} 个有效PDF")

# temp 目录应已被清理
for root, dirs, files in os.walk(OUT):
    if 'temp' in dirs:
        print(f"  ⚠️ 残留 temp 目录: {root}")
