# -*- mode: python ; coding: utf-8 -*-
# 目录版(onefile 的替代): 不做运行时自解压,完全不依赖 %TEMP%,
# 规避 "Could not create temporary directory!" 闪退问题。
# 构建后产物为 dist/电子报下载器-v0.7.1-目录版/ 文件夹,整个文件夹分发,入口 exe 在其中。
import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('icon.ico', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'requests',
        'PyPDF2',
        'PIL',
        'Pillow',
        'bs4',
        'beautifulsoup4',
        'src',
        'src.config',
        'src.downloaders',
        'src.downloaders.base',
        'src.downloaders.rmrb',
        'src.downloaders.xuexishibao',
        'src.downloaders.guangming',
        'src.downloaders.xinhua_daily',
        'src.downloaders.zhonghuadushu',
        'src.downloaders.wenzhai',
        'src.downloaders.fcyym',
        'src.downloaders.jiefangjun',
        'src.downloaders.zqb',
        'src.utils',
        'src.utils.storage',
        'src.utils.logger',
        'src.utils.pdf_tools',
        'src.gui',
        'src.gui.main_window',
        'src.gui.controller',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'IPython',
        'jupyter',
        'cv2',
        'scipy',
        'sympy',
        'notebook',
        'pytest',
        'sphinx',
        'docutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # 目录版关键项:二进制不打进 exe,放同目录
    name='电子报下载器-v0.7.1-目录版',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='电子报下载器-v0.7.1-目录版',
)
