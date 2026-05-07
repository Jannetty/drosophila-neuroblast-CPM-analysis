"""Compositor for docs/tex_draft/figures/fig4/fig4.svg.

Swaps the matplotlib bitmap panels into the hand-authored SVG template.
Run this whenever a matplotlib panel is regenerated.

Run:
    uv run python docs/tex_draft/_build_fig4_svg.py

Layout of fig4.svg  (canvas 186.35728 × 204.89467 mm)
------------------
Top    (x~19–167 mm, y 0–53 mm) : figure4_panel_a_draft   [inline <g id="figure_1"> → replaced with <image>]
Middle (x 0–186 mm, y 62–107 mm): figure4_metrics_grid_panel      [id: image1]
Bottom (x 0–177 mm, y 113–205 mm): figure4_representative_lineages_panel [id: image1-3]

Panel D (figure4_best_vs_exp_panel) is NOT yet in the SVG — add in Inkscape.

Panel A: the inline matplotlib SVG group (id="figure_1") is replaced with a PNG
<image> at the same position/size derived from the original embed transform:
  transform="matrix(0.16074583,0,0,0.16074583,9.3815203,8.7855515)"
  matplotlib canvas: 917.64022 × 326.52219 pt → display 147.56 × 52.50 mm

Box widths for B/C are kept fixed; only heights updated from PNG aspect.
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

# ── Panel A inline-group replacement config ────────────────────────────────────
# Original embed transform: matrix(0.16074583, 0, 0, 0.16074583, 9.3815203, 8.7855515)
# matplotlib canvas in pt:  917.64022 wide × 326.52219 tall
# → display in SVG mm:      147.556 wide × 52.497 tall at (x=9.382, y=8.786) in layer1
PANEL_A_GROUP_ID = "figure_1"
PANEL_A_X        = 9.3815203   # in layer1 local coords (mm)
PANEL_A_Y        = 8.7855515   # in layer1 local coords (mm)
PANEL_A_WIDTH    = 917.64022 * 0.16074583  # ≈ 147.556 mm

# ── panel definitions ──────────────────────────────────────────────────────────

PANELS: list[dict] = [
    {
        "name":         "panel_a",
        "source":       FIG_DIR / "figure4_panel_a_draft.png",
        "replace_group": PANEL_A_GROUP_ID,  # remove inline SVG, insert <image>
    },
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


def _find_group_bounds(svg: str, group_id: str) -> tuple[int, int]:
    """Return (start, end) byte offsets of <g id="group_id">...</g> in svg."""
    pat = re.compile(r'<g\b(?=[^>]*\bid="' + re.escape(group_id) + r'")[^>]*>', re.DOTALL)
    m = pat.search(svg)
    if not m:
        raise ValueError(f"<g id={group_id!r}> not found in SVG")
    start = m.start()
    pos   = m.end()
    depth = 1
    while depth > 0:
        next_open  = svg.find("<g",   pos)
        next_close = svg.find("</g>", pos)
        if next_close == -1:
            raise ValueError(f"Unmatched <g> for id={group_id!r}")
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 2
        else:
            depth -= 1
            pos = next_close + 4
    return start, pos


def _replace_group_with_image(svg: str, group_id: str, data_uri: str,
                               x: float, y: float, width: float, height: float) -> str:
    start, end = _find_group_bounds(svg, group_id)
    tag = (
        f'<image\n'
        f'       id="panel_a"\n'
        f'       x="{x:.6f}"\n'
        f'       y="{y:.6f}"\n'
        f'       width="{width:.6f}"\n'
        f'       height="{height:.6f}"\n'
        f'       preserveAspectRatio="none"\n'
        f'       xlink:href="{data_uri}" />'
    )
    return svg[:start] + tag + svg[end:]


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
        data_uri     = _png_to_data_uri(source)

        if panel.get("replace_group"):
            # Panel A: replace inline SVG group with PNG <image>
            display_w = PANEL_A_WIDTH
            display_h = display_w / png_aspect
            print(f"  [panel_a] replacing <g id=\"{panel['replace_group']}\"> with PNG image")
            print(f"    position: x={PANEL_A_X:.3f}, y={PANEL_A_Y:.3f} mm (layer1 coords)")
            print(f"    display:  {display_w:.2f} × {display_h:.2f} mm  "
                  f"(PNG {png_w}×{png_h}, aspect {png_aspect:.4f})")
            svg = _replace_group_with_image(svg, panel["replace_group"], data_uri,
                                            PANEL_A_X, PANEL_A_Y, display_w, display_h)
            print(f"Embedded {source.name} ({png_w}×{png_h}) → replaced group id={panel['replace_group']!r}")

        elif panel.get("adjust_height"):
            new_w: float | None = None
            new_h: float | None = None
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
            for image_id in panel["ids"]:
                svg = _replace_image_element(svg, image_id, data_uri,
                                             new_width=new_w, new_height=new_h)
            print(f"Embedded {source.name} ({png_w}×{png_h}) → ids: {panel['ids']}")

    OUTPUT_SVG.write_text(svg, encoding="utf-8")
    print(f"\nWrote {OUTPUT_SVG}")
    print()
    print("Reminders:")
    print("  • figure4_best_vs_exp_panel is NOT yet in the SVG — add in Inkscape.")
    print("  • Panel A is now a PNG <image id='panel_a'>; realign in Inkscape if needed.")


if __name__ == "__main__":
    build()
