# 项目约定（AGENTS.md）

> 本项目为「B站视频下载器」。本文件是给在本项目目录下工作的 AI/agent 的约定，随项目文件夹分发。

## 交付物要求

- 每个版本完成/修改后必须保证以下文件存在且可用：`install.bat`、`start.bat`、`stop.bat`、`README.md`、`DEPLOY.md`、`requirements.txt`（锁定版本）。
- 交付前必须**自测通过**：改完代码要自己跑一遍验证，测试过程记录在 `tests/TEST_REPORT.md`。

## 项目铁律

1. **自包含**：所有依赖锁定版本；所有运行时数据（`data/`、`downloads/`、`logs/`）都在项目目录内，复制整个文件夹即可带走。
2. **禁止硬编码**：端口、路径等差异通过环境变量（`BILI_PORT`/`BILI_HOST`）或 `data/settings.json` 配置。
3. **bat 脚本规范**：`.bat` 文件必须用 **CRLF 换行**、内容尽量用 **ASCII**（中文放 README），且 `if` 块内的 `echo` 文本**不要出现括号**（cmd 解析会崩）。
4. **默认中文**：与用户交流、README、注释用简体中文。
5. **安全底线**：服务只监听 `127.0.0.1`，写操作必须校验 `data/token.txt` 里的令牌。

## 常用命令

```bat
install.bat   rem 首次安装依赖
start.bat     rem 启动服务（自动开浏览器）
stop.bat      rem 停止服务
check.bat     rem 环境自检
```

手动调试：

```bat
.venv\Scripts\python.exe -m app.server
```

日志在 `logs\server.log`。

---

# 项目档案与维护记忆（2026-09 整理，供后续修改前速览）

## 架构速览

| 组件 | 作用 |
| ---- | ---- |
| main.py | 入口 |
| app/ | Flask 本地服务，127.0.0.1:8787（BILI_PORT/BILI_HOST 可改）；令牌 `config.py` 里 `TOKEN = get_token()`，首次运行随机生成存 `data/token.txt`，**不入库** |
| extension/ | Chrome MV3 扩展 |
| tools/install_bookmark.ps1 | 书签安装核心（自研）；**保留 UTF-8 BOM**（PS5.1 中文显示依赖，勿去 BOM） |
| tests/ | 测试（TEST_REPORT.md 已脱敏） |
| requirements.txt | 锁版本：Flask==3.1.3 / yt-dlp==2026.7.4 / imageio-ffmpeg==0.6.0 等 10 个 |
| .env.example | 环境变量模板 |

## 本仓库 = GitHub 公开裁剪版（重要边界）

刻意不入库：真实令牌（运行时生成，data/ 已被 ignore）、.env、`.venv`(135MB)、`build`/`dist`、`downloads`(9.1GB)、`data/`、`logs/`、`__pycache__`、`*.spec`（含本机绝对路径，DEPLOY.md 第 4 节有等价 exe 打包法）。

> 代码中多处 `token` 字样是令牌机制变量引用（config/server/main.js/options.js/ps1），非真实密钥，扫描误报时勿改名。

## 维护约定补充

- 新增功能后同步更新 README.md / DEPLOY.md / 本文件；bat 纯 ASCII+CRLF+无 BOM
- 提交：`git add . && git commit -m "..." && git push origin main`
- 合规：仅供个人学习/已授权内容，注意 B站条款；README 已含免责声明

