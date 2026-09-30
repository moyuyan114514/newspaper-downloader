# 报纸下载器

<p align="center">
  <img src="icon.ico" alt="Logo" width="128" height="128">
</p>

<p align="center">
  Windows GUI 工具，用于下载 9 份报纸（人民日报/学习时报/光明日报/新华每日电讯/中华读书报/文摘报/讽刺与幽默/解放军报/中国青年报）的版面 PDF
</p>

<p align="center">
  <a href="#功能特性">功能特性</a> •
  <a href="#下载安装">下载安装</a> •
  <a href="#使用说明">使用说明</a> •
  <a href="#开发构建">开发构建</a>
</p>

---

## 功能特性

- **多报纸支持** - 人民日报、学习时报、光明日报、新华每日电讯、中华读书报、文摘报、讽刺与幽默、解放军报、中国青年报
- **批量下载** - 支持下载最新一期、一周、一月、半年
- **历史日期** - 支持指定历史日期下载（各报近三个月均实测可用）
- **自动合并** - 多版面 PDF/图片自动合并为单个 PDF
- **图片转 PDF** - 附带 png2pdf.py，把已保存的 PNG/JPG 报纸图片合并为 PDF
- **进度显示** - 实时下载进度和日志
- **记住设置** - 自动保存用户配置
- **无需安装** - 单文件 exe，双击即用

## 下载安装

### 方式一：直接下载 exe（推荐）

前往 [Releases](../../releases) 页面下载最新版本的 `电子报下载器-v0.6.0.exe`，双击运行即可。

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/your-username/newspaper-downloader.git
cd newspaper-downloader

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 版本历史

### v0.6.0 (2026-09-30)
- ✨ 新增讽刺与幽默、解放军报、中国青年报支持（现共 9 份报纸）
- ✨ 新增 png2pdf.py：把已保存的 PNG/JPG 报纸图片合并为 PDF
- 🔧 修复光明日报无法下载的问题（版面图片 URL 解析返回了错误类型）
- 🔧 修复光明网系报纸（光明日报/中华读书报/文摘报）历史日期失效的问题（此前任何日期都返回最新一期）
- 🔧 新增整版图通用提取兜底，兼容中国青年报的版面结构
- 🎨 重绘界面主题：卡片式分组、红色主按钮、圆角进度条
- 🐛 修复进度条不动的两个原因：批量下载通道未接进度信号；流式响应无 content-length 时进度被丢弃
- 📝 更新说明文档与打包配置

### v0.5.0 (2026-02-23)
- ✨ 新增中华读书报支持
- ✨ 新增文摘报支持
- ✨ 新增JPG转PDF功能
- 🔧 优化下载器架构，支持图片格式下载
- 📦 支持更多报纸批量下载

### v0.4.1 (2024-01-15)
- ✨ 新增光明日报支持
- ✨ 新增新华每日电讯支持
- 🎨 优化界面布局
- 🔧 修复下载稳定性问题
- 📦 改进打包流程

## 使用说明

### GUI 模式

1. 选择报纸（下拉框共 9 份，见下方"支持的报纸"）
2. 选择日期（支持历史日期）
3. 选择保存目录
4. 点击下载按钮：
   - **开始下载** - 下载指定日期
   - **最新一期** - 下载最近一期
   - **最近一周** - 下载最近7天
   - **最近一月** - 下载最近30天
   - **最近半年** - 下载最近180天

### CLI 工具

```bash
# 把已保存的 PNG/JPG 报纸图片合并为 PDF（原始图片不动）
python png2pdf.py ./downloads/人民日报/2026-09-30 -o 人民日报_20260930.pdf
python png2pdf.py 第1版.png 第2版.png 第3版.png
```

## 支持的报纸

| 报纸 | 更新频率 | 历史日期 | 批量下载 |
|------|----------|----------|----------|
| 人民日报 | 每日 | ✅ 支持 | ✅ 每天 |
| 学习时报 | 周一/三/五 | ✅ 支持 | ✅ 出版日 |
| 光明日报 | 每日 | ✅ 支持 | ✅ 每天 |
| 新华每日电讯 | 每日 | ✅ 支持 | ✅ 每天 |
| 中华读书报 | 周三 | ✅ 支持 | ✅ 出版日 |
| 文摘报 | 周三/周六 | ✅ 支持 | ✅ 出版日 |
| 讽刺与幽默 | 周五 | ✅ 支持 | ✅ 出版日 |
| 解放军报 | 每日 | ✅ 支持 | ✅ 每天 |
| 中国青年报 | 每日 | ✅ 支持 | ✅ 每天 |

> 注：中华读书报在光明网电子报平台上自 2026-09-16 起未再更新，为站点侧问题，此前的历史期仍可下载。

## 开发构建

### 环境要求

- Python 3.8+
- 依赖见 `requirements.txt`（PySide6、requests、pypdf、beautifulsoup4、Pillow）

### 构建步骤

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 PyInstaller
pip install pyinstaller

# 构建
pyinstaller newspaper_downloader.spec --noconfirm

# 输出文件
# dist/电子报下载器-v0.6.0.exe
```

## 项目结构

```
newspaper-downloader/
├── main.py                  # 主程序入口
├── config.json              # 配置文件
├── icon.ico                 # 应用图标
├── requirements.txt         # 依赖清单
├── png2pdf.py               # PNG/JPG 报纸图片转 PDF 工具（CLI）
├── newspaper_downloader.spec # 打包配置
├── src/
│   ├── config.py           # 配置管理
│   ├── downloaders/        # 下载器模块
│   │   ├── base.py         # 下载器基类
│   │   ├── rmrb.py         # 人民日报（人民日报平台子报复用此模板）
│   │   ├── xuexishibao.py  # 学习时报
│   │   ├── gmw_base.py     # 光明网系公共基类（含中国青年报复用的提取逻辑）
│   │   ├── guangming.py    # 光明日报
│   │   ├── zhonghuadushu.py # 中华读书报
│   │   ├── wenzhai.py      # 文摘报
│   │   ├── xinhua_daily.py # 新华每日电讯
│   │   ├── fcyym.py        # 讽刺与幽默
│   │   ├── jiefangjun.py   # 解放军报
│   │   └── zqb.py          # 中国青年报
│   ├── gui/                # GUI 模块
│   │   ├── main_window.py  # 主窗口
│   │   └── controller.py   # 下载控制器
│   └── utils/              # 工具模块
│       ├── storage.py      # 存储管理
│       ├── logger.py       # 日志模块
│       └── pdf_tools.py    # PDF 工具（合并、JPG转PDF）
├── dist/                   # 发布目录
│   └── 电子报下载器-v0.6.0.exe
├── docs/                   # 文档
└── PLAN.md                 # 改进计划
```

## 扩展开发

添加新报纸支持：

1. 在 `src/downloaders/` 创建新文件
2. 继承 `PlatformDownloaderBase` 类
3. 实现以下方法：
   ```python
   def get_platform_name(self) -> str:
       return "报纸名称"
   
   def get_platform_id(self) -> str:
       return "paper_id"
   
   def get_latest_edition(self, date: str = None) -> EditionInfo:
       # 获取报纸信息和 PDF 链接
       pass
   ```
4. 在 `src/downloaders/__init__.py` 注册
5. 在 `config.json` 和 `src/config.py` 的 `DEFAULT_CONFIG` 中添加配置

> 提示：`paper.people.com.cn` 平台下的子报（如讽刺与幽默）只需继承 `PeopleDailyDownloader`
> 并覆盖 `PAPER_PATH`、`get_platform_name()`、`get_platform_id()` 三个成员即可，见 `fcyym.py`；
> 光明网系/同构站点可继承 `GMWDownloaderBase` 并按需覆盖 `_page_node_url()`，见 `zqb.py`。

## 许可证

本项目仅供学习和个人使用。请勿用于商业目的。

## 免责声明

- 本工具仅用于学习交流，请勿用于商业用途
- 下载的报纸内容版权归原作者所有
- 使用本工具下载的内容仅供个人阅读

---

<p align="center">
  Made with ❤️ for newspaper readers
</p>
