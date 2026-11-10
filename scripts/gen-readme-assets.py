#!/usr/bin/env python3
"""README visuals for dsh-customs-doc-check — read off what the package ships.

Outputs (docs/assets/, idempotent overwrite):

  dsh-customs-doc-check-hero-{zh,en}-{light,dark}.webp   1440x576
  dsh-customs-doc-check-flow-v5-{light,dark}.svg         1100x660

Both figures are derived from this package's own artifacts, not from a generic
checker template:

  * `src/model.ts` — the reader's contract: 17 canonical columns (docKind, docNo,
    hsCode, goodsName, quantity, unit, unitPrice, amount, currency, tradeTerms,
    origin, destination, grossWeight, netWeight, packages, declaredAt, note),
    each with Chinese and English aliases; 5 optional header fields
    (declarationNo, consignee, contractNo, invoiceNo, declaredAt); the material
    is accepted only when at least one known column name is recognised.
  * `src/shared/table.ts` — alias matching lowercases and strips spaces (incl.
    the ideographic space), `_` and `-`.
  * `rules/customs-doc-check.yaml` — pack `2026.1`, 7 rules, all `warn` because
    every basis is `derived-from-principle` (the cap the loader enforces). The
    check kinds are the ones drawn in the flow: presenceAny, pattern (x2),
    unique, fieldComparison, date, containsAny.
  * `samples/quickstart/input/CD-001-unsafe.json` — the row drawn in the hero is
    that file, cell for cell: INV-2026-0001 / 8471300000 / empty goodsName /
    empty amount / USD / 1250.5 & 1180.0 / 2026-03-10.
  * `src/shared/rows.ts` — the two output channels: a rule that cannot run lands
    in `skipped` with its own reason ("材料没有「毛重」列，本条不适用", "该规则
    在当前配置中被禁用", the `only` narrowing reason), and a rule that ran and
    found nothing lands in neither list (explicitly not a skipped rule).
  * `src/view.ts` — the view fields drawn in the report band (summary, issue
    count, skipped count, rulesetVersion, markdown + reportJson), plus the
    wording guard and the mandatory disclaimer.

Hero: left column is the copy block (kicker / two-line wordmark / two value
lines / one subtitle / one meta line / footer). The right side is this plugin's
own artifact: one register row opened up as the eight columns the rules read,
each column tagged with the rule that reads it, the two blank cells marked,
and the CD-001 finding that the blank cells produce beneath.

Flow: grammar = DUAL-CHANNEL CONFLUENCE, not a row of nodes. The material is
normalised into 17 columns, seven rules are dispatched from one rail, and every
rule leaves through one of two channels — `issues[]` for what it found,
`skipped[]` for what it could not run — which converge on a single report band
and end at the reviewer. Nothing is drawn as a straight five-box pipeline.

Every label is measured before it is drawn; a label that would overflow aborts
the run instead of shipping clipped text. Node text inside the 1100px SVG is
12.5-13.5px (figure title 30px) and annotations are >= 11px.

Old single-skin assets (`…-flow.svg`, `…-hero.png`, `…-demo.*`, `quickstart.*`)
are deliberately left on disk so existing external links keep resolving; the
READMEs reference only the new hero and flow-v5 pair.

Run once:  python scripts/gen-readme-assets.py
Requires:  Pillow + Windows fonts msyh.ttc / msyhbd.ttc / consola.ttf.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from html import escape

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")
NAME = "dsh-customs-doc-check"

FONT_FILES = {
    "cjk": r"C:\Windows\Fonts\msyh.ttc",
    "cjk_bold": r"C:\Windows\Fonts\msyhbd.ttc",
    "mono": r"C:\Windows\Fonts\consola.ttf",
    "mono_bold": r"C:\Windows\Fonts\consolab.ttf",
}
for _kind, _path in FONT_FILES.items():
    if not os.path.exists(_path):
        raise SystemExit(f"FATAL: font missing: {_path}")

RADIUS = 20
os.makedirs(OUT, exist_ok=True)

FONT_CSS_SANS = ("'Microsoft YaHei','Segoe UI','PingFang SC',"
                 "'Noto Sans CJK SC',sans-serif")
FONT_CSS_MONO = "Consolas,'Microsoft YaHei',ui-monospace,monospace"

SKIN = {
    "light": dict(
        bg_from="#f9f6fd", bg_to="#e4eaf8",
        card="#ffffff", edge="#e6e2ef",
        text="#141419", sub="#4d5261", faint="#8f94a4",
        accent="#4B67B4", ok="#15803d", warn="#b45309", danger="#b3261e",
        pill="#ece7f9", band="#f5f2fb", grid="#e7e4f0",
        warn_bg="#fbf1e4", miss_bg="#f7f2ea",        shadow=(43, 35, 80), shadow_alpha=52, glow=32,
    ),
    "dark": dict(
        bg_from="#131a2a", bg_to="#0c1016",
        card="#1b2231", edge="#2e374b",
        text="#f0f3f9", sub="#a8b1c4", faint="#737b8d",
        accent="#8496f5", ok="#3fb950", warn="#d9a441", danger="#f0776a",
        pill="#242d42", band="#202839", grid="#2b3348",
        warn_bg="#292217", miss_bg="#2a3040",
        shadow=(0, 0, 0), shadow_alpha=150, glow=44,
    ),
}

FLOW = {
    "light": dict(
        bg_from="#f9f6fd", bg_to="#e4eaf8",
        panel="#ffffff", card="#ffffff", edge="#e6e2ef",
        band="#f5f2fb", pill="#ece7f9", tint="#f7f4ec",
        text="#141419", sub="#4d5261", faint="#8f94a4",
        accent="#4B67B4", ok="#15803d", warn="#b45309",
        rule="#e7e4f0", shadow="#2b2440", shadow_op="0.14",
        dot="#cfc8e2", dot_op="0.5",
    ),
    "dark": dict(
        bg_from="#131a2a", bg_to="#0c1016",
        panel="#1b2231", card="#1b2231", edge="#2e374b",
        band="#202839", pill="#242d42", tint="#2a2419",
        text="#f0f3f9", sub="#a8b1c4", faint="#737b8d",
        accent="#8496f5", ok="#3fb950", warn="#d9a441",
        rule="#2b3348", shadow="#000000", shadow_op="0.52",
        dot="#2a3346", dot_op="0.5",
    ),
}

# ---------------------------------------------------------------------------
# fonts + measuring
# ---------------------------------------------------------------------------
_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}
_MEASURE = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def font(size: float, kind: str = "cjk") -> ImageFont.FreeTypeFont:
    key = (kind, int(round(size)))
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONT_FILES[kind], key[1])
    return _font_cache[key]


def measure(text: str, size: float, kind: str = "cjk") -> float:
    return _MEASURE.textlength(text, font=font(size, kind))


def require_w(text: str, size: float, kind: str, max_w: float,
              what: str) -> None:
    got = measure(text, size, kind)
    if got > max_w + 0.4:
        raise SystemExit(f"FATAL: {what} overflows: {text!r} needs "
                         f"{got:.1f}px > {max_w:.0f}px")


def fit(text: str, kind: str, max_w: float, start: float,
        minimum: float) -> float:
    size = float(start)
    while size > minimum:
        if measure(text, size, kind) <= max_w:
            return size
        size -= 1
    raise SystemExit(f"FATAL: text does not fit {max_w:.0f}px at >= "
                     f"{minimum}px: {text!r}")


def fit_lines(lines: list[str], kind: str, max_w: float, start: float,
              minimum: float) -> float:
    return min(fit(line, kind, max_w, start, minimum) for line in lines)


def hx(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------------------
# raster primitives
# ---------------------------------------------------------------------------
def gradient(w: int, h: int, top: str, bottom: str) -> Image.Image:
    base = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(base)
    a, b = hx(top), hx(bottom)
    for y in range(h):
        t = 0.12 * (y / h) + 0.88 * (y / h) ** 1.3
        draw.line([(0, y), (w, y)],
                  fill=tuple(int(p + (q - p) * t) for p, q in zip(a, b)))
    return base


def glow(img: Image.Image, cx: int, cy: int, r: int, color: str,
         alpha: int) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rgb = hx(color)
    for i in range(10, 0, -1):
        rr = r * i / 10
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                  fill=rgb + (int(alpha * (1 - i / 11)),))
    return Image.alpha_composite(img.convert("RGBA"),
                                 layer.filter(ImageFilter.GaussianBlur(26))
                                 ).convert("RGB")


def card(img: Image.Image, box: tuple[int, int, int, int], s: dict,
         radius: int = RADIUS, shadow: int = 22,
         fill: str | None = None, edge: str | None = None) -> Image.Image:
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x0 + 2, y0 + max(4, shadow // 2), x1 + 2,
                         y1 + max(5, shadow // 2)],
                        radius=radius, fill=s["shadow"] + (s["shadow_alpha"],))
    base = Image.alpha_composite(img.convert("RGBA"),
                                 layer.filter(ImageFilter.GaussianBlur(shadow / 2)))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle(box, radius=radius, fill=hx(fill or s["card"]),
                        outline=hx(edge or s["edge"]), width=2)
    return base.convert("RGB")


def pill(img: Image.Image, xy: tuple[float, float], text: str, s: dict,
         size: float = 16, fg: str | None = None, bg: str | None = None,
         kind: str = "cjk_bold") -> float:
    d = ImageDraw.Draw(img)
    f = font(size, kind)
    w = d.textlength(text, font=f)
    x, y = xy
    h = size + 22
    d.rounded_rectangle([x, y, x + w + 36, y + h], radius=h / 2,
                        fill=hx(bg or s["pill"]))
    d.text((x + 18, y + h / 2), text, font=f, fill=hx(fg or s["accent"]),
           anchor="lm")
    return x + w + 36


def chip_right(img: Image.Image, right: float, y: float, text: str, fg: str,
               bg: str, size: float = 12, height: float = 25,
               kind: str = "mono_bold", pad: float = 10) -> float:
    d = ImageDraw.Draw(img)
    w = d.textlength(text, font=font(size, kind)) + pad * 2
    x = right - w
    d.rounded_rectangle([x, y, right, y + height], radius=height / 2,
                        fill=hx(bg))
    d.text((x + pad, y + height / 2 + 0.5), text, font=font(size, kind),
           fill=hx(fg), anchor="lm")
    return x


def rich_line(img: Image.Image, x: float, y: float,
              runs: list[tuple[str, str, str]], size: float) -> float:
    """Draw runs of (text, colour, kind) left to right; return the end x."""
    d = ImageDraw.Draw(img)
    cursor = float(x)
    for text, color, kind in runs:
        d.text((cursor, y), text, font=font(size, kind), fill=hx(color),
               anchor="ls")
        cursor += measure(text, size, kind)
    return cursor


# ---------------------------------------------------------------------------
# hero copy + the one row the hero opens up
# ---------------------------------------------------------------------------
HERO = {
    "zh": dict(
        kicker="DeepSeek Harness 插件 · 报关单证核查",
        title=("dsh-customs-", "doc-check"),
        value=("逐行核对报关单证台账，", "哪一行、哪一栏、差什么，列清。"),
        sub="栏名中英皆可；只核台账，不判申报真实性。",
        meta=[("customs_doc_check", "mono"),
              (" · 7 条规则 · ", "cjk"),
              ("CD-001..CD-007", "mono")],
        foot="Apache-2.0 · 只读 · 不联网 · 不调用模型 · 不写文件",
        card_title=("rows[0]", "  第 1 行"),
        card_sub="规则读到的 8 个栏目 · 台账共 17 个规范栏目",
        chip_issue="issues 1",
        chip_skip="skipped 0",
        fields=[
            ("单证编号", "INV-2026-0001", "CD-004", False),
            ("商品编号", "8471300000", "CD-002", False),
            ("商品名称", "（空）", "CD-001 · CD-007", True),
            ("总价", "（空）", "CD-001", True),
            ("币制", "USD", "CD-003", False),
            ("毛重 / 净重", "1250.5 / 1180.0", "CD-005", False),
            ("申报日期", "2026-03-10", "CD-006", False),
        ],
        label_x=676, value_x=860, label_kind="cjk", label_size=22,
        empty_text="（空）",
        find_head=("CD-001", "warn", "第 1 行 · goodsName"),
        find_rows=[("found", "第 1 行 goodsName、amount 都为空"),
                   ("expected", "goodsName、amount 至少应填写一项"),
                   ("fix", "补填品名与总价；本条只核对是否填写，不判断申报内容是否真实")],
        find_sizes=(17.5, 16.5, 15.5),
        source="samples/quickstart/input/CD-001-unsafe.json",
        body_kind="cjk",
    ),
    "en": dict(
        kicker="DeepSeek Harness plugin · register check",
        title=("dsh-customs-", "doc-check"),
        value=("Check the register row by row;", "which row, column, what to fix."),
        sub="Chinese or English headers; the register only.",
        meta=[("customs_doc_check", "mono"),
              (" · 7 rules · ", "cjk"),
              ("CD-001..CD-007", "mono")],
        foot="Apache-2.0 · read-only · no network · no model call",
        card_title=("rows[0]", "  row 1"),
        card_sub="the 8 columns the rules read · 17 canonical columns in all",
        chip_issue="issues 1",
        chip_skip="skipped 0",
        fields=[
            ("docNo", "INV-2026-0001", "CD-004", False),
            ("hsCode", "8471300000", "CD-002", False),
            ("goodsName", "(empty)", "CD-001 · CD-007", True),
            ("amount", "(empty)", "CD-001", True),
            ("currency", "USD", "CD-003", False),
            ("grossWeight / netWeight", "1250.5 / 1180.0", "CD-005", False),
            ("declaredAt", "2026-03-10", "CD-006", False),
        ],
        label_x=676, value_x=966, label_kind="mono", label_size=20,
        empty_text="(empty)",
        find_head=("CD-001", "warn", "row 1 · goodsName"),
        find_rows=[("found", "goodsName and amount are both empty on row 1"),
                   ("expected", "at least one of the two must be filled"),
                   ("fix", "fill in the goods name and the amount; presence only")],
        find_sizes=(16.5, 16, 15.5),
        source="samples/quickstart/input/CD-001-unsafe.json",
        body_kind="cjk",
    ),
}


def hero(lang: str, skin: str) -> None:
    s = SKIN[skin]
    h = HERO[lang]
    W, H = 1440, 576
    img = gradient(W, H, s["bg_from"], s["bg_to"])
    img = glow(img, 1170, 40, 420, s["accent"], s["glow"])
    img = glow(img, 150, 560, 300, s["accent"], max(8, s["glow"] // 3))

    m, col_w = 56, 558
    d = ImageDraw.Draw(img)

    # ---- left copy column ---------------------------------------------------
    kicker_w = measure(h["kicker"], 19, "cjk_bold") + 36
    if kicker_w > 600:
        raise SystemExit(f"FATAL: kicker pill {kicker_w:.0f}px wide")
    pill(img, (m, 44), h["kicker"], s, size=19)
    d = ImageDraw.Draw(img)

    title_size = fit_lines(list(h["title"]), "mono_bold", col_w, 84, 72)
    for line in h["title"]:
        require_w(line, title_size, "mono_bold", col_w, "hero title")
    d.text((m - 1, 176), h["title"][0], font=font(title_size, "mono_bold"),
           fill=hx(s["text"]), anchor="ls")
    d.text((m - 1, 260), h["title"][1], font=font(title_size, "mono_bold"),
           fill=hx(s["accent"]), anchor="ls")

    value_size = fit_lines(list(h["value"]), "cjk_bold", col_w,
                           34 if lang == "zh" else 30, 26)
    for index, line in enumerate(h["value"]):
        require_w(line, value_size, "cjk_bold", col_w, "hero value line")
        d.text((m, 318 + index * 42), line, font=font(value_size, "cjk_bold"),
               fill=hx(s["text"]), anchor="ls")

    sub_size = fit(h["sub"], "cjk", col_w, 25, 20)
    require_w(h["sub"], sub_size, "cjk", col_w, "hero subtitle")
    d.text((m, 404), h["sub"], font=font(sub_size, "cjk"),
           fill=hx(s["sub"]), anchor="ls")

    meta_runs = [(text, s["faint"], kind) for text, kind in h["meta"]]
    meta_end = m + sum(measure(text, 20, kind) for text, kind in h["meta"])
    if meta_end > m + col_w:
        raise SystemExit("FATAL: hero meta overflows")
    rich_line(img, m + 1, 446, meta_runs, 20)

    d = ImageDraw.Draw(img)
    d.line([m + 1, 474, m + col_w - 4, 474], fill=hx(s["grid"]), width=2)
    foot_size = fit(h["foot"], "cjk", col_w, 16, 13)
    d.text((m + 1, 500), h["foot"], font=font(foot_size, "cjk"),
           fill=hx(s["faint"]), anchor="ls")

    # ---- right: one register row, opened up ---------------------------------
    img = card(img, (648, 40, 1392, 540), s, radius=20, shadow=26)
    d = ImageDraw.Draw(img)

    # header band
    d.rounded_rectangle([648, 40, 1392, 114], radius=20, fill=hx(s["band"]))
    d.rectangle([648, 90, 1392, 114], fill=hx(s["band"]))
    d.line([648, 114, 1392, 114], fill=hx(s["edge"]), width=1)

    d.text((676, 78), h["card_title"][0], font=font(25, "mono_bold"),
           fill=hx(s["text"]), anchor="ls")
    tw = measure(h["card_title"][0], 25, "mono_bold")
    d.text((682 + tw, 79), h["card_title"][1], font=font(21, "cjk_bold"),
           fill=hx(s["accent"]), anchor="ls")
    require_w(h["card_sub"], 14, "cjk", 640, "card subtitle")
    d.text((676, 100), h["card_sub"], font=font(14, "cjk"),
           fill=hx(s["faint"]), anchor="ls")

    x = chip_right(img, 1364, 56, h["chip_skip"], s["accent"], s["pill"],
                   size=12.5, height=26)
    chip_right(img, x - 8, 56, h["chip_issue"], s["warn"], s["warn_bg"],
               size=12.5, height=26)

    # the eight read columns, one row
    top = 122
    for index, (label, value, rules, empty) in enumerate(h["fields"]):
        y = top + index * 40
        if empty:
            d.rounded_rectangle([660, y + 1, 1380, y + 37], radius=10,
                                fill=hx(s["warn_bg"]))
        d.text((h["label_x"], y + 26), label,
               font=font(h["label_size"], h["label_kind"]),
               fill=hx(s["sub"]), anchor="ls")
        if empty:
            vx = h["value_x"]
            d.text((vx, y + 26), value, font=font(21, "cjk"),
                   fill=hx(s["warn"]), anchor="ls")
        else:
            d.text((h["value_x"], y + 26), value, font=font(21, "mono"),
                   fill=hx(s["text"]), anchor="ls")
        chip_right(img, 1364, y + 8, rules, s["accent"], s["pill"],
                   size=14, height=24)

    d = ImageDraw.Draw(img)
    d.line([676, 408, 1364, 408], fill=hx(s["grid"]), width=1)

    # ---- the finding the two blank cells produce ----------------------------
    d.ellipse([678, 424, 690, 436], fill=hx(s["warn"]))
    d.text((702, 434), h["find_head"][0], font=font(17, "mono_bold"),
           fill=hx(s["text"]), anchor="ls")
    cw = measure(h["find_head"][0], 17, "mono_bold")
    d.rounded_rectangle([702 + cw + 10, 418, 702 + cw + 10 +
                         measure(h["find_head"][1], 12, "mono_bold") + 20, 440],
                        radius=11, fill=hx(s["warn_bg"]))
    d.text((702 + cw + 20, 430), h["find_head"][1], font=font(12, "mono_bold"),
           fill=hx(s["warn"]), anchor="ls")
    d.text((702 + cw + 38 + measure(h["find_head"][1], 12, "mono_bold"),
            434), h["find_head"][2], font=font(14.5, "cjk"),
           fill=hx(s["sub"]), anchor="ls")

    for index, (tag, text) in enumerate(h["find_rows"]):
        y = 458 + index * 22
        d.text((676, y), tag, font=font(11.5, "mono"),
               fill=hx(s["faint"]), anchor="ls")
        size = h["find_sizes"][index]
        require_w(text, size, "cjk", 600, f"finding {tag}")
        d.text((762, y), text, font=font(size, "cjk"),
               fill=hx(s["text"] if index < 2 else s["sub"]), anchor="ls")

    require_w(h["source"], 11.5, "mono", 500, "source line")
    d.text((676, 528), h["source"], font=font(11.5, "mono"),
           fill=hx(s["faint"]), anchor="ls")
    d.rounded_rectangle([648, 40, 1392, 540], radius=20,
                        outline=hx(s["edge"]), width=2)

    name = f"{NAME}-hero-{lang}-{skin}.webp"
    img.save(os.path.join(OUT, name), "WEBP", quality=92, method=6)
    print(f"wrote {name} ({W}x{H})")


# ---------------------------------------------------------------------------
# flow: normalise -> seven rules -> two channels -> one report -> reviewer
# ---------------------------------------------------------------------------
RULES = [
    ("CD-001", "presenceAny", "goodsName + amount"),
    ("CD-002", "pattern", "hsCode ^[0-9]{10}$"),
    ("CD-003", "pattern", "currency ^[A-Z]{3}$"),
    ("CD-004", "unique", "docNo"),
    ("CD-005", "fieldComparison", "grossWeight >= netWeight"),
    ("CD-006", "date", "declaredAt <= 核对日"),
    ("CD-007", "containsAny", "goodsName 词表"),
]


class Svg:
    """Tiny SVG writer that measures every label before it is emitted."""

    def __init__(self, s: dict) -> None:
        self.s = s
        self.parts: list[str] = []
        self.bad: list[str] = []

    def add(self, markup: str) -> None:
        self.parts.append(markup)

    def _w(self, content: str, size: float, kind: str,
           tracking: float | None = None) -> float:
        got = measure(content, size, kind)
        if tracking:
            got += tracking * max(len(content) - 1, 0)
        return got

    def text(self, x: float, y: float, content: str, size: float, fill: str, *,
             anchor: str = "start", weight: int | None = None,
             mono: bool = False, max_w: float | None = None,
             opacity: float | None = None, tracking: float | None = None) -> None:
        kind = "mono" if mono else "cjk"
        if weight:
            kind += "_bold"
        if max_w is not None and self._w(content, size, kind, tracking) > max_w + 0.4:
            self.bad.append(f"{content!r} needs "
                            f"{self._w(content, size, kind):.1f}px > {max_w:.0f}px")
        attrs = [f'x="{x}"', f'y="{y}"', f'fill="{fill}"',
                 f'font-family="{FONT_CSS_MONO if mono else FONT_CSS_SANS}"',
                 f'font-size="{size}"']
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if weight:
            attrs.append(f'font-weight="{weight}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        if tracking:
            attrs.append(f'letter-spacing="{tracking}"')
        self.add(f'<text {" ".join(attrs)}>{escape(content)}</text>')

    def rich(self, x: float, y: float, runs: list[tuple[str, str, str]],
             size: float, *, anchor: str = "start",
             max_w: float | None = None) -> float:
        """Draw runs of (text, fill, kind[mono|cjk + optional bold])."""
        widths = [self._w(text, size, kind) for text, _, kind in runs]
        total = sum(widths)
        if max_w is not None and total > max_w + 0.4:
            self.bad.append(f"{''.join(r[0] for r in runs)!r} needs "
                            f"{total:.1f}px > {max_w:.0f}px")
        cursor = x - total if anchor == "end" else x
        for (text, fill, kind), width in zip(runs, widths):
            mono = kind.startswith("mono")
            attrs = [f'x="{cursor}"', f'y="{y}"', f'fill="{fill}"',
                     f'font-family="{FONT_CSS_MONO if mono else FONT_CSS_SANS}"',
                     f'font-size="{size}"']
            if kind.endswith("_bold"):
                attrs.append('font-weight="700"')
            self.add(f'<text {" ".join(attrs)}>{escape(text)}</text>')
            cursor += width
        return cursor

    def rect(self, x: float, y: float, w: float, h: float, *, fill: str,
             rx: float = 0, stroke: str | None = None, sw: float = 1.5,
             shadow: bool = False, dash: str | None = None,
             opacity: float | None = None) -> None:
        attrs = [f'x="{x}"', f'y="{y}"', f'width="{w}"', f'height="{h}"']
        if rx:
            attrs.append(f'rx="{rx}"')
        attrs.append(f'fill="{fill}"')
        if stroke:
            attrs += [f'stroke="{stroke}"', f'stroke-width="{sw}"']
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        if shadow:
            attrs.append('filter="url(#soft)"')
        self.add(f'<rect {" ".join(attrs)}/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, *, stroke: str,
             sw: float = 1.5, dash: str | None = None,
             opacity: float | None = None) -> None:
        attrs = [f'x1="{x1}"', f'y1="{y1}"', f'x2="{x2}"', f'y2="{y2}"',
                 f'stroke="{stroke}"', f'stroke-width="{sw}"']
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.add(f'<line {" ".join(attrs)}/>')

    def path(self, d: str, *, stroke: str, sw: float = 1.5,
             fill: str = "none", dash: str | None = None,
             opacity: float | None = None) -> None:
        attrs = [f'd="{d}"', f'fill="{fill}"', f'stroke="{stroke}"',
                 f'stroke-width="{sw}"', 'stroke-linejoin="round"',
                 'stroke-linecap="round"']
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.add(f'<path {" ".join(attrs)}/>')

    def circle(self, cx: float, cy: float, r: float, *, fill: str,
               stroke: str | None = None, sw: float = 1.5) -> None:
        attrs = [f'cx="{cx}"', f'cy="{cy}"', f'r="{r}"', f'fill="{fill}"']
        if stroke:
            attrs += [f'stroke="{stroke}"', f'stroke-width="{sw}"']
        self.add(f'<circle {" ".join(attrs)}/>')

    def chip_right(self, right: float, y: float, label: str, fg: str, bg: str,
                   *, size: float = 11, pad: float = 9, height: float = 22,
                   mono: bool = False, weight: int | None = None) -> float:
        kind = "mono" if mono else "cjk"
        if weight:
            kind += "_bold"
        w = self._w(label, size, kind) + pad * 2
        x = right - w
        self.rect(x, y, w, height, fill=bg, rx=height / 2)
        self.text(x + pad, y + height / 2 + size * 0.35, label, size, fg,
                  mono=mono, weight=weight)
        return x

    def arrow_right(self, x1: float, x2: float, y: float, color: str,
                    sw: float = 1.6) -> None:
        self.path(f"M{x1} {y}H{x2 - 8}", stroke=color, sw=sw)
        self.add(f'<path d="M{x2} {y}l-9 -4.6v9.2z" fill="{color}"/>')

    def arrow_down(self, x: float, y1: float, y2: float, color: str,
                   sw: float = 1.6) -> None:
        self.path(f"M{x} {y1}V{y2 - 8}", stroke=color, sw=sw)
        self.add(f'<path d="M{x} {y2}l-4.6 -9h9.2z" fill="{color}"/>')

    def svg(self, w: int, h: int, title: str, desc: str) -> str:
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
                f'height="{h}" viewBox="0 0 {w} {h}" role="img" '
                f'aria-labelledby="title desc">')
        return "\n".join([head, f'<title id="title">{escape(title)}</title>',
                          f'<desc id="desc">{escape(desc)}</desc>',
                          *self.parts, "</svg>"]) + "\n"


def flow_svg(skin: str) -> str:
    f = FLOW[skin]
    W, H = 1100, 660
    v = Svg(f)

    v.add("<defs>")
    v.add(f'<linearGradient id="bg" x1="0" y1="0" x2="0.2" y2="1">'
          f'<stop offset="0" stop-color="{f["bg_from"]}"/>'
          f'<stop offset="1" stop-color="{f["bg_to"]}"/></linearGradient>')
    v.add(f'<filter id="soft" x="-30%" y="-30%" width="160%" height="180%">'
          f'<feDropShadow dx="0" dy="7" stdDeviation="9" '
          f'flood-color="{f["shadow"]}" flood-opacity="{f["shadow_op"]}"/>'
          f'</filter>')
    v.add(f'<pattern id="dots" width="24" height="24" '
          f'patternUnits="userSpaceOnUse">'
          f'<circle cx="1.2" cy="1.2" r="1.2" fill="{f["dot"]}"/></pattern>')
    v.add("</defs>")

    v.rect(0, 0, W, H, fill="url(#bg)")
    v.rect(0, 0, W, H, fill="url(#dots)", opacity=f["dot_op"])

    # ---- header -------------------------------------------------------------
    v.text(44, 56, NAME, 30, f["text"], weight=700, mono=True, max_w=620)
    v.text(44, 86, "一份台账，7 条规则：命中的进 issues[]，跑不了的进 skipped[]，"
                   "两边汇进同一份报告。", 15, f["sub"], max_w=790)
    v.chip_right(1056, 30, "rules/customs-doc-check.yaml · v2026.1",
                 f["accent"], f["pill"], size=11.5, pad=12, height=28,
                 mono=True)
    v.text(44, 112, "IN  ·  file | material  ·  JSON / YAML  ·  rows[] + 表头 5 个声明栏  ·  只读",
           11, f["faint"], mono=False, max_w=560)
    v.text(1056, 112, "OUT  ·  summary · issues[] · skipped[] · markdown · reportJson",
           11, f["faint"], mono=True, anchor="end", max_w=460)
    v.line(44, 126, 1056, 126, stroke=f["rule"], sw=1, opacity=0.75)

    # ---- material and normalisation (left) ----------------------------------
    v.rect(44, 136, 496, 196, fill=f["panel"], rx=18, stroke=f["edge"],
           sw=1.5, shadow=True)
    v.text(68, 166, "IN · 材料", 13, f["text"], weight=700, max_w=180)
    v.chip_right(516, 154, "JSON / YAML", f["accent"], f["pill"], size=11,
                 height=22, mono=True)

    # the row, three of its sixteen filled cells
    v.rect(60, 206, 468, 32, fill=f["tint"], rx=8)
    v.text(68, 200, "#", 12, f["faint"], mono=True, max_w=16)
    v.text(100, 200, "单证编号", 12, f["faint"], max_w=90)
    v.text(300, 200, "商品名称", 12, f["faint"], max_w=90)
    v.text(430, 200, "总价", 12, f["faint"], max_w=50)
    v.text(68, 228, "#1", 12, f["sub"], mono=True, max_w=20)
    v.text(100, 228, "INV-2026-0001", 13, f["text"], mono=True, max_w=180)
    v.text(300, 228, "（空）", 13.5, f["warn"], max_w=60)
    v.text(430, 228, "（空）", 13.5, f["warn"], max_w=60)

    v.text(68, 262, "17 个规范栏目 · 别名归一（大小写 / 空格 / _ / - 都忽略）",
           12.5, f["sub"], max_w=450)
    v.text(68, 286, "requireAnyOf：至少认得一个已知栏名，否则拒读", 12.5,
           f["sub"], max_w=450)
    v.text(68, 308, "表头 5 个声明栏可选；rows[] 才是必读的那张表", 11,
           f["faint"], max_w=450)

    # ---- the rule pack (right) ----------------------------------------------
    v.rect(564, 136, 492, 196, fill=f["card"], rx=18, stroke=f["edge"],
           sw=1.5, shadow=True)
    v.text(588, 166, "RULES · 规则包是数据，不是代码", 13, f["text"],
           weight=700, max_w=340)
    v.chip_right(1032, 154, "v2026.1 · 7 条 · 全部 warn", f["accent"],
                 f["pill"], size=11, height=22)

    cell_x = (588, 820)
    for index, (rid, kind, field) in enumerate(RULES):
        col = 0 if index < 4 else 1
        row = index % 4
        x = cell_x[col]
        y = 200 + row * 30
        v.text(x, y, rid, 13.5, f["text"], weight=700, mono=True, max_w=60)
        v.text(x + 58, y, kind, 11, f["sub"], mono=True, max_w=112)
        v.text(x, y + 16, field, 12, f["sub"], max_w=210)
    v.text(588, 324, "severity 由依据等级封顶：derived-from-principle ≤ warn",
           11, f["faint"], max_w=440)

    # material feeds the rule pack
    v.arrow_right(542, 560, 234, f["accent"], sw=1.5)

    # dispatch bus: one rail, two channels
    v.path("M700 332V342H250", stroke=f["accent"], sw=1.6, opacity=0.9)
    v.arrow_down(250, 342, 354, f["accent"])
    v.arrow_down(700, 342, 354, f["accent"])

    # ---- channel A: issues[] ------------------------------------------------
    v.rect(44, 354, 496, 140, fill=f["card"], rx=18, stroke=f["edge"],
           sw=1.5, shadow=True)
    v.rect(47, 366, 4, 116, fill=f["warn"], rx=2, opacity=0.9)
    v.text(68, 380, "CH-A · issues[]", 13, f["text"], weight=700, mono=True,
           max_w=210)
    v.chip_right(516, 368, "1 条 · warn", f["warn"], f["pill"], size=11,
                 height=22)
    v.rich(68, 406, [("CD-001", f["accent"], "mono_bold"),
                     (" · warn · 第 1 行 · ", f["sub"], "cjk"),
                     ("goodsName", f["sub"], "mono")], 11.5, max_w=430)
    v.text(68, 432, "第 1 行 goodsName、amount 都为空", 13.5, f["text"],
           max_w=430)
    v.text(68, 456, "应至少填写一项 · fix 补填品名与总价", 11.5, f["sub"],
           max_w=430)
    v.text(68, 478, "locator { row: 1, column: goodsName }", 11, f["faint"],
           mono=True, max_w=430)

    # ---- channel B: skipped[] -----------------------------------------------
    v.rect(564, 354, 492, 140, fill=f["card"], rx=18, stroke=f["edge"],
           sw=1.5, shadow=True)
    v.rect(567, 366, 4, 116, fill=f["accent"], rx=2, opacity=0.55)
    v.text(588, 380, "CH-B · skipped[]", 13, f["text"], weight=700,
           mono=True, max_w=230)
    v.chip_right(1032, 368, "0 条", f["accent"], f["pill"], size=11,
                 height=22)
    v.text(588, 406, "跑不了的检查逐条写原因，绝不静默通过", 12.5, f["sub"],
           max_w=430)
    v.text(588, 430, "例 · 材料没有「毛重」列，本条不适用", 11.5, f["faint"],
           max_w=430)
    v.text(588, 452, "例 · 该规则在当前配置中被禁用", 11.5, f["faint"],
           max_w=430)
    v.text(588, 474, "例 · only 收窄后未执行", 11.5, f["faint"], max_w=430)
    v.text(1032, 478, "skipped 只装没能执行的检查", 11, f["faint"],
           anchor="end", max_w=240)

    # ---- confluence: one report band ---------------------------------------
    v.arrow_down(250, 494, 508, f["accent"])
    v.arrow_down(700, 494, 508, f["accent"])
    v.rect(44, 508, 1012, 104, fill=f["panel"], rx=20, stroke=f["edge"],
           sw=1.5, shadow=True)
    v.line(780, 526, 780, 596, stroke=f["rule"], sw=1)

    v.text(68, 532, "report · makeReport + buildView", 12, f["faint"],
           mono=True, max_w=330)
    v.text(68, 558, "error 0 · warn 1 · info 0", 17, f["text"], weight=700,
           mono=True, max_w=300)
    v.text(68, 580, "issueCount 1 · skippedCount 0 · rulesetVersion 2026.1",
           11.5, f["sub"], mono=True, max_w=520)
    v.text(68, 600, "markdown + reportJson · 措辞守卫 + 免责声明", 11.5,
           f["sub"], max_w=520)

    v.arrow_right(756, 776, 566, f["accent"], sw=1.5)
    v.text(804, 532, "审核人", 14, f["text"], weight=700, max_w=70)
    v.text(858, 532, "结论不在报告里", 11, f["faint"], max_w=160)
    v.text(804, 560, "不判合规", 12, f["sub"], max_w=90)
    v.text(930, 560, "不判归类", 12, f["sub"], max_w=90)
    v.text(804, 586, "不判真实性", 12, f["sub"], max_w=90)
    v.text(930, 586, "不判税款", 12, f["sub"], max_w=90)
    v.text(804, 602, "报告只列差异，不定性", 10.5, f["faint"], max_w=230)

    # ---- footer -------------------------------------------------------------
    v.text(44, 630, "issues[] 为空 ≠ 没问题：没能跑的检查进 skipped[] 并写明原因；"
                    "跑过而未命中的规则两栏都不进。", 12.5, f["sub"], max_w=780)
    v.text(44, 650, "表头声明栏（可选）declarationNo / consignee / contractNo / "
                    "invoiceNo / declaredAt", 10.5, f["faint"], max_w=700)
    v.text(1056, 650, "7 条规则 · 6 种 check · 全部 warn · 只读", 10.5,
           f["faint"], anchor="end", max_w=260)

    if v.bad:
        raise SystemExit("FATAL: SVG label overflow:\n  " + "\n  ".join(v.bad))
    return v.svg(
        W, H,
        "dsh-customs-doc-check register checks: one row, seven rules, "
        "two output channels",
        "The material (JSON or YAML) is normalised into 17 canonical columns "
        "after alias matching that ignores case, spaces, underscores and "
        "hyphens; at least one known column name must be recognised. Seven "
        "rules read eight of those columns: CD-001 presenceAny on goodsName + "
        "amount, CD-002 pattern ^[0-9]{10}$ on hsCode, CD-003 pattern "
        "^[A-Z]{3}$ on currency, CD-004 uniqueness of docNo, CD-005 "
        "grossWeight >= netWeight, CD-006 a parseable declaredAt not after the "
        "check date, CD-007 placeholder terms in goodsName. Each rule leaves "
        "through one of two channels: issues[] for what it found (one warn for "
        "row 1, whose goodsName and amount are both blank) and skipped[] for "
        "what it could not run (missing column, disabled rule, only-narrowed "
        "rule), each with its own reason. A rule that ran and found nothing "
        "enters neither list. Both channels converge on one report "
        "(error 0, warn 1, info 0; issueCount 1, skippedCount 0) rendered as "
        "markdown plus reportJson under the wording guard and disclaimer, and "
        "the verdict stays with the reviewer: no compliance, classification, "
        "truthfulness or duty judgement.",
    )


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for skin in ("light", "dark"):
        for lang in ("zh", "en"):
            hero(lang, skin)
        name = f"{NAME}-flow-v5-{skin}.svg"
        text = flow_svg(skin)
        ET.fromstring(text)  # never ship malformed XML
        with open(os.path.join(OUT, name), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(text)
        print(f"wrote {name} (1100x660)")


if __name__ == "__main__":
    main()
