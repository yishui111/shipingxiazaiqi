<div align="center">

# 🎬 B站视频下载器（Bili Downloader）

> ⭐ **喜欢这个项目？请先点个 Star 支持一下，让更多人看到！** ⭐

![GitHub stars](https://img.shields.io/github/stars/yishui111/shipingxiazaiqi.svg?style=flat-square&color=orange)
![GitHub forks](https://img.shields.io/github/forks/yishui111/shipingxiazaiqi.svg?style=flat-square)
![GitHub repo size](https://img.shields.io/github/repo-size/yishui111/shipingxiazaiqi.svg?style=flat-square)

**在浏览器里看 B站时点一下书签 / 扩展按钮，视频就自动下载到本机 —— 支持单P、多P（分P）、合集、收藏夹，可选画质，还能用浏览器登录态解锁高清。**

</div>

---

## ✨ 项目简介

一个**完全自包含**的本地 B站视频下载工具（Python + Flask + yt-dlp）。你在浏览器网页版打开 B站、观看任意视频时，点一下书签（或工具栏扩展按钮），当前视频就会**整个下载**到本机 —— 支持单P、多P（分P）、合集批量、收藏夹，可选画质（最高可用 / 1080P / 720P / 480P / 360P / 仅音频），并可读取 Chrome / Edge / Firefox 登录态或粘贴 Cookie 解锁更高画质（未登录上限 480P，大会员可更高）。

**为什么推荐浏览器网页版而不是 App？** App 里拿不到视频页地址、无法自动化；而网页版一键就能把当前视频链接发给本机下载器。因此本工具面向**浏览器网页版**设计，整个下载链路在本机完成。

> 适合谁用：想在本地收藏 B站视频、需要批量下载自己订阅的合集、或离线观看的个人用户（仅限个人学习与研究用途）。

## 🎯 主要功能

- 🔖 **一键书签下载**：浏览器看视频时点书签 → 自动开始下载并弹出进度页；书签只把「当前页面链接 + 本机令牌」发给本机服务，**不上传任何数据**
- 📚 **合集自动批量下载**：检测到视频属于合集（系列）时，**自动把整个合集全部下载**（每集一个任务，最多 3 个同时下载，其余排队；上限 500 集，可在 `app/bili.py` 调整）
- ▶️ **多P / 合集支持**：默认下载全部分P / 整个合集，文件按 `_P01 _P02…` 自动编号
- ⌨️ **手动下载**：粘贴任意 B站链接（视频 / 分P / 合集 `/list/`、`/video/part/` / 收藏夹）即可解析并下载
- 🎚️ **画质选择**：最高可用 / 1080P / 720P / 480P / 360P / 仅音频
- 👑 **高清解锁**：读取 Chrome / Edge / Firefox 等浏览器登录态，或手动粘贴 Cookie（Cookie 只保存在本机 `data/`，绝不外传）
- 🎮 **本地播放**：下载完直接在页面里点「播放」，支持进度条拖拽；也可一键打开下载文件夹
- 🔁 **断点续传 / 自动重试**：网络中断自动重试（5 次），已下载过的同名文件默认跳过，可勾选「覆盖」重下
- 🧩 **Chrome 扩展（可选）**：MV3 工具栏按钮（`extension/` 目录），加载即用
- 🛡️ **安全**：服务只监听本机 `127.0.0.1`；随机访问令牌防止任意网页触发下载
- 📦 **复制即用**：所有代码、依赖、运行时数据都在项目文件夹内；换电脑复制文件夹按 DEPLOY.md 几步即可运行

## 🗂️ 目录结构

```
shipingxiazaiqi/
├── main.py                # 打包入口（PyInstaller 用；普通运行走 python -m app.server）
├── app/                   # 后端源码（Flask + yt-dlp）
│   ├── server.py          # Web 服务与 API（任务/设置/播放）
│   ├── bili.py            # 下载核心（yt-dlp + 内置 ffmpeg + 合集识别/批量）
│   ├── config.py          # 路径/令牌/设置（环境变量 BILI_HOST/BILI_PORT）
│   ├── templates/index.html   # 主页面
│   └── static/            # 前端样式与脚本
├── extension/             # 可选 Chrome 扩展（MV3）
├── tests/                 # 自测脚本与 TEST_REPORT.md
├── tools/install_bookmark.ps1   # 一键安装书签脚本（由 install_bookmark.bat 调用）
├── install.bat            # 首次安装：建虚拟环境 + 按锁版本装依赖
├── start.bat / stop.bat   # 一键启动（自动开浏览器）/ 停止
├── check.bat              # 环境自检（排查问题）
├── install_bookmark.bat   # 一键把「下载B站视频」书签装进 Chrome / Edge
├── requirements.txt       # 依赖锁定版本（可复现安装）
├── .env.example           # 环境变量模板（端口等）
├── AGENTS.md              # 项目约定
├── README.md              # 本文件
└── DEPLOY.md              # 新机器部署方案
```

> 💡 本仓库只包含**源代码 / 脚本 / 配置 / 文档**等关键内容。
> 运行时数据不随仓库分发：`data/`（令牌、设置、Cookie）、`downloads/`（下载的视频）、`logs/`（日志）由程序首次运行时自动创建（已写入 `.gitignore`）。

## 🚀 快速开始（拉到新电脑即可部署）

### 环境要求

- 操作系统：Windows 10 / 11（64 位）（源码为 Python，Linux/macOS 可用 `python -m app.server` 运行，一键脚本为 Windows 版）
- 运行时：**Python 3.10 ~ 3.14**（安装时勾选 “Add python.exe to PATH”，或用 py 启动器）；或用 DEPLOY.md 方案 B 打包出的免 Python 独立 exe
- 网络：安装依赖时需联网；运行期间需能访问 bilibili.com

### 1. 克隆

```bash
git clone https://github.com/yishui111/shipingxiazaiqi.git
cd shipingxiazaiqi
```

> 不会用 git？到仓库页面点绿色 `Code` → `Download ZIP` 解压，效果一样。

### 2. 安装依赖（Windows 一键）

```bat
install.bat     rem 自动检测 Python → 创建 .venv → 按 requirements.txt 锁定版本安装
```

或手动：

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

> ffmpeg 无需系统安装：`imageio-ffmpeg` 依赖包自带 ffmpeg 二进制（含 libx264）。

### 3. 配置

默认**无需任何配置**即可运行。可选：复制环境变量模板按需修改端口等：

```bash
copy .env.example .env        # Windows；Linux/macOS: cp .env.example .env
```

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `BILI_HOST` | `127.0.0.1` | 监听地址，建议保持本机回环 |
| `BILI_PORT` | `8787` | 服务端口，被占用时可改（如 8788） |

### 4. 启动

```bat
start.bat       rem Windows：启动服务并自动打开浏览器
```

手动方式：`.venv\Scripts\python.exe -m app.server`（Linux/macOS：`.venv/bin/python -m app.server`）

### 5. 验证

浏览器自动打开 <http://127.0.0.1:8787>（或手动访问），看到下载器页面即部署成功。粘贴一个 B站视频链接点「解析」能出标题与封面 → 点「开始下载」即完成端到端验证。

### 6. （可选）安装书签 / Chrome 扩展

- **一键书签**：先运行 `start.bat` 一次 → **完全关闭** Chrome / Edge → 双击 `install_bookmark.bat` → 重开浏览器，书签栏出现「下载B站视频」，看视频时点它即可触发下载（合集会自动整批下载）。
- **Chrome 扩展**：浏览器打开 `chrome://extensions` → 开启「开发者模式」→ 「加载已解压的扩展程序」→ 选择本仓库的 `extension` 文件夹 → 在扩展详情「扩展选项」里填入页面「①」区域书签代码中 `var t="..."` 里的令牌。

详细步骤（含打包免 Python exe 方案）见 **[DEPLOY.md](DEPLOY.md)**。

## 📥 大件资源下载（模型 / 素材 / 运行时）

本项目为**纯代码仓库，无模型 / 素材 / 运行时大件**需要单独下载。全部第三方能力由 pip 依赖提供：`yt-dlp`（B站解析与下载）、`imageio-ffmpeg`（内置 ffmpeg 二进制，用于音视频合并）。安装方式见上「安装依赖」。

## 🛠️ 本地开发 & 提交

```bash
git add .
git commit -m "feat: xxx"
git push origin main
```

- 修改后请保证 `install.bat / start.bat / stop.bat / README.md / DEPLOY.md / requirements.txt` 齐全可用；
- 交付前自测，过程与结果记录到 `tests/TEST_REPORT.md`；
- 端口等差异走环境变量（`BILI_PORT` / `BILI_HOST`），禁止硬编码；`.bat` 用 CRLF + 纯 ASCII。

## ❓ 常见问题（FAQ）

- **Q：点书签没反应 / 提示「下载器未启动」？** A：先运行 `start.bat`。
- **Q：书签栏找不到书签？** A：双击运行 `install_bookmark.bat`（需先完全关闭浏览器），或手动新建书签并粘贴下载器页面「①」里的代码。
- **Q：合集下到一半想停？** A：在任务列表点各任务的「取消」；已下载的集不会重复下。
- **Q：下载只有 480P，想要更高画质？** A：B站对未登录用户的画质限制。按页面「③ 下载设置」配置 Cookie 来源（浏览器登录态或手动粘贴 Cookie）。
- **Q：提示 `ERROR: unable to download video data` 之类？** A：多为 B站风控或网络波动，稍后重试；服务会自动重试 5 次。
- **Q：下载的是收费 / 会员专属视频？** A：会报错，属正常限制，本工具无法也不打算绕过。
- **Q：打不开页面 / 端口被占用？** A：运行 `check.bat` 自检；若 8787 被占用，设置环境变量 `BILI_PORT=其他端口` 后重启（改了端口，书签代码里的端口也要同步更新）。
- **Q：杀毒软件报警？** A：本工具为本地开源逻辑（Flask + yt-dlp），如遇误报请加入白名单。

## ⚠️ 注意事项

- 敏感信息（Cookie、令牌、账号密码）一律保存在本机 `data/` 目录并已被 `.gitignore` 忽略，**禁止提交到仓库**；
- Cookie 仅用于解锁你自己账号可观看画质的下载，只保存在本机，绝不外传；
- 本仓库仅供**个人学习与研究**使用：请遵守《哔哩哔哩用户协议》及相关法律法规，**不要用于商业用途、不要批量搬运他人作品、不要绕过付费/会员限制**；因使用本工具产生的任何问题由使用者自行承担。

## 📄 许可证

MIT License（如项目自带 LICENSE 则以仓库内为准）

## 🙏 支持与致谢

如果这个项目帮到了你，**请点亮右上角的 ⭐ Star**，你的支持是我持续更新的最大动力！
