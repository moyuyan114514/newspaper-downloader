# 报纸下载器开发文档

> Windows GUI 工具，用于下载 9 份报纸的版面 PDF（人民日报/学习时报/光明日报/新华每日电讯/中华读书报/文摘报/讽刺与幽默/解放军报/中国青年报）

## 目录结构

```
newspaper-downloader/
├── dist/                        # 发布目录
│   └── 电子报下载器-v0.5.1.exe  # 单文件可执行程序（约 69 MB）
├── icon.ico                     # 应用图标
├── main.py                      # 主程序入口
├── config.json                  # 配置文件（报纸清单、下载参数）
├── requirements.txt             # 依赖清单
├── png2pdf.py                   # PNG/JPG 报纸图片转 PDF 工具（CLI）
├── newspaper_downloader.spec    # PyInstaller 打包配置
├── src/                         # 源代码
│   ├── __init__.py
│   ├── config.py               # 配置管理（单例，DEFAULT_CONFIG 与 config.json 合并加载）
│   ├── downloaders/            # 下载器模块
│   │   ├── __init__.py         # DOWNLOADER_REGISTRY 注册表
│   │   ├── base.py             # 下载器基类（会话、重试、进度回调）
│   │   ├── rmrb.py             # 人民日报（PeopleDailyDownloader，子报模板）
│   │   ├── fcyym.py            # 讽刺与幽默（复用 rmrb 模板）
│   │   ├── xuexishibao.py      # 学习时报
│   │   ├── gmw_base.py         # 光明网系公共基类（版面图提取、历史日期扫描）
│   │   ├── guangming.py        # 光明日报
│   │   ├── zhonghuadushu.py    # 中华读书报
│   │   ├── wenzhai.py          # 文摘报
│   │   ├── zqb.py              # 中国青年报（复用 gmw_base，覆写 URL 规则）
│   │   ├── xinhua_daily.py     # 新华每日电讯
│   │   └── jiefangjun.py       # 解放军报（JSON 接口，每版直连 PDF）
│   ├── gui/                    # GUI 模块
│   │   ├── __init__.py
│   │   ├── main_window.py      # 主窗口
│   │   └── controller.py       # 下载控制器（QThread 工作对象）
│   └── utils/                  # 工具模块
│       ├── __init__.py
│       ├── storage.py          # 存储管理（输出路径、临时目录）
│       ├── logger.py           # 日志模块
│       └── pdf_tools.py        # PDF 合并、JPG 转 PDF
├── PLAN.md                     # 改进计划
└── docs/                       # 本文档目录
```

## 各报纸数据源与解析方式

| 报纸 | 平台 | 下载器 | 解析方式 | 版面格式 |
|------|------|--------|---------|---------|
| 人民日报 | paper.people.com.cn | rmrb.py | 版面页正则提取 attachement PDF | PDF |
| 讽刺与幽默 | paper.people.com.cn/fcyym | fcyym.py | 同上（复用） | PDF |
| 学习时报 | paper.studytimes.cn | xuexishibao.py | 首页期号 → 版面页 PDF 链接 | PDF |
| 光明日报/中华读书报/文摘报 | epaper.gmw.cn | gmw_base 系 | 按日期扫 node_XX 版面页 → 提取整版图（.jpg.2 去 .2） | JPG→PDF |
| 中国青年报 | zqb.cyol.com | zqb.py | 同光明网系（URL 规则不同，无报代码段） | JPG→PDF |
| 新华每日电讯 | mrdx.cn | xinhua_daily.py | Page01BC.htm 提取整版图 | JPG→PDF |
| 解放军报 | www.81.mil.cn | jiefangjun.py | 每日 index.json → paperPDF 直连 | PDF |

> 站点备注：中华读书报自 2026-09-16 起在 epaper.gmw.cn 停更；mrdx.cn 页面上的"PDF下载"
> 按钮为死链（服务器无文件），因此新华每日电讯走图片路线；学习时报实际出版日为周一/三/五
> （config 中 update_days [0,2,4] 按 Python weekday 编号即为周一/三/五）。

## 当前实现状态

### 已完成 ✅
- [x] 9 份报纸下载器（近三个月历史日期均实测可用）
- [x] GUI 主窗口 (PySide6)：单日下载 + 批量下载（最新一期/一周/一月/半年）
- [x] 下载进度显示、实时日志、重复下载自动跳过
- [x] 记住设置（目录、报纸、窗口位置）
- [x] 多版面自动合并为单个 PDF（PDF 直接连拼 / JPG 转 PDF 两条路线）
- [x] png2pdf.py 图片转 PDF 工具
- [x] Windows 单文件 exe 打包

### 已验证（2026-09-30 实测）
- 人民日报：2026-07-01 / 07-15 / 08-15 / 09-15（真 PDF）
- 学习时报：2026-07-03 / 08-12 / 09-25 / 09-28 / 09-30（真 PDF，周一/三/五出版）
- 光明日报：2026-07-01 / 07-15 / 08-15 / 09-15 / 09-20 / 09-30
- 新华每日电讯：2026-07-01 / 07-15 / 09-15 / 09-30（8 月 14-16 日为站点归档空洞）
- 中华读书报：2026-07-01 / 07-29 / 08-19 / 09-09 / 09-16（09-16 后站点停更）
- 文摘报：2026-07-01 / 07-15 / 08-15 / 09-09 / 09-23 / 09-26（周三/周六出版）
- 讽刺与幽默：2026-07-03 / 08-14 / 09-25（周五出版，真 PDF）
- 解放军报：2026-07-01 / 08-15 / 09-15 / 09-30（真 PDF）
- 中国青年报：2026-07-15 / 08-15 / 09-15 / 09-30

## 使用方式

### 方式一：直接运行 EXE（推荐）
双击 `dist/电子报下载器-v0.5.1.exe` 即可运行

### 方式二：从源码运行
```bash
pip install -r requirements.txt
python main.py
```

### 方式三：图片转 PDF
```bash
python png2pdf.py ./downloads/人民日报/2026-09-30 -o 人民日报_20260930.pdf
```

## 打包发布

```bash
pyinstaller newspaper_downloader.spec --noconfirm
# 输出: dist/电子报下载器-v0.5.1.exe（约 69 MB）
# 注意: 新增下载器模块后需同步更新 spec 的 hiddenimports
```

## 扩展开发

添加新报纸支持：
1. 在 `src/downloaders/` 创建新的下载器文件
2. 按平台选择基类：
   - `paper.people.com.cn` 子报 → 继承 `PeopleDailyDownloader`，覆盖 `PAPER_PATH`（见 `fcyym.py`，两行代码即可）
   - 光明网系/同构站点 → 继承 `GMWDownloaderBase`，设置 `PAPER_CODE`/`PAPER_NAME`，URL 结构不同时覆盖 `_page_node_url()`（见 `zqb.py`）
   - 其它站点 → 继承 `PlatformDownloaderBase`，实现 `get_latest_edition()`（见 `jiefangjun.py`）
3. 在 `src/downloaders/__init__.py` 注册到 `DOWNLOADER_REGISTRY`
4. 在 `config.json` 和 `src/config.py` 的 `DEFAULT_CONFIG` 中添加配置
5. 若新增了下载器文件，在 `newspaper_downloader.spec` 的 `hiddenimports` 中补充模块名

## 相关文档

- [根 README](../README.md)：功能介绍、使用说明、支持的报纸清单
- [PLAN.md](../PLAN.md)：项目审计与改进计划
