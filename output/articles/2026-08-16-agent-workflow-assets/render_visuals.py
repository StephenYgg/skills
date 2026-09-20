#!/usr/bin/env python3
"""Render deterministic editorial images for the AI Agent article."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1200
HEIGHT = 675
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
OUT = Path(__file__).resolve().parent / "assets"

INK = "#17212B"
PAPER = "#F7F8FA"
WHITE = "#FFFFFF"
CYAN = "#22B8CF"
CORAL = "#FF6B5F"
YELLOW = "#F4C95D"
GREEN = "#38A169"
BLUE = "#3B82F6"
MUTED = "#687584"
LINE = "#D8DEE6"


def font(size):
    return ImageFont.truetype(FONT_PATH, size=size)


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw, xy, value, size, fill=INK, anchor=None):
    draw.text(xy, value, font=font(size), fill=fill, anchor=anchor)


def save(image, name):
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / name, format="PNG", optimize=True)


def render_cover():
    image = Image.new("RGB", (WIDTH, HEIGHT), INK)
    draw = ImageDraw.Draw(image)

    rounded(draw, (72, 62, 500, 112), 8, CYAN)
    text(draw, (92, 74), "TECH SIGNALS  |  2026.08.09-13", 22, INK)
    text(draw, (72, 160), "AI Agent 的", 68, WHITE)
    text(draw, (72, 242), "新战场", 86, YELLOW)
    text(draw, (76, 370), "真正值钱的不是模型", 34, WHITE)
    text(draw, (76, 420), "而是上下文与工作流", 34, WHITE)
    text(draw, (76, 548), "5 天  |  174 条信息  |  6 个高频项目", 24, "#B9C3CD")

    stages = [
        ("模型", BLUE, 510),
        ("技能", CYAN, 420),
        ("上下文", YELLOW, 330),
        ("编排", CORAL, 240),
    ]
    for index, (label, color, y) in enumerate(stages):
        x = 745 + index * 80
        draw.line((720, y + 35, x, y + 35), fill="#52606D", width=5)
        rounded(draw, (x, y, x + 190, y + 72), 18, color)
        text(draw, (x + 95, y + 36), label, 30, INK, anchor="mm")
    draw.line((720, 545, 1080, 185), fill=WHITE, width=3)
    draw.polygon([(1080, 185), (1056, 193), (1072, 210)], fill=WHITE)

    save(image, "cover.png")


def render_frequency():
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)
    text(draw, (70, 55), "五份技术日报里的高频 Agent 项目", 42)
    text(draw, (72, 110), "出现天数，只表示采集窗口内的重复信号，不代表产品排名", 23, MUTED)

    data = [
        ("agent-skills", 4, CYAN),
        ("prime-agent", 4, BLUE),
        ("agency-agents", 4, CORAL),
        ("code-graph-rag", 3, GREEN),
        ("semantica", 3, YELLOW),
        ("paperclip", 3, "#9B7EDE"),
    ]
    left = 300
    top = 180
    bar_width = 165
    for index, (label, count, color) in enumerate(data):
        y = top + index * 72
        text(draw, (70, y + 22), label, 24, INK)
        rounded(draw, (left, y, left + bar_width * 5, y + 42), 10, "#E5E9EF")
        rounded(draw, (left, y, left + bar_width * count, y + 42), 10, color)
        text(draw, (left + bar_width * count - 20, y + 21), str(count), 24, INK, anchor="mm")

    for day in range(1, 6):
        x = left + bar_width * day
        text(draw, (x - bar_width / 2, 626), f"{day} 天", 18, MUTED, anchor="mm")

    save(image, "figure-01.png")


def render_stack():
    image = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)
    text(draw, (70, 50), "Agent 的价值，正在向模型之上堆叠", 42)
    text(draw, (72, 104), "模型决定能力上限，持久资产决定能否稳定工作", 23, MUTED)

    layers = [
        ("治理与控制", "目标、预算、成本、审计", CORAL),
        ("项目上下文", "代码图谱、来源、决策历史", YELLOW),
        ("技能与规则", "流程、角色、质量门槛", CYAN),
        ("基础模型", "推理、生成、工具调用", BLUE),
    ]
    for index, (title, desc, color) in enumerate(layers):
        y = 175 + index * 105
        inset = index * 34
        rounded(draw, (95 + inset, y, 700 - inset, y + 76), 14, color)
        text(draw, (130 + inset, y + 19), title, 29, INK)
        text(draw, (365 + inset, y + 23), desc, 21, INK)

    draw.line((790, 555, 790, 205), fill=INK, width=5)
    draw.polygon([(790, 180), (775, 210), (805, 210)], fill=INK)
    text(draw, (830, 210), "越往上", 26, INK)
    text(draw, (830, 250), "越接近真实工作", 30, CORAL)
    text(draw, (830, 322), "越难迁移", 26, INK)
    text(draw, (830, 362), "也越需要用户掌控", 30, BLUE)

    save(image, "figure-02.png")


def render_checklist():
    image = Image.new("RGB", (WIDTH, HEIGHT), INK)
    draw = ImageDraw.Draw(image)
    text(draw, (70, 52), "选择 Agent 工具，先问这四件事", 43, WHITE)
    text(draw, (72, 108), "演示效果会过期，可迁移能力才决定长期成本", 23, "#B9C3CD")

    cards = [
        ("01", "规则能否导出？", "技能、提示和流程不应被锁住", CYAN),
        ("02", "上下文归谁保存？", "历史、项目知识和权限必须可控", YELLOW),
        ("03", "执行能否审计？", "知道做了什么、为何做、花了多少", CORAL),
        ("04", "模型能否替换？", "更换底座后，工作资产仍然可用", GREEN),
    ]
    positions = [(70, 185), (625, 185), (70, 405), (625, 405)]
    for (number, title, desc, color), (x, y) in zip(cards, positions):
        rounded(draw, (x, y, x + 505, y + 170), 16, WHITE)
        rounded(draw, (x + 24, y + 24, x + 88, y + 88), 12, color)
        text(draw, (x + 56, y + 56), number, 24, INK, anchor="mm")
        text(draw, (x + 112, y + 28), title, 28, INK)
        text(draw, (x + 112, y + 78), desc, 20, MUTED)

    save(image, "figure-03.png")


def main():
    render_cover()
    render_frequency()
    render_stack()
    render_checklist()


if __name__ == "__main__":
    main()
