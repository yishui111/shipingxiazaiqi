# 🚚 部署方案（DEPLOY.md）

> 目标：在一台**新电脑**上，把本项目拉下来即可运行，复现出与本机一致的环境。
> 本仓库只含源代码/脚本/配置/文档；`data/`、`downloads/`、`logs/` 由程序首次运行时自动创建。

---

## 1. 环境要求

| 项目 | 要求 |
| --- | --- |
| 操作系统 | Windows 10 / 11（64 位） |
| 方案 A（推荐） | 已安装 **Python 3.10 ~ 3.14**（安装时勾选 “Add python.exe to PATH”，或用 py 启动器） |
| 方案 B（免 Python） | 无需 Python，使用按第 4 节打包出的独立 `bili-downloader.exe` |
| 网络 | 安装依赖时需联网；运行期间需能访问 bilibili.com |

---

## 2. 获取代码

```bash
git clone https://github.com/yishui111/shipingxiazaiqi.git
cd shipingxiazaiqi
```

> 不会用 git？仓库页面点绿色 `Code` → `Download ZIP`，解压到任意目录即可，效果完全一样。

---

## 3. 方案 A：一键安装运行（推荐）

### 步骤

1. 进入项目根目录（本仓库无 `.venv`，由 `install.bat` 现场创建，不用删）。
2. 双击 `install.bat`：自动检测 Python → 创建 `.venv` → 按 `requirements.txt` **锁定版本**安装全部依赖（含 yt-dlp、内置 ffmpeg）。
3. 双击 `start.bat`：启动下载器并自动打开浏览器 <http://127.0.0.1:8787>。
4. 验证：粘贴一个 B站视频链接 → 「解析」→ 出标题/封面 → 「开始下载」→ 在 `downloads/` 看到文件，即部署成功。
5. 停止：`stop.bat`（按 PID 精确停止，端口释放）。
6. 排错：`check.bat` 逐项自检 Python / 依赖 / ffmpeg / 端口 / 目录。

### 依赖说明

`requirements.txt` 为精确版本锁定（如 `Flask==3.1.3`、`yt-dlp==2026.7.4`、`imageio-ffmpeg==0.6.0`），任何机器安装结果一致。
其中 `imageio-ffmpeg` 自带 ffmpeg 二进制（含 libx264），**无需在系统里安装 ffmpeg**。

### 书签（推荐装法）

1. 先运行 `start.bat` 一次（生成访问令牌 `data/token.txt`）。
2. **完全关闭** Chrome / Edge 浏览器。
3. 双击 `install_bookmark.bat` → 看到「✅ 安装成功」。
4. 重开浏览器（`Ctrl+Shift+B` 显示书签栏），书签栏出现「下载B站视频」。之后在 B站网页看视频点它：当前视频自动下载；若属于合集则**整个合集自动批量下载**，页面自动弹出任务进度页。

> 书签原理：把「当前页面链接 + 本机令牌」发给 `127.0.0.1:8787`，不上传任何数据。不想用脚本也可以手动建书签：复制下载器页面「①」区域里的代码 → 书签管理器 → 新建书签 → 粘贴到网址栏。
> `install_bookmark.bat` 会先把原书签文件备份为 `Bookmarks.bak-时间戳`，出问题可改回 `Bookmarks` 恢复。

### Chrome 扩展（可选，工具栏按钮）

1. 先运行 `start.bat` 一次。
2. 浏览器打开 `chrome://extensions` → 右上角开启「开发者模式」。
3. 点「加载已解压的扩展程序」→ 选择本项目里的 `extension` 文件夹。
4. 在扩展详情打开「扩展选项」，填入令牌：令牌在下载器页面「①」区域的书签代码里，即 `var t="..."` 引号中的内容（也可直接打开本机 `data/token.txt` 查看）。
5. 之后在 B站视频页点工具栏 🎬 按钮即可触发下载。

> 扩展默认指向 `127.0.0.1:8787`（见 `extension/manifest.json` 与 `popup.js`）；若你改了 `BILI_PORT`，需同步修改这两处后重新加载扩展。

---

## 4. 方案 B：免 Python，直接跑 exe（可选）

如果新电脑没有 Python，可在**本机**用 PyInstaller 打包出独立可执行文件：

```bat
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --name bili-downloader ^
  --collect-submodules yt_dlp --collect-data yt_dlp --collect-binaries imageio_ffmpeg ^
  --add-data "app\templates;app\templates" --add-data "app\static;app\static" ^
  --hidden-import imageio_ffmpeg main.py
```

- 入口**必须是 `main.py`**（不能用 `app\server.py`，否则包内相对导入报错）。
- 产物在 `dist\bili-downloader.exe`（该目录已被 `.gitignore` 忽略，不随仓库分发）。
- 把 exe 放到任意文件夹双击即运行（自动开浏览器）；停止时关闭 exe 窗口，或删除其旁的 `data\server.pid` 后结束进程。
- exe 模式下 `data/`、`downloads/`、`logs/` 创建在 **exe 所在目录**，依然复制即带走。

---

## 5. 配置说明

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `BILI_HOST` | `127.0.0.1` | 监听地址。**建议保持 127.0.0.1**（只本机可访问）；改成 `0.0.0.0` 前请务必考虑安全 |
| `BILI_PORT` | `8787` | 服务端口，被占用时可改（如 8788）；改后书签/扩展代码里的端口需同步更新 |

设置方式：Windows 系统环境变量，或在项目内新建 `.env` 后由启动脚本导出（`.env.example` 为模板，已随仓库分发）。

其他用户级配置（画质、下载范围、Cookie 来源、遇到合集自动处理、覆盖开关）都在页面「③ 下载设置」中保存，存于运行时生成的 `data/settings.json`。

### 目录与数据

| 目录/文件 | 说明 |
| --- | --- |
| `data/` | 运行时数据：`token.txt`（访问令牌）、`settings.json`（设置）、`cookies_netscape.txt`（手动 Cookie 转换文件）、`server.pid`（进程号）。**含敏感信息，勿提交** |
| `downloads/` | 所有下载的视频文件 |
| `logs/server.log` | 服务日志，排错看这里 |
| `extension/` | 可选 Chrome 扩展源码 |

### 合集批量下载机制

- **识别**：B站 `x/web-interface/view` 接口的 `ugc_season` 字段判断视频是否属于合集，再用 `seasons_archives_list` 分页拉取全部剧集（每页 30 集、上限 500 集），逐集创建下载任务。
- **并发**：最多 **3 个**下载同时进行，其余排队（`app/bili.py` 中 `SERIES_MAX_CONCURRENCY` 可调）。
- **触发**：书签 / 粘贴视频链接（页面设置「遇到合集自动处理」= 自动下载整个合集）都会触发整集合集下载；也可直接粘贴合集链接（`/list/`、`/video/part/`）。
- **限制**：合集识别依赖 B站官方接口，若被临时风控会返回空列表，稍后重试即可。

---

## 6. 新电脑与本机的差异

| 项目 | 说明 |
| --- | --- |
| Python 路径 | 以 `install.bat` 自动检测为准（`py -3` → `python`） |
| 虚拟环境 `.venv` | 无需从旧机器带，`install.bat` 现场重建 |
| 端口 | 默认 8787；被占用时通过 `BILI_PORT` 修改 |
| 书签/扩展 | 新电脑需重新安装一次（运行 `start.bat` 后令牌自动生成，书签脚本自动读取） |
| 数据（令牌/设置/Cookie） | 仓库不包含 `data/`；如需迁移旧机器数据，把旧机器项目内 `data/`、`downloads/` 复制过来即可 |

---

## 7. 常见问题排查

1. **`install.bat` 报 “Python not found”**：去 python.org 装 Python 3.10+，安装时勾选 “Add python.exe to PATH”。
2. **启动后浏览器没自动打开**：手动访问 <http://127.0.0.1:8787>，并看 `logs\server.log`。
3. **端口被占用**：`netstat -ano | findstr ":8787"` 查看占用；改 `BILI_PORT` 后重启。
4. **下载只有 480P**：未登录限制，按页面「③ 下载设置」配置 Cookie（浏览器登录态或手动粘贴）。
5. **下载报错 / 失败**：先看任务卡片错误信息与 `logs\server.log`；多为网络波动或 B站风控，稍后重试。
6. **杀毒误报**：本工具为本地开源组件（Flask / yt-dlp / imageio-ffmpeg），如被拦截请加入白名单。
7. **书签装不上 / 提示浏览器未关闭**：确认已完全退出 Chrome/Edge（含后台进程）后再运行 `install_bookmark.bat`。
8. **自检**：运行 `check.bat`，会逐项检查 Python、依赖、ffmpeg、端口、目录。

---

## 8. 验证清单（部署完成后逐项打勾）

- [ ] `check.bat` 各项显示正常
- [ ] `start.bat` 后浏览器能打开页面（<http://127.0.0.1:8787>）
- [ ] 粘贴一个视频链接能解析出标题与封面
- [ ] 点「开始下载」能完成下载并在 `downloads/` 里看到文件
- [ ] 书签（或扩展）能一键从 B站页面发起下载
- [ ] `stop.bat` 能停止服务、端口释放

---

## 9. 更新约定

每次修改代码后同步更新本文件与 README.md；改动经过自测后再提交（自测记录写入 `tests/TEST_REPORT.md`）。
