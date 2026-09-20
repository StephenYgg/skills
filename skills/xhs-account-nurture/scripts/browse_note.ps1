# 单篇笔记的拟人化浏览循环（Windows / PowerShell）
#   搜索关键词 -> 优先挑穿搭/时尚博主类笔记 -> 随机停留与滚动 -> 可选"漫无目的"行为
#
# 用法:
#   powershell -ExecutionPolicy Bypass -File browse_note.ps1 -Keyword "穿搭博主" [-Wander 1]
#
# 依赖环境变量（调用前设置，详见 references/troubleshooting.md 第 8 节）:
#   $env:AGENT_BROWSER_EXECUTABLE_PATH = "C:\Program Files\Google\Chrome\Application\chrome.exe"
#   $env:AGENT_BROWSER_PROFILE         = "$env:USERPROFILE\.workbuddy\xhs-chrome-profile"
#   $env:AGENT_BROWSER_HEADED          = "1"
#   $env:LOG                           = "$env:TEMP\xhs_session_log.jsonl"   # 会话日志，用于去重
#
# 输出: 一行 JSON（关键词、停留、滚动、标题、URL），并追加到 $env:LOG

param(
    [Parameter(Mandatory = $true)][string]$Keyword,
    [int]$Wander = 0,
    # search：按关键词搜索页进入（默认）；feed：首页信息流，用于会话开头的热身浏览
    [string]$Mode = "search"
)

$ErrorActionPreference = "Continue"
$ab = if ($env:AGENT_BROWSER_BIN) { $env:AGENT_BROWSER_BIN } else { "agent-browser" }
$log = if ($env:LOG) { $env:LOG } else { Join-Path $env:TEMP "xhs_session_log.jsonl" }
# 跨会话去重记录（默认 %USERPROFILE%\.workbuddy\xhs-seen-urls.txt，只保留最近 2000 条）
$seenFile = if ($env:XHS_SEEN_FILE) { $env:XHS_SEEN_FILE } else { Join-Path $env:USERPROFILE ".workbuddy\xhs-seen-urls.txt" }
if (-not (Test-Path $seenFile)) { New-Item -ItemType File -Path $seenFile -Force | Out-Null }

# 1) 打开入口页：搜索结果页 或 首页信息流
if ($Mode -eq "feed") {
    & $ab open "https://www.xiaohongshu.com/explore" | Out-Null
    Start-Sleep -Seconds 4
    & $ab scroll down (200 + (Get-Random -Maximum 400)) | Out-Null
    Start-Sleep -Seconds 2
} else {
    $enc = [uri]::EscapeDataString($Keyword)
    & $ab open "https://www.xiaohongshu.com/search_result?keyword=$enc&source=web_search_result_notes" | Out-Null
    Start-Sleep -Seconds (3 + (Get-Random -Maximum 4))
}

# 2) 抓取候选（只取带 xsec_token 的链接；无 token 的 /explore/<id> 会返回 300031）
$js = '(()=>{const out=[];[...document.querySelectorAll("section.note-item")].slice(0,12).forEach(c=>{const a=c.querySelector("a[href*=xsec_token]");if(!a)return;const t=c.querySelector("span.title")||c.querySelector("a[href*=xsec_token] span")||c.querySelector("span");out.push({href:a.getAttribute("href"),title:t?t.innerText:""});});return JSON.stringify(out);})()'
$raw = & $ab eval $js
$text = ($raw | Where-Object { $_ -and $_.Trim() -ne "" } | Select-Object -Last 1)

$items = @()
if ($text) {
    try {
        $parsed = $text | ConvertFrom-Json
        if ($parsed -is [string]) { $parsed = $parsed | ConvertFrom-Json }
        $items = @($parsed)
    } catch { $items = @() }
}

# 3) 选一篇：优先穿搭/时尚博主类，跳过本次会话与历史已看过的
$seen = @()
foreach ($f in @($log, $seenFile)) {
    if (Test-Path $f) {
        Get-Content $f -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_ -match '"url":"([^"]+)"') { $seen += $matches[1].Split("?")[0] }
            elseif ($_.Trim() -and -not $_.StartsWith("{")) { $seen += $_.Trim().Split("?")[0] }
        }
    }
}
# 首页热身不套用垂类偏好，纯随机（真人刷首页就是这样）
if ($Mode -eq "feed") {
    $pref = @()
} else {
    $pref = @($items | Where-Object { $_.title -match '博主|OOTD|穿搭|时尚|同款|搭配|灵感|每日|衣品|显高|显瘦' })
}
$pool = @($pref | Where-Object { $seen -notcontains ($_.href.Split("?")[0]) })
if ($pool.Count -eq 0) { $pool = $pref }
if ($pool.Count -eq 0) { $pool = $items }

$href = ""
$title = ""
if ($pool.Count -gt 0) {
    $pick = $pool | Get-Random
    $href = $pick.href
    $title = $pick.title
}

# 4) 打开笔记，落到 404 时换一篇，最多 3 次
$url = ""
for ($i = 0; $i -lt 3; $i++) {
    if (-not $href) { break }
    if ($href -notmatch '^http') { $href = "https://www.xiaohongshu.com$href" }
    & $ab open $href | Out-Null
    Start-Sleep -Seconds 4
    $cur = (& $ab get url | Select-Object -Last 1)
    if ($cur -match '/404|error_code') { $href = ""; $title = ""; continue }
    if (-not $title) { $title = (& $ab get title | Select-Object -Last 1) }
    $url = $cur
    break
}

# 5) 停留时长：多数快刷、少数细读
$r = Get-Random -Maximum 100
if ($r -lt 60) {
    $dwell = 20 + (Get-Random -Maximum 21); $sc = 2 + (Get-Random -Maximum 2)
} elseif ($r -lt 90) {
    $dwell = 45 + (Get-Random -Maximum 36); $sc = 2 + (Get-Random -Maximum 3)
} else {
    $dwell = 90 + (Get-Random -Maximum 61); $sc = 4 + (Get-Random -Maximum 3)
}
$interval = [math]::Max(3, [math]::Floor($dwell / $sc))
for ($i = 0; $i -lt $sc; $i++) {
    Start-Sleep -Seconds ($interval + (Get-Random -Maximum 4))
    & $ab scroll down (300 + (Get-Random -Maximum 301)) | Out-Null
}

# 6) 15% 概率小幅回滚
if ((Get-Random -Maximum 100) -lt 15) {
    Start-Sleep -Seconds 2
    & $ab scroll up (100 + (Get-Random -Maximum 101)) | Out-Null
}
Start-Sleep -Seconds 2

# 7) 看评论（真人阅读的重要特征）：滚到评论区停留 5-15s，偶尔多看一屏
$viewedComments = 0
if ((Get-Random -Maximum 100) -lt 70) {
    & $ab scroll down 2000 | Out-Null
    Start-Sleep -Seconds 3
    $viewedComments = 1
    Start-Sleep -Seconds (5 + (Get-Random -Maximum 11))
    if ((Get-Random -Maximum 100) -lt 40) {
        & $ab scroll down (300 + (Get-Random -Maximum 301)) | Out-Null
        Start-Sleep -Seconds (4 + (Get-Random -Maximum 7))
    }
    if ((Get-Random -Maximum 100) -lt 40) {
        & $ab scroll up (200 + (Get-Random -Maximum 301)) | Out-Null
        Start-Sleep -Seconds 2
    }
}

# 8) 记录已看过的 URL（跨会话去重），只保留最近 2000 条
if ($url) {
    $base = $url.Split("?")[0]
    Add-Content -Path $seenFile -Value $base -Encoding utf8
    $all = Get-Content $seenFile -ErrorAction SilentlyContinue
    if ($all.Count -gt 2000) { Set-Content -Path $seenFile -Value ($all | Select-Object -Last 2000) -Encoding utf8 }
}

# 9) 漫无目的行为
if ($Wander -eq 1) {
    switch (Get-Random -Maximum 3) {
        0 { & $ab open "https://www.xiaohongshu.com/explore" | Out-Null }
        1 { Start-Sleep -Seconds (30 + (Get-Random -Maximum 31)) }
        2 { & $ab reload | Out-Null }
    }
    Start-Sleep -Seconds 3
}

$row = [ordered]@{ kw = $Keyword; dwell = $dwell; scrolls = $sc; comments = $viewedComments; title = $title; url = $url }
$line = $row | ConvertTo-Json -Compress
Add-Content -Path $log -Value $line -Encoding utf8
Write-Output $line
