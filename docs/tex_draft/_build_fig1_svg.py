"""Compositor for docs/tex_draft/figures/fig1/fig1.svg.

Swaps the matplotlib bitmap panels into the hand-authored SVG template while
preserving every other element (arrows, text, schematic shapes, clip paths,
transforms).  Run this whenever a matplotlib panel is regenerated.

Run:
    uv run python docs/tex_draft/_build_fig1_svg.py

Layout of fig1.svg  (canvas 87.75 × 144.05 mm)
------------------
Top     (~y 2.9 – 56 mm)   : hand-drawn SVG schematic (division rules)
Middle  (~y 56 – 117 mm)   : figure1_wt_examples_panel  [image id: image1-4-4]
Gap     (~2 mm)
Bottom  (~y 119 – 147 mm)  : figure1_wt_calibration_panel [image id: image1, base64-embedded]

After resize (panels now 111.8 mm wide, SVG canvas needs to grow):
  The compositor sets width and height on each image element from the PNG
  dimensions at SCALE_FACTOR 0.40, then the user realigns in Inkscape.

clipPath6 is defined in the SVG but is no longer referenced by any image element.
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

    OUTPUT_SVG.write_text(svg, encoding="utf-8")
    print(f"\nWrote {OUTPUT_SVG}")
    print()
    print("Reminders:")
    print(f"  • Panel boxes are now {display_w_mm:.1f} mm wide; expand SVG canvas in Inkscape and realign.")


if __name__ == "__main__":
    build()
