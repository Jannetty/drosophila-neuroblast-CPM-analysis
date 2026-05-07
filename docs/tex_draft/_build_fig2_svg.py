"""Compositor for docs/tex_draft/figures/fig2/fig2.svg.

Swaps the matplotlib bitmap panels and updates hand-drawn text labels to the
current nomenclature.  Run this whenever a matplotlib panel is regenerated.

Run:
    uv run python docs/tex_draft/_build_fig2_svg.py

Layout of fig2.svg  (canvas 139.35 × 174.96 mm)
------------------
Left col  (x 0–60 mm, y 0–58 mm)  : hand-drawn SVG schematics (division rules)
Top-right (x 60–139 mm, y 0–28 mm): figure2_wt_mixing_panel    [id: image1-8]
Mid-right (x 61–140 mm, y 30–58 mm): figure2_wt_exposure_panel  [id: image1-1]
Bottom    (x 4–140 mm, y 62–175 mm): figure2_wt_geometry_examples_panel [id: image1-4]

Mixing and exposure panels (figsize 11 in, scale 0.40) are resized to
display_w = 111.8 mm.  The compositor updates both width and height on those
image elements; realign in Inkscape after running.

Geometry examples panel is NOT resized (already at correct scale ~0.39).

NOTE – composition panel:
    figure2_wt_composition_panel.png is NOT currently embedded in fig2.svg.
    It needs to be added as a new <image> element in Inkscape.

Text replacements (hand-drawn SVG labels) — only applied if old text still present:
    "Intergenerational rotation" + "mean shift"  →  "Apical axis" + "reorientation"
    "Fixed-axis" + "variance sweep"              →  "Spindle orientation" + "variance"
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
FIG2_DIR  = FIG_DIR / "fig2"

TEMPLATE_SVG = FIG2_DIR / "fig2.svg"
OUTPUT_SVG   = FIG2_DIR / "fig2.svg"

# Scale factor for mixing/exposure panels.
SCALE_FACTOR   = 0.40
FIGSIZE_W_IN   = 11.0   # matches make_grouped_metric_panel figsize

# ── panel definitions ──────────────────────────────────────────────────────────

PANELS: list[dict] = [
    {
        "name":    "wt_geometry_examples",
        "source":  FIG_DIR / "figure2_wt_geometry_examples_panel.png",
        "ids":     ["image1-4"],
        "resize":  False,
        "adjust_height": True,   # only update height (aspect may change between runs)
    },
    {
        "name":    "wt_mixing",
        "source":  FIG_DIR / "figure2_wt_mixing_panel.png",
        "ids":     ["image1-8"],
        "resize":  True,         # update both width and height
        "adjust_height": False,
    },
    {
        "name":    "wt_exposure",
        "source":  FIG_DIR / "figure2_wt_exposure_panel.png",
        "ids":     ["image1-1"],
        "resize":  True,
        "adjust_height": False,
    },
]

# ── nomenclature replacements ──────────────────────────────────────────────────

TEXT_REPLACEMENTS: list[tuple[str, str]] = [
    ("Intergenerational rotation", "Apical axis"),
    ("mean shift",                 "reorientation"),
    ("Fixed-axis",                 "Spindle orientation"),
    ("variance sweep",             "variance"),
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


def _get_image_attr(svg: str, image_id: str, attr: str) -> str | None:
    pattern = re.compile(
        r'<image(?=[^>]*\bid="' + re.escape(image_id) + r'"[^>]*>)[^>]*>',
        re.DOTALL,
    )
    m = pattern.search(svg)
    if not m:
        return None
    tag = m.group(0)
    av = re.search(rf'\b{re.escape(attr)}="([^"]*)"', tag)
    return av.group(1) if av else None


def _replace_tspan_text(svg: str, old: str, new: str) -> tuple[str, int]:
    pattern = re.compile(
        r'(<tspan[^>]*>)' + re.escape(old) + r'(</tspan>)'
    )
    result, n = pattern.subn(rf'\g<1>{new}\g<2>', svg)
    return result, n


# ── main ───────────────────────────────────────────────────────────────────────

def build() -> None:
    svg = TEMPLATE_SVG.read_text(encoding="utf-8")

    display_w_mm = SCALE_FACTOR * FIGSIZE_W_IN * 25.4
    print(f"Target display width for resized panels: {display_w_mm:.2f} mm  "
          f"(scale {SCALE_FACTOR}, figsize {FIGSIZE_W_IN} in)")

    # ── 1. swap bitmap panels ──────────────────────────────────────────────────
    for panel in PANELS:
        source: Path = panel["source"]
        if not source.exists():
            raise FileNotFoundError(f"Panel source not found: {source}")

        png_w, png_h = _get_png_size(source)
        png_aspect   = png_w / png_h

        new_w: float | None = None
        new_h: float | None = None

        if panel.get("resize"):
            new_w = display_w_mm
            new_h = display_w_mm / png_aspect
            print(f"  [{panel['name']}] display: {new_w:.2f} × {new_h:.2f} mm  "
                  f"(PNG {png_w}×{png_h}, aspect {png_aspect:.3f})")

        elif panel.get("adjust_height"):
            # Read current SVG width, derive height from PNG aspect
            for image_id in panel["ids"]:
                svg_w_str = _get_image_attr(svg, image_id, "width")
                if svg_w_str:
                    svg_w  = float(svg_w_str)
                    new_h  = svg_w / png_aspect
                    old_h_str = _get_image_attr(svg, image_id, "height")
                    old_h  = float(old_h_str) if old_h_str else None
                    print(f"  [{panel['name']}] height: {old_h:.3f} → {new_h:.3f} mm "
                          f"(aspect {png_w}/{png_h} = {png_aspect:.4f})")

        data_uri = _png_to_data_uri(source)
        for image_id in panel["ids"]:
            svg = _replace_image_element(svg, image_id, data_uri,
                                         new_width=new_w, new_height=new_h)

        print(f"Embedded {source.name} ({png_w}×{png_h}) → ids: {panel['ids']}")

    # ── 2. update nomenclature in hand-drawn text ──────────────────────────────
    print()
    for old, new in TEXT_REPLACEMENTS:
        svg, n = _replace_tspan_text(svg, old, new)
        if n:
            print(f"Text: {old!r:40s} → {new!r}  [{n} replacement(s)]")

    # ── 3. write ───────────────────────────────────────────────────────────────
    OUTPUT_SVG.write_text(svg, encoding="utf-8")
    print(f"\nWrote {OUTPUT_SVG}")
    print()
    print("Reminders:")
    print("  • figure2_wt_composition_panel.png is NOT yet embedded — add in Inkscape.")
    print(f"  • Mixing/exposure boxes are now {display_w_mm:.1f} mm wide; expand canvas and realign in Inkscape.")


if __name__ == "__main__":
    build()
