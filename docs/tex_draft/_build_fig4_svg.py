"""Compositor for docs/tex_draft/figures/fig4/fig4.svg.

Swaps the matplotlib bitmap panels into the hand-authored SVG template.
Run this whenever a matplotlib panel is regenerated.

Run:
    uv run python docs/tex_draft/_build_fig4_svg.py

Layout of fig4.svg  (canvas 186.35728 × 204.89467 mm)
------------------
Top    (x 0–186 mm, y 0–62 mm)   : Panel A — VCV schematic (inline matplotlib SVG, not a <image>)
Middle (x 0–186 mm, y 62–113 mm) : figure4_metrics_grid_panel        [id: image1]
Bottom (x 0–177 mm, y 113–208 mm): figure4_representative_lineages_panel [id: image1-3]

Panel D (figure4_best_vs_exp_panel) is NOT yet in the SVG — add in Inkscape.

Box widths are kept fixed (full canvas); only heights are updated from PNG aspect.
Target scale: figsize_B=18.4in, figsize_C=17.4in at scale=0.40 → 8pt effective.
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
FIG4_DIR  = FIG_DIR / "fig4"

TEMPLATE_SVG = FIG4_DIR / "fig4.svg"
OUTPUT_SVG   = FIG4_DIR / "fig4.svg"

# ── panel definitions ──────────────────────────────────────────────────────────

PANELS: list[dict] = [
    {
        "name":          "metrics_grid",
        "source":        FIG_DIR / "figure4_metrics_grid_panel.png",
        "ids":           ["image1"],
        "adjust_height": True,   # keep SVG box width, update height from PNG aspect
    },
    {
        "name":          "repr_lineages",
        "source":        FIG_DIR / "figure4_representative_lineages_panel.png",
        "ids":           ["image1-3"],
        "adjust_height": True,
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

    for panel in PANELS:
        source: Path = panel["source"]
        if not source.exists():
            raise FileNotFoundError(f"Panel source not found: {source}")

        png_w, png_h = _get_png_size(source)
        png_aspect   = png_w / png_h

        new_w: float | None = None
        new_h: float | None = None

        if panel.get("adjust_height"):
            for image_id in panel["ids"]:
                svg_w_str = _get_image_attr(svg, image_id, "width")
                if svg_w_str:
                    svg_w = float(svg_w_str)
                    new_h = svg_w / png_aspect
                    old_h_str = _get_image_attr(svg, image_id, "height")
                    old_h = float(old_h_str) if old_h_str else None
                    print(f"  [{panel['name']}] width={svg_w:.3f} mm, "
                          f"height: {old_h:.3f} → {new_h:.3f} mm "
                          f"(PNG {png_w}×{png_h}, aspect {png_aspect:.4f})")

        data_uri = _png_to_data_uri(source)
        for image_id in panel["ids"]:
            svg = _replace_image_element(svg, image_id, data_uri,
                                         new_width=new_w, new_height=new_h)
        print(f"Embedded {source.name} ({png_w}×{png_h}) → ids: {panel['ids']}")

    OUTPUT_SVG.write_text(svg, encoding="utf-8")
    print(f"\nWrote {OUTPUT_SVG}")
    print()
    print("Reminders:")
    print("  • Panel A (VCV schematic) is inline SVG — not updated by this script.")
    print("  • figure4_best_vs_exp_panel is NOT yet in the SVG — add in Inkscape.")
    print("  • Realign panels in Inkscape after running (heights changed).")


if __name__ == "__main__":
    build()
