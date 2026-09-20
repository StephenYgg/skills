---
name: xhs-account-nurture
description: 自动浏览小红书网页版笔记，模拟真人使用习惯进行账号养号。当用户提到"小红书养号"、"养号"、"自动刷小红书"、"模拟浏览小红书笔记"、"提升账号活跃度/权重"等需求时使用此技能。基于浏览器自动化实现：随机搜索关键词、打开笔记、模拟阅读停留与滚动、轻度互动（点赞/收藏），行为参数随机化以贴近真人节奏。仅支持单账号、已登录的网页版小红书（xiaohongshu.com）。
agent_created: true
---

# 小红书自动浏览养号

## 概述

通过浏览器自动化驱动小红书网页版（xiaohongshu.com），以随机化、拟人化的方式浏览笔记，帮助账号保持活跃。核心原则：**行为像人，频率克制**——快速、机械、高频的自动化行为容易被风控识别且违反平台规则，务必按本文件的节奏控制参数执行。

## 前置条件

1. **加载 agent-browser 技能**：本技能的所有浏览器操作（打开页面、点击、滚动、截图、等待）均通过 agent-browser 技能完成。执行前必须先调用 Skill 工具加载 `agent-browser`。
2. **配置浏览器环境（决定成败）**：本技能**必须**使用正式版 Chrome 二进制 + 带登录态的配置副本启动，否则小红书会在页面加载前直接返回 `300012` 拦截页（默认的 Chrome for Testing 构建会被识别）。必读 `references/troubleshooting.md` 第 2、3 节，按该节命令准备配置副本并导出环境变量：

   ```bash
   export AGENT_BROWSER_EXECUTABLE_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
   export AGENT_BROWSER_PROFILE="$HOME/.workbuddy/xhs-chrome-profile"   # 带登录态的配置副本
   export AGENT_BROWSER_HEADED=1
   ```
3. **确认登录状态**：打开 `https://www.xiaohongshu.com/explore`，点击侧边栏「我」确认出现头像与小红书号。登录态存放于 Local Storage，**不要用 Cookie 数据库查询来判断是否登录**。未登录时保持可视化窗口，引导用户扫码登录一次，登录态会写回配置目录长期复用。
4. **确认执行环境为用户本人账号**：本技能仅用于用户本人单账号。若用户要求批量操作多个账号或矩阵养号，拒绝并说明风险。

## 第一步：收集养号参数

开始前向用户确认以下参数（若用户未指定则使用默认值）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 养号时长 | 20 分钟 | 单次会话总时长，建议 15–30 分钟 |
| 兴趣关键词 | 穿搭博主 / 时尚博主 / OOTD / 每日穿搭 / 通勤穿搭 / 穿搭灵感 / 早春穿搭 / 博主同款 | 8 个（关键词池 8–10 个可显著降低重复率）。账号定位变更时替换为对应垂类，参考："咖啡探店"、"家居收纳" |
| 内容偏好 | 优先穿搭与时尚博主类 | 脚本在候选中优先挑标题含 "博主/OOTD/穿搭/时尚/同款/搭配/灵感/每日/衣品" 的笔记 |
| 互动开关 | 仅点赞 | 可选：仅浏览 / 点赞 / 点赞+收藏。**禁止自动评论、关注、私信** |
| 互动概率 | 30% | 每篇浏览的笔记执行互动的概率 |

### 关键词初始化（4 + 4 + 2 三段式）

首次养号或账号定位变更时，用**三段式推荐**帮用户凑满约 10 个主关键词（一次性甩 10 个让人挑体验很差）：

1. **第一批 4 个（核心垂类）**：最常见的入口词，如 穿搭博主 / 时尚博主 / OOTD / 每日穿搭
2. **第二批 4 个（细分场景）**：具体场景或风格，如 通勤穿搭 / 早春穿搭 / 韩系穿搭 / 小个子穿搭
3. **第三批 2 个（长尾补充）**：如 博主同款 / 穿搭灵感

每批说明用途，用户可替换其中任意几个。确认后**必须写入** `~/.workbuddy/xhs-keywords.json`：

```json
{
  "pool": ["穿搭博主", "时尚博主", "OOTD", "每日穿搭", "通勤穿搭", "早春穿搭", "韩系穿搭", "小个子穿搭", "博主同款", "穿搭灵感"],
  "inferred": ["今日OOTD分享", "一周穿搭不重样", "上班族穿搭公式", "显高穿搭技巧"],
  "prefer_regex": "博主|OOTD|穿搭|时尚|同款|搭配|灵感|每日|衣品|显高|显瘦|ootd"
}
```

`inferred` 是根据 pool **推断出的扩展词**（更长尾、更口语），供下文"7+3"机制使用，建议给 12–16 个以保证每次抽取不重样。默认模板见 `assets/keywords-pool.json`。

### 每次会话的关键词：7 主 + 3 推断

**不要每次都用同一批固定词**——搜索词完全不变会让行为模式过于规整，容易被判定为机械行为。规则：

- 从 `pool` 随机抽 **7 个**主词；
- 从 `inferred` 随机抽 **3 个**推断词；
- 合并打乱后供本会话随机取用。

`run_session.*` 在不传关键词参数时会自动执行这套抽取。

## 第二步：执行拟人化浏览循环

**直接使用现成脚本，不要手工重复敲命令**。

macOS / Linux：

```bash
LOG=/tmp/xhs_session_log.jsonl bash scripts/run_session.sh 5 \
  穿搭博主 时尚博主 OOTD 每日穿搭 通勤穿搭
```

Windows（PowerShell）：

```powershell
$env:AGENT_BROWSER_EXECUTABLE_PATH = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$env:AGENT_BROWSER_PROFILE         = "$env:USERPROFILE\.workbuddy\xhs-chrome-profile"
$env:AGENT_BROWSER_HEADED          = "1"
$env:LOG                           = "$env:TEMP\xhs_session_log.jsonl"

# 不传 -Keywords 即自动 7 主 + 3 推断
powershell -ExecutionPolicy Bypass -File scripts\run_session.ps1 -Count 5
```

- `run_session.*` `<篇数> [关键词...]`：段调度器。**省略关键词**时按"7 主 + 3 推断"自动抽取，并随机穿插漫无目的行为。
- `browse_note.*` `<关键词> [wander]`：单篇循环，输出一行 JSON（关键词/停留/滚动/标题/URL），两条平台各有一版。

脚本已实现的关键行为（修改前先读 `references/browsing-behavior.md`）：

0. **会话开头先刷首页（热身）**：真人打开小红书的第一个动作是随手刷首页，而不是立刻搜索。**会话第一段必须先浏览 2–3 篇首页推荐**，再进入关键词搜索循环：

   ```bash
   WARMUP=3 bash scripts/run_session.sh 5        # 会话第一段：先热身 3 篇
   WARMUP=0 bash scripts/run_session.sh 5        # 后续各段：不再热身
   ```

   热身篇用 `feed` 模式：**不套用垂类偏好正则**（纯随机，因为首页刷什么看什么），但仍参与去重。Windows 侧用 `$env:WARMUP = 3`。
1. **选择入口**：热身之后按关键词进入搜索结果页（比首页信息流更稳定，且能锚定账号兴趣标签）。关键词按"7 主 + 3 推断"抽取。
2. **选择笔记**：抓取前 12 张卡片，**优先标题命中穿搭/时尚博主正则的候选**；**跳过已看过的笔记**（本次会话日志 + 跨会话历史 `~/.workbuddy/xhs-seen-urls.txt`，两处都查）；随机取一篇。
3. **进入笔记并阅读**：**必须读取带 `xsec_token` 的卡片链接**（选择器 `a[href*=xsec_token]`），无 token 的 `/explore/<id>` 会被返回 `300031`，脚本内置换一篇重试。停留按 "多数快刷、少数细读" 分布取 20–150 秒；期间 2–6 次滚动，每次 300–600 像素，间隔随机；约 15% 概率小幅回滚。
4. **看评论（提升真实性的关键）**：约 70% 概率滚到评论区停留 5–15 秒，其中 40% 再多看一屏、40% 回滚一点看正文。真人阅读笔记时普遍会翻评论，缺失这一环行为会显得机械。
5. **轻度互动**（按互动概率与开关执行）：仅点赞或收藏，每篇最多一个动作；单次会话互动总数不超过浏览笔记数的 40%。
6. **节奏切换**：每 3–5 篇穿插一次"漫无目的"行为（回首页、刷新、静置 30–60 秒）。

会话分段建议：单次 15–30 分钟，每段 4–5 篇（约 5 分钟），分 6 段左右完成，避免单次命令超时。

## 第三步：输出养号报告（Nature Distilled 风格 HTML）

**默认交付一个 HTML 报告**，而不是纯 Markdown。**风格以用户指定的 Nature Distilled 为准**（此前试过日系和风、清新简约，用户均不满意，不要再改回）：

- **样式直接复用 `assets/style-nature-distilled.css`**（从参考稿 `report-gallery/pages/06-nature-distilled.html` 整体抽取的完整 CSS，963 行），生成器原样注入，**不要手写简化版**。
- 关键视觉特征（改版时务必保留）：
  - 陶土色系：terracotta `#C67B5C`、clay `#B5651D`、sand `#D4C4A8`、cream `#F5F0E1`、olive `#6B7B3C`；对比度校验过的文本色 `--clay-deep #8A4A16` / `--olive-deep #4F5C2A` / `--ink #3A322A`。
  - **纸纹颗粒**：全屏 `.grain` 层（feTurbulence 生成的 SVG 噪声，`mix-blend-mode:multiply`，透明度 .1）——这是这套风格的灵魂，不能省。
  - 排版：Lora + Noto Serif SC（衬线）做标题与正文，Raleway + Noto Sans SC（无衬线）做 UI 标签；正文行高 1.95、measure 66ch、大留白；小字号大写字母 + 宽字距（`.kicker` / `.stamp`）。
  - 结构件：固定 topbar、带径向渐变光晕与地层波浪（`.strata`）的封面、圆形编号 `.sec-num`、叶片分隔符 `.rule-leaf`、粘性表头 `table.detail`、波浪分隔的引言带 `.band-quote`。
  - 层次感靠**细线 + 极淡暖色阴影**（`--shadow-soft`），不要冷灰阴影、不要重投影。
- **图形必须用 SVG**：直方图（带渐变柱 + `.gridline`/`.baseline`/`.ax`/`.val`）、环形图（`.donut-box` + `.donut-legend`）、时序折线，全部内联 SVG（不引外部图表库）。
- **必须有交互**：关键词条与 chip 联动筛选明细表、表头排序（`.th-sort`）、行点击展开完整链接（`.linkrow`）、图表 hover tooltip、`.reveal` 滚动入场。数据以 JSON 内联，由 JS 渲染。
- 生成器：`scripts/gen_report.py`（读会话日志直接出报告）。注意 `<html class="no-js">` + 脚本替换为 `js`，否则 `.reveal` 元素会保持透明不可见。
- 内容包含：封面元信息、摘要与 KPI、阅读时长分布、会话时序、关键词分布、逐篇明细、本次踩坑、下次建议、数据来源口径。

`assets/session-report-template.md` 是字段清单（供数据结构对齐用），HTML 才是交付形态。报告生成后用 present_files 打开预览。

## 安全与频率红线（必须遵守）

- 单次会话不超过 30 分钟；同一账号每天最多执行 1 次养号会话。
- 禁止自动评论、自动关注、自动私信、自动发布——这些行为对他人造成打扰且极易触发风控。
- 页面出现验证码、异常登录提示、"操作频繁"等风控信号时，立即停止会话并在报告中记录，告知用户手动处理。
- 提醒用户：自动化操作与小红书用户协议存在冲突风险，可能导致账号限流或封禁，由用户自行权衡使用频率。

## 资源说明

- `scripts/run_session.sh` / `run_session.ps1`：养号段调度器（随机关键词 + 漫无目的行为），第二步直接调用。mac/Linux 用 sh，Windows 用 ps1。
- `scripts/browse_note.sh` / `browse_note.ps1`：单篇笔记拟人化浏览（穿搭博主优先 + 会话去重 + 随机停留滚动 + token 链接重试），被调度器调用。
- `references/browsing-behavior.md`：拟人化行为参数细则（停留时长分布、滚动、节奏随机化规则），调整脚本参数前必读。
- `references/troubleshooting.md`：环境安装、正式版 Chrome 配置、登录态副本、300012/300031 故障处理，首次执行或遇到异常时必读。
- `assets/style-nature-distilled.css`：报告样式资产（Nature Distilled，用户指定风格），生成器注入用。
- `assets/keywords-pool.json`：默认关键词池（10 主词 + 14 推断词 + 偏好正则）。
- `assets/session-report-template.md`：字段清单（供数据结构对齐用），非最终交付形态。
