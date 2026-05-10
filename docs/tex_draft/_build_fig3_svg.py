"""Compositor for docs/tex_draft/figures/fig3/fig3.svg.

Swaps the matplotlib bitmap panels into the hand-authored SVG template.
Run this whenever a matplotlib panel is regenerated.

Run:
    uv run python docs/tex_draft/_build_fig3_svg.py

Layout of fig3.svg  (canvas 111.76 × ~150.57 mm)
------------------
Hand-drawn  (document y 0–34 mm)  : mutant hypothesis schematic
Top         (document y ~34–74 mm): figure3_endpoint_metrics_panel [id: image1-6]
Bottom      (document y ~71–151mm): figure3_mutant_examples_panel  [id: image1]

layer1 transform: translate(-20.241961, 9.8207353)
  → image local x=20.24 maps to document x=0 (full-width panels)
  → image local y=24.42 (endpoint_metrics) → document y≈34mm
  → image local y=60.91 (mutant_examples) → document y≈71mm

figure3_mutant_hypothesis_panel is NOT embedded here — it is the hand-drawn
schematic at the top of the SVG template.

Panel sizing: figsize=11in, SCALE_FACTOR=0.40 → display 111.76 mm wide → 8pt
effective TITLE at print.  After running, realign panels in Inkscape if the
endpoint_metrics height changed (the panel uses constrained_layout so its
aspect ratio can shift slightly when fonts or data change).
"""
from __future__ import annotations

import base64
import re
import struct
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]
TEX_DIR   = REPO_ROOT / "docs" / "tex_draft"
FIG_DIR   = TEX_DIR / "figures"
FIG3_DIR  = FIG_DIR / "fig3"

TEMPLATE_SVG = FIG3_DIR / "fig3.svg"
OUTPUT_SVG   = FIG3_DIR / "fig3.svg"

SCALE_FACTOR = 0.40
FIGSIZE_W_IN = 11.0

# ── panel definitions ──────────────────────────────────────────────────────────

PANELS: list[dict] = [
    {
        "name":   "endpoint_metrics",
        "source": FIG_DIR / "figure3_endpoint_metrics_panel.png",
        "ids":    ["image1-6"],
        "resize": True,
    },
    {
        "name":   "mutant_examples",
        "source": FIG_DIR / "figure3_mutant_examples_panel.png",
        "ids":    ["image1"],
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

        data_uri = _png_to_data_uri(source)
        for image_id in panel["ids"]:
            svg = _replace_image_element(svg, image_id, data_uri,
                                         new_width=new_w, new_height=new_h)
        print(f"Embedded {source.name} ({png_w}×{png_h}) → ids: {panel['ids']}")

    OUTPUT_SVG.write_text(svg, encoding="utf-8")
    print(f"\nWrote {OUTPUT_SVG}")
    print()
    print("Reminders:")
    print(f"  • Panel boxes are now {display_w_mm:.1f} mm wide; expand SVG canvas and realign in Inkscape.")
    print("  • figure3_mutant_hypothesis_panel is NOT yet embedded — add in Inkscape.")


if __name__ == "__main__":
    build()
