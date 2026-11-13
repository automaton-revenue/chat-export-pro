#!/usr/bin/env python3
"""Generate the product demo GIF (terminal mock-up) with PIL. One-off build script.

The scenes reproduce the real output of chat_export.py 2.0 on a synthetic
sample export (the same output shape as running the tool on a test fixture),
so the demo stays truthful.
"""

from PIL import Image, ImageDraw, ImageFont

W, H = 860, 520
FONT_PATH = r"C:\Windows\Fonts\consola.ttf"
FONT_BOLD = r"C:\Windows\Fonts\consolab.ttf"

def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_PATH, size)

F_CMD = font(22, True)
F_OUT = font(22)
F_TITLE = font(26, True)
F_SMALL = font(16)

GREEN = (42, 200, 120)
WHITE = (232, 236, 240)
GREY = (120, 128, 140)
BLUE = (110, 170, 255)
BG = (24, 26, 32)
BAR = (38, 41, 50)

SCENES = [
    [
        ("c", "$ python chat_export.py convert conversations.json --outdir backup/", None),
        ("o", "scanning conversations.json ...", 0.9),
        ("o", "   412 conversations found", 0.8),
    ],
    [
        ("c", "$ python chat_export.py convert conversations.json --outdir backup/", None),
        ("o", "scanning conversations.json ...", None),
        ("o", "   412 conversations found", 0.9),
        ("o", "Converted 412 chat(s) from chatgpt format into backup/", 0.8),
        ("o", "  412 Markdown file(s)", 0.7),
        ("g", "  Archive (one file, works offline): backup/index.html", 1.0),
    ],
    [
        ("c", '$ python chat_export.py search backup/ "deploy checklist" -i', None),
        ("o", "deploy-checklist.md:1: # Deploy checklist", 0.6),
        ("o", "deploy-checklist.md:9: - [ ] run the deploy checklist", 0.6),
    ],
]

def render(lines):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # title bar
    d.rectangle([0, 0, W, 46], fill=BAR)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([16 + i * 26, 16, 30 + i * 26, 30], fill=c)
    d.text((W // 2 - 120, 11), "chat-export-pro — demo", font=F_SMALL, fill=GREY)
    y = 78
    for kind, text in lines:
        color, fnt = {"c": (GREEN, F_CMD), "o": (WHITE, F_OUT), "g": (GREEN, F_OUT), "b": (BLUE, F_OUT), "t": (WHITE, F_TITLE)}[kind]
        d.text((36, y), text, font=fnt, fill=color)
        y += 40 if kind != "t" else 52
    # hint
    d.text((36, H - 44),
           "ChatGPT & Claude export  ->  Markdown + searchable offline archive.  Pay what you want",
           font=F_SMALL, fill=GREY)
    return img

frames = []
durations = []

for scene in SCENES:
    shown_lines = []
    for kind, text, hold in scene:
        if text is None:  # command line: show full at once
            shown_lines.append((kind, text))
            continue
        # progressive reveal, chunked to keep the frame count small
        step = max(3, (len(text) + 11) // 12)
        for i in range(step, len(text) + 1, step):
            frames.append(render(shown_lines + [(kind, text[:i])]))
            durations.append(70)
        shown_lines.append((kind, text))
        frames.append(render(shown_lines))
        durations.append(int((hold or 0.5) * 1000))
    frames.append(render(shown_lines))
    durations.append(1200)

frames[0].save(
    "demo.gif", save_all=True, append_images=frames[1:],
    duration=durations, loop=0, optimize=False,
)
print(f"OK: demo.gif with {len(frames)} frames")
