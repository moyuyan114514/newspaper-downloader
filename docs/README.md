# 报纸下载器 · 开发文档

> Windows GUI 工具，用于下载 9 份报纸的版面 PDF（人民日报/学习时报/光明日报/新华每日电讯/中华读书报/文摘报/讽刺与幽默/解放军报/中国青年报）

---

## 目录

- [项目架构](#项目架构)
- [目录结构](#目录结构)
- [核心数据结构](#核心数据结构)
- [下载器体系](#下载器体系)
- [添加新报纸](#添加新报纸)
- [GUI 架构](#gui-架构)
- [存储与 PDF 工具](#存储与-pdf-工具)
- [配置系统](#配置系统)
- [构建与发布](#构建与发布)
- [调试与排错](#调试与排错)
- [常见坑点](#常见坑点)
- [已知限制与待改进](#已知限制与待改进)

---

## 项目架构

```
┌─────────────────────────────────────────────────────────────┐
│                          GUI 层                              │
│  main_window.py  ←  signals  →  controller.py               │
│  (PySide6 界面)              (DownloadController / Worker)   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                       下载器层 (downloaders)                 │
│  PlatformDownloaderBase (抽象基类)                            │
│    ├── PeopleDailyDownloader (人民日报社模板)                 │
│    │     └── FengciyuyuDownloader (讽刺与幽默，2行接入)       │
│    ├── GMWDownloaderBase (光明网系模板)                       │
│    │     ├── GuangmingRibaoDownloader (光明日报)             │
│    │     ├── ZhonghuadushuDownloader (中华读书报)            │
│    │     └── WenzhaiDownloader (文摘报)                      │
│    ├── StudyTimesDownloader (学习时报，独立)                 │
│    ├── XinhuaDailyDownloader (新华每日电讯，独立)            │
│    ├── JiefangjunDailyDownloader (解放军报，JSON→PDF)        │
│    └── ZhongguoQingnianbaoDownloader (中国青年报，gmw变种)   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                        工具层 (utils)                        │
│  storage.py  │  pdf_tools.py  │  logger.py                  │
└─────────────────────────────────────────────────────────────┘
```

**分层职责：**

| 层 | 职责 | 不应该做 |
|----|------|----------|
| GUI 层 | 界面展示、用户交互、进度显示 | 直接发起网络请求、解析 HTML |
| 控制器层 | 线程管理、下载编排、信号转发 | 知道具体报纸的解析逻辑 |
| 下载器层 | 版面发现、图片/PDF URL 提取、单文件下载 | 操作 GUI、管理文件存储 |
| 工具层 | 存储路径、PDF 合并、日志 | 包含业务逻辑 |

---

## 目录结构

```
newspaper-downloader/
├── main.py                      # 主程序入口（含全局 QSS 主题）
├── config.json                  # 运行时配置（报纸清单、下载参数）
├── icon.ico                     # 应用图标
├── requirements.txt             # 依赖清单
├── png2pdf.py                   # PNG/JPG 报纸图片转 PDF 工具（CLI）
├── newspaper_downloader.spec    # PyInstaller 打包配置
├── assets/                      # 界面资源（PNG 箭头图标等）
├── src/
│   ├── __init__.py
│   ├── config.py               # 配置管理（单例，DEFAULT_CONFIG 与 config.json 合并加载）
│   ├── downloaders/            # 下载器模块
│   │   ├── __init__.py         # DOWNLOADER_REGISTRY 注册表 + get_downloader()
│   │   ├── base.py             # 基类：PlatformDownloaderBase / EditionInfo / DownloadProgress
│   │   ├── rmrb.py             # 人民日报（PeopleDailyDownloader，子报模板）
│   │   ├── fcyym.py            # 讽刺与幽默（继承 rmrb，覆写 PAPER_PATH）
│   │   ├── xuexishibao.py      # 学习时报（独立解析）
│   │   ├── gmw_base.py         # 光明网系公共基类（版面扫描、整版图提取兜底）
│   │   ├── guangming.py        # 光明日报
│   │   ├── zhonghuadushu.py    # 中华读书报
│   │   ├── wenzhai.py          # 文摘报
│   │   ├── zqb.py              # 中国青年报（继承 gmw_base，覆写 URL 规则）
│   │   ├── xinhua_daily.py     # 新华每日电讯（独立解析）
│   │   └── jiefangjun.py       # 解放军报（JSON 接口直连 PDF）
│   ├── gui/                    # GUI 模块
│   │   ├── __init__.py
│   │   ├── main_window.py      # 主窗口（PySide6）
│   │   └── controller.py       # 下载控制器（QThread Worker 模式）
│   └── utils/                  # 工具模块
│       ├── __init__.py
│       ├── storage.py          # 存储管理（输出路径、临时目录）
│       ├── logger.py           # 日志模块
│       └── pdf_tools.py        # PDF 合并、JPG 转 PDF
├── docs/                       # 文档（本文档所在目录）
└── PLAN.md                     # 项目审计与改进计划
```

---

## 核心数据结构

### EditionInfo

```python
@dataclass
class EditionInfo:
    url: str              # 单版面时的直接 URL（多版面时为空）
    filename: str         # 输出文件名（如 "人民日报_20260930.pdf"）
    mime_type: str        # 默认为 "application/pdf"
    size_bytes: int       # 文件大小（字节，可能为 0）
    date: str             # 日期 "YYYY-MM-DD"
    page_urls: List[str]  # 版面 URL 列表（核心字段）
```

**关键约定：**
- `page_urls` 是版面内容的来源，可以是 PDF 也可以是 JPG
- 控制器通过 `page_urls[0].lower().endswith(('.jpg', '.jpeg'))` 判断走 JPG→PDF 路线还是 PDF 直连路线
- 单版面报纸也要把 URL 放进 `page_urls` 里（保持接口一致）

### DownloadProgress

```python
@dataclass
class DownloadProgress:
    current: int     # 已下载字节数
    total: int       # 总字节数（无 content-length 时为 0）
    filename: str    # 当前下载的文件名
    status: str      # "starting" / "downloading" / "completed"
```

---

## 下载器体系

### 继承关系

```
PlatformDownloaderBase (ABC)
│
├── PeopleDailyDownloader       — paper.people.com.cn 模板
│   └── FengciyuyuDownloader    — 讽刺与幽默（子报，2行接入）
│
├── GMWDownloaderBase           — epaper.gmw.cn 模板
│   ├── GuangmingRibaoDownloader    — 光明日报
│   ├── ZhonghuadushuDownloader     — 中华读书报
│   └── WenzhaiDownloader           — 文摘报
│
├── ZhongguoQingnianbaoDownloader — 中国青年报（继承 gmw_base，覆写 URL）
├── StudyTimesDownloader        — 学习时报（独立站点）
├── XinhuaDailyDownloader       — 新华每日电讯（独立站点）
└── JiefangjunDailyDownloader   — 解放军报（JSON API 直连 PDF）
```

### 各报纸数据源与解析方式

| 报纸 | 平台 | 下载器 | 解析方式 | 版面格式 |
|------|------|--------|---------|---------|
| 人民日报 | paper.people.com.cn | rmrb.py | 版面页正则提取 attachment PDF | PDF |
| 讽刺与幽默 | paper.people.com.cn/fcyym | fcyym.py | 同上（复用 rmrb 模板） | PDF |
| 学习时报 | paper.studytimes.cn | xuexishibao.py | 首页期号 → 版面页 PDF 链接 | PDF |
| 光明日报 | epaper.gmw.cn/gmrb | gmw_base 系 | 按日期扫 node_XX 版面页 → 提取整版图 | JPG→PDF |
| 中华读书报 | epaper.gmw.cn/zhdshb | gmw_base 系 | 同上 | JPG→PDF |
| 文摘报 | epaper.gmw.cn/wzb | gmw_base 系 | 同上 + 备用提取逻辑 | JPG→PDF |
| 中国青年报 | zqb.cyol.com | zqb.py | gmw_base 框架 + 覆写 URL 规则 | JPG→PDF |
| 新华每日电讯 | mrdx.cn | xinhua_daily.py | Page01BC.htm 提取整版图 | JPG→PDF |
| 解放军报 | www.81.mil.cn | jiefangjun.py | 每日 index.json → paperPDF 直连 | PDF |

> **站点备注：**
> - 中华读书报自 2026-09-16 起在 epaper.gmw.cn 停更（站点侧问题）
> - mrdx.cn 页面上的"PDF下载"按钮为死链，新华每日电讯走图片路线
> - 学习时报出版日为周一/三/五（config 中 `update_days: [0,2,4]` 对应 Python weekday 编号）

### PlatformDownloaderBase 必须实现的方法

```python
class MyDownloader(PlatformDownloaderBase):
    def get_latest_edition(self, date: str = None) -> Optional[EditionInfo]:
        """获取指定日期的版面信息；date=None 时返回最新一期"""
        pass

    def get_platform_name(self) -> str:
        """报纸中文名"""
        return "某报纸"

    def get_platform_id(self) -> str:
        """报纸 ID（与 config.json / DOWNLOADER_REGISTRY 中的 key 一致）"""
        return "mypaper"
```

### 基类提供的能力

- `self._session` — `requests.Session` 实例，带统一 UA
- `self.config` — 配置对象（`max_retries` / `timeout` / `chunk_size`）
- `download_file(url, dest_path)` — 带重试、流式下载、进度回调的通用下载方法
- `set_progress_callback(callback)` — 设置进度回调函数

---

## 添加新报纸

### 快速判断：属于哪个模板？

1. **paper.people.com.cn 子报** → 继承 `PeopleDailyDownloader`（2 行代码）
2. **epaper.gmw.cn 子报** → 继承 `GMWDownloaderBase`（~10 行代码）
3. **URL 结构类似光明网系** → 继承 `GMWDownloaderBase` + 覆写 `_page_node_url()`
4. **其他站点** → 继承 `PlatformDownloaderBase`，实现三个抽象方法

### 模板一：人民日报社子报（最简单）

```python
# src/downloaders/mypaper.py
from .rmrb import PeopleDailyDownloader

class MyPaperDownloader(PeopleDailyDownloader):
    PAPER_PATH = "mypaper"  # paper.people.com.cn/<PAPER_PATH>/...

    def get_platform_name(self) -> str:
        return "某某报"

    def get_platform_id(self) -> str:
        return "mypaper"
```

然后在 `src/downloaders/__init__.py` 注册：

```python
from .mypaper import MyPaperDownloader

DOWNLOADER_REGISTRY = {
    # ...
    "mypaper": MyPaperDownloader,
}
```

在 `config.json` 和 `src/config.py` 的 `DEFAULT_CONFIG` 中添加：

```json
"mypaper": {
    "name": "某某报",
    "enabled": true,
    "update_days": [0, 1, 2, 3, 4, 5, 6]
}
```

在 `newspaper_downloader.spec` 的 `hiddenimports` 中补充模块名：

```python
'src.downloaders.mypaper',
```

### 模板二：光明网系子报

```python
# src/downloaders/mypaper.py
from .gmw_base import GMWDownloaderBase

class MyPaperDownloader(GMWDownloaderBase):
    PAPER_CODE = "mypaper"   # epaper.gmw.cn/<PAPER_CODE>/html/...
    PAPER_NAME = "某某报"

    def get_latest_edition(self, date: str = None):
        if date is None:
            return self._get_latest_edition()
        return self._get_edition_by_date(date)

    def _get_page_image_url(self, page_url: str):
        img_url, _ = self._extract_image_from_page_gmrb(page_url)
        return img_url

    def get_platform_name(self) -> str:
        return self.PAPER_NAME

    def get_platform_id(self) -> str:
        return "mypaper"
```

### 模板三：URL 结构不同但页面结构类似（如中国青年报）

继承 `GMWDownloaderBase`，覆写 `_page_node_url()` 方法：

```python
def _page_node_url(self, date_formatted: str, page_num: int) -> str:
    # 原版: BASE_URL/PAPER_CODE/html/layout/YYYYMM/DD/node_XX.html
    # 中青报: https://zqb.cyol.com/html/2026-09/30/nbs.D110000zgqnb_01.htm
    return f"https://zqb.cyol.com/html/{date_formatted.replace('/', '-')}/nbs.D110000zgqnb_{page_num:02d}.htm"
```

### 模板四：从零开始（独立站点）

继承 `PlatformDownloaderBase`，实现三个抽象方法。参考 `jiefangjun.py`（最简 JSON 接口）或 `xuexishibao.py`（首页 → 版面页模式）。

### 验证清单

添加新报纸后，请按此清单检查：

- [ ] `get_latest_edition(None)` 能获取最新一期
- [ ] `get_latest_edition("2026-09-15")` 能获取指定历史日期
- [ ] `page_urls` 非空且 URL 可直接下载
- [ ] 输出 PDF 能正常打开、版面顺序正确
- [ ] 在 config 中设置 `update_days`，界面出版频率显示正确
- [ ] spec 的 hiddenimports 已更新
- [ ] README 支持的报纸表格已更新

> ⚠️ 注意：`update_days` 目前**只影响界面上的出版频率显示**，批量下载的日期过滤尚未读取它（详见「已知限制与待改进」）。周报/隔日报新增后，批量下载仍会逐日尝试。

---

## GUI 架构

### 线程模型

GUI 使用 **QThread + Worker Object** 模式，下载操作全部在子线程中执行，通过 Qt 信号与主线程通信。

```
MainWindow (主线程)
    │
    ├── DownloadController (主线程，管理线程生命周期)
    │     │
    │     └── QThread (子线程)
    │           └── DownloadWorker / BatchDownloadWorker
    │                 ├── progress_signal  → 进度条
    │                 ├── log_signal       → 日志面板
    │                 └── complete_signal  → 完成回调
```

### 信号定义

**DownloadWorker（单日下载）：**
- `progress_signal(int, int, str)` — 当前值, 最大值, 状态文本（千分比进度，0~1000）
- `log_signal(str)` — 日志消息
- `complete_signal(bool, str)` — 成功/失败, 消息

**BatchDownloadWorker（批量下载）：**
- `progress_signal(int, int, str)` — 整体进度（跨全部日期）
- `date_progress_signal(int, int, str)` — 当前第几天/共几天/日期
- `log_signal(str)` — 日志消息
- `complete_signal(int, int, int)` — 成功数, 无版面数, 失败数

### 进度计算

- **单日下载**：`(版面序号 - 1) / 总版数 + (已下载字节 / 总字节) / 总版数`
- **批量下载**：`(已完成天数 + 当前天进度) / 总天数`
- 无 `content-length` 时，总字节为 0，进度只按版面数步进（仍能正常推进）

---

## 存储与 PDF 工具

### StorageManager

```python
storage = StorageManager(base_path)

# 构建输出路径: <base>/<报纸名>/<YYYYMMDD>/<报纸名>_<YYYYMMDD>.pdf
output_path = storage.build_output_path("人民日报", "2026-09-30")

# 获取临时下载目录: <base>/<报纸名>/<YYYYMMDD>/temp/
temp_dir = storage.get_temp_dir("人民日报", "2026-09-30")

# 清理临时目录
storage.cleanup_temp_dir("人民日报", "2026-09-30")
```

### PDF 合并路线

| 路线 | 场景 | 函数 |
|------|------|------|
| PDF 直连 | 人民日报、学习时报、讽刺与幽默、解放军报 | `merge_pdfs_sorted(files, output)` |
| JPG → PDF | 光明网系、新华每日电讯、中国青年报 | `merge_images_to_pdf(files, output)` |

判断依据：`edition.page_urls[0]` 的后缀是否为 `.jpg`/`.jpeg`。

---

## 配置系统

### 加载流程

```
DEFAULT_CONFIG (代码内默认值)
       │
       ▼  merge
config.json (运行时配置文件)
       │
       ▼
Config 单例 (config.py)
```

- `DEFAULT_CONFIG` 是完整的默认配置，保证即使没有 config.json 也能运行
- `config.json` 中的字段会覆盖 `DEFAULT_CONFIG` 中对应的字段
- 合并是**浅合并**（一级 key 对应的值整体替换/更新），所以 `newspapers` 下的子字典会整体更新

### `update_days` 的含义与现状

- 取值是 Python `datetime.weekday()` 编号的列表（周一=0 … 周日=6），如学习时报周一/三/五出版 → `[0, 2, 4]`。
- **当前用途**：仅驱动界面上的出版频率文案（`main_window.format_frequency()`，长度为 7 时显示「每日出版」）。
- **尚未生效**：批量下载的日期过滤写在 `controller.get_dates_for_range()` 里，目前只对学习时报硬编码了 `[0, 2, 4]`，其余报纸一律按自然日尝试。因此周报类报纸批量下载时会对非出版日产生「未找到任何版面」告警（见根目录 `error_log.json`）。GUI 的「日期区间」模式直接构造日期列表调 `start_batch_download()`，不经过 `get_dates_for_range()`，因此同样不做出版日过滤。

### 添加新配置项

1. 在 `DEFAULT_CONFIG` 中添加默认值
2. 在 `Config` 类中添加对应的 `@property`（如果需要便捷访问）
3. 可选：在 `config.json` 中添加覆盖值

---

## 构建与发布

### 环境要求

- Python 3.8+
- 依赖：`pip install -r requirements.txt`
- PyInstaller：`pip install pyinstaller`

### 构建命令

```bash
pyinstaller newspaper_downloader.spec --noconfirm
# 输出: dist/电子报下载器-v0.6.0.exe
```

### spec 文件注意事项

- `hiddenimports` 中列出了各下载器模块，**新增下载器必须同步添加**
  - 注：公共基类 `src.downloaders.gmw_base` 未显式列入，靠 `guangming`/`zhonghuadushu`/`wenzhai`/`zqb` 的导入关系被传递打包（实测正常）；新增独立基类时建议显式补齐
- `datas` 中列出了需要打包进 exe 的数据文件（config.json、icon.ico）
- `excludes` 中列出了不需要的大体积依赖（tkinter、matplotlib、numpy 等），减小 exe 体积
- 输出文件名 `name='电子报下载器-v0.6.0'` 需与版本号同步更新

### 发布流程

1. 更新版本号（见下方"版本号位置"）
2. 本地构建并测试 exe
3. 提交代码并 push 到 GitHub
4. 创建 Release 并上传 exe：

```bash
gh release create v0.6.0 dist/电子报下载器-v0.6.0.exe \
  --title "v0.6.0" \
  --notes-file release_notes.md
```

### 版本号位置（6 处，必须同步更新）

| 文件 | 字段/位置 |
|------|-----------|
| `config.json` | `version` |
| `src/config.py` | `DEFAULT_CONFIG["version"]` 和 `version` 属性的 fallback |
| `newspaper_downloader.spec` | `name='电子报下载器-vX.Y.Z'` |
| `README.md` | 下载链接、版本历史、项目结构图 |
| `docs/README.md` | 三处 exe 文件名引用 |
| `PLAN.md` | 版本引用 |

快捷搜索：`grep -r "0\.6\.0" .` 检查是否有遗漏。

---

## 调试与排错

### 日志面板

GUI 底部深色日志控制台会输出实时日志，格式为 `[LEVEL] message`。常见级别：
- `[INFO]` — 正常流程信息
- `[WARNING]` — 可恢复的问题（某版下载失败、无版面等）
- `[ERROR]` — 致命错误

### 测试脚本

**端到端测试**（需要联网）：

```bash
python _e2e_test.py
```

测试内容包括：
- 人民日报单日下载（PDF 路线）
- 重复下载跳过
- 新华每日电讯（JPG 合并路线）
- 光明日报最新一期
- 学习时报批量近 7 天
- 产物 PDF 有效性校验

**下载器功能测试**（需要联网）：

```bash
python test_downloader_functions.py
```

### 快速验证某个下载器

在 Python REPL 中：

```python
from src.config import config
from src.downloaders import get_downloader

d = get_downloader("rmrb", config)
edition = d.get_latest_edition("2026-09-15")
print(f"找到 {len(edition.page_urls)} 个版面")
print(f"第一版: {edition.page_urls[0]}")
```

### 常见问题排查

**Q: 下载报"未找到任何版面"？**
- 检查日期是否为出版日（周报类报纸不是每天都有）
- 检查站点是否能正常访问（浏览器打开官网）
- 检查 HTML 结构是否变了（可能站点改版，需要更新解析逻辑）

**Q: 进度条不动？**
- 检查下载器是否调用了 `set_progress_callback()` 和 `download_file()`
- 检查 controller 中是否连接了 `progress_signal`
- 无 `content-length` 的流式响应也会推进（按版面数步进）

**Q: 合并后的 PDF 打不开？**
- 检查 `page_urls` 中的 URL 是否真的是 PDF/JPG（用浏览器直接访问试试）
- JPG 路线检查图片是否损坏（能否正常打开）
- 查看日志中是否有合并错误

---

## 常见坑点

### 1. 光明网系的 `.jpg.2` 后缀

epaper.gmw.cn 的版面图默认是 `.jpg.2`（缩略图/低清），需要把 `.2` 去掉才是原图：

```python
jpg_url = abs_url.replace('.jpg.2', '.jpg')
```

### 2. 光明网系历史日期

旧版本直接拼 URL 访问，结果任何日期都返回最新一期内容。正确做法是：
- 最新一期：从 `index.html` 解析最新日期，再按日期访问
- 指定日期：直接按日期构造 URL（返回 404 或空内容说明该日期无报）

### 3. 版号不连续

不要假设版号从 1 到 N 连续。使用**连续失败阈值**（`consecutive_misses < 3`）来终止扫描。

### 4. 编码问题

requests 默认可能猜错编码，中文乱码会导致解析失败。显式设置：

```python
resp.encoding = 'utf-8'
```

### 5. PyInstaller 的 hiddenimports

新增下载器模块后，**必须**在 spec 的 `hiddenimports` 中注册，否则打包后的 exe 会报 `ModuleNotFoundError`。

### 6. config.json 的布尔值

JSON 中是 `true`/`false`（小写），Python 中是 `True`/`False`（大写）。`json.load` 会自动转换，但手写 config.json 时注意不要写错。

### 7. update_days 的编号

`update_days` 使用 Python `datetime.weekday()` 的编号：周一=0, 周二=1, ..., 周日=6。
学习时报周一/三/五出版 → `[0, 2, 4]`；讽刺与幽默周五出版 → `[4]`。
其当前生效范围见「配置系统 → update_days 的含义与现状」。

---

## 已知限制与待改进

以下是代码层面已确认、但尚未修复的限制，完整待办见 [PLAN.md](../PLAN.md)。

### 1. 批量下载未按出版日过滤

`controller.get_dates_for_range()` 只对学习时报硬编码了 `[0, 2, 4]`，其余报纸按自然日逐日尝试。周报/隔日报（讽刺与幽默、中华读书报、文摘报）批量下载时会对非出版日产生「未找到任何版面」告警。**修复方向**：改为统一读取 `config` 的 `update_days`。

### 2. 部分报纸的 update_days 与实际出版频率不符

`config.json` / `DEFAULT_CONFIG` 中中华读书报、文摘报的 `update_days` 均为全天 `[0..6]`，界面因此显示「每日出版」，与 README 声明的「周三」「周三/周六」不一致。**修复方向**：中华读书报改 `[2]`、文摘报改 `[2, 5]`（需与上述第 1 项一并处理才有实际效果）。

### 3. 测试依赖真实网络

`test_downloader_functions.py` 与 `_e2e_test.py` 均为联网脚本，无 mock，CI 不稳定。**修复方向**：补充基于 mock 的单元测试。

### 4. 批量完成信号参数语义不清

`BatchDownloadWorker.complete_signal` 发送 3 个参数（成功/无版面/失败），而 `DownloadController._on_batch_complete` 只接收 2 个（PySide6 会自动丢弃多余参数）。行为正常，但语义容易误读。

---

## 相关文档

本仓库三份文档分工如下，避免内容重复：

- [根 README](../README.md) — **用户向**：功能介绍、下载安装、使用说明、支持的报纸、版本历史
- 本文档（docs/README.md） — **开发向**：架构、目录结构、下载器体系、添加新报纸、GUI、配置、构建发布、排错、已知限制
- [PLAN.md](../PLAN.md) — **路线图**：审计结论、改进优先级、变更记录
