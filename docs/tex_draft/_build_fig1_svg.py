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

clipPath6 is defined in the SVG but is no longer referenced by any image element.
"""
from __future__ import annotations

import base64
import re
import shutil
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]
TEX_DIR   = REPO_ROOT / "docs" / "tex_draft"
FIG_DIR   = TEX_DIR / "figures"
FIG1_DIR  = FIG_DIR / "fig1"

TEMPLATE_SVG = FIG1_DIR / "fig1.svg"      # edited in-place; is also the template
OUTPUT_SVG   = FIG1_DIR / "fig1.svg"

# ── panel definitions ──────────────────────────────────────────────────────────
# Each entry describes one logical matplotlib panel.
#
# mode="file_ref"  → SVG references a local PNG by filename.
#   source   : path to the up-to-date PNG in docs/tex_draft/figures/
#   filename : the bare filename used in the SVG xlink:href attribute
#   ids      : list of SVG image element ids that carry this panel
#
# mode="base64"    → panel is embedded as a data URI inside the SVG.
#   source   : path to the up-to-date PNG
#   ids      : list of SVG image element ids

PANELS: list[dict] = [
    {
        "name": "wt_examples",
        "mode": "file_ref",
        "source": FIG_DIR / "figure1_wt_examples_panel.png",
        "filename": "figure1_wt_examples_panel.png",
        "ids": ["image1-4-4"],  # image1-4 (clipped duplicate) was removed in Inkscape
    },
    {
        "name": "wt_calibration",
        "mode": "base64",
        "source": FIG_DIR / "figure1_wt_calibration_panel.png",
        "ids": ["image1"],
    },
]

# ── helpers ────────────────────────────────────────────────────────────────────

def _png_to_data_uri(path: Path) -> str:
    """Return a data URI string for the given PNG file."""
    data = path.read_bytes()
    b64  = base64.b64encode(data).decode("ascii")
    # Inkscape wraps base64 at ~76 chars with &#10; line breaks
    wrapped = "\n".join(b64[i:i+76] for i in range(0, len(b64), 76))
    return f"data:image/png;base64,{wrapped}"


def _replace_image_element(svg: str, image_id: str, new_href: str) -> str:
    """Replace xlink:href inside the <image id="{image_id}" …> element."""
    # Match the full opening tag by id, then replace xlink:href within it
    def patch(m: re.Match) -> str:
        tag = m.group(0)
        tag = re.sub(r'xlink:href="[^"]*"', f'xlink:href="{new_href}"', tag)
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

        if panel["mode"] == "file_ref":
            dest = FIG1_DIR / panel["filename"]
            shutil.copy2(source, dest)
            print(f"Copied {source.name} → {dest}")
            # href already matches panel["filename"]; no SVG text change needed
            # (but we still run through ids in case the href had drifted)
            for image_id in panel["ids"]:
                svg = _replace_image_element(svg, image_id, panel["filename"])
            print(f"  Updated ids: {panel['ids']}")

        elif panel["mode"] == "base64":
            # Keep a local copy in the fig1 dir for reference, then embed
            dest = FIG1_DIR / source.name
            shutil.copy2(source, dest)
            data_uri = _png_to_data_uri(source)
            for image_id in panel["ids"]:
                svg = _replace_image_element(svg, image_id, data_uri)
            print(f"Copied {source.name} → {dest}"  )
            print(f"Embedded {source.name} as base64 → ids: {panel['ids']}")

    OUTPUT_SVG.write_text(svg, encoding="utf-8")
    print(f"\nWrote {OUTPUT_SVG}")


if __name__ == "__main__":
    build()
