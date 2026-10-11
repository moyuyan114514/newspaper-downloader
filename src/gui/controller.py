# -*- coding: UTF-8 -*-
"""
下载控制器 - 使用 Qt 信号进行线程安全通信
"""
import os
from typing import Optional, List
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, Signal, QThread

from ..config import config
from ..downloaders import get_downloader, EditionInfo, DownloadProgress
from ..utils import StorageManager, logger, merge_pdfs_sorted, merge_images_to_pdf


class DownloadWorker(QObject):
    # (当前值, 最大值, 状态文本)——值为千分比进度，避免依赖 content-length
    progress_signal = Signal(int, int, str)
    log_signal = Signal(str)
    complete_signal = Signal(bool, str)
    
    def __init__(self, platform_id: str, date: Optional[str], output_dir: str):
        super().__init__()
        self.platform_id = platform_id
        self.date = date
        self.output_dir = output_dir
        self._cancel_requested = False
        self.storage = StorageManager(config.default_output_dir)
    
    def run(self):
        try:
            success, message = self._do_download()
            self.complete_signal.emit(success, message)
        except Exception as e:
            self.complete_signal.emit(False, str(e))
    
    def cancel(self):
        self._cancel_requested = True
    
    def _do_download(self) -> tuple:
        if self.output_dir:
            self.storage = StorageManager(self.output_dir)
        
        downloader = get_downloader(self.platform_id, config)
        if not downloader:
            self._log("ERROR", f"未知的平台: {self.platform_id}")
            return False, f"未知的平台: {self.platform_id}"
        
        newspaper_info = config.get_newspaper(self.platform_id)
        newspaper_name = newspaper_info.get("name", self.platform_id) if newspaper_info else self.platform_id
        
        self._log("INFO", f"开始获取 {newspaper_name} 的报纸信息...")
        
        edition = downloader.get_latest_edition(self.date)
        if not edition:
            self._log("ERROR", "未找到报纸信息")
            return False, "未找到报纸信息"
        
        self._log("INFO", f"找到 {len(edition.page_urls)} 个版面")
        
        if self._cancel_requested:
            return False, "已取消"
        
        output_path = self.storage.build_output_path(newspaper_name, edition.date)
        
        if os.path.exists(output_path):
            self._log("INFO", f"文件已存在，跳过: {output_path}")
            return True, output_path
        
        temp_dir = self.storage.get_temp_dir(newspaper_name, edition.date)
        downloaded_files = []
        total_pages = len(edition.page_urls)
        first_url = edition.page_urls[0] if edition.page_urls else ""
        is_jpg = first_url.lower().endswith(('.jpg', '.jpeg'))

        def make_page_callback(page_index: int):
            """按整期进度上报：第 i/N 版内部再按已下载字节细分"""
            def callback(progress: DownloadProgress):
                if self._cancel_requested:
                    return
                frac = (page_index - 1) / total_pages
                if progress.total > 0:
                    frac += (progress.current / progress.total) / total_pages
                size_mb = progress.current / 1048576
                text = f"下载第 {page_index}/{total_pages} 版: {progress.filename} ({size_mb:.1f}MB)"
                self.progress_signal.emit(int(frac * 1000), 1000, text)
            return callback

        for i, page_url in enumerate(edition.page_urls, 1):
            if self._cancel_requested:
                break

            self._log("INFO", f"下载第 {i}/{len(edition.page_urls)} 版...")
            downloader.set_progress_callback(make_page_callback(i))

            if is_jpg:
                temp_file = os.path.join(temp_dir, f"page_{i:02d}.jpg")
            else:
                temp_file = os.path.join(temp_dir, f"page_{i:02d}.pdf")

            if downloader.download_file(page_url, temp_file):
                downloaded_files.append((i, temp_file))
                self._log("INFO", f"第 {i} 版下载成功")
            else:
                self._log("WARNING", f"第 {i} 版下载失败")

        if not self._cancel_requested and downloaded_files:
            self.progress_signal.emit(1000, 1000, "下载完成，正在合并...")
        
        if self._cancel_requested:
            self.storage.cleanup_temp_dir(newspaper_name, edition.date)
            return False, "已取消"
        
        if not downloaded_files:
            file_type = "JPG" if is_jpg else "PDF"
            self._log("ERROR", f"没有下载到任何{file_type}文件")
            return False, f"没有下载到任何{file_type}文件"
        
        self._log("INFO", f"正在合并 {len(downloaded_files)} 个版面...")
        
        try:
            if is_jpg:
                merge_images_to_pdf(downloaded_files, output_path)
            else:
                merge_pdfs_sorted(downloaded_files, output_path)
            self._log("INFO", f"合并完成: {output_path}")
        except Exception as e:
            self._log("ERROR", f"合并失败: {e}")
            return False, f"合并失败: {e}"
        
        self.storage.cleanup_temp_dir(newspaper_name, edition.date)
        
        file_size = self.storage.get_file_size(output_path)
        size_str = self.storage.format_size(file_size)
        self._log("INFO", f"下载完成! 文件大小: {size_str}")
        
        return True, output_path
    
    def _log(self, level: str, message: str):
        self.log_signal.emit(f"[{level}] {message}")


class BatchDownloadWorker(QObject):
    # (当前值, 最大值, 状态文本)——值为跨全部日期的千分比整体进度
    progress_signal = Signal(int, int, str)
    log_signal = Signal(str)
    # (成功期数, 无版面期数, 失败期数)
    complete_signal = Signal(int, int, int)
    date_progress_signal = Signal(int, int, str)
    
    def __init__(self, platform_id: str, dates: List[str], output_dir: str):
        super().__init__()
        self.platform_id = platform_id
        self.dates = dates
        self.output_dir = output_dir
        self._cancel_requested = False
        self.storage = StorageManager(config.default_output_dir)
    
    def run(self):
        success_count = 0
        skip_count = 0
        fail_count = 0

        try:
            if self.output_dir:
                self.storage = StorageManager(self.output_dir)

            downloader = get_downloader(self.platform_id, config)
            if not downloader:
                self._log("ERROR", f"未知的平台: {self.platform_id}")
                self.complete_signal.emit(0, 0, len(self.dates))
                return

            newspaper_info = config.get_newspaper(self.platform_id)
            newspaper_name = newspaper_info.get("name", self.platform_id) if newspaper_info else self.platform_id

            total = len(self.dates)
            self._log("INFO", f"开始批量下载 {newspaper_name}，共 {total} 期")

            for idx, date in enumerate(self.dates, 1):
                if self._cancel_requested:
                    self._log("INFO", "已取消下载")
                    break

                self.date_progress_signal.emit(idx, total, date)
                self._log("INFO", f"[{idx}/{total}] 正在下载 {date}...")

                try:
                    status = self._download_single(downloader, newspaper_name, date, idx, total)
                    if status == "ok":
                        success_count += 1
                    elif status == "skip":
                        skip_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    self._log("WARNING", f"下载 {date} 失败: {str(e)[:50]}")
                    fail_count += 1

            self._log("INFO", f"批量下载完成: 成功 {success_count}，无版面 {skip_count}，失败 {fail_count}")

        except Exception as e:
            self._log("ERROR", f"批量下载出错: {str(e)[:50]}")

        self.complete_signal.emit(success_count, skip_count, fail_count)

    def _download_single(self, downloader, newspaper_name: str, date: str,
                         date_index: int = 1, total_dates: int = 1) -> str:
        """返回 'ok' / 'skip'(无版面或已存在) / 'fail'"""
        def snap(text):
            self.progress_signal.emit(int(date_index / total_dates * 1000), 1000,
                                      f"[{date_index}/{total_dates}] {text}")

        edition = downloader.get_latest_edition(date)
        if not edition:
            self._log("WARNING", f"未找到 {date} 的报纸")
            snap(f"{date} · 无版面")
            return "skip"

        if not edition.page_urls:
            self._log("WARNING", f"{date} 无版面信息")
            snap(f"{date} · 无版面")
            return "skip"

        output_path = self.storage.build_output_path(newspaper_name, edition.date)

        if os.path.exists(output_path):
            self._log("INFO", f"文件已存在，跳过: {output_path}")
            snap(f"{date} · 已存在，跳过")
            return "skip"

        temp_dir = self.storage.get_temp_dir(newspaper_name, edition.date)
        downloaded_files = []
        total_pages = len(edition.page_urls)
        first_url = edition.page_urls[0] if edition.page_urls else ""
        is_jpg = first_url.lower().endswith(('.jpg', '.jpeg'))

        def make_page_callback(page_index: int):
            """按"全部日期 × 全部版面"的整体进度上报"""
            def callback(progress: DownloadProgress):
                if self._cancel_requested:
                    return
                frac = date_index - 1 + ((page_index - 1) / total_pages)
                if progress.total > 0:
                    frac += (progress.current / progress.total) / total_pages / total_dates
                size_mb = progress.current / 1048576
                text = (f"[{date_index}/{total_dates}] {date} · "
                        f"第 {page_index}/{total_pages} 版 ({size_mb:.1f}MB)")
                self.progress_signal.emit(min(int(frac / total_dates * 1000), 1000), 1000, text)
            return callback

        for i, page_url in enumerate(edition.page_urls, 1):
            if self._cancel_requested:
                break

            downloader.set_progress_callback(make_page_callback(i))

            if is_jpg:
                temp_file = os.path.join(temp_dir, f"page_{i:02d}.jpg")
            else:
                temp_file = os.path.join(temp_dir, f"page_{i:02d}.pdf")

            if downloader.download_file(page_url, temp_file):
                downloaded_files.append((i, temp_file))
                self._log("INFO", f"第 {i} 版下载成功")

        if self._cancel_requested:
            self.storage.cleanup_temp_dir(newspaper_name, edition.date)
            return "fail"

        if not downloaded_files:
            self._log("WARNING", f"没有下载到任何文件")
            self.storage.cleanup_temp_dir(newspaper_name, edition.date)
            return "fail"

        self._log("INFO", f"正在合并 {len(downloaded_files)} 个版面...")
        self.progress_signal.emit(int(date_index / total_dates * 1000), 1000,
                                  f"[{date_index}/{total_dates}] {date} · 正在合并...")

        try:
            if is_jpg:
                merge_images_to_pdf(downloaded_files, output_path)
            else:
                merge_pdfs_sorted(downloaded_files, output_path)
            self._log("INFO", f"合并完成: {output_path}")
        except Exception as e:
            self._log("ERROR", f"合并失败: {e}")
            self.storage.cleanup_temp_dir(newspaper_name, edition.date)
            return "fail"

        self.storage.cleanup_temp_dir(newspaper_name, edition.date)
        return "ok"
    
    def cancel(self):
        self._cancel_requested = True
    
    def _log(self, level: str, message: str):
        self.log_signal.emit(f"[{level}] {message}")


class LatestFindWorker(BatchDownloadWorker):
    """「最新一期」Worker：从今天起逐日轻量探测，找到最近有版面的日期后下载该期。

    继承 BatchDownloadWorker 以复用其 _download_single 下载通道与信号定义；
    仅覆写 run()：先做 has_edition 探测（忙碌进度 maximum=0），探到日期后
    把 dates 收敛为单期再走父类批量流程（单期）。
    """

    # 往前探测边界：半年内必有一期（各报纸官网历史数据保留范围），探到即停
    MAX_PROBE_DAYS = 180

    def __init__(self, platform_id: str, output_dir: str,
                 max_days: int = MAX_PROBE_DAYS):
        super().__init__(platform_id, [], output_dir)
        self.max_days = max_days

    def run(self):
        try:
            if self.output_dir:
                self.storage = StorageManager(self.output_dir)

            downloader = get_downloader(self.platform_id, config)
            if not downloader:
                self._log("ERROR", f"未知的平台: {self.platform_id}")
                self.complete_signal.emit(0, 0, 1)
                return

            newspaper_info = config.get_newspaper(self.platform_id)
            newspaper_name = newspaper_info.get("name", self.platform_id) if newspaper_info else self.platform_id

            self._log("INFO", f"开始查找 {newspaper_name} 的最新一期（最多往前 {self.max_days} 天）...")

            # 探测阶段：从今天起逐日 has_edition（轻量，仅查第一版）。
            # 回看窗口较大（半年），改用确定性进度：已探测天数 / 总天数
            found_date = None
            for i in range(self.max_days):
                if self._cancel_requested:
                    self._log("INFO", "已取消查找")
                    self.complete_signal.emit(0, 0, 0)
                    return

                check_date = datetime.now() - timedelta(days=i)
                date_str = check_date.strftime('%Y-%m-%d')
                self.progress_signal.emit(i, self.max_days, f"正在探测 {date_str} 是否有报…（{i + 1}/{self.max_days}）")
                self._log("INFO", f"正在探测 {date_str} 是否有报…（{i + 1}/{self.max_days}）")

                try:
                    has = downloader.has_edition(date_str)
                except Exception as e:
                    # 单日探测失败不中断整体流程，与 check_available_dates 的处理一致
                    self._log("WARNING", f"探测 {date_str} 出错: {str(e)[:50]}")
                    has = False

                if has:
                    found_date = date_str
                    break
                self._log("INFO", f"{date_str} 无版面，继续往前尝试")

            if not found_date:
                self._log("WARNING", f"最近 {self.max_days} 天内未找到任何版面")
                self.complete_signal.emit(0, 0, 0)
                return

            self._log("INFO", f"找到最近一期: {found_date}，开始下载")

            # 「最新一期」语义：该期文件已存在则直接提示结束，不继续往前找更早的
            output_path = self.storage.build_output_path(newspaper_name, found_date)
            if os.path.exists(output_path):
                self._log("INFO", f"最新一期已存在，跳过下载: {output_path}")
                self.progress_signal.emit(1000, 1000, "最新一期已存在")
                self.complete_signal.emit(1, 0, 0)
                return

            # 收敛为单期日期列表，复用父类批量下载通道（含跳过/合并/清理逻辑）
            self.dates = [found_date]
            super().run()

        except Exception as e:
            self._log("ERROR", f"最新一期下载出错: {str(e)[:50]}")
            self.complete_signal.emit(0, 0, 1)


class DownloadController(QObject):
    def __init__(self):
        super().__init__()
        self._worker = None
        self._thread = None
    
    def get_available_newspapers(self) -> dict:
        return config.get_enabled_newspapers()
    
    def start_download(
        self,
        platform_id: str,
        date: Optional[str],
        output_dir: str,
        on_progress=None,
        on_log=None,
        on_complete=None
    ):
        if self._thread and self._thread.isRunning():
            return
        
        self._worker = DownloadWorker(platform_id, date, output_dir)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        
        if on_progress:
            self._worker.progress_signal.connect(on_progress)
        if on_log:
            self._worker.log_signal.connect(on_log)
        if on_complete:
            self._worker.complete_signal.connect(on_complete)
        
        self._worker.complete_signal.connect(self._on_complete)
        self._thread.started.connect(self._worker.run)
        self._thread.start()
    
    def start_batch_download(
        self,
        platform_id: str,
        dates: List[str],
        output_dir: str,
        on_progress=None,
        on_log=None,
        on_complete=None,
        on_date_progress=None
    ):
        if self._thread and self._thread.isRunning():
            return
        
        self._worker = BatchDownloadWorker(platform_id, dates, output_dir)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        
        if on_progress:
            self._worker.progress_signal.connect(on_progress)
        if on_log:
            self._worker.log_signal.connect(on_log)
        if on_complete:
            self._worker.complete_signal.connect(on_complete)
        if on_date_progress:
            self._worker.date_progress_signal.connect(on_date_progress)
        
        self._worker.complete_signal.connect(self._on_batch_complete)
        self._thread.started.connect(self._worker.run)
        self._thread.start()
    
    def start_latest_download(
        self,
        platform_id: str,
        output_dir: str,
        on_progress=None,
        on_log=None,
        on_complete=None
    ):
        """启动「最新一期」下载：先逐日探测再下载（线程模型与其它模式一致）"""
        if self._thread and self._thread.isRunning():
            return

        self._worker = LatestFindWorker(platform_id, output_dir)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        if on_progress:
            self._worker.progress_signal.connect(on_progress)
        if on_log:
            self._worker.log_signal.connect(on_log)
        if on_complete:
            self._worker.complete_signal.connect(on_complete)

        self._worker.complete_signal.connect(self._on_batch_complete)
        self._thread.started.connect(self._worker.run)
        self._thread.start()

    def _on_complete(self, success: bool, message: str):
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None
    
    def _on_batch_complete(self, success_count: int, fail_count: int):
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None
    
    def cancel(self):
        if self._worker:
            self._worker.cancel()
    
    def is_downloading(self) -> bool:
        return self._thread is not None and self._thread.isRunning()
    
    def get_dates_for_range(self, platform_id: str, days: int) -> List[str]:
        dates = []
        today = datetime.now()
        
        if platform_id == "xuexishibao":
            update_days = [0, 2, 4]
            for i in range(days):
                check_date = today - timedelta(days=i)
                if check_date.weekday() in update_days:
                    dates.append(check_date.strftime('%Y-%m-%d'))
        else:
            for i in range(days):
                check_date = today - timedelta(days=i)
                dates.append(check_date.strftime('%Y-%m-%d'))
        
        return dates
