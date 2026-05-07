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

NOTE – composition panel:
    figure2_wt_composition_panel.png is NOT currently embedded in fig2.svg.
    It needs to be added as a new <image> element in Inkscape.

NOTE – geometry examples aspect ratio:
    Old embedded panel: 4036×3377 px  (aspect 1.195, wider-than-tall)
    New panel:          4086×4449 px  (aspect 0.918, taller-than-wide)
    The SVG bounding box is 135.9×113.7 mm (aspect 1.195).  Embedding the new
    panel into this box will distort it.  The script adjusts the box height to
    preserve the correct aspect at the current width, which shifts everything
    below.  Review in Inkscape after running and extend the canvas if needed.

Text replacements (hand-drawn SVG labels):
    "Intergenerational rotation" + "mean shift"  →  "Apical axis" + "reorientation"
    "Fixed-axis" + "variance sweep"              →  "Spindle orientation" + "variance"
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]
TEX_DIR   = REPO_ROOT / "docs" / "tex_draft"
FIG_DIR   = TEX_DIR / "figures"
FIG2_DIR  = FIG_DIR / "fig2"

TEMPLATE_SVG = FIG2_DIR / "fig2.svg"
OUTPUT_SVG   = FIG2_DIR / "fig2.svg"

# ── panel definitions ──────────────────────────────────────────────────────────
# All panels are base64-embedded (no local file copies in fig2/).

PANELS: list[dict] = [
    {
        "name":    "wt_geometry_examples",
        "source":  FIG_DIR / "figure2_wt_geometry_examples_panel.png",
        "ids":     ["image1-4"],
        "adjust_height": True,   # new panel has different aspect — recompute height
    },
    {
        "name":    "wt_mixing",
        "source":  FIG_DIR / "figure2_wt_mixing_panel.png",
        "ids":     ["image1-8"],
        "adjust_height": False,
    },
    {
        "name":    "wt_exposure",
        "source":  FIG_DIR / "figure2_wt_exposure_panel.png",
        "ids":     ["image1-1"],
        "adjust_height": False,
    },
]

# ── nomenclature replacements ──────────────────────────────────────────────────
# Each tuple is (old_text, new_text) matched against tspan text content exactly.

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
    # Read PNG dimensions without PIL dependency by parsing the IHDR chunk
    data = path.read_bytes()
    # PNG signature is 8 bytes, IHDR chunk starts at byte 8
    # width at bytes 16-19, height at bytes 20-23
    import struct
    w = struct.unpack(">I", data[16:20])[0]
    h = struct.unpack(">I", data[20:24])[0]
    return w, h


def _replace_image_element(svg: str, image_id: str, new_href: str,
                            new_height: float | None = None) -> str:
    """Replace xlink:href (and optionally height) in the named <image> element."""
    def patch(m: re.Match) -> str:
        tag = m.group(0)
        tag = re.sub(r'xlink:href="[^"]*"', f'xlink:href="{new_href}"', tag)
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
    """Return a named attribute value from a specific <image> element."""
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
    """Replace text content of tspan elements matching old exactly."""
    pattern = re.compile(
        r'(<tspan[^>]*>)' + re.escape(old) + r'(</tspan>)'
    )
    result, n = pattern.subn(rf'\g<1>{new}\g<2>', svg)
    return result, n


# ── main ───────────────────────────────────────────────────────────────────────

def build() -> None:
    svg = TEMPLATE_SVG.read_text(encoding="utf-8")

    # ── 1. swap bitmap panels ──────────────────────────────────────────────────
    for panel in PANELS:
        source: Path = panel["source"]
        if not source.exists():
            raise FileNotFoundError(f"Panel source not found: {source}")

        png_w, png_h = _get_png_size(source)
        png_aspect   = png_w / png_h

        new_height = None
        for image_id in panel["ids"]:
            if panel.get("adjust_height"):
                svg_w_str = _get_image_attr(svg, image_id, "width")
                if svg_w_str:
                    svg_w     = float(svg_w_str)
                    new_height = svg_w / png_aspect
                    old_h_str = _get_image_attr(svg, image_id, "height")
                    old_h     = float(old_h_str) if old_h_str else None
                    print(f"  [{panel['name']}] height: {old_h:.3f} → {new_height:.3f} mm "
                          f"(aspect {png_w}/{png_h} = {png_aspect:.4f})")

        data_uri = _png_to_data_uri(source)
        for image_id in panel["ids"]:
            svg = _replace_image_element(svg, image_id, data_uri,
                                         new_height=new_height)

        print(f"Embedded {source.name} ({png_w}×{png_h}) → ids: {panel['ids']}")

    # ── 2. update nomenclature in hand-drawn text ──────────────────────────────
    print()
    for old, new in TEXT_REPLACEMENTS:
        svg, n = _replace_tspan_text(svg, old, new)
        status = f"{n} replacement(s)" if n else "NOT FOUND — check SVG manually"
        print(f"Text: {old!r:40s} → {new!r}  [{status}]")

    # ── 3. write ───────────────────────────────────────────────────────────────
    OUTPUT_SVG.write_text(svg, encoding="utf-8")
    print(f"\nWrote {OUTPUT_SVG}")
    print()
    print("Reminders:")
    print("  • figure2_wt_composition_panel.png is NOT yet embedded — add in Inkscape.")
    print("  • Geometry examples height was adjusted; extend canvas in Inkscape if clipped.")


if __name__ == "__main__":
    build()
