"""Compositor for docs/tex_draft/figures/fig1/fig1.svg.

Swaps the matplotlib bitmap panels into the hand-authored SVG template while
preserving every other element (arrows, text, schematic shapes, clip paths,
transforms).  Run this whenever a matplotlib panel is regenerated.

Run:
    uv run python docs/tex_draft/_build_fig1_svg.py

Layout of fig1.svg  (canvas 112.19 × 148.96 mm)
------------------
A (top-left)    (~y 2.9 – 33.6 mm, x 0 – 63 mm)  : hand-drawn schematic, WT division rules
B (top-right)   (~y 2.9 – 33.6 mm, x 63 – 112 mm) : hand-drawn schematic, GMC division
C (middle-left) (~y 33.6 – 116.7 mm)              : figure1_wt_examples_panel [image id: image1-4-4]
D (bottom-left) (~y 116.7 – 153.4 mm)             : figure1_wt_calibration_panel [image id: image1]

layer1 transform: translate(-0.29889275, -1.7726092)
  → layer1 local coords = document coords + (0.299, 1.773)

Panel labels A/B/C/D are managed by this script (LABELS constant below).
Positions are in layer1 local coordinates (mm).
"""
from __future__ import annotations

import base64
import re
import shutil
import struct
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]
TEX_DIR   = REPO_ROOT / "docs" / "tex_draft"
FIG_DIR   = TEX_DIR / "figures"
FIG1_DIR  = FIG_DIR / "fig1"

TEMPLATE_SVG = FIG1_DIR / "fig1.svg"
OUTPUT_SVG   = FIG1_DIR / "fig1.svg"

# Scale factor: SVG display width = SCALE_FACTOR × matplotlib figsize width.
# At SCALE_FACTOR=0.40 with FONT_SIZE_TITLE=20pt the effective print size is 8pt.
SCALE_FACTOR = 0.40
FIGSIZE_W_IN = 11.0    # figsize used in make_wt_calibration_figure and make_wt_examples_figure

# ── panel label definitions (layer1 local coords, mm) ─────────────────────────

LABEL_STYLE = (
    "font-style:normal;font-weight:bold;font-size:2.8222px;"
    "font-family:Arial,Helvetica,sans-serif;fill:#000000"
)

LABELS: list[dict] = [
    {"id": "label_a", "x": 2.2715294, "y": 7.056941,  "text": "A"},
    {"id": "label_b", "x": 63.056221, "y": 7.056941,  "text": "B"},
    {"id": "label_c", "x": 2.2715294, "y": 37.400002, "text": "C"},
    {"id": "label_d", "x": 2.2343228, "y": 119.44305, "text": "D"},
]

# ── panel definitions ──────────────────────────────────────────────────────────

PANELS: list[dict] = [
    {
        "name": "wt_examples",
        "mode": "file_ref",
        "source": FIG_DIR / "figure1_wt_examples_panel.png",
        "filename": "figure1_wt_examples_panel.png",
        "ids": ["image1-4-4"],
        "resize": True,   # update SVG width + height to match new display size
    },
    {
        "name": "wt_calibration",
        "mode": "base64",
        "source": FIG_DIR / "figure1_wt_calibration_panel.png",
        "ids": ["image1"],
        "resize": True,
    },
]

# ── helpers ────────────────────────────────────────────────────────────────────

def _png_to_data_uri(path: Path) -> str:
    data = path.read_bytes()
    b64  = base64.b64encode(data).decode("ascii")
    wrapped = "\n".join(b64[i:i+76] for i in range(0, len(b64), 76))
    return f"data:image/png;base64,{wrapped}"


def _get_png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    w = struct.unpack(">I", data[16:20])[0]
    h = struct.unpack(">I", data[20:24])[0]
    return w, h


def _upsert_label(svg: str, label: dict) -> str:
    """Update x/y of an existing panel label <text>, or insert it before </g></svg>."""
    pattern = re.compile(
        r'(<text\b[^>]*\bid="' + re.escape(label["id"]) + r'"[^>]*>)',
        re.DOTALL,
    )
    def patch(m: re.Match) -> str:
        tag = m.group(1)
        tag = re.sub(r'\bx="[^"]*"', f'x="{label["x"]}"', tag)
        tag = re.sub(r'\by="[^"]*"', f'y="{label["y"]}"', tag)
        return tag

    result, n = pattern.subn(patch, svg)
    if n > 0:
        return result

    new_tag = (
        f'    <text\n'
        f'       id="{label["id"]}"\n'
        f'       style="{LABEL_STYLE}"\n'
        f'       x="{label["x"]}"\n'
        f'       y="{label["y"]}">{label["text"]}</text>\n'
    )
    return svg.replace('</g></svg>', new_tag + '  </g></svg>')


def _replace_image_element(svg: str, image_id: str, new_href: str,
                            new_width: float | None = None,
                            new_height: float | None = None) -> str:
    """Replace xlink:href (and optionally width/height) in the named <image> element."""
    def patch(m: re.Match) -> str:
        tag = m.group(0)
        tag = re.sub(r'xlink:href="[^"]*"', f'xlink:href="{new_href}"', tag)
        if new_width is not None:
            tag = re.sub(r'\bwidth="[^"]*"', f'width="{new_width:.6f}"', tag)
        if new_height is not None:
            tag = re.sub(r'\bheight="[^"]*"', f'height="{new_height:.6f}"', tag)
        return tag

    pattern = re.compile(
        r'<image(?=[^>]*\bid="' + re.escape(image_id) + r'"[^>]*>)[^>]*>',
        re.DOTALL,
    )
    result, n = pattern.subn(patch, svg)
    if n == 0:
        raise ValueError(f"Image element id={image_id!r} not found in SVG")
    return result


# ── main ───────────────────────────────────────────────────────────────────────

def build() -> None:
    svg = TEMPLATE_SVG.read_text(encoding="utf-8")

    display_w_mm = SCALE_FACTOR * FIGSIZE_W_IN * 25.4
    print(f"Target display width: {display_w_mm:.2f} mm  (scale {SCALE_FACTOR}, figsize {FIGSIZE_W_IN} in)")

    for panel in PANELS:
        source: Path = panel["source"]
        if not source.exists():
            raise FileNotFoundError(f"Panel source not found: {source}")

        png_w, png_h = _get_png_size(source)
        png_aspect   = png_w / png_h

        new_w = display_w_mm if panel.get("resize") else None
        new_h = (display_w_mm / png_aspect) if panel.get("resize") else None
        if new_w is not None:
            print(f"  [{panel['name']}] display: {new_w:.2f} × {new_h:.2f} mm  "
                  f"(PNG {png_w}×{png_h}, aspect {png_aspect:.3f})")

        if panel["mode"] == "file_ref":
            dest = FIG1_DIR / panel["filename"]
            shutil.copy2(source, dest)
            print(f"Copied {source.name} → {dest}")
            for image_id in panel["ids"]:
                svg = _replace_image_element(svg, image_id, panel["filename"],
                                             new_width=new_w, new_height=new_h)
            print(f"  Updated ids: {panel['ids']}")

        elif panel["mode"] == "base64":
            dest = FIG1_DIR / source.name
            shutil.copy2(source, dest)
            data_uri = _png_to_data_uri(source)
            for image_id in panel["ids"]:
                svg = _replace_image_element(svg, image_id, data_uri,
                                             new_width=new_w, new_height=new_h)
            print(f"Copied {source.name} → {dest}")
            print(f"Embedded {source.name} as base64 → ids: {panel['ids']}")

    for label in LABELS:
        svg = _upsert_label(svg, label)
        print(f"  [label_{label['text'].lower()}] x={label['x']}, y={label['y']}")

    OUTPUT_SVG.write_text(svg, encoding="utf-8")
    print(f"\nWrote {OUTPUT_SVG}")


if __name__ == "__main__":
    build()
