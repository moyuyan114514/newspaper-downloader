# 报纸下载器

<p align="center">
  <img src="icon.ico" alt="Logo" width="128" height="128">
</p>

<p align="center">
  Windows GUI 工具，用于下载人民日报、学习时报、光明日报和新华每日电讯 PDF
</p>

<p align="center">
  <a href="#功能特性">功能特性</a> •
  <a href="#下载安装">下载安装</a> •
  <a href="#使用说明">使用说明</a> •
  <a href="#开发构建">开发构建</a>
</p>

---

## 功能特性

- **多报纸支持** - 人民日报、学习时报、光明日报、新华每日电讯、中华读书报、文摘报
- **批量下载** - 支持下载最新一期、一周、一月、半年
- **历史日期** - 支持指定历史日期下载
- **自动合并** - 多版面 PDF 自动合并为单文件
- **进度显示** - 实时下载进度和日志
- **记住设置** - 自动保存用户配置
- **无需安装** - 单文件 exe，双击即用

## 下载安装

### 方式一：直接下载 exe（推荐）

前往 [Releases](../../releases) 页面下载最新版本的 `报纸下载器.exe`，双击运行即可。

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/your-username/newspaper-downloader.git
cd newspaper-downloader

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py

## 版本历史

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

1. 选择报纸（人民日报/学习时报/光明日报/新华每日电讯）
2. 选择日期（人民日报支持历史日期）
3. 选择保存目录
4. 点击下载按钮：
   - **开始下载** - 下载指定日期
   - **最新一期** - 下载今天
   - **最近一周** - 下载最近7天
   - **最近一月** - 下载最近30天
   - **最近半年** - 下载最近180天

### CLI 模式

```bash
# 人民日报
python download_rmrb.py -d 2026-02-20 -o ./downloads

# 学习时报
python download_xuexishibao.py -o ./downloads
```

## 支持的报纸

| 报纸 | 更新频率 | 历史日期 | 批量下载 |
|------|----------|----------|----------|
| 人民日报 | 每日 | ✅ 支持 | ✅ 每天 |
| 学习时报 | 不定期 | ❌ 仅最新期 | ✅ 仅更新日 |
| 光明日报 | 每日 | ✅ 支持 | ✅ 每天 |
| 新华每日电讯 | 每日 | ✅ 支持 | ✅ 每天 |
| 中华读书报 | 每日 | ✅ 支持 | ✅ 每天 |
| 文摘报 | 每日 | ✅ 支持 | ✅ 每天 |

## 开发构建

### 环境要求

- Python 3.8+
- PySide6
- requests
- PyPDF2

### 构建步骤

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 PyInstaller
pip install pyinstaller

# 构建
pyinstaller newspaper_downloader.spec --noconfirm

# 输出文件
# dist/报纸下载器.exe
```

## 项目结构

```
newspaper-downloader/
├── main.py                  # 主程序入口
├── config.json              # 配置文件
├── icon.ico                 # 应用图标
├── requirements.txt         # 依赖清单
├── newspaper_downloader.spec # 打包配置
├── src/
│   ├── config.py           # 配置管理
│   ├── downloaders/        # 下载器模块
│   │   ├── base.py         # 下载器基类
│   │   ├── rmrb.py         # 人民日报
│   │   ├── xuexishibao.py  # 学习时报
│   │   ├── guangming.py    # 光明日报
│   │   └── xinhua_daily.py # 新华每日电讯
│   ├── gui/                # GUI 模块
│   │   ├── main_window.py  # 主窗口
│   │   └── controller.py   # 下载控制器
│   └── utils/              # 工具模块
│       ├── storage.py      # 存储管理
│       ├── logger.py       # 日志模块
│       └── pdf_tools.py    # PDF 工具
├── dist/                   # 发布目录
│   └── 报纸下载器.exe
└── docs/                   # 文档
    └── 开发文档/
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
5. 在 `config.json` 添加配置

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
