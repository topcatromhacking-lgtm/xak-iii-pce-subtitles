#!/usr/bin/env python3
"""Xak III subtitle font: build, preview, and convert to PC Engine sprite tiles.

Source of truth is font/xak3_subfont.png: a 16x6 grid of 8x12 cells for
ASCII 0x20-0x7F (cell = code - 0x20). White = ink. Advance width is the
rightmost ink column + 2 (1 px gap + 1 px drop shadow); space = 3 px.
font/glyphs.txt is the editable ASCII-art source the PNG was drawn from.

Subcommands
  sheet   glyphs.txt -> xak3_subfont.png (+ 4x preview)
  render  TEXT [-o line.png]          preview one subtitle line (or "a|b")
  line    TEXT -o out.bin             PCE sprite patterns for one line
  asm     -o font.inc                 glyph rows + width table (ca65) for a runtime renderer
  info                                print metrics/limits used by lint_script.py

Renderer constants (see docs/renderer-design.md):
  band width 256 px, CRT-safe text width MAX_LINE_PX = 240 px = 15 sprites of
  16 px, which also leaves 1 of the 16 hardware sprites/scanline for anything
  native that touches the band. Strip height 16 px (one 16x16 sprite row).
PCE sprite pattern: 16x16, 4 bitplanes, 64 words: plane0 rows0-15, plane1
rows0-15, plane2, plane3; bit15 = leftmost pixel; words little-endian.
Pixel value 1 = text, 2 = shadow (sprite palette entries 1 and 2).
"""
import argparse, json, os, struct, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONT_DIR = os.path.join(ROOT, "font")
PNG = os.path.join(FONT_DIR, "xak3_subfont.png")
TXT = os.path.join(FONT_DIR, "glyphs.txt")
CELL_W, CELL_H, COLS, ROWS = 8, 12, 16, 6
INK_TOP = 2            # first cell row used by glyphs.txt
SPACE_ADV = 3
SCREEN_W = 256
MAX_LINE_PX = 240      # 15 x 16 px sprites
SPRITE_W = 16
STRIP_H = 16
MAX_SPRITES_PER_LINE = MAX_LINE_PX // SPRITE_W
MAX_LINES = 2

def parse_txt(path=TXT):
    glyphs, cur = {}, None
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if (cur is None and line.startswith("#")) or not line.strip():
            continue
        if line.startswith("== "):
            name = line[3:]
            cur = " " if name == "SPACE" else name
            if len(cur) != 1:
                raise SystemExit(f"bad glyph name {name!r}")
            glyphs[cur] = []
        else:
            glyphs[cur].append(line)
    for ch, rows in glyphs.items():
        if len(rows) != 9 or len({len(r) for r in rows}) != 1 or len(rows[0]) > 7:
            raise SystemExit(f"glyph {ch!r}: need 9 rows of equal width <= 7")
    return glyphs

def build_sheet(glyphs, out=PNG):
    img = Image.new("L", (CELL_W * COLS, CELL_H * ROWS), 0)
    for ch, rows in glyphs.items():
        i = ord(ch) - 0x20
        cx, cy = (i % COLS) * CELL_W, (i // COLS) * CELL_H
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c == "#":
                    img.putpixel((cx + x, cy + INK_TOP + y), 255)
    img.save(out)
    img.resize((img.width * 4, img.height * 4), Image.NEAREST).save(out.replace(".png", "_x4.png"))
    return out

class Font:
    def __init__(self, png=PNG):
        im = Image.open(png).convert("L")
        self.bits, self.adv = {}, {}
        for i in range(COLS * ROWS):
            ch = chr(0x20 + i)
            cx, cy = (i % COLS) * CELL_W, (i // COLS) * CELL_H
            rows = [[im.getpixel((cx + x, cy + y)) > 127 for x in range(CELL_W)] for y in range(CELL_H)]
            ink = [x for x in range(CELL_W) if any(r[x] for r in rows)]
            if ch == " ":
                self.bits[ch], self.adv[ch] = rows, SPACE_ADV
            elif ink:
                self.bits[ch], self.adv[ch] = rows, max(ink) + 2
    def supports(self, ch):
        return ch in self.adv
    def width(self, text):
        """Pixel width of a rendered line incl. trailing shadow column."""
        if not text:
            return 0
        return sum(self.adv[c] for c in text) - 1
    def render(self, text):
        """Return 2D list of pixel values (0/1 text/2 shadow), STRIP_H rows."""
        w = max(self.width(text), 1)
        buf = [[0] * (w + 1) for _ in range(STRIP_H)]
        x = 0
        for c in text:
            for y in range(CELL_H):
                for gx in range(CELL_W):
                    if self.bits[c][y][gx]:
                        buf[y][x + gx] = 1
            x += self.adv[c]
        # drop shadow (+1,+1) where empty
        for y in range(STRIP_H - 1, 0, -1):
            for xx in range(w, 0, -1):
                if buf[y][xx] == 0 and buf[y - 1][xx - 1] == 1:
                    buf[y][xx] = 2
        return [r[:w] for r in buf]

def to_sprites(pix, sprite_w=SPRITE_W):
    """Center a rendered line in a whole number of 16 px sprites.
    Returns (sprite_bytes_list, x_left_on_screen)."""
    w = len(pix[0])
    n = max(1, -(-w // sprite_w))
    pad = (n * sprite_w - w) // 2
    full = [[0] * pad + r + [0] * (n * sprite_w - w - pad) for r in pix]
    out = []
    for s in range(n):
        words = []
        for plane in range(4):
            for y in range(16):
                v = 0
                for x in range(16):
                    p = full[y][s * 16 + x] if y < len(full) else 0
                    if (p >> plane) & 1:
                        v |= 0x8000 >> x
                words.append(v)
        out.append(struct.pack("<64H", *words))
    x_left = (SCREEN_W - n * sprite_w) // 2
    return out, x_left

def preview(font, lines, scale=3):
    W, H = SCREEN_W, STRIP_H * len(lines) + 4 * (len(lines) - 1) + 8
    im = Image.new("RGB", (W, H), (0, 0, 0))
    pal = {1: (255, 255, 255), 2: (72, 72, 72)}
    for li, t in enumerate(lines):
        pix = font.render(t)
        x0 = (W - len(pix[0])) // 2
        for y, r in enumerate(pix):
            for x, p in enumerate(r):
                if p:
                    im.putpixel((x0 + x, 4 + li * (STRIP_H + 4) + y), pal[p])
    return im.resize((W * scale, H * scale), Image.NEAREST)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sheet")
    r = sub.add_parser("render"); r.add_argument("text"); r.add_argument("-o", default="line_preview.png")
    l = sub.add_parser("line"); l.add_argument("text"); l.add_argument("-o", required=True)
    a = sub.add_parser("asm"); a.add_argument("-o", required=True)
    sub.add_parser("info")
    ns = ap.parse_args()
    if ns.cmd == "sheet":
        print(build_sheet(parse_txt())); return
    f = Font()
    if ns.cmd == "render":
        lines = ns.text.split("|")
        for t in lines:
            print(f"{t!r}: {f.width(t)} px, {-(-f.width(t)//16)} sprites")
        preview(f, lines).save(ns.o); print(ns.o)
    elif ns.cmd == "line":
        spr, x = to_sprites(f.render(ns.text))
        open(ns.o, "wb").write(b"".join(spr))
        print(f"{ns.o}: {len(spr)} sprites, x_left={x}")
    elif ns.cmd == "asm":
        with open(ns.o, "w") as o:
            o.write("; generated by tools/font_build.py asm - 12 bytes/glyph (bit7=left), ASCII $20-$7F\n")
            o.write("font_widths:\n")
            for i in range(96):
                o.write(f"  .byte {f.adv.get(chr(0x20+i), 0)}\n")
            o.write("font_rows:\n")
            for i in range(96):
                rows = f.bits.get(chr(0x20 + i), [[False] * 8] * 12)
                bs = [sum(0x80 >> x for x in range(8) if r[x]) for r in rows]
                o.write("  .byte " + ",".join(f"${b:02X}" for b in bs) + f" ; {chr(0x20+i)!r}\n")
        print(ns.o)
    elif ns.cmd == "info":
        avg = sum(f.adv[c] for c in "etaoinshrdlucmfwypvbgk ") / 23
        print(json.dumps(dict(glyphs=len(f.adv), max_line_px=MAX_LINE_PX, max_sprites_per_line=MAX_SPRITES_PER_LINE,
                              avg_lowercase_advance=round(avg, 2), est_chars_per_line=int(MAX_LINE_PX // avg),
                              fixed8_chars_per_line=MAX_LINE_PX // 8), indent=1))

if __name__ == "__main__":
    main()
