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
