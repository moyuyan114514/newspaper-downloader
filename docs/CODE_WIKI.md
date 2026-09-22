# 报纸下载器 Code Wiki

> 基于对仓库 `newspaper-downloader` 的静态分析生成的开发维护文档。
> 覆盖项目整体架构、模块职责、关键类/函数、依赖关系与运行方式。

---

## 1. 项目概览

| 项目 | 说明 |
|------|------|
| 项目名称 | 报纸下载器（Newspaper Downloader） |
| 当前版本 | 0.5.1（`config.json` / `src/config.py`） |
| 技术栈 | Python 3.8+、PySide6、requests、BeautifulSoup、pypdf/PyPDF2、Pillow、PyInstaller |
| 形态 | Windows GUI 桌面应用（单文件 exe）；核心逻辑同时支持无 GUI 复用 |
| 用途 | 从各大报纸官网抓取每日版面资源，按日期下载并合并为单个 PDF |
| 许可证 | MIT + 仅供学习/个人使用声明 |

### 支持的报纸

| 平台 ID | 报纸 | 下载源 | 资源类型 | 历史日期 | 更新频率 |
|---------|------|--------|----------|----------|----------|
| `rmrb` | 人民日报 | paper.people.com.cn（人民网） | PDF | ✅ | 每日 |
| `xuexishibao` | 学习时报 | paper.studytimes.cn | PDF | ✅ | 不定期 |
| `guangming` | 光明日报 | epaper.gmw.cn（光明网） | JPG 图片 | ✅ | 每日 |
| `xinhua_daily` | 新华每日电讯 | mrdx.cn | JPG 图片 | ✅ | 每日 |
| `zhonghuadushu` | 中华读书报 | epaper.gmw.cn | JPG 图片 | ✅ | 每日 |
| `wenzhai` | 文摘报 | epaper.gmw.cn | JPG 图片 | ✅ | 每日 |

### 核心能力

- 单期下载与批量下载（最新一期 / 近 7 天 / 近 30 天 / 近 180 天）
- 多版面资源自动合并为单个 PDF（支持 PDF 合并与 JPG 转 PDF）
- 实时下载进度与日志回显（基于 Qt 信号/槽，线程安全）
- 用户配置自动记忆（QSettings）与 JSON 配置加载
- 历史可用日期检测与缓存（日历高亮显示）

---

## 2. 目录结构与整体架构

### 2.1 目录结构

```
newspaper-downloader/
├── main.py                       # 程序入口（GUI 启动）
├── config.json                   # 运行时配置文件
├── icon.ico                      # 应用图标
├── requirements.txt              # Python 依赖清单
├── newspaper_downloader.spec     # PyInstaller 打包脚本
├── test_downloader_functions.py  # 手动测试脚本
├── PLAN.md                       # 架构改进评审文档
├── README.md                     # 用户说明文档
├── docs/
│   ├── README.md                 # 开发文档索引
│   ├── CODE_WIKI.md              # ★ 本文档
│   └── main.png
└── src/
    ├── __init__.py               # 导出 Config
    ├── config.py                 # 配置管理（单例）
    ├── downloaders/              # 下载器子包
    │   ├── __init__.py           # 注册表 + 工厂 + 日期检测
    │   ├── base.py               # 抽象基类 + 数据结构
    │   ├── gmw_base.py           # 光明系（光明/中华/文摘）公共基类
    │   ├── rmrb.py               # 人民日报下载器
    │   ├── xuexishibao.py        # 学习时报下载器
    │   ├── guangming.py          # 光明日报下载器
    │   ├── xinhua_daily.py       # 新华每日电讯下载器
    │   ├── zhonghuadushu.py      # 中华读书报下载器
    │   └── wenzhai.py            # 文摘报下载器
    ├── gui/                      # GUI 子包
    │   ├── __init__.py           # 导出 MainWindow / DownloadController
    │   ├── main_window.py        # 主窗口 UI
    │   └── controller.py         # 下载控制器 + 工作线程
    └── utils/                    # 工具子包
        ├── __init__.py           # 导出工具符号
        ├── storage.py            # StorageManager 存储管理
        ├── logger.py             # Logger 日志模块
        └── pdf_tools.py          # PDF/图片合并工具
```

### 2.2 分层架构

整体采用 **经典的三层结构**，自底向上为：

```
┌─────────────────────────────────────────────────────────┐
│  UI 层 (src/gui)                                        │
│  MainWindow（PySide6 控件）                             │
│    └─ DownloadController（启动/取消线程，信号桥接）      │
└───────────────┬─────────────────────────────────────────┘
                │  Qt 信号/槽（progress/log/complete）
┌───────────────▼─────────────────────────────────────────┐
│  业务层 (src/downloaders + src/utils)                   │
│  DownloadWorker/BatchDownloadWorker（QObject 工作线程）  │
│    ├─ PlatformDownloaderBase（多态下载器调度）           │
│    ├─ GMWDownloaderBase（光明系下载器基类）              │
│    ├─ StorageManager（目录/临时文件管理）                │
│    └─ pdf_tools（PDF / 图片合并）                        │
└───────────────┬─────────────────────────────────────────┘
                │  requests HTTP 请求
┌───────────────▼─────────────────────────────────────────┐
│  数据源层 (外部)                                         │
│  人民网 / 学习时时报 / 光明网 / 新华每日电讯             │
└─────────────────────────────────────────────────────────┘
```

跨层共享的基础设施：`src/config.py`（全局配置单例）与 `src/utils/logger.py`（全局日志单例）。

### 2.3 核心数据流

一次下载的完整流程：

```
用户点击"开始下载"
   │
   ▼
MainWindow._on_download / _on_batch_download
   │  构造 DownloadController
   ▼
DownloadController.start_download / start_batch_download
   │  创建 QThread + Worker 并 moveToThread
   ▼
DownloadWorker.run / BatchDownloadWorker.run   （子线程）
   │
   ├─ get_downloader(platform_id, config)  → 得到具体下载器
   ├─ downloader.get_latest_edition(date)  → 解析出版面资源 URL 列表
   ├─ 逐个 downloader.download_file(...)   → 下载到临时目录
   │      └─ 通过 set_progress_callback 回调进度
   ├─ merge_pdfs_sorted / merge_images_to_pdf → 合并为单 PDF
   └─ StorageManager.cleanup_temp_dir      → 清理临时文件
   │
   ▼
complete_signal 发射 → MainWindow._on_complete / _on_batch_complete
```

---

## 3. 主要模块职责

### 3.1 入口与配置

| 文件 | 职责 |
|------|------|
| `main.py` | 初始化 sys.path，加载 `config.json`，创建 `QApplication` 与 `MainWindow` 并进入事件循环 |
| `src/config.py` | 定义 `Config` 单例与 `DEFAULT_CONFIG` 默认配置，负责 JSON 的加载/合并/保存，以及报纸/下载参数的读取 |
| `config.json` | 仓库自带的实际默认配置，与 `DEFAULT_CONFIG` 内容保持一致 |

### 3.2 下载器子包 `src/downloaders/`

| 文件 | 职责 |
|------|------|
| `base.py` | 定义数据模型（`EditionInfo`、`DownloadProgress`）与抽象基类 `PlatformDownloaderBase`（通用 HEADERS、requests 会话、download_file 下载逻辑、进度回调） |
| `gmw_base.py` | `GMWDownloaderBase`：光明系三家报纸（光明日报/中华读书报/文摘报）共用基类，实现统一的版面列表解析与图片提取策略 |
| `rmrb.py` | `PeopleDailyDownloader`：解析人民网版面 HTML，提取各版面 PDF 直链 |
| `xuexishibao.py` | `StudyTimesDownloader`：解析学习时时报版面，提取 PDF 列表 |
| `guangming.py` | `GuangmingRibaoDownloader`：继承 GMW 基类，实现光明日报图片提取 |
| `xinhuia_daily.py` | `XinhuaDailyDownloader`：独立解析 mrdx.cn 版面图片链接 |
| `zhonghuadushu.py` | `ZhonghuadushuDownloader`：继承 GMW 基类，中华读书报 |
| `wenzhai.py` | `WenzhaiDownloader`：继承 GMW 基类，使用备用图片提取逻辑 |
| `__init__.py` | 集中导出全部下载器；`DOWNLOADER_REGISTRY` 注册表；`get_downloader` 工厂；`get_available_platforms`；`check_available_dates` 日期检测 |

### 3.3 GUI 子包 `src/gui/`

| 文件 | 职责 |
|------|------|
| `main_window.py` | 构建完整主窗口 UI（报纸选择、日期选择、保存目录、批量下载按钮、进度条、日志框），绑定信号，处理用户交互 |
| `controller.py` | `DownloadController`（线程生命周期管理）、`DownloadWorker`（单期下载工作线程）、`BatchDownloadWorker`（批量下载工作线程），通过 Qt 信号与主线程通信 |
| `__init__.py` | 导出 `MainWindow`、`DownloadController` |

### 3.4 工具子包 `src/utils/`

| 文件 | 职责 |
|------|------|
| `storage.py` | `StorageManager`：构造输出目录结构、临时目录、检测文件存在、文件大小格式化 |
| `logger.py` | `Logger`：日志缓冲 + 回调 + 错误/警告持久化到 `error_log.json`，提供 `logger` 全局实例 |
| `pdf_tools.py` | `merge_pdfs` / `merge_pdfs_sorted` / `merge_images_to_pdf`：多文件合并 |
| `__init__.py` | 汇总导出上述工具类与函数 |

---

## 4. 关键类与函数说明

### 4.1 `src/config.py`

#### `class Config`（单例）
通过 `__new__` 实现单例；实例持有 `_config`（dict）与 `_config_path`。

| 成员 | 类型 | 说明 |
|------|------|------|
| `load(config_path)` | 方法 | 读取 JSON 并 `_merge_config` 合并到默认配置，保存路径 |
| `save(config_path=None)` | 方法 | 将当前配置写回 JSON |
| `_merge_config(loaded)` | 方法 | 递归合并 dict；嵌套 dict 仅做浅层 `update` |
| `app_name` / `version` / `default_output_dir` | property | 基础应用元信息 |
| `newspapers` | property | 所有报纸配置 dict |
| `max_retries` / `timeout` / `chunk_size` | property | 下载参数（读 `download.*`） |
| `get_newspaper(paper_id)` | 方法 | 取单个报纸配置 |
| `get_enabled_newspapers()` | 方法 | 过滤出 `enabled=true` 的报纸 |
| `get_cached_dates(platform_id)` | 方法 | 返回 24 小时内的日期缓存，超时返回空 |
| `set_cached_dates(platform_id, dates)` | 方法 | 写入日期缓存带时间戳 |

> 模块尾部实例化全局 `config = Config()`，供全项目使用。

### 4.2 `src/downloaders/base.py`

#### 数据类 `EditionInfo`
| 字段 | 类型 | 说明 |
|------|------|------|
| `url` | str | 唯一资源 URL（单版时） |
| `filename` | str | 输出文件名（如 `人民日报_20260220.pdf`） |
| `mime_type` | str | MIME 类型，默认 `application/pdf` |
| `size_bytes` | int | 资源大小 |
| `date` | str | 发行日期 `YYYY-MM-DD` |
| `page_urls` | List[str] | 所有版面的资源 URL 列表 |

#### 数据类 `DownloadProgress`
`current` / `total` / `filename` / `status`，用于进度回调。

#### `class PlatformDownloaderBase(ABC)`
| 成员 | 类型 | 说明 |
|------|------|------|
| `__init__(config)` | 方法 | 保存 config，创建 requests.Session 并加入 HEADERS |
| `get_latest_edition(date=None)` | 抽象方法 | 子类实现，返回 `EditionInfo` 或 `None` |
| `get_platform_name()` | 抽象方法 | 返回报纸中文名 |
| `get_platform_id()` | 抽象方法 | 返回平台 ID |
| `set_progress_callback(callback)` | 方法 | 注册进度回调 |
| `_report_progress(progress)` | 方法 | 触发回调 |
| `download_file(url, dest_path)` | 方法 | 流式下载单个资源，含重试（`max_retries`）、超时、分块写盘与进度上报，成功返回 `True` |
| `close()` | 方法 | 关闭 session |

### 4.3 `src/downloaders/gmw_base.py`

#### `class GMWDownloaderBase(PlatformDownloaderBase)`
光明网系共同基类。类属性 `BASE_URL`、`PAPER_CODE`、`PAPER_NAME`。

| 成员 | 说明 |
|------|------|
| `__init__` | 构造 `_index_url = BASE_URL/{PAPER_CODE}/html/layout/index.html` |
| `_log_error` / `_log_warning` | 封装 logger |
| `_get_edition_by_date(date)` | 解析 `ul#list` 版面列表构造 page URL；无列表则回退按 `node_XX.html` 遍历 1-19；最终 `_fetch_all_page_images` |
| `_fetch_all_page_images(...)` | 对每个版面页调用 `_get_page_image_url` 收集图片 URL |
| `_get_page_image_url(page_url)` | 默认返回 `None`，子类重写 |
| `_extract_image_from_page_gmrb(page_url)` | 光明日报风格：查找 `div.m-paper-version` 取版名 + `img#map` 取 src，将 `.jpg.2` 转 `.jpg` |
| `_extract_image_from_page_wenzhai(page_url)` | 文摘报备用：先试光明逻辑，失败则遍历 `soup.find_all('img')` 匹配含 `page/.jpg/images` 的 src，替换 `../../../` 为 `https://img.gmw.cn/` |

### 4.4 各具体下载器

#### `PeopleDailyDownloader`（rmrb）
| 成员 | 说明 |
|------|------|
| `get_latest_edition(date)` | 有 date 走 `_get_edition_by_date`，否则 `_get_latest_from_main_page` |
| `_get_latest_from_main_page()` | 正则 `href="(\d{6}/\d{2}/node_\d+\.html)"` 解析主页面，取各节点 PDF |
| `_get_edition_by_date(date)` | 按 `yyyyMM/dd` 路径逐页构造 `node_XX.html`，最多 30 页 |
| `_get_pdf_url(page_url)` | 正则 `attachement/(\d{6}/\d{2}/[a-f0-9-]+\.pdf)` 提取 PDF 直链 |

#### `StudyTimesDownloader`（xuexishibao）
| 成员 | 说明 |
|------|------|
| `get_latest_edition(date)` | 同上路由 |
| `_get_latest_from_main_page()` | 解析首页 `\./(\d{4}-\d{2}/\d{2})/node_1\.html` 定位最新日期 |
| `_get_edition_by_date(date)` | 过滤 404 与跳转页；正则提取 `.../images/*.pdf` 直链并去重 |
| `get_weekday_name(date)` | 返回中文星期名 |

#### `GuangmingRibaoDownloader`（guangming）
继承 GMW。`PAPER_CODE="gmrb"`，`_get_page_image_url` 复用 `_extract_image_from_page_gmrb`。

#### `XinhuaDailyDownloader`（xinhua_daily）
独立于 GMW。`BASE_URL="http://mrdx.cn"`。
| 成员 | 说明 |
|------|------|
| `_get_latest_edition()` | 用今天日期 `%Y%m%d` |
| `_get_edition_by_date(date)` | 请求 `content/{date}/Page01BC.htm`，BeautifulSoup 解析 |
| `_get_image_urls_from_page(soup, date)` | 提取含 `Page` 与 `.jpg` 的 `<img>` src，处理相对路径并去重排序 |

#### `ZhonghuadushuDownloader`（zhonghuadushu）
继承 GMW。`PAPER_CODE="zhdsb"`，`_get_page_image_url` 调用光明提取逻辑。

#### `WenzhaiDownloader`（wenzhai）
继承 GMW。`PAPER_CODE="wzb"`，`_get_page_image_url` 调用备用文摘提取逻辑。

### 4.5 `src/downloaders/__init__.py`（注册表与工厂）

| 成员 | 说明 |
|------|------|
| `DOWNLOADER_REGISTRY` | `{platform_id: DownloaderClass}` 映射表 |
| `get_downloader(platform_id, config)` | 工厂函数，按 ID 实例化下载器，未知返回 `None` |
| `get_available_platforms()` | 返回全部平台 ID 列表 |
| `check_available_dates(platform_id, config, days=7)` | 对近 N 天逐日调用 `get_latest_edition` 判断是否有版面，返回有更新的日期列表 |

### 4.6 `src/gui/controller.py`

#### `class DownloadWorker(QObject)`
单期下载工作线程。信号：`progress_signal(str,int,int)`、`log_signal(str)`、`complete_signal(bool,str)`。
- `run()`：执行 `_do_download()`，成功/失败经 `complete_signal` 上报。
- `_do_download()`：核心流程（获取 edition → 检测已存在文件 → 下载各版面 → 合并 → 清理临时目录 → 返回 `(success, path)`）。
- `cancel()`：置 `_cancel_requested` 标志实现协作式取消。
- 资源类型检测：`is_jpg = first_url 以 .jpg/.jpeg 结尾`，决定合并方式。

#### `class BatchDownloadWorker(QObject)`
批量下载工作线程。信号新增 `date_progress_signal(int,int,str)`，`complete_signal(int,int)`（成功数，失败数）。
- `run()`：遍历日期列表，逐期调用 `_download_single` 统计成功率。
- `_download_single(downloader, newspaper_name, date)`：单期完整下载流程，异常不中断批量。

#### `class DownloadController(QObject)`
线程生命周期与信号桥接管理。
| 成员 | 说明 |
|------|------|
| `get_available_newspapers()` | 返回启用的报纸 dict |
| `start_download(platform_id, date, output_dir, on_*)` | 创建单期 Worker + QThread，绑定回调并启动 |
| `start_batch_download(platform_id, dates, output_dir, on_*)` | 批量版本 |
| `_on_complete` / `_on_batch_complete` | 线程结束清理（quit/wait 并置空引用） |
| `cancel()` | 通知当前 Worker 取消 |
| `is_downloading()` | 是否在下载 |
| `get_dates_for_range(platform_id, days)` | 生成批量日期列表；学习时报仅取周一/周三/周五（weekday 0/2/4），其余取连续日期 |

### 4.7 `src/gui/main_window.py`

#### `class MainWindow(QMainWindow)`
| 成员 | 说明 |
|------|------|
| `__init__` | 初始化 QSettings、DownloadController，构建 UI / 加载设置 / 绑定信号 |
| `_init_ui()` | 构造"下载设置 / 批量下载 / 下载进度 / 日志 / 操作按钮"各分组控件 |
| `_populate_newspapers()` | 用启用报纸填充下拉框（data=平台 ID） |
| `_load_settings` / `_save_settings` | 用 QSettings 读写输出目录、报纸、窗口几何 |
| `_on_download()` | 拉起单期下载 |
| `_on_batch_download(days)` | 拉起批量下载（1/7/30/180 天） |
| `_on_cancel()` | 触发取消 |
| `_on_progress` / `_on_date_progress` | 更新进度条与状态标签 |
| `_on_log` / `_on_complete` / `_on_batch_complete` | 日志回显与结束态处理 |
| `_on_refresh_dates` / `_do_refresh_dates` | 异步检测可用日期并缓存 |
| `_update_date_calendar(available_dates)` | 用红色背景高亮有更新的日期 |
| `_set_downloading_state(downloading)` | 统一控制控件可用态 |
| `closeEvent` | 退出前保存设置 |

### 4.8 `src/utils/storage.py`

#### `class StorageManager`
| 成员 | 说明 |
|------|------|
| `__init__` | 保存 `base_path`（绝对路径） |
| `ensure_output_dir(newspaper, date)` | 创建 `<base>/<报纸>/<yyyyMMdd>` 目录 |
| `build_output_path(newspaper, date)` | 返回 `<报纸>/<yyyyMMdd>/<报纸>_<yyyyMMdd>.pdf` |
| `get_temp_dir(newspaper, date)` | 输出目录下的 `temp/` 子目录 |
| `cleanup_temp_dir(newspaper, date)` | 递归删除 temp 目录（吞异常） |
| `file_exists(newspaper, date)` | 输出 PDF 是否存在 |
| `get_file_size(filepath)` | 文件字节数 |
| `format_size(size_bytes)` | 人类可读大小（B/KB/MB/GB/TB） |

### 4.9 `src/utils/logger.py`

#### `Logger`
| 成员 | 说明 |
|------|------|
| `add_callback(cb)` | 注册日志回调 |
| `_log(level, message, details)` | 记录条目；仅 ERROR/WARNING 持久化 |
| `_persist_error_log(entry)` | 追加写入项目根 `error_log.json`（上限 1000 条） |
| `debug/info/warning/error` | 各等级日志便捷方法 |
| `export_json(filepath)` | 导出全部日志为 JSON |
| `get_entries()` / `clear()` | 读取/清空内存日志 |

> `LogLevel` 枚举 + `LogEntry` dataclass。模块尾实例化全局 `logger = Logger()`。

### 4.10 `src/utils/pdf_tools.py`

| 函数 | 说明 |
|------|------|
| `merge_pdfs(pdf_files, output_path)` | 用 `pypdf.PdfWriter`（缺失时回退 `PyPDF2.PdfMerger`）合并 |
| `merge_pdfs_sorted(pdf_files, output_path)` | 按页码排序后合并，输入 `[(page, path), ...]` |
| `merge_images_to_pdf(image_files, output_path)` | 用 Pillow 将每张 JPG 转 RGB 并保存为临时 PDF，再合并；输入 `[(page, path), ...]` |

---

## 5. 依赖关系

### 5.1 模块依赖图

```
main.py
  └─ src.config (config)
  └─ src.gui (MainWindow)
       └─ src.gui.controller (DownloadController)
            ├─ src.config (config)
            ├─ src.downloaders (get_downloader / EditionInfo / DownloadProgress)
            └─ src.utils (StorageManager / logger / merge_pdfs*)
                 └─ src.utils.storage / src.utils.logger / src.utils.pdf_tools
       └─ src.downloaders.__init__ (check_available_dates)
src.gui.main_window ──> src.config / src.gui.controller / src.utils

src.downloaders.base ──> src.utils.logger
src.downloaders.<各下载器> ──> src.downloaders.base / gmw_base

外部第三方：requests / pypdf / PyPDF2 / Pillow(PIL) / BeautifulSoup(bs4) / PySide6.Qt*
```

### 5.2 Python 依赖清单（`requirements.txt`）

| 包 | 用途 |
|----|------|
| `requests>=2.28.0` | HTTP 抓取与流式下载 |
| `pypdf>=4.0.0`（回退 PyPDF2） | PDF 合并 |
| `PySide6>=6.4.0` | Qt GUI 框架 |
| `pyinstaller>=5.0.0` | 打包单文件 exe |
| `beautifulsoup4>=4.0.0` | HTML 版面解析 |
| `Pillow>=10.0.0` | JPG 转 PDF |

### 5.3 配置数据依赖

- `config.json`（与 `DEFAULT_CONFIG` 对齐）必须在项目根目录；`main.py` 检测到即 `config.load()`。
- 打包时 `config.json` 与 `icon.ico` 通过 spec 的 `datas` 打进 exe。

---

## 6. 运行方式

### 6.1 从源码运行（GUI）

```bash
pip install -r requirements.txt
python main.py
```

### 6.2 命令行/手动测试

仓库无独立 CLI 入口，可使用提供的手动测试脚本验证下载器与 GUI 集成（会发起真实网络请求）：

```bash
python test_downloader_functions.py
```

### 6.3 打包为单文件 exe

```bash
pip install pyinstaller
pyinstaller newspaper_downloader.spec --noconfirm
# 输出: dist/电子报下载器-v0.5.1.exe
```

> 注意：spec 中 exe 名称为 `电子报下载器-v0.5.1`（与 README 中的 `报纸下载器.exe` 不一致，打包时以 spec 为准）。

### 6.4 GUI 使用流程

1. 选择报纸 → 选择日期 → 选择保存目录
2. 点击 **开始下载**（指定日期）或 **最新一期 / 最近一周 / 最近一月 / 最近半年**（批量）
3. 观察进度条与日志；完成后可"打开目录"
4. 设置自动记忆（QSettings）

### 6.5 运行环境要求

- Python 3.8+
- 联网环境（需访问各家报纸官网）
- Windows（GUI/打包默认目标，其他平台可运行核心逻辑）

---

## 7. 扩展指南（新增报纸）

1. 在 `src/downloaders/` 新建下载器，继承 `PlatformDownloaderBase`（或 `GMWDownloaderBase` 若为光明系）。
2. 实现抽象方法：`get_platform_name()`、`get_platform_id()`、`get_latest_edition(date=None)`。
3. 如资源为图片，实现/复用 `_get_page_image_url` 或 `_extract_image_from_page_*`。
4. 在 `src/downloaders/__init__.py` 的 `DOWNLOADER_REGISTRY` 注册。
5. 在 `config.json`（与 `src/config.py` 的 `DEFAULT_CONFIG`）添加报纸配置项。
6. 如存在特殊情况（如学习时报的更新日），在 `DownloadController.get_dates_for_range` 补充逻辑。

---

## 8. 已知注意点 / 潜在改进

- **配置双源**：`DEFAULT_CONFIG`（代码）与 `config.json`（文件）需手工保持一致。
- **测试依赖真实网络**：`test_downloader_functions.py` 会访问线上站点，CI 不稳定；可引入 pytest + mock 模拟 HTTP。
- **GUI 与业务耦合**：下载流程主要在 Worker 中，但日期范围生成逻辑（`get_dates_for_range`）位于 Controller，建议抽取为独立服务便于复用/测试。
- **异常趋向静默**：多处 `except Exception: pass`（如下载器解析、清理目录），排障时主要依赖 `error_log.json`。
- **pypdf / PyPDF2 回退**：`pdf_tools` 已做兼容，建议统一使用 `pypdf`。
- **构建产物**（`build/`、`dist/`、`__pycache__`）应通过 `.gitignore` 排除并定期清理。