# 养号会话调度（Windows / PowerShell）：跑 N 篇，随机关键词、随机穿插漫无目的行为
#
# 用法:
#   powershell -ExecutionPolicy Bypass -File run_session.ps1 -Count 5 -Keywords "穿搭博主","时尚博主","OOTD","每日穿搭"
#
# 节奏建议：单次会话 15-30 分钟，每段 4-5 篇（约 5 分钟），分段调用。
# 依赖环境变量同 browse_note.ps1（正式版 Chrome 路径、配置副本、HEADED、LOG）。

param(
    [int]$Count = 5,
    [string[]]$Keywords = @()
)

$ErrorActionPreference = "Continue"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$noteScript = Join-Path $dir "browse_note.ps1"

# 未显式传入关键词时：从关键词池随机抽 7 个主词 + 3 个推断词
if ($Keywords.Count -eq 0) {
    $kwFile = if ($env:XHS_KEYWORDS_FILE) { $env:XHS_KEYWORDS_FILE } else { Join-Path $env:USERPROFILE ".workbuddy\xhs-keywords.json" }
    $defaultPool = Join-Path (Split-Path -Parent $dir) "assets\keywords-pool.json"
    $poolFile = $null
    foreach ($f in @($kwFile, $defaultPool)) { if ($f -and (Test-Path $f)) { $poolFile = $f; break } }
    if ($poolFile) {
        $data = Get-Content $poolFile -Raw -Encoding utf8 | ConvertFrom-Json
        $pool = @($data.pool)
        $inferred = @($data.inferred)
        $picks = @()
        if ($pool.Count -gt 0) { $picks += ($pool | Get-Random -Count ([Math]::Min(7, $pool.Count))) }
        if ($inferred.Count -gt 0) { $picks += ($inferred | Get-Random -Count ([Math]::Min(3, $inferred.Count))) }
        $Keywords = @($picks | Sort-Object { Get-Random })
    } else {
        $Keywords = @("穿搭博主", "时尚博主", "OOTD", "每日穿搭", "通勤穿搭")
    }
}

Write-Host "[关键词] 本次会话使用 $($Keywords.Count) 个: $($Keywords -join ' / ')" -ForegroundColor DarkCyan

# 热身：先看首页推荐若干篇（会话第一段建议 $env:WARMUP = 2 或 3，后续段设为 0）
$warmup = 0
if ($env:WARMUP) { $warmup = [int]$env:WARMUP }
for ($w = 1; $w -le $warmup; $w++) {
    Write-Host "[$(Get-Date -Format HH:mm:ss)] 热身 $w/$warmup | 入口=首页推荐" -ForegroundColor DarkGray
    & powershell -ExecutionPolicy Bypass -File $noteScript -Keyword "首页推荐" -Wander 0 -Mode feed
}

for ($i = 1; $i -le $Count; $i++) {
    $kw = $Keywords | Get-Random
    $wander = 0
    if ((Get-Random -Maximum 3) -eq 0) { $wander = 1 }
    if ($i -eq $Count) { $wander = 1 }
    Write-Host "[$(Get-Date -Format HH:mm:ss)] 第 $i/$Count 篇 | 关键词=$kw | wander=$wander" -ForegroundColor DarkGray
    & powershell -ExecutionPolicy Bypass -File $noteScript -Keyword $kw -Wander $wander
}
