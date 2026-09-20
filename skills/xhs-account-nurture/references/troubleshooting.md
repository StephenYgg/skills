# 环境准备与常见故障排查

## 1. 首次安装 agent-browser

```bash
# 使用受管 Node 的 npm 做全局安装（避免污染系统环境）
PATH="/Users/stephen/.workbuddy/binaries/node/versions/22.22.2/bin:$PATH" npm install -g agent-browser
PATH="/Users/stephen/.workbuddy/binaries/node/versions/22.22.2/bin:$PATH" agent-browser install   # 下载浏览器运行时
```

安装后 `agent-browser` 位于受管 node 的 bin 目录，命令前需前置 PATH：

```bash
export PATH="/Users/stephen/.workbuddy/binaries/node/versions/22.22.2/bin:$PATH"
```

注意：macOS 无 `timeout` 命令（除非装了 coreutils），不要用它包裹 agent-browser 命令。zsh 下数组下标从 1 开始，需要数组逻辑时用 `bash script.sh` 显式以 bash 运行。

## 2. 关键结论（已实测跑通，务必按此配置）

小红书网页端只放行**正式版 Chrome 二进制**。默认情况下 agent-browser 会使用自己下载的 **Chrome for Testing**，该构建会被小红书识别并拦截，表现为：

```
https://www.xiaohongshu.com/website-login/error?...&error_code=300012&error_msg=IP存在风险，请切换可靠网络环境后重试
```

页面标题显示「安全限制」，且**在任何交互之前就被重定向**。这段文案里的 "IP" 具有误导性——已排除的无关因素：

- 与网络/代理无关（用户自己的 Chrome 走同一网络可正常访问）
- 与登录态无关（未登录的新环境同样被拦，登录后同样被拦）
- 与沙箱执行环境无关（脱离沙箱仍被拦）

**唯一有效的配置组合**：

```bash
export AGENT_BROWSER_EXECUTABLE_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"   # 正式版 Chrome，关键
export AGENT_BROWSER_PROFILE="/Users/stephen/.workbuddy/xhs-chrome-profile"                          # 持久化配置目录，保留登录态
export AGENT_BROWSER_HEADED=1
```

## 3. 准备一份带登录态的配置副本

小红书网页端的登录态存放在 **Local Storage / IndexedDB**（不是 Cookie 表，用 sqlite 查 `Cookies` 文件查不到 xiaohongshu 记录，不要据此判断未登录）。

复制方式（用户的 Chrome 可以继续开着，两个实例各用各的数据目录，互不影响）：

```bash
SRC="$HOME/Library/Application Support/Google/Chrome"
DST="$HOME/.workbuddy/xhs-chrome-profile"
rm -rf "$DST"; mkdir -p "$DST"
rsync -a "$SRC/Local State" "$DST/"
rsync -a --exclude 'Extensions' --exclude 'Service Worker' --exclude 'Code Cache' \
         --exclude 'GPUCache' --exclude 'Cache' --exclude 'Application Cache' \
         --exclude 'Sessions' --exclude 'History' "$SRC/Default" "$DST/"
```

副本约 27MB。登录态验证：启动后打开 `https://www.xiaohongshu.com/explore`，点击侧边栏「我」，若出现头像与小红书号即为已登录。

若需要用户现场登录：保持 `AGENT_BROWSER_HEADED=1`，让用户在可见窗口中扫码即可，登录态会自动写回该配置目录，后续会话长期复用。

## 4. 笔记链接必须携带 xsec_token

小红书网页端的笔记访问强依赖 URL 中的 `xsec_token`。信息流卡片内通常有多个 `<a>`：

| 链接形式 | 结果 |
|----------|------|
| `/explore/<note_id>`（无 token） | 跳转 404，`error_code=300031 当前笔记暂时无法浏览` |
| `/explore/<note_id>?xsec_token=...&xsec_source=...` | 正常打开 |

因此提取卡片链接时必须用 `a[href*=xsec_token]` 选择器，**不要用 `a[href*=explore]`**（会命中无 token 的第一个链接）。卡片结构参考：

```
section.note-item > a[0]=/explore/<id>（无 token）
                  > a[1]=/explore/<id>?xsec_token=...（用这个）
                  > a[3]=/user/profile/...（作者主页）
```

另外，直接 `open` 无 token 链接失败后重试仍会失败，脚本里应做「读取链接 → 带 token 打开 → 校验 URL 未落到 /404 → 否则换一篇」的重试逻辑（见 `scripts/browse_note.sh`）。

## 5. 命令状态不一致时用 batch

`open` 与后续命令之间的"当前页"偶尔不同步（`get url` 读到旧页面）。把相关命令串在一次 batch 执行里可获得一致状态：

```bash
agent-browser batch --bail "open https://www.xiaohongshu.com/explore" "wait 3000" "get url" "get title"
```

`batch` 形式不接收 `--profile`/`--executable-path` 等参数，这些必须通过 `AGENT_BROWSER_*` 环境变量传入。

`snapshot -c` 在 SPA 首屏未渲染完成时可能返回 `(empty page)`，先 `wait 3000` 再抓取。

## 6. 会话收尾

任务结束务必执行，避免僵尸 daemon 与浏览器进程泄漏：

```bash
agent-browser close --all
pkill -f "agent-browser-chrome"      # 兜底清理
```

用同一份配置副本时，close 之后用户自己的 Chrome 不受任何影响（两者数据目录独立）。

若曾用 `dangerouslyDisableSandbox` 启动过用户正式版 Chrome 且带了 `--no-sandbox`，收尾时必须优雅退出（`osascript -e 'tell application "Google Chrome" to quit'`）并用 `open -a "Google Chrome"` 干净重启，恢复默认安全状态。

## 7. Windows 部署（脚本已提供 PowerShell 版）

脚本对应关系：`scripts/browse_note.ps1` + `scripts/run_session.ps1`（Windows）／`scripts/browse_note.sh` + `scripts/run_session.sh`（macOS、Linux）。两版逻辑一致。

安装：

```powershell
npm install -g agent-browser
agent-browser install        # 下载浏览器运行时
```

环境变量（每次会话前设置，注意 Windows 上路径含空格要用引号）：

```powershell
$env:AGENT_BROWSER_EXECUTABLE_PATH = "C:\Program Files\Google\Chrome\Application\chrome.exe"   # 关键：必须是正式版 Chrome
$env:AGENT_BROWSER_PROFILE         = "$env:USERPROFILE\.workbuddy\xhs-chrome-profile"          # 带登录态的配置副本
$env:AGENT_BROWSER_HEADED          = "1"
$env:LOG                           = "$env:TEMP\xhs_session_log.jsonl"
```

准备带登录态的配置副本（可用 Chrome 运行状态，robocopy 复制登录相关文件即可）：

```powershell
$src = "$env:LOCALAPPDATA\Google\Chrome\User Data"
$dst = "$env:USERPROFILE\.workbuddy\xhs-chrome-profile"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item "$src\Local State" $dst -Force
robocopy "$src\Default" "$dst\Default" /E /XD Extensions "Service Worker" "Code Cache" GPUCache Cache "Application Cache" Sessions /XF History /NFL /NDL /NJH /NJS
```

注意：Windows 上 Chrome 用户数据目录是 `%LOCALAPPDATA%\Google\Chrome\User Data`（mac 是 `~/Library/Application Support/Google/Chrome`），其中 `Default` 才是配置文件夹，多配置时可能有 `Profile 1` 等，复制对应那个即可。

执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_session.ps1 -Count 5 -Keywords "穿搭博主","时尚博主","OOTD"
```

Windows 侧差异与坑：

- PowerShell 5.1 起支持 `ConvertFrom-Json`，脚本依赖它解析候选列表；如遇解析失败先确认 `agent-browser eval` 的原始输出未被截断。
- `Start-Sleep` 代替 `sleep`，`Get-Random -Maximum N` 生成 0..N-1，语义与 bash 的 `$RANDOM % N` 一致。
- 使用 `\` 路径分隔符；`-File` 传参数时关键词含空格需加引号。
- 若 PowerShell 执行策略受限，用 `-ExecutionPolicy Bypass`；长期可 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`。
- 同样适用于 Windows 的关键结论：必须用正式版 Chrome，Chrome for Testing 会被 300012 拦截；笔记链接必须带 xsec_token（第 2、4 节）。

## 8. 其他环境细节

- 用 `nohup ... &` 在后台启动浏览器进程会被工具会话回收（进程消失）；需要常驻时改用 `run_in_background` 的参数运行，或直接交给 agent-browser daemon 管理。
- Chrome 开启 `--remote-debugging-port` 时拒绝使用默认数据目录（`DevTools remote debugging requires a non-default data directory`），且在本环境的沙箱内会因 GPU 沙箱失败而崩溃。
- 本机存在 fake-IP（198.18.x.x）TUN 代理层，属正常现象，与小红书拦截无关，不要在这上面浪费排查时间。
