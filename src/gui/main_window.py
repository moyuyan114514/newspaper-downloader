# -*- coding: UTF-8 -*-
"""
主窗口界面（重设计版）

设计要点：
- 报纸选择：3x3 卡片芯片网格，替代原来的下拉框，每张卡片显示报名与出版频率
- 下载范围：分段控件（指定日期 / 最新一期 / 最近一周 / 最近一月 / 最近两月），
  统一由一个主按钮执行，替代原来四个各自触发的批量按钮
- 进度：大号渐变进度条 + 独立百分比 + 状态行
- 日志：深色控制台，INFO / WARNING / ERROR 分级着色
"""
import os
import html
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QDateEdit, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QSpinBox, QLineEdit, QFrame, QButtonGroup, QSizePolicy,
    QScrollArea
)
from PySide6.QtCore import (
    Qt, QDate, QRect, QSize, Slot, QSettings, QTimer, QPoint
)
from PySide6.QtGui import (
    QFont, QIcon, QTextCharFormat, QColor, QPainter, QPen, QPainterPath
)

from ..config import config
from ..downloaders import check_available_dates
from .controller import DownloadController

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# 下载范围模式：mode_id -> (显示名, 批量天数；None 表示按指定日期单期下载)
DOWNLOAD_MODES = [
    ("single", "指定日期", None),
    ("latest", "最新一期", 1),
    ("week", "最近一周", 7),
    ("month", "最近一月", 30),
    ("half_year", "最近两月", 62),
    # 日期区间模式：天数无意义（由用户选择的起止日期决定），走独立分支
    ("range", "日期区间", 0),
]

# 批量下载日期范围上限（约两个月），避免对报纸网站产生过大压力
MAX_BATCH_DAYS = 62
# 批量天数超过该值时，下载前输出大范围提示
LARGE_RANGE_THRESHOLD = 30
# 大范围批量下载提示文案
LARGE_RANGE_NOTICE = (
    "批量下载范围较大，会产生较频繁的网络请求，为避免对报纸网站造成压力，"
    "不建议大批量下载，已限制最多下载两个月。"
)


def format_frequency(update_days) -> str:
    """把 config 里的 weekday 列表（0=周一）转成人类可读的出版频率。"""
    days = sorted(update_days or [])
    if len(days) >= 7:
        return "每日出版"
    return " · ".join(WEEKDAY_NAMES[d] for d in days if 0 <= d <= 6)


CHIP_HEIGHT = 46


class PaperChip(QPushButton):
    """报纸选择卡片：单行布局——报名居左、出版频率居右、选中圆点贴右。"""

    def __init__(self, paper_id: str, name: str, frequency: str, parent=None):
        super().__init__(parent)
        self.paper_id = paper_id
        self._name = name
        self._frequency = frequency
        self._hover = False
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(CHIP_HEIGHT)
        self.setMaximumHeight(CHIP_HEIGHT)

    def sizeHint(self) -> QSize:
        return QSize(180, CHIP_HEIGHT)

    def minimumSizeHint(self) -> QSize:
        return QSize(120, CHIP_HEIGHT)

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        if not self.isEnabled():
            p.setOpacity(0.5)

        rect = self.rect().adjusted(1, 1, -2, -2)

        if self.isChecked():
            pen = QPen(QColor("#C62828"))
            pen.setWidthF(1.6)
            p.setPen(pen)
            p.setBrush(QColor("#FDF3F3"))
        elif self._hover:
            pen = QPen(QColor("#E8A6A6"))
            pen.setWidthF(1.2)
            p.setPen(pen)
            p.setBrush(QColor("#FFFBFB"))
        else:
            p.setPen(QPen(QColor("#E6E8EC"), 1))
            p.setBrush(QColor("#FFFFFF"))
        p.drawRoundedRect(rect, 9, 9)

        cy = rect.center().y()

        # 右侧选中圆点
        cx = rect.right() - 17
        radius = 8
        if self.isChecked():
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#C62828"))
            p.drawEllipse(QPoint(cx, cy), radius, radius)

            check = QPainterPath()
            check.moveTo(cx - 4.0, cy + 0.2)
            check.lineTo(cx - 1.0, cy + 3.0)
            check.lineTo(cx + 4.2, cy - 3.2)
            p.setPen(QPen(QColor("#FFFFFF"), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.setBrush(Qt.NoBrush)
            p.drawPath(check)
        else:
            p.setPen(QPen(QColor("#C9CCD4"), 1.4))
            p.setBrush(QColor("#FFFFFF"))
            p.drawEllipse(QPoint(cx, cy), radius, radius)

        left = 14

        # 报名（左）
        name_font = QFont(self.font())
        name_font.setWeight(QFont.Weight.DemiBold)
        name_font.setPointSize(10)
        p.setFont(name_font)
        p.setPen(QColor("#1F2329") if not self.isChecked() else QColor("#C62828"))
        name_right = left + int(rect.width() * 0.42)
        p.drawText(QRect(left, 0, name_right - left, rect.height()),
                   Qt.AlignLeft | Qt.AlignVCenter, self._name)

        # 出版频率（右，圆点左侧）
        freq_font = QFont(self.font())
        freq_font.setPointSize(8)
        p.setFont(freq_font)
        p.setPen(QColor("#86909C"))
        freq_left = name_right
        freq_right = cx - radius - 8
        p.drawText(QRect(freq_left, 0, max(freq_right - freq_left, 20), rect.height()),
                   Qt.AlignRight | Qt.AlignVCenter, self._frequency)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("NewspaperDownloader", "Settings")
        self.controller = DownloadController()
        self.paper_chips = []
        self.paper_group = QButtonGroup(self)
        self.paper_group.setExclusive(True)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_buttons = {}
        self._downloading = False
        self._init_ui()
        self._load_settings()
        self._connect_signals()

    # ------------------------------------------------------------------ UI

    def _init_ui(self):
        self.setWindowTitle(f"{config.app_name} v{config.version}")
        self.setMinimumSize(840, 560)
        self.resize(920, 920)

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central = QWidget()
        self.setCentralWidget(central)
        page = QVBoxLayout(central)
        page.setContentsMargins(0, 0, 0, 0)
        page.setSpacing(0)

        # 可滚动内容区：窗口高度不足（含 QSettings 恢复的旧尺寸）时整体滚动，
        # 卡片保持自然高度，不会被网格压扁而重叠
        scroll = QScrollArea()
        scroll.setObjectName("mainScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.viewport().setAutoFillBackground(False)

        container = QWidget()
        container.setObjectName("scrollContainer")
        root = QVBoxLayout(container)
        root.setContentsMargins(18, 14, 18, 10)
        root.setSpacing(9)

        root.addLayout(self._build_header())
        root.addWidget(self._build_paper_card())
        root.addWidget(self._build_params_card())
        root.addWidget(self._build_mode_card())
        root.addWidget(self._build_progress_card())
        root.addWidget(self._build_log_card(), 1)

        scroll.setWidget(container)
        page.addWidget(scroll, 1)

        # 底部操作栏固定不滚动，主按钮始终可见
        footer = QFrame()
        footer.setObjectName("footerBar")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(18, 8, 18, 10)
        footer_layout.addLayout(self._build_footer())
        page.addWidget(footer)

    def _build_header(self):
        bar = QHBoxLayout()
        bar.setSpacing(12)

        icon_label = QLabel()
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'icon.ico')
        if os.path.exists(icon_path):
            icon_label.setPixmap(QIcon(icon_path).pixmap(42, 42))
        icon_label.setFixedSize(42, 42)
        bar.addWidget(icon_label)

        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel(config.app_name)
        title.setObjectName("appTitle")
        subtitle = QLabel("9 份主流报纸电子报 · 版面自动合并为单个 PDF")
        subtitle.setObjectName("appSubtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        bar.addLayout(titles)

        bar.addStretch()

        version = QLabel(f"v{config.version}")
        version.setObjectName("versionTag")
        bar.addWidget(version, 0, Qt.AlignTop)
        return bar

    def _card(self, title_text: str, growing: bool = False):
        """生成一张白色卡片，返回 (card, body_layout)。

        growing=False 时卡片纵向尺寸固定为其期望高度，窗口空间不足时不会被
        压扁（避免内部网格/控件重叠）；日志卡用 growing=True 弹性伸缩。
        """
        card = QFrame()
        card.setObjectName("card")
        if growing:
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        else:
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        outer = QVBoxLayout(card)
        outer.setContentsMargins(16, 11, 16, 12)
        outer.setSpacing(8)
        title = QLabel(title_text)
        title.setObjectName("cardTitle")
        outer.addWidget(title)
        return card, outer

    def _build_paper_card(self):
        card, outer = self._card("选择报纸")
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        newspapers = self.controller.get_available_newspapers()
        for index, (paper_id, info) in enumerate(newspapers.items()):
            chip = PaperChip(
                paper_id,
                info.get("name", paper_id),
                format_frequency(info.get("update_days", []))
            )
            self.paper_chips.append(chip)
            self.paper_group.addButton(chip)
            row, col = divmod(index, 3)
            grid.addWidget(chip, row, col)
        if self.paper_chips:
            self.paper_chips[0].setChecked(True)
        for col in range(3):
            grid.setColumnStretch(col, 1)
        outer.addLayout(grid)
        return card

    def _build_params_card(self):
        card, outer = self._card("下载参数")

        # 日期行
        date_row = QHBoxLayout()
        date_row.setSpacing(10)
        date_label = QLabel("出版日期")
        date_label.setFixedWidth(64)
        date_row.addWidget(date_label)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setFixedWidth(150)
        date_row.addWidget(self.date_edit)

        self.today_btn = QPushButton("回到今天")
        self.today_btn.setObjectName("ghostBtn")
        self.today_btn.setFixedWidth(88)
        date_row.addWidget(self.today_btn)

        date_row.addStretch()

        self.refresh_days_spin = QSpinBox()
        self.refresh_days_spin.setRange(1, 60)
        self.refresh_days_spin.setValue(7)
        self.refresh_days_spin.setPrefix("近 ")
        self.refresh_days_spin.setSuffix(" 天")
        self.refresh_days_spin.setFixedWidth(92)
        date_row.addWidget(self.refresh_days_spin)

        self.refresh_date_btn = QPushButton("刷新可用日期")
        self.refresh_date_btn.setFixedWidth(116)
        date_row.addWidget(self.refresh_date_btn)
        outer.addLayout(date_row)

        # 保存目录行
        output_row = QHBoxLayout()
        output_row.setSpacing(10)
        output_label = QLabel("保存目录")
        output_label.setFixedWidth(64)
        output_row.addWidget(output_label)

        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("选择保存目录…")
        self.output_edit.setText(config.default_output_dir)
        output_row.addWidget(self.output_edit, 1)

        self.browse_btn = QPushButton("浏览…")
        self.browse_btn.setFixedWidth(88)
        output_row.addWidget(self.browse_btn)
        outer.addLayout(output_row)

        return card

    def _build_mode_card(self):
        card, outer = self._card("下载范围")
        bar = QFrame()
        bar.setObjectName("modeBar")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(6, 6, 6, 6)
        bar_layout.setSpacing(6)

        for mode_id, label, _days in DOWNLOAD_MODES:
            btn = QPushButton(label)
            btn.setObjectName("modeBtn")
            btn.setCheckable(True)
            btn.setMinimumHeight(36)
            btn.setCursor(Qt.PointingHandCursor)
            self.mode_group.addButton(btn)
            self.mode_buttons[mode_id] = btn
            bar_layout.addWidget(btn, 1)

        self.mode_buttons["single"].setChecked(True)
        outer.addWidget(bar)

        # 日期区间行：仅「日期区间」模式下可用，与 date_edit 的启用/禁用方式保持一致
        range_row = QHBoxLayout()
        range_row.setSpacing(10)
        range_start_label = QLabel("开始日期")
        range_start_label.setFixedWidth(64)
        range_row.addWidget(range_start_label)

        self.range_start_edit = QDateEdit()
        self.range_start_edit.setCalendarPopup(True)
        self.range_start_edit.setDate(QDate.currentDate().addDays(-7))
        self.range_start_edit.setDisplayFormat("yyyy-MM-dd")
        self.range_start_edit.setFixedWidth(150)
        range_row.addWidget(self.range_start_edit)

        range_end_label = QLabel("结束日期")
        range_row.addWidget(range_end_label)

        self.range_end_edit = QDateEdit()
        self.range_end_edit.setCalendarPopup(True)
        self.range_end_edit.setDate(QDate.currentDate())
        self.range_end_edit.setDisplayFormat("yyyy-MM-dd")
        self.range_end_edit.setFixedWidth(150)
        range_row.addWidget(self.range_end_edit)
        range_row.addStretch()

        self.range_row_widget = QWidget()
        self.range_row_widget.setLayout(range_row)
        outer.addWidget(self.range_row_widget)
        return card

    def _build_progress_card(self):
        card, outer = self._card("下载进度")

        top_row = QHBoxLayout()
        state_title = QLabel("实时进度")
        state_title.setObjectName("stateTitle")
        top_row.addWidget(state_title)
        top_row.addStretch()
        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("percentLabel")
        top_row.addWidget(self.percent_label)
        outer.addLayout(top_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        outer.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("statusLabel")
        outer.addWidget(self.status_label)
        return card

    def _build_log_card(self):
        card, outer = self._card("运行日志", growing=True)

        head_row = QHBoxLayout()
        head_row.addStretch()
        self.clear_log_btn = QPushButton("清空")
        self.clear_log_btn.setObjectName("flatBtn")
        self.clear_log_btn.setCursor(Qt.PointingHandCursor)
        head_row.addWidget(self.clear_log_btn)
        outer.addLayout(head_row)

        self.log_text = QTextEdit()
        self.log_text.setObjectName("logView")
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMinimumHeight(120)
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        outer.addWidget(self.log_text)
        return card

    def _build_footer(self):
        bar = QHBoxLayout()
        bar.setSpacing(10)

        hint = QLabel("下载内容版权归原媒体所有，仅供个人学习使用")
        hint.setObjectName("hintLabel")
        bar.addWidget(hint)
        bar.addStretch()

        self.open_folder_btn = QPushButton("打开目录")
        self.open_folder_btn.setFixedWidth(96)
        self.open_folder_btn.setMinimumHeight(40)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedWidth(88)
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setEnabled(False)

        self.download_btn = QPushButton("开始下载")
        self.download_btn.setObjectName("primaryBtn")
        self.download_btn.setFixedWidth(160)
        self.download_btn.setMinimumHeight(44)
        self.download_btn.setCursor(Qt.PointingHandCursor)

        bar.addWidget(self.open_folder_btn)
        bar.addWidget(self.cancel_btn)
        bar.addWidget(self.download_btn)
        return bar

    # ------------------------------------------------------------- 设置

    def _load_settings(self):
        output_dir = self.settings.value("output_dir", config.default_output_dir)
        self.output_edit.setText(output_dir)

        paper_id = self.settings.value("newspaper_id", "", type=str)
        target = None
        if paper_id:
            target = next((c for c in self.paper_chips if c.paper_id == paper_id), None)
        if target is None:
            target = self.paper_chips[0] if self.paper_chips else None
        if target:
            target.setChecked(True)
            self._load_cached_dates()

        mode_id = self.settings.value("download_mode", "single", type=str)
        if mode_id in self.mode_buttons:
            self.mode_buttons[mode_id].setChecked(True)
        self._apply_mode_state()

        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def _save_settings(self):
        self.settings.setValue("output_dir", self.output_edit.text())
        current = self._current_paper_id()
        if current:
            self.settings.setValue("newspaper_id", current)
        self.settings.setValue("download_mode", self._current_mode())
        self.settings.setValue("geometry", self.saveGeometry())

    def _connect_signals(self):
        self.download_btn.clicked.connect(self._on_download)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.open_folder_btn.clicked.connect(self._on_open_folder)
        self.browse_btn.clicked.connect(self._on_browse)
        self.today_btn.clicked.connect(
            lambda: self.date_edit.setDate(QDate.currentDate()))
        self.clear_log_btn.clicked.connect(self.log_text.clear)
        self.paper_group.idClicked.connect(self._on_paper_changed)
        self.mode_group.idClicked.connect(lambda _id: self._apply_mode_state())
        self.refresh_date_btn.clicked.connect(self._on_refresh_dates)

    # ------------------------------------------------------------- 状态

    def _current_paper_id(self):
        chip = self.paper_group.checkedButton()
        return chip.paper_id if chip else None

    def _current_mode(self):
        for mode_id, btn in self.mode_buttons.items():
            if btn.isChecked():
                return mode_id
        return "single"

    def _apply_mode_state(self):
        """日期控件仅在「指定日期」模式下可用；区间控件仅在「日期区间」模式下可用。"""
        single = self._current_mode() == "single" and not self._downloading
        self.date_edit.setEnabled(single)
        self.today_btn.setEnabled(single)
        # 与 single 模式处理 date_edit 的方式一致：非该模式时禁用（不隐藏）
        range_mode = self._current_mode() == "range" and not self._downloading
        self.range_start_edit.setEnabled(range_mode)
        self.range_end_edit.setEnabled(range_mode)

    def _set_downloading_state(self, downloading: bool):
        self._downloading = downloading
        self.download_btn.setEnabled(not downloading)
        self.cancel_btn.setEnabled(downloading)
        self.browse_btn.setEnabled(not downloading)
        self.refresh_date_btn.setEnabled(not downloading)
        self.refresh_days_spin.setEnabled(not downloading)
        self.open_folder_btn.setEnabled(not downloading)
        for chip in self.paper_chips:
            chip.setEnabled(not downloading)
        for btn in self.mode_buttons.values():
            btn.setEnabled(not downloading)

        if downloading:
            self.download_btn.setText("下载中…")
            self.status_label.setText("正在获取版面信息…")
        else:
            self.download_btn.setText("开始下载")
            if self.progress_bar.maximum() == 0:
                self.progress_bar.setRange(0, 1000)
                self.progress_bar.setValue(0)
                self._set_percent(0)
        self._apply_mode_state()

    def _set_percent(self, value: float):
        self.percent_label.setText(f"{int(round(value))}%")

    # ----------------------------------------------------------- 日期刷新

    def _on_paper_changed(self, _button_id):
        self._load_cached_dates()

    def _load_cached_dates(self):
        platform_id = self._current_paper_id()
        if not platform_id:
            return
        cached_dates = config.get_cached_dates(platform_id)
        if cached_dates:
            self._update_date_calendar(cached_dates)
            self._log(f"已加载缓存：{len(cached_dates)} 个更新日期")

    def _on_refresh_dates(self):
        platform_id = self._current_paper_id()
        if not platform_id:
            return

        self.refresh_date_btn.setEnabled(False)
        self.refresh_date_btn.setText("刷新中…")
        self._log("正在刷新更新日期…")
        QTimer.singleShot(100, lambda: self._do_refresh_dates(platform_id))

    def _do_refresh_dates(self, platform_id: str):
        try:
            days = self.refresh_days_spin.value()
            available_dates = check_available_dates(platform_id, config, days=days)
            config.set_cached_dates(platform_id, available_dates)
            self._update_date_calendar(available_dates)
            if available_dates:
                self._log(f"检测到 {len(available_dates)} 个更新日期（近 {days} 天）")
            else:
                self._log(f"未检测到更新日期（近 {days} 天）")
        except Exception as e:
            self._log(f"刷新失败：{e}", level="WARNING")
        finally:
            self.refresh_date_btn.setEnabled(True)
            self.refresh_date_btn.setText("刷新可用日期")

    def _update_date_calendar(self, available_dates: list):
        calendar = self.date_edit.calendarWidget()
        if not calendar:
            return

        default_format = QTextCharFormat()
        marked_format = QTextCharFormat()
        marked_format.setBackground(QColor("#FDECEC"))
        marked_format.setForeground(QColor("#C62828"))
        marked_format.setFontWeight(QFont.DemiBold)

        available_set = set()
        for date_str in available_dates:
            parts = date_str.split('-')
            if len(parts) == 3:
                available_set.add((int(parts[0]), int(parts[1]), int(parts[2])))

        shown_month = self.date_edit.date().month()
        shown_year = self.date_edit.date().year()
        for day in range(1, 32):
            test_date = QDate(shown_year, shown_month, day)
            if not test_date.isValid():
                break
            if (test_date.year(), test_date.month(), test_date.day()) in available_set:
                calendar.setDateTextFormat(test_date, marked_format)
            else:
                calendar.setDateTextFormat(test_date, default_format)

    # ------------------------------------------------------------- 事件

    def closeEvent(self, event):
        self._save_settings()
        event.accept()

    def _on_browse(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if dir_path:
            self.output_edit.setText(dir_path)
            self._save_settings()

    def _on_open_folder(self):
        output_dir = self.output_edit.text().strip()
        if output_dir and os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            self.status_label.setText("保存目录不存在，请先选择目录")

    # ------------------------------------------------------------- 下载

    def _on_download(self):
        platform_id = self._current_paper_id()
        output_dir = self.output_edit.text().strip()
        if not platform_id or not output_dir:
            self.status_label.setText("请先选择报纸和保存目录")
            return

        self._save_settings()
        self._set_downloading_state(True)
        self.log_text.clear()
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        self._set_percent(0)

        callbacks = dict(
            on_progress=self._on_progress,
            on_log=self._on_log,
        )

        mode = self._current_mode()
        if mode == "single":
            date = self.date_edit.date().toString("yyyy-MM-dd")
            self.controller.start_download(
                platform_id=platform_id,
                date=date,
                output_dir=output_dir,
                on_complete=self._on_complete,
                **callbacks
            )
        elif mode == "latest":
            # 「最新一期」独立分支：从今天起逐日探测（子线程内做网络请求），
            # 找到最近一个有版面的日期后下载该期，而不是只尝试今天
            self.progress_bar.setRange(0, 0)  # 探测阶段：忙碌指示
            self._set_percent(0)
            self.status_label.setText("正在探测最新一期…")
            self.controller.start_latest_download(
                platform_id=platform_id,
                output_dir=output_dir,
                on_complete=self._on_batch_complete,
                **callbacks
            )
        else:
            if mode == "range":
                # 日期区间模式：用户任选起止日期，逐日构造日期列表直接批量下载。
                # 注意：该模式不做出版日过滤（如 xuexishibao 仅 [0,2,4] 出版），
                # 非出版日逐日尝试、无版面时由批量通道告警跳过，属可接受现状。
                start = self.range_start_edit.date()
                end = self.range_end_edit.date()
                # 校验开始不晚于结束，倒挂时提示并放弃本次下载
                if start > end:
                    self._set_downloading_state(False)
                    self._log("开始日期不能晚于结束日期，请检查日期区间。", level="WARNING")
                    self.status_label.setText("日期区间无效")
                    return
                # 限制批量下载范围上限，超出部分截断为开始+61 天（含首尾共 62 天）
                span = start.daysTo(end) + 1
                if span > MAX_BATCH_DAYS:
                    end = start.addDays(MAX_BATCH_DAYS - 1)
                    self._log(f"日期区间已限制为最多 {MAX_BATCH_DAYS} 天（约两个月）。", level="WARNING")
                # 范围较大时给出提示，提醒用户注意对报纸网站的压力
                if start.daysTo(end) + 1 > LARGE_RANGE_THRESHOLD:
                    self._log(LARGE_RANGE_NOTICE, level="WARNING")
                dates = []
                cur = start
                while cur <= end:
                    dates.append(cur.toString("yyyy-MM-dd"))
                    cur = cur.addDays(1)
                on_complete = self._on_batch_complete
                extra = dict(on_date_progress=self._on_date_progress)
            else:
                days = dict((m, d) for m, _l, d in DOWNLOAD_MODES)[mode]
                # 限制批量下载范围上限，超出部分截断并提示用户
                if days > MAX_BATCH_DAYS:
                    days = MAX_BATCH_DAYS
                    self._log(f"批量下载范围已限制为最多 {MAX_BATCH_DAYS} 天（约两个月）。", level="WARNING")
                # 范围较大时给出提示，提醒用户注意对报纸网站的压力
                if days > LARGE_RANGE_THRESHOLD:
                    self._log(LARGE_RANGE_NOTICE, level="WARNING")
                dates = self.controller.get_dates_for_range(platform_id, days)
                on_complete = self._on_batch_complete
                extra = dict(on_date_progress=self._on_date_progress)
            self.controller.start_batch_download(
                platform_id=platform_id,
                dates=dates,
                output_dir=output_dir,
                on_complete=on_complete,
                **extra,
                **callbacks
            )

    def _on_cancel(self):
        self.controller.cancel()
        self._log("正在取消…", level="WARNING")

    @Slot(int, int, str)
    def _on_progress(self, value: int, maximum: int, text: str):
        if maximum > 0:
            clamped = min(value, maximum)
            self.progress_bar.setRange(0, maximum)
            self.progress_bar.setValue(clamped)
            self._set_percent(clamped * 100.0 / maximum)
        else:
            self.progress_bar.setRange(0, 0)  # 忙碌指示
            self.percent_label.setText("…")
        if text:
            self.status_label.setText(text)

    @Slot(int, int, str)
    def _on_date_progress(self, current: int, total: int, date: str):
        self.status_label.setText(f"正在下载 {date}（第 {current}/{total} 期）")

    @Slot(str)
    def _on_log(self, message: str):
        level = "INFO"
        if message.startswith("[WARNING]"):
            level = "WARNING"
        elif message.startswith("[ERROR]"):
            level = "ERROR"
        self._log(message, level=level)

    @Slot(bool, str)
    def _on_complete(self, success: bool, message: str):
        self._set_downloading_state(False)
        if success:
            self.progress_bar.setRange(0, 1000)
            self.progress_bar.setValue(1000)
            self._set_percent(100)
            self.status_label.setText("下载完成")
            self._log(f"完成：{message}")
        else:
            self.status_label.setText("下载失败")
            self._log(f"失败：{message}", level="ERROR")

    @Slot(int, int, int)
    def _on_batch_complete(self, success_count: int, skip_count: int, fail_count: int):
        self._set_downloading_state(False)
        summary = f"批量下载完成：成功 {success_count}，无版面/已存在 {skip_count}，失败 {fail_count}"
        if fail_count == 0:
            self.progress_bar.setRange(0, 1000)
            self.progress_bar.setValue(1000)
            self._set_percent(100)
        self.status_label.setText(summary)
        level = "INFO" if fail_count == 0 else "WARNING"
        self._log(summary, level=level)

    # ------------------------------------------------------------- 日志

    def _log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "ERROR":
            color = "#F0807E"
        elif level == "WARNING":
            color = "#E5A23B"
        else:
            color = "#C9CCD4"
        safe_message = html.escape(message)
        self.log_text.append(
            f'<span style="color:#6B7280">[{timestamp}]</span> '
            f'<span style="color:{color}">{safe_message}</span>'
        )
