#!/bin/bash
# 单篇笔记的拟人化浏览循环（macOS / Linux）
#   搜索关键词 -> 优先挑穿搭/时尚博主类笔记 -> 随机停留与滚动 -> 可选"漫无目的"行为
#
# 用法: browse_note.sh <关键词> [wander]
#   wander=1 表示本篇结束后额外做一次漫无目的行为（回首页/刷新/静置 30-60s）
#
# 依赖环境变量（调用方导出，详见 references/troubleshooting.md）:
#   AGENT_BROWSER_EXECUTABLE_PATH  正式版 Chrome 二进制（关键！Chrome for Testing 会被拦截）
#   AGENT_BROWSER_PROFILE          带登录态的持久化配置目录
#   AGENT_BROWSER_HEADED=1         可视化窗口
#   LOG                            会话日志，用于会话内去重（默认 /tmp/xhs_session_log.jsonl）
#
# 输出: 一行 JSON（关键词、停留、滚动、标题、URL）

set -uo pipefail

KW="${1:?用法: browse_note.sh <关键词> [wander] [mode]}"
WANDER="${2:-0}"
# mode: search（默认，按关键词搜索页进入）| feed（首页信息流，用于会话开头的"热身"浏览）
MODE="${3:-search}"
AB="${AGENT_BROWSER_BIN:-agent-browser}"
PY="${PYTHON_BIN:-python3}"
LOG="${LOG:-/tmp/xhs_session_log.jsonl}"
# 跨会话去重记录（默认 ~/.workbuddy/xhs-seen-urls.txt，最多保留最近 2000 条）
SEEN_FILE="${XHS_SEEN_FILE:-$HOME/.workbuddy/xhs-seen-urls.txt}"
mkdir -p "$(dirname "$SEEN_FILE")" 2>/dev/null || true
touch "$SEEN_FILE" 2>/dev/null || true

# 1) 打开入口页：搜索结果页 或 首页信息流
if [ "$MODE" = "feed" ]; then
  "$AB" open "https://www.xiaohongshu.com/explore" >/dev/null 2>&1
  # 首页流需要滚动一下才加载出更多卡片
  sleep 4
  "$AB" scroll down $((200 + RANDOM % 400)) >/dev/null 2>&1
  sleep 2
else
  enc=$("$PY" -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$KW")
  "$AB" open "https://www.xiaohongshu.com/search_result?keyword=${enc}&source=web_search_result_notes" >/dev/null 2>&1
  sleep $((3 + RANDOM % 4))
fi

# 2) 抓取候选笔记（标题 + 带 xsec_token 的链接）
#    注意：卡片里第一个 <a> 是无 token 的 /explore/<id>，打开必得 300031，必须取带 xsec_token 的那个
JS='(()=>{const out=[];[...document.querySelectorAll("section.note-item")].slice(0,12).forEach(c=>{const a=c.querySelector("a[href*=xsec_token]");if(!a)return;const t=c.querySelector("span.title")||c.querySelector("a[href*=xsec_token] span")||c.querySelector("span");out.push({href:a.getAttribute("href"),title:t?t.innerText:""});});return JSON.stringify(out);})()'

# 3) 选一篇：跳过已看过的；搜索模式下优先垂类关键词命中项，首页模式纯随机
[ "$MODE" = "feed" ] && export PREFER=0 || export PREFER=1
pick=$("$AB" eval "$JS" 2>/dev/null | tail -1 | "$PY" -c '
import sys, json, random, re, os
# 去重来源：本次会话日志 + 跨会话历史记录
seen = set()
for path in (os.environ.get("LOG", "/tmp/xhs_session_log.jsonl"),
             os.environ.get("XHS_SEEN_FILE", os.path.expanduser("~/.workbuddy/xhs-seen-urls.txt"))):
    if path and os.path.exists(path):
        try:
            for line in open(path, encoding="utf-8", errors="ignore"):
                m = re.search(r"\"url\":\"([^\"]+)\"", line)
                if m:
                    seen.add(m.group(1).split("?")[0])
                elif line.strip() and not line.startswith("{"):
                    seen.add(line.strip().split("?")[0])
        except Exception:
            pass
raw = sys.stdin.read().strip()
v = None
for _ in range(2):
    try:
        v = json.loads(raw)
    except Exception:
        v = None
    if isinstance(v, str):
        raw = v
        continue
    break
items = v if isinstance(v, list) else []
# 首页热身浏览不套用垂类偏好，纯随机（真人刷首页就是这样）
prefer = os.environ.get("PREFER", "1") != "0"
pat = re.compile("博主|OOTD|穿搭|时尚|同款|搭配|灵感|每日|衣品|显高|显瘦|ootd", re.I)
pref = [i for i in items if prefer and pat.search(i.get("title") or "")]
pool = [i for i in (pref or items) if (i.get("href") or "").split("?")[0] not in seen]
if not pool:
    pool = pref or items
if not pool:
    sys.exit(0)
p = random.choice(pool)
print((p.get("href") or "") + "\t" + (p.get("title") or "").replace("\t", " ").replace("\n", " "))
')

href="${pick%%$'\t'*}"
title="${pick##*$'\t'}"

# 4) 打开笔记，落到 404（300031）时换一篇，最多重试 3 次
url=""
for _ in 1 2 3; do
  if [ -z "$href" ] || [ "$href" = "$title" ]; then
    href=$("$AB" eval "$JS" 2>/dev/null | tail -1 | "$PY" -c 'import sys,json,random;raw=sys.stdin.read().strip();v=None
for _ in range(2):
    try: v=json.loads(raw)
    except Exception: v=None
    if isinstance(v,str): raw=v; continue
    break
items=v if isinstance(v,list) else []
print(random.choice(items).get("href","") if items else "")')
    [ -z "$href" ] && continue
  fi
  case "$href" in http*) ;; *) href="https://www.xiaohongshu.com${href}" ;; esac
  "$AB" open "$href" >/dev/null 2>&1
  sleep 4
  cur=$("$AB" get url 2>/dev/null | tail -1)
  if [ -n "$title" ]; then :; else title=$("$AB" get title 2>/dev/null | tail -1 | tr -d '"' | tr '\n' ' '); fi
  case "$cur" in *"/404"*|*"error_code"*) href=""; title=""; continue ;; esac
  url="$cur"
  break
done

# 5) 停留时长：模拟"多数快刷、少数细读"
r=$((RANDOM % 100))
if [ "$r" -lt 60 ]; then
  dwell=$((20 + RANDOM % 21)); sc=$((2 + RANDOM % 2))
elif [ "$r" -lt 90 ]; then
  dwell=$((45 + RANDOM % 36)); sc=$((2 + RANDOM % 3))
else
  dwell=$((90 + RANDOM % 61)); sc=$((4 + RANDOM % 3))
fi
interval=$((dwell / sc)); [ "$interval" -lt 3 ] && interval=3

for _ in $(seq 1 "$sc"); do
  sleep $((interval + RANDOM % 4))
  "$AB" scroll down $((300 + RANDOM % 301)) >/dev/null 2>&1
done

# 6) 15% 概率小幅回滚
if [ $((RANDOM % 100)) -lt 15 ]; then
  sleep 2
  "$AB" scroll up $((100 + RANDOM % 101)) >/dev/null 2>&1
fi
sleep 2

# 7) 看评论（真人阅读的重要特征）：滚到评论区，停留 5-15s，偶尔再看两屏
viewed_comments=0
if [ $((RANDOM % 100)) -lt 70 ]; then
  "$AB" scroll down 2000 >/dev/null 2>&1
  sleep 3
  viewed_comments=1
  sleep $((5 + RANDOM % 11))
  if [ $((RANDOM % 100)) -lt 40 ]; then
    "$AB" scroll down $((300 + RANDOM % 301)) >/dev/null 2>&1
    sleep $((4 + RANDOM % 7))
  fi
  # 40% 概率回滚一点，模拟回头看正文
  if [ $((RANDOM % 100)) -lt 40 ]; then
    "$AB" scroll up $((200 + RANDOM % 301)) >/dev/null 2>&1
    sleep 2
  fi
fi

# 8) 记录已看过的 URL（跨会话去重），只保留最近 2000 条
if [ -n "$url" ]; then
  base="${url%%\?*}"
  printf '%s\n' "$base" >> "$SEEN_FILE"
  tail -n 2000 "$SEEN_FILE" > "${SEEN_FILE}.tmp" 2>/dev/null && mv "${SEEN_FILE}.tmp" "$SEEN_FILE" 2>/dev/null
fi

# 9) 漫无目的行为
if [ "$WANDER" = "1" ]; then
  case $((RANDOM % 3)) in
    0) "$AB" open "https://www.xiaohongshu.com/explore" >/dev/null 2>&1 ;;
    1) sleep $((30 + RANDOM % 31)) ;;
    2) "$AB" reload >/dev/null 2>&1 ;;
  esac
  sleep 3
fi

echo "{\"kw\":\"${KW}\",\"dwell\":${dwell},\"scrolls\":${sc},\"comments\":${viewed_comments},\"title\":\"${title}\",\"url\":\"${url}\"}"
