# -*- coding: UTF-8 -*-
"""
报纸下载器 - 主程序入口
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from src.config import config
from src.gui import MainWindow

# 全局主题：Fusion 风格 + 浅色卡片样式表，主色取人民日报红
STYLESHEET = """
* {
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog { background: #F5F6F8; }
QLabel { color: #1F2329; background: transparent; }

QToolTip {
    background: #1F2329;
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
}

/* 顶部标题区 */
QLabel#appTitle { font-size: 18px; font-weight: 700; color: #1F2329; }
QLabel#appSubtitle { font-size: 11px; color: #86909C; }
QLabel#versionTag {
    color: #C62828;
    background: #FDECEC;
    border-radius: 9px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 700;
}

/* 卡片容器 */
QFrame#card {
    background: #FFFFFF;
    border: 1px solid #E8EAED;
    border-radius: 12px;
}
QLabel#cardTitle { color: #86909C; font-size: 12px; font-weight: 700; }

/* 可滚动页面：滚动区与内容容器透明，露出窗口底色 */
QScrollArea#mainScroll { background: transparent; border: none; }
QWidget#scrollContainer { background: transparent; }

/* 固定底部操作栏 */
QFrame#footerBar {
    background: #F5F6F8;
    border: none;
    border-top: 1px solid #E8EAED;
}

/* 普通按钮 */
QPushButton {
    background: #FFFFFF;
    border: 1px solid #D8DBE0;
    border-radius: 8px;
    padding: 7px 16px;
    color: #1F2329;
}
QPushButton:hover { background: #FFF7F7; border-color: #C62828; color: #C62828; }
QPushButton:pressed { background: #FDECEC; }
QPushButton:disabled { color: #A9AEB8; background: #F5F6F8; border-color: #E8EAED; }

QPushButton#ghostBtn {
    background: #FFFFFF;
    border: 1px solid #D8DBE0;
    color: #4E5969;
    border-radius: 8px;
    padding: 6px 12px;
}
QPushButton#ghostBtn:hover { border-color: #C62828; color: #C62828; background: #FFF7F7; }
QPushButton#ghostBtn:disabled { color: #A9AEB8; background: #F5F6F8; border-color: #E8EAED; }

QPushButton#flatBtn {
    border: none;
    background: transparent;
    color: #86909C;
    padding: 2px 8px;
    font-size: 11px;
}
QPushButton#flatBtn:hover { color: #C62828; background: transparent; }

/* 主按钮 */
QPushButton#primaryBtn {
    background: #C62828;
    border: none;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 700;
    border-radius: 10px;
}
QPushButton#primaryBtn:hover { background: #AD1F1F; color: #FFFFFF; }
QPushButton#primaryBtn:pressed { background: #961B1B; }
QPushButton#primaryBtn:disabled { background: #E8B4B4; color: #FDF3F3; }

/* 下载范围分段控件 */
QFrame#modeBar { background: #F2F3F5; border-radius: 10px; }
QPushButton#modeBtn {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px 10px;
    color: #4E5969;
    font-weight: 600;
}
QPushButton#modeBtn:hover { color: #C62828; background: rgba(198, 40, 40, 0.08); }
QPushButton#modeBtn:checked { background: #C62828; color: #FFFFFF; }
QPushButton#modeBtn:disabled { color: #A9AEB8; background: transparent; }

/* 输入控件 */
QLineEdit, QDateEdit, QSpinBox {
    background: #FFFFFF;
    border: 1px solid #D8DBE0;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 22px;
    color: #1F2329;
}
QLineEdit:hover, QDateEdit:hover, QSpinBox:hover { border-color: #C62828; }
QLineEdit:focus, QDateEdit:focus, QSpinBox:focus { border-color: #C62828; }
QLineEdit:read-only { background: #F7F8FA; color: #4E5969; }
QLineEdit:read-only:hover { border-color: #D8DBE0; }

/* 日期下拉箭头与数字框调节按钮在 main() 中以 PNG 资源动态注入，
   因为 QSS 的 image: url() 需要运行时拼出的绝对路径 */

/* 进度区 */
QLabel#stateTitle { font-size: 12px; font-weight: 700; color: #4E5969; }
QLabel#percentLabel { font-size: 14px; font-weight: 700; color: #C62828; }
QLabel#statusLabel { font-size: 11px; color: #86909C; }
QLabel#hintLabel { font-size: 10px; color: #A9AEB8; }

QProgressBar {
    background: #EEF0F3;
    border: none;
    border-radius: 7px;
    min-height: 14px;
    max-height: 14px;
}
QProgressBar::chunk {
    border-radius: 7px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #E05252, stop:1 #C62828);
}

/* 深色日志控制台 */
QTextEdit#logView {
    background: #202124;
    border: 1px solid #202124;
    border-radius: 10px;
    color: #C9CCD4;
    padding: 10px;
    selection-background-color: #C62828;
    selection-color: #FFFFFF;
}

/* 日历弹出框 */
QCalendarWidget QWidget#qt_calendar_navigation_bar {
    background: #C62828;
}
QCalendarWidget QToolButton {
    color: #FFFFFF;
    background: transparent;
    border: none;
    font-weight: 700;
    padding: 6px 12px;
}
QCalendarWidget QToolButton:hover { background: rgba(255, 255, 255, 0.18); border-radius: 6px; }
QCalendarWidget QToolButton::menu-indicator { image: none; }
QCalendarWidget QMenu {
    background: #FFFFFF;
    color: #1F2329;
    border: 1px solid #E8EAED;
}
QCalendarWidget QSpinBox {
    color: #FFFFFF;
    background: transparent;
    border: none;
}
QCalendarWidget QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #E8EAED;
    selection-background-color: #C62828;
    selection-color: #FFFFFF;
    alternate-background-color: #F7F8FA;
}

/* 细滚动条 */
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: #C9CCD4; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #A9AEB8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 8px; margin: 2px; }
QScrollBar::handle:horizontal { background: #C9CCD4; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #A9AEB8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }

#logView QScrollBar::handle:vertical { background: #4A4D53; }
#logView QScrollBar::handle:vertical:hover { background: #6B7280; }
"""


def main():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        config.load(config_path)

    # 日期/数字框箭头用 PNG 资源。实测 QSS 的 image 只接受
    # 纯绝对路径（正斜杠，不能加 file:/// 头），中文路径亦可
    assets_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets").replace("\\", "/")
    down_url = assets_dir + "/chevron-down.png"
    up_url = assets_dir + "/chevron-up.png"
    controls_qss = f"""
QDateEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    border: none;
    width: 24px;
    background: transparent;
}}
QDateEdit::down-arrow {{
    image: url({down_url});
    width: 11px;
    height: 11px;
}}
QDateEdit:disabled::down-arrow {{ image: none; }}
QSpinBox::up-button, QSpinBox::down-button {{
    subcontrol-origin: padding;
    width: 18px;
    border: none;
    background: transparent;
}}
QSpinBox::up-button {{ subcontrol-position: top right; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; }}
QSpinBox::up-arrow {{
    image: url({up_url});
    width: 9px;
    height: 9px;
}}
QSpinBox::down-arrow {{
    image: url({down_url});
    width: 9px;
    height: 9px;
}}
QSpinBox:disabled::up-arrow, QSpinBox:disabled::down-arrow {{ image: none; }}
"""

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET + controls_qss)
    app.setApplicationName(config.app_name)
    app.setApplicationVersion(config.version)

    icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
