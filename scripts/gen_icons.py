#!/usr/bin/env python3
"""Generador de iconos PNG para la PWA (sin dependencias externas)."""
import struct
import zlib
import math
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

# Paleta
BG_TOP = (13, 110, 113)      # teal oscuro
BG_BOT = (16, 138, 130)      # teal
CROSS = (255, 255, 255)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rounded(x, y, w, h, r):
    """¿El pixel (x,y) está dentro del rect redondeado [0,w]x[0,h] con radio r?"""
    cx = min(max(x, r), w - r)
    cy = min(max(y, r), h - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def in_cross(x, y, w, h):
    """Cruz médica centrada."""
    arm = w * 0.16          # grosor del brazo
    length = w * 0.30       # medio-largo del brazo
    cx, cy = w / 2, h / 2
    horiz = abs(y - cy) <= arm and abs(x - cx) <= length
    vert = abs(x - cx) <= arm and abs(y - cy) <= length
    return horiz or vert


def make_icon(size, maskable=False):
    pad = 0 if not maskable else int(size * 0.10)
    inner = size - 2 * pad
    radius = int(inner * (0.5 if maskable else 0.22))
    rows = []
    for y in range(size):
        row = bytearray()
        row.append(0)  # filter type 0
        for x in range(size):
            lx, ly = x - pad, y - pad
            inside = (0 <= lx < inner and 0 <= ly < inner and
                      rounded(lx, ly, inner, inner, radius))
            if inside:
                t = ly / inner
                col = lerp(BG_TOP, BG_BOT, t)
                if in_cross(lx, ly, inner, inner):
                    col = CROSS
                row += bytes(col)
                row.append(255)
            else:
                row += bytes((0, 0, 0))
                row.append(0)  # transparente
        rows.append(bytes(row))
    raw = b"".join(rows)
    return png_bytes(size, size, raw)


def png_chunk(tag, data):
    c = tag + data
    return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)


def png_bytes(w, h, raw_rgba):
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)  # 8-bit RGBA
    idat = zlib.compress(raw_rgba, 9)
    return (sig + png_chunk(b"IHDR", ihdr) +
            png_chunk(b"IDAT", idat) + png_chunk(b"IEND", b""))


def write(name, data):
    path = os.path.join(OUT, name)
    with open(path, "wb") as f:
        f.write(data)
    print("escrito", path, len(data), "bytes")


if __name__ == "__main__":
    write("icon-192.png", make_icon(192))
    write("icon-512.png", make_icon(512))
    write("icon-maskable-512.png", make_icon(512, maskable=True))
    write("favicon-64.png", make_icon(64))
