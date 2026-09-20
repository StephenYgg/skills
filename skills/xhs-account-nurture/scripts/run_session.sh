#!/bin/bash
# 养号会话调度：跑 N 篇笔记，随机关键词、随机穿插漫无目的行为
#
# 用法:
#   bash run_session.sh <篇数> [关键词1 关键词2 ...]
#   例: bash run_session.sh 5 穿搭博主 时尚博主 OOTD
#   不传关键词时：从关键词池随机抽 7 个主词 + 3 个推断词（避免每次都是同一批词）
#
# 关键词池优先级:
#   1) $XHS_KEYWORDS_FILE（默认 ~/.workbuddy/xhs-keywords.json，初始化流程生成）
#   2) 技能自带 assets/keywords-pool.json（默认穿搭/时尚博主向）
#
# 依赖环境变量（必须导出，详见 references/troubleshooting.md）:
#   AGENT_BROWSER_EXECUTABLE_PATH  正式版 Chrome 二进制路径（关键！Chrome for Testing 会被拦截）
#   AGENT_BROWSER_PROFILE          带登录态的持久化配置目录
#   AGENT_BROWSER_HEADED=1         可视化窗口
#   LOG                            结果日志路径（默认 /tmp/xhs_session_log.jsonl）
#
# 节奏建议：单次会话 15-30 分钟，约 4-5 篇为一段，分段调用本脚本。

set -uo pipefail

N="${1:-5}"
shift || true
# WARMUP: 本段开始前先看 N 篇首页推荐（真人习惯：先随手刷两下首页，再主动搜索）
WARMUP="${WARMUP:-0}"

SCRIPT="$(dirname "$0")/browse_note.sh"
LOG="${LOG:-/tmp/xhs_session_log.jsonl}"
PY="${PYTHON_BIN:-python3}"
KW_FILE="${XHS_KEYWORDS_FILE:-$HOME/.workbuddy/xhs-keywords.json}"
DEFAULT_POOL="$(dirname "$0")/../assets/keywords-pool.json"

if [ "$#" -gt 0 ]; then
  KWS=("$@")
else
  # 7 个主词 + 3 个推断词，顺序打乱
  # 注意：macOS 自带 bash 3.2 不支持 mapfile，且不支持在进程替换里嵌套 heredoc，故落临时文件再读取
  _tmp=$(mktemp)
  "$PY" - "$KW_FILE" "$DEFAULT_POOL" > "$_tmp" <<'PYEOF'
import json, os, random, sys
kw_file, default_pool = sys.argv[1], sys.argv[2]
data = None
for p in (kw_file, default_pool):
    if p and os.path.exists(p):
        try:
            data = json.load(open(p, encoding="utf-8"))
            break
        except Exception:
            continue
if not data:
    data = {"pool": ["穿搭博主", "时尚博主", "OOTD", "每日穿搭"], "inferred": ["今日OOTD分享"]}
pool = data.get("pool", [])
inferred = data.get("inferred", [])
picks = random.sample(pool, min(7, len(pool))) if pool else []
picks += random.sample(inferred, min(3, len(inferred))) if inferred else []
random.shuffle(picks)
print("\n".join(picks))
PYEOF
  KWS=()
  while IFS= read -r _line; do
    [ -n "$_line" ] && KWS+=("$_line")
  done < "$_tmp"
  rm -f "$_tmp"
fi

echo "[关键词] 本次会话使用 ${#KWS[@]} 个: ${KWS[*]}" >&2
touch "$LOG"

# 热身：先看首页推荐若干篇（会话第一段建议 WARMUP=2~3，后续段为 0）
if [ "$WARMUP" -gt 0 ]; then
  for w in $(seq 1 "$WARMUP"); do
    echo "[$(date +%H:%M:%S)] 热身 $w/$WARMUP | 入口=首页推荐" >&2
    "$SCRIPT" "首页推荐" 0 feed >> "$LOG"
  done
fi

for i in $(seq 1 "$N"); do
  kw="${KWS[$((RANDOM % ${#KWS[@]}))]}"
  wander=0
  # 约 1/3 概率穿插漫无目的行为；每段最后一篇必定执行一次，保证"每 3-5 篇"的节奏
  [ $((RANDOM % 3)) -eq 0 ] && wander=1
  [ "$i" -eq "$N" ] && wander=1
  echo "[$(date +%H:%M:%S)] 第 $i/$N 篇 | 关键词=$kw | wander=$wander" >&2
  "$SCRIPT" "$kw" "$wander" >> "$LOG"
done
