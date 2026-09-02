# 自测报告（TEST_REPORT.md）

> 记录本项目的自测过程与结论，方便复查。测试日期：2026-08-15
> 测试环境：Windows（x64），Python 3.14.4（项目本地虚拟环境 `.venv` 内），网络可访问 bilibili.com

---

## 1. 环境与依赖

| 检查项 | 结果 |
| --- | --- |
| Python 3.14.4 + pip 26.0.1 | ✅ 可用（PATH 里的 `python` 是微软商店占位符，须用 `py` 或真实路径，已记录） |
| 虚拟环境 `.venv` 创建 | ✅ 成功 |
| 依赖安装（Flask 3.1.3 / yt-dlp 2026.7.4 / imageio-ffmpeg 0.6.0） | ✅ 成功，版本已锁定到 `requirements.txt` |
| 内置 ffmpeg（imageio-ffmpeg 自带，v7.1 全功能版） | ✅ `ffmpeg -version` 正常，无需系统安装 ffmpeg |

## 2. 单元/冒烟验证

| 用例 | 结果 |
| --- | --- |
| `fetch_info()` 解析真实视频 `BV1GJ411x7h7` | ✅ 标题「【官方 MV】Never Gonna Give You Up - Rick Astley」、UP主「索尼音乐中国」正确（中文无乱码，此前控制台乱码为显示编码问题，写入文件验证无误） |
| yt-dlp 输出模板条件语法 | ✅ 排查出 `&` 条件须用 `{0}` 占位符（`%(playlist_index&_P{0:02d}|)s`），单P不产生后缀、多P产生 `_P01` |

## 3. Web 服务接口测试（HTTP 直连 127.0.0.1:8787）

| 接口 | 结果 |
| --- | --- |
| `GET /` 首页渲染 | ✅ HTTP 200 |
| `GET /api/parse`（真实视频解析） | ✅ 返回标题/封面/UP主/分P数 |
| `GET /api/add`（无令牌） | ✅ 403 拒绝 |
| `GET /api/tasks`（无令牌） | ✅ 403 拒绝 |
| `POST /api/remove`（无令牌） | ✅ 403 拒绝 |
| `POST /api/settings` 保存/回读 | ✅ 画质、范围、Cookie 来源、覆盖开关均正确保存；Cookie 明文不回显（显示“已保存”） |
| `GET /files/<视频>` 播放端点 | ✅ HTTP 200，`Content-Type: video/mp4` |
| `GET /files` + `Range: bytes=0-1023` | ✅ HTTP 206 返回 1024 字节（支持进度条拖拽） |
| CORS 头 | ✅ `Access-Control-Allow-Origin: *`（配合令牌使用） |

## 4. 真实下载端到端测试

### 4.1 单P视频
- 链接：`https://www.bilibili.com/video/BV1GJ411x7h7`
- 操作：`/api/add` 默认画质 → 轮询任务
- 结果：✅ 状态 `done`，进度 22.7% → 99.9% → 100%
- 产物：`downloads/【官方 MV】Never Gonna Give You Up - Rick Astley_BV1GJ411x7h7NA.mp4`，20.5 MB
- 完整性：✅ ffmpeg 全量解码（`-v error -f null -`）通过，无报错，可播放

### 4.2 多P视频（分P，验证“整个视频”）
- 链接：`https://www.bilibili.com/video/BV1FRgn6pEph`（2P，共约 5 分钟）
- 操作：解析（`parts=2`）→ 360P 全P下载
- 结果：✅ 状态 `done`，`parts_done=2/2`，进度单调递增（修复了分P切换时的进度回跳）
- 产物：`..._p1_P01.mp4`（7.6MB）+ `..._p2_P02.mp4`（7.6MB），编号正确
- 文件归属：✅ 任务 `files` 列表只包含本视频 ID 的文件，不混入其他任务产物（修复了 `re` 未导入导致的收集失败，及按 ID 过滤）

### 4.3 覆盖/跳过逻辑
- 同视频再次下载（未勾选覆盖）：✅ 状态 `done`，提示“同名文件已存在，本次未重复下载”，不重复下载
- 勾选“覆盖已有文件”后：✅ 重新下载成功

### 4.4 手动 Cookie（Netscape 转换）
- 设置 `cookie_source=text` 并粘贴 `SESSDATA=abc; bili_jct=xyz`：✅ 下载正常，`data/cookies_netscape.txt` 正确生成（B站域名、URL 编码键值）

## 5. 一键脚本测试（cmd 实际执行）

| 脚本 | 结果 |
| --- | --- |
| `start.bat` | ✅ 177ms 内返回；`Start-Process` 启动 pythonw；PID 文件写入；端口 8787 可访问；浏览器自动打开 |
| `stop.bat` | ✅ 输出 `Server stopped, PID xxxx`；端口释放；PID 文件删除；Python 3.14 venv 的空壳父进程随之自动退出（残留进程数 0） |
| 已运行时的 `start.bat` | ✅ 检测到旧实例，提示 already running 并打开页面，不重复启动 |
| `check.bat` | ✅ 环境自检各项目正常（注：check.bat 内 `if` 块的 echo 亦无括号，避免 cmd 解析错误） |

> 排错记录：bat 曾报 `. was unexpected at this time.` —— 原因有二：① LF 换行，cmd 需要 CRLF（已全部转 CRLF）；② `if` 块内 `echo` 文本含括号 `(PID ...)`（已改写）。另外 `cmd /c` 管道测试挂起是子进程继承管道句柄所致，最终改为 `Start-Process` 启动，行为干净。

## 6. 已知边界 / 未测项

| 项目 | 说明 |
| --- | --- |
| Chrome 扩展 | 代码已写好（manifest MV3 + 弹窗 + 选项页），本机无浏览器自动化环境，**未做真实浏览器加载测试**；书签方式已等效验证接口链路 |
| 大会员 4K/8K | 未登录/未配置真实 Cookie，未验证高画质解锁；机制依赖 yt-dlp 官方 B站解析器，配置 Cookie 后应自动生效 |
| 收藏夹链接 | 依赖登录态，逻辑与分P一致（yt-dlp playlist 处理），未单独实测 |
| Linux/macOS | 脚本仅提供 Windows 版本；Python 源码跨平台（`os.startfile` 仅 Windows 分支使用） |

## 7. 结论

✅ **核心链路全部自测通过**：解析 → 下载（单P/多P）→ ffmpeg 合并 → 本地播放 → 覆盖/跳过 → Cookie 配置 → 安全令牌 → 一键启停。项目满足「复制即用」交付标准。

---

## 8. 追加：合集批量下载 与 一键安装书签（2026-08-16）

### 8.1 合集识别与批量下载（真实测试）

| 用例 | 结果 |
| --- | --- |
| `video_id_from_url` 提取 BV 号 | ✅ 修复了 BV 号大写化导致 API 查不到的问题（BV 号大小写敏感，保留原始大小写） |
| B站 `x/web-interface/view` 拿 `ugc_season` | ✅ 真实视频 `BV1Z9gT61EnM` 识别出合集《AI音乐合集》8 集 |
| `seasons_archives_list` 分页拉剧集 | ✅ 拉到全部 8 集（bvid + 标题）；**修复了完整 UA 触发 B站 -352 风控**的问题，改用简单 UA 后正常 |
| `/api/parse` 返回合集信息 | ✅ 返回合集标题、集数、剧集标题列表 |
| `/api/add?series=auto` 自动批量 | ✅ 一个书签/一次粘贴 → 自动创建 8 个下载任务，返回 `task_ids` + 多任务 `gui_url` |
| 剧集标题预填 | ✅ 排队中的任务直接显示各集标题（无需等解析） |
| 并发控制 | ✅ 最多 3 个同时下载，其余排队（信号量 `SERIES_MAX_CONCURRENCY=3`） |
| 合集完整下载 | ✅ 8 集全部 `done`，文件均在 `downloads/`（每集 3~10MB），抽样 ffmpeg 解码可播放 |
| 取消/删除 | ✅ working/queued 任务可取消；排队中被取消的任务不启动下载 |

### 8.2 一键安装书签脚本

| 用例 | 结果 |
| --- | --- |
| `tools/install_bookmark.ps1`（UTF-8 BOM，中文显示正常） | ✅ 在书签文件**副本**上实测：备份 → 追加「下载B站视频」节点 → 写回 |
| 写回 JSON 合法性 | ✅ 无 BOM、`ConvertFrom-Json` 可解析、根节点 checksum/roots/version 保留 |
| 书签节点内容 | ✅ name=下载B站视频、type=url、url=`javascript:...`（内含本机令牌） |
| 原有书签保护 | ✅ 其余 5 个书签原样保留；真实 Edge 书签文件未被测试改动（仅在副本验证） |
| `install_bookmark.bat` | ✅ CRLF + ASCII，调用 ps1 并等待浏览器关闭 |

> 说明：真实书签安装需用户在浏览器关闭后运行 `install_bookmark.bat`；本报告记录的是对真实 Edge 书签文件副本的完整验证。
