# ============================================================
#  B站下载器 —— 一键安装"下载B站视频"书签到 Chrome / Edge
#  用法：双击 install_bookmark.bat（请先完全关闭浏览器）
# ============================================================
param(
    [string]$BookmarksFileOverride = '',   # 测试用：指定书签文件
    [switch]$SkipBrowserCheck             # 测试用：跳过浏览器进程检查
)
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$tokenFile = Join-Path $root 'data\token.txt'
$port = if ($env:BILI_PORT) { $env:BILI_PORT } else { '8787' }
$gui = "http://127.0.0.1:$port"

Write-Host ''
Write-Host '============================================'
Write-Host '  B站下载器 一键安装书签'
Write-Host '============================================'

# 1. 读取令牌
if (-not (Test-Path $tokenFile)) {
    Write-Host '[错误] 未找到令牌文件。请先运行 start.bat 启动一次下载器。' -ForegroundColor Red
    exit 1
}
$token = (Get-Content $tokenFile -Raw -Encoding UTF8).Trim()
if (-not $token) {
    Write-Host '[错误] 令牌为空。请先运行 start.bat。' -ForegroundColor Red
    exit 1
}

# 2. 书签代码（与下载器页面一致：点一下自动下载当前视频；属合集则自动下整个合集）
$bookmarkUrl = "javascript:(function(){var t=`"$token`";var g=window.open(`"$gui/`",`"_blank`");var u=location.href;fetch(`"$gui/api/add?url=`"+encodeURIComponent(u)+`"&token=`"+t).then(function(r){return r.json()}).then(function(j){if(j.ok){if(g){g.location.href=j.gui_url}}else{if(g){g.close()}alert(`"下载器返回：`"+(j.error||`"未知错误`"))}}).catch(function(){if(g){g.close()}alert(`"下载器未启动！请先运行 start.bat`")})})();"

# 3. 找书签文件（Chrome 优先，其次 Edge）
if ($BookmarksFileOverride) {
    $bookmarkFile = $BookmarksFileOverride
    if (-not (Test-Path $bookmarkFile)) {
        Write-Host "[错误] 指定的书签文件不存在: $bookmarkFile" -ForegroundColor Red
        exit 1
    }
} else {
    $candidates = @()
    $chromeBase = Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data'
    $edgeBase   = Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\User Data'
    if (Test-Path $chromeBase) { $candidates += (Join-Path $chromeBase 'Default\Bookmarks') }
    if (Test-Path $edgeBase)   { $candidates += (Join-Path $edgeBase 'Default\Bookmarks') }
    # 多 Profile 情况（Default 不存在时找 Profile N）
    if (Test-Path $chromeBase) {
        Get-ChildItem $chromeBase -Directory -Filter 'Profile*' -ErrorAction SilentlyContinue |
            ForEach-Object { $candidates += (Join-Path $_.FullName 'Bookmarks') }
    }
    if (Test-Path $edgeBase) {
        Get-ChildItem $edgeBase -Directory -Filter 'Profile*' -ErrorAction SilentlyContinue |
            ForEach-Object { $candidates += (Join-Path $_.FullName 'Bookmarks') }
    }

    $bookmarkFile = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $bookmarkFile) {
        Write-Host '[错误] 没有找到 Chrome / Edge 的书签文件。' -ForegroundColor Red
        Write-Host '请确认已安装并至少打开过一次 Chrome 或 Edge 浏览器，然后重试。'
        exit 1
    }
}
Write-Host "[1/4] 书签文件: $bookmarkFile"

# 4. 等浏览器关闭（防止浏览器把改动覆盖掉）
$procs = Get-Process -Name chrome,msedge -ErrorAction SilentlyContinue
if ($procs -and -not $SkipBrowserCheck) {
    Write-Host '[2/4] 检测到浏览器还在运行，请完全关闭 Chrome / Edge ...'
    $wait = 0
    while ($procs -and $wait -lt 90) {
        Start-Sleep -Seconds 3
        $wait += 3
        $procs = Get-Process -Name chrome,msedge -ErrorAction SilentlyContinue
        if ($procs) {
            Write-Host "      等待中... ($($procs.Count) 个进程还在运行，已等待 ${wait}s)"
        }
    }
    if ($procs) {
        Write-Host '[错误] 浏览器一直没关闭。请手动关闭 Chrome/Edge 后重新运行本脚本。' -ForegroundColor Red
        exit 1
    }
}

# 5. 备份 + 写入书签
$backupFile = "$bookmarkFile.bak-$((Get-Date).ToString('yyyyMMddHHmmss'))"
Copy-Item $bookmarkFile $backupFile -Force
Write-Host "[3/4] 已备份原书签到: $backupFile"

try {
    $j = Get-Content $bookmarkFile -Raw -Encoding UTF8 | ConvertFrom-Json
} catch {
    Write-Host '[错误] 书签文件解析失败（JSON 损坏？）。已备份原文件，请手动检查。' -ForegroundColor Red
    exit 1
}

$bar = $j.roots.bookmark_bar
$existing = @($bar.children | Where-Object { $_.name -eq '下载B站视频' })

if ($existing.Count -gt 0) {
    $existing[0].url = $bookmarkUrl
    Write-Host '[4/4] 已更新现有书签「下载B站视频」'
} else {
    $maxId = 0
    foreach ($c in @($bar.children)) {
        try { if ([int64]$c.id -gt $maxId) { $maxId = [int64]$c.id } } catch {}
    }
    $node = [pscustomobject]@{
        date_added     = (([DateTimeOffset]::UtcNow.Ticks - 621355968000000000) * 10).ToString()
        date_last_used = '0'
        guid           = [guid]::NewGuid().ToString()
        id             = $maxId + 1
        name           = '下载B站视频'
        type           = 'url'
        url            = $bookmarkUrl
    }
    $bar.children = @($bar.children) + $node
    Write-Host '[4/4] 已添加新书签「下载B站视频」'
}

# 写回（必须是 UTF-8 无 BOM，Chrome 才能解析）
$jsonText = $j | ConvertTo-Json -Depth 100
[System.IO.File]::WriteAllText($bookmarkFile, $jsonText, (New-Object System.Text.UTF8Encoding($false)))

Write-Host ''
Write-Host '✅ 安装成功！' -ForegroundColor Green
Write-Host '现在重新打开浏览器（Ctrl+Shift+B 显示书签栏），就能在书签栏看到「下载B站视频」。'
Write-Host '在B站看视频时点它：自动下载当前视频；如果它属于某个合集，会自动把整个合集全部下载。'
Write-Host ''
