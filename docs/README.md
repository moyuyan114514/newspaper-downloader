# 报纸下载器开发文档

> Windows GUI 工具，用于下载人民日报和学习时报 PDF

## 目录结构

```
newspaper-app/
├── dist/                        # 发布目录
│   └── 报纸下载器.exe           # 可执行文件 (46 MB)
├── icon.ico                     # 应用图标
├── main.py                      # 主程序入口
├── config.json                  # 配置文件
├── requirements.txt             # 依赖清单
├── newspaper_downloader.spec    # PyInstaller 打包配置
├── src/                         # 源代码
│   ├── __init__.py
│   ├── config.py               # 配置管理
│   ├── downloaders/            # 下载器模块
│   │   ├── __init__.py
│   │   ├── base.py             # 下载器基类
│   │   ├── rmrb.py             # 人民日报下载器
│   │   └── xuexishibao.py      # 学习时报下载器
│   ├── gui/                    # GUI 模块
│   │   ├── __init__.py
│   │   ├── main_window.py      # 主窗口
│   │   └── controller.py       # 下载控制器
│   └── utils/                  # 工具模块
│       ├── __init__.py
│       ├── storage.py          # 存储管理
│       ├── logger.py           # 日志模块
│       └── pdf_tools.py        # PDF 工具
├── download_rmrb.py            # 人民日报 CLI 脚本
├── download_xuexishibao.py     # 学习时报 CLI 脚本
└── 开发文档/                    # 开发文档
    ├── README.md
    ├── CHANGELOG.md
    └── docs/
```

## 快速导航

| 文档 | 说明 | 状态 |
|------|------|------|
| [项目概述](docs/project_overview.md) | 目标、范围、可交付物 | ✅ 完成 |
| [架构设计](docs/architecture.md) | 模块划分、组件交互 | ✅ 完成 |
| [MVP规格](docs/mvp_spec.md) | 核心需求、功能清单 | ✅ 完成 |
| [接口定义](docs/interface_spec.md) | 类、方法、数据结构 | ✅ 完成 |
| [环境配置](docs/setup_instructions.md) | Python、依赖、打包 | ✅ 完成 |
| [打包指南](scripts/build_instructions.md) | PyInstaller 使用 | ✅ 完成 |
| [开发日志](CHANGELOG.md) | 进度追踪、变更记录 | 持续更新 |

## 当前实现状态

### 已完成 ✅
- [x] 人民日报下载器 - 支持历史日期
- [x] 学习时报下载器 - 自动获取最新期
- [x] GUI 主窗口 (PySide6)
- [x] 下载进度显示
- [x] 批量下载（最新一期/一周/一月/半年）
- [x] 记住设置（目录、报纸、窗口位置）
- [x] 打开目录按钮
- [x] 应用图标
- [x] Windows 可执行文件打包

### 已验证
- 人民日报：2026-02-18, 2026-02-19, 2026-02-20
- 学习时报：2026-02-13

## 使用方式

### 方式一：直接运行 EXE（推荐）
双击 `dist/报纸下载器.exe` 即可运行

### 方式二：从源码运行
```bash
pip install -r requirements.txt
python main.py
```

### 方式三：命令行
```bash
python download_rmrb.py -d 2026-02-20 -o ./downloads
python download_xuexishibao.py -o ./downloads
```

## 功能列表

| 功能 | 说明 |
|------|------|
| 单日下载 | 选择日期下载指定日期报纸 |
| 批量下载 | 最新一期/一周/一月/半年 |
| 进度显示 | 实时显示下载进度和状态 |
| 日志记录 | 实时日志显示 |
| 记住设置 | 自动保存上次设置 |
| 打开目录 | 快速打开下载目录 |

## 支持的报纸

| 报纸 | 更新频率 | 历史日期 | 批量下载 |
|------|----------|----------|----------|
| 人民日报 | 每日 | ✅ 支持 | ✅ 每天 |
| 学习时报 | 不定期 | ❌ 仅最新期 | ✅ 仅更新日 |

## 打包发布

```bash
pyinstaller newspaper_downloader.spec --noconfirm
# 输出: dist/报纸下载器.exe (约 46 MB)
```

## 扩展开发

添加新报纸支持：
1. 在 `src/downloaders/` 创建新的下载器文件
2. 继承 `PlatformDownloaderBase` 基类
3. 实现 `get_latest_edition()` 和 `get_platform_name()` 方法
4. 在 `src/downloaders/__init__.py` 注册到 `DOWNLOADER_REGISTRY`
5. 在 `config.json` 添加配置项

详见 [接口定义](docs/interface_spec.md)。
