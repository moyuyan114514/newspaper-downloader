# -*- coding: UTF-8 -*-
"""
主窗口界面
"""
import sys
import os
import json
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QDateEdit, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QGroupBox, QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt, QDate, Signal, Slot, QSettings, QTimer
from PySide6.QtGui import QFont, QIcon, QTextCharFormat, QColor

from ..config import config
from ..downloaders import check_available_dates
from .controller import DownloadController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("NewspaperDownloader", "Settings")
        self.controller = DownloadController()
        self._init_ui()
        self._load_settings()
        self._connect_signals()
    
    def _init_ui(self):
        self.setWindowTitle(f"{config.app_name} v{config.version}")
        self.setMinimumSize(700, 600)
        self.resize(750, 650)
        
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        config_group = QGroupBox("下载设置")
        config_layout = QVBoxLayout(config_group)
        
        newspaper_layout = QHBoxLayout()
        newspaper_label = QLabel("选择报纸:")
        newspaper_label.setFixedWidth(80)
        self.newspaper_combo = QComboBox()
        self._populate_newspapers()
        newspaper_layout.addWidget(newspaper_label)
        newspaper_layout.addWidget(self.newspaper_combo)
        config_layout.addLayout(newspaper_layout)
        
        date_layout = QHBoxLayout()
        date_label = QLabel("选择日期:")
        date_label.setFixedWidth(80)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        
        self.refresh_date_btn = QPushButton("刷新日期")
        self.refresh_date_btn.setFixedWidth(80)
        self.refresh_date_btn.clicked.connect(self._on_refresh_dates)
        
        self.refresh_days_spin = QSpinBox()
        self.refresh_days_spin.setRange(1, 60)
        self.refresh_days_spin.setValue(7)
        self.refresh_days_spin.setPrefix("近")
        self.refresh_days_spin.setSuffix("天")
        self.refresh_days_spin.setFixedWidth(80)
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        date_layout.addWidget(self.refresh_date_btn)
        date_layout.addWidget(self.refresh_days_spin)
        
        date_layout.addStretch()
        config_layout.addLayout(date_layout)
        
        output_layout = QHBoxLayout()
        output_label = QLabel("保存目录:")
        output_label.setFixedWidth(80)
        self.output_edit = QTextEdit()
        self.output_edit.setFixedHeight(30)
        self.output_edit.setPlaceholderText("选择保存目录...")
        self.output_edit.setText(config.default_output_dir)
        self.output_edit.setReadOnly(True)
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setFixedWidth(80)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.browse_btn)
        config_layout.addLayout(output_layout)
        
        layout.addWidget(config_group)
        
        batch_group = QGroupBox("批量下载")
        batch_layout = QHBoxLayout(batch_group)
        
        self.btn_latest = QPushButton("最新一期")
        self.btn_latest.setMinimumHeight(35)
        self.btn_latest.clicked.connect(lambda: self._on_batch_download(1))
        
        self.btn_week = QPushButton("最近一周")
        self.btn_week.setMinimumHeight(35)
        self.btn_week.clicked.connect(lambda: self._on_batch_download(7))
        
        self.btn_month = QPushButton("最近一月")
        self.btn_month.setMinimumHeight(35)
        self.btn_month.clicked.connect(lambda: self._on_batch_download(30))
        
        self.btn_half_year = QPushButton("最近半年")
        self.btn_half_year.setMinimumHeight(35)
        self.btn_half_year.clicked.connect(lambda: self._on_batch_download(180))
        
        batch_layout.addWidget(self.btn_latest)
        batch_layout.addWidget(self.btn_week)
        batch_layout.addWidget(self.btn_month)
        batch_layout.addWidget(self.btn_half_year)
        
        layout.addWidget(batch_group)
        
        progress_group = QGroupBox("下载进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v / %m KB")
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("就绪")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setFixedWidth(100)
        self.download_btn.setMinimumHeight(35)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedWidth(70)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setMinimumHeight(35)
        
        self.open_folder_btn = QPushButton("打开目录")
        self.open_folder_btn.setFixedWidth(80)
        self.open_folder_btn.setMinimumHeight(35)
        
        btn_layout.addWidget(self.download_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.open_folder_btn)
        
        layout.addLayout(btn_layout)
    
    def _populate_newspapers(self):
        newspapers = self.controller.get_available_newspapers()
        for paper_id, paper_info in newspapers.items():
            name = paper_info.get("name", paper_id)
            self.newspaper_combo.addItem(name, paper_id)
    
    def _load_settings(self):
        output_dir = self.settings.value("output_dir", config.default_output_dir)
        self.output_edit.setText(output_dir)
        
        newspaper_index = self.settings.value("newspaper_index", 0, type=int)
        if newspaper_index < self.newspaper_combo.count():
            self.newspaper_combo.setCurrentIndex(newspaper_index)
        
        window_geometry = self.settings.value("geometry")
        if window_geometry:
            self.restoreGeometry(window_geometry)
    
    def _save_settings(self):
        self.settings.setValue("output_dir", self.output_edit.toPlainText())
        self.settings.setValue("newspaper_index", self.newspaper_combo.currentIndex())
        self.settings.setValue("geometry", self.saveGeometry())
    
    def _connect_signals(self):
        self.download_btn.clicked.connect(self._on_download)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.open_folder_btn.clicked.connect(self._on_open_folder)
        self.browse_btn.clicked.connect(self._on_browse)
        self.newspaper_combo.currentIndexChanged.connect(self._on_newspaper_changed)
        self.date_edit.dateChanged.connect(self._on_date_changed)
        self.refresh_date_btn.clicked.connect(self._on_refresh_dates)
    
    def _on_newspaper_changed(self, index):
        self._load_cached_dates()
    
    def _on_date_changed(self, date):
        pass
    
    def _load_cached_dates(self):
        platform_id = self.newspaper_combo.currentData()
        if not platform_id:
            return
        
        cached_dates = config.get_cached_dates(platform_id)
        if cached_dates:
            self._update_date_calendar(cached_dates)
            self._log(f"已加载缓存: {len(cached_dates)} 个更新日期")
    
    def _on_refresh_dates(self):
        platform_id = self.newspaper_combo.currentData()
        if not platform_id:
            return
        
        self.refresh_date_btn.setEnabled(False)
        self.refresh_date_btn.setText("刷新中...")
        self._log("正在刷新更新日期...")
        
        QTimer.singleShot(100, lambda: self._do_refresh_dates(platform_id))
    
    def _do_refresh_dates(self, platform_id: str):
        try:
            days = self.refresh_days_spin.value()
            available_dates = check_available_dates(platform_id, config, days=days)
            config.set_cached_dates(platform_id, available_dates)
            self._update_date_calendar(available_dates)
            
            if available_dates:
                self._log(f"检测到 {len(available_dates)} 个更新日期 (近{days}天)")
            else:
                self._log(f"未检测到更新日期 (近{days}天)")
        except Exception as e:
            self._log(f"刷新失败: {e}")
        finally:
            self.refresh_date_btn.setEnabled(True)
            self.refresh_date_btn.setText("刷新日期")
    
    def _check_available_dates(self):
        platform_id = self.newspaper_combo.currentData()
        if not platform_id:
            return
        
        try:
            available_dates = check_available_dates(platform_id, config, days=7)
            config.set_cached_dates(platform_id, available_dates)
            self._update_date_calendar(available_dates)
        except Exception:
            pass
    
    def _update_date_calendar(self, available_dates: list):
        calendar = self.date_edit.calendarWidget()
        if not calendar:
            return
        
        default_format = QTextCharFormat()
        red_format = QTextCharFormat()
        red_format.setBackground(QColor(255, 200, 200))
        
        available_set = set()
        for date_str in available_dates:
            parts = date_str.split('-')
            if len(parts) == 3:
                available_set.add((int(parts[0]), int(parts[1]), int(parts[2])))
        
        today = QDate.currentDate()
        for day in range(1, 32):
            test_date = QDate(today.year(), today.month(), day)
            if not test_date.isValid():
                break
            if (test_date.year(), test_date.month(), test_date.day()) in available_set:
                calendar.setDateTextFormat(test_date, red_format)
            else:
                calendar.setDateTextFormat(test_date, default_format)
    
    def closeEvent(self, event):
        self._save_settings()
        event.accept()
    
    def _on_browse(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if dir_path:
            self.output_edit.setText(dir_path)
            self._save_settings()
    
    def _on_open_folder(self):
        output_dir = self.output_edit.toPlainText().strip()
        if output_dir and os.path.exists(output_dir):
            os.startfile(output_dir)
    
    def _set_downloading_state(self, downloading: bool):
        self.download_btn.setEnabled(not downloading)
        self.cancel_btn.setEnabled(downloading)
        self.newspaper_combo.setEnabled(not downloading)
        self.date_edit.setEnabled(not downloading)
        self.browse_btn.setEnabled(not downloading)
        self.btn_latest.setEnabled(not downloading)
        self.btn_week.setEnabled(not downloading)
        self.btn_month.setEnabled(not downloading)
        self.btn_half_year.setEnabled(not downloading)
        
        if downloading:
            self.download_btn.setText("下载中...")
        else:
            self.download_btn.setText("开始下载")
    
    def _on_download(self):
        platform_id = self.newspaper_combo.currentData()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        output_dir = self.output_edit.toPlainText().strip()
        
        if not output_dir:
            return
        
        self._save_settings()
        self._set_downloading_state(True)
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        self.controller.start_download(
            platform_id=platform_id,
            date=date,
            output_dir=output_dir,
            on_progress=self._on_progress,
            on_log=self._on_log,
            on_complete=self._on_complete
        )
    
    def _on_batch_download(self, days: int):
        platform_id = self.newspaper_combo.currentData()
        output_dir = self.output_edit.toPlainText().strip()
        
        if not output_dir:
            return
        
        self._save_settings()
        self._set_downloading_state(True)
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        dates = self.controller.get_dates_for_range(platform_id, days)
        
        self.controller.start_batch_download(
            platform_id=platform_id,
            dates=dates,
            output_dir=output_dir,
            on_progress=self._on_progress,
            on_log=self._on_log,
            on_complete=self._on_batch_complete,
            on_date_progress=self._on_date_progress
        )
    
    def _on_cancel(self):
        self.controller.cancel()
        self._log("正在取消...")
    
    @Slot(str, int, int)
    def _on_progress(self, filename: str, current: int, total: int):
        if total > 0:
            self.progress_bar.setMaximum(total // 1024)
            self.progress_bar.setValue(current // 1024)
            self.status_label.setText(f"下载中: {filename}")
    
    @Slot(int, int, str)
    def _on_date_progress(self, current: int, total: int, date: str):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"%p% - %v/%m 期")
        self.status_label.setText(f"正在下载 {date} ({current}/{total})")
    
    @Slot(str)
    def _on_log(self, message: str):
        self._log(message)
    
    @Slot(bool, str)
    def _on_complete(self, success: bool, message: str):
        self._set_downloading_state(False)
        
        if success:
            self.status_label.setText("下载完成!")
            self._log(f"完成: {message}")
        else:
            self.status_label.setText("下载失败")
            self._log(f"失败: {message}")
    
    @Slot(int, int)
    def _on_batch_complete(self, success_count: int, fail_count: int):
        self._set_downloading_state(False)
        self.status_label.setText(f"批量下载完成: 成功 {success_count}，失败 {fail_count}")
    
    def _log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
