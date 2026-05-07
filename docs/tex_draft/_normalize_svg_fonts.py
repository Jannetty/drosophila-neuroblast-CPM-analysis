"""Normalize font sizes in Inkscape assembly SVGs to a universal 3-tier style guide.

Tiers are derived from docs/tex_draft/_style.py at the standard scale factor (0.40):
    effective print size = FONT_SIZE_TITLE(20pt) × scale(0.40) = 8pt

    SVG_TITLE = 8.0 pt = 2.8222 px  (1pt = 0.35278mm; 1px ≈ 1mm in these SVGs)
    SVG_LABEL = 6.4 pt = 2.2578 px  (= TITLE × 16/20, matching FONT_SIZE_LABEL)
    SVG_SMALL = 5.2 pt = 1.8344 px  (= TITLE × 13/20, matching FONT_SIZE_SMALL)

Snapping rule: a size is assigned to the highest tier whose value is within ±15%
of that size.  Sizes outside all tier windows fall back to nearest-tier (handles
legacy large values such as the 12pt text in fig4/fig5 before those panels are
resized).

Run: uv run python docs/tex_draft/_normalize_svg_fonts.py --dry-run
     uv run python docs/tex_draft/_normalize_svg_fonts.py
     uv run python docs/tex_draft/_normalize_svg_fonts.py fig1/fig1.svg fig2/fig2.svg
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIGS = REPO_ROOT / "docs" / "tex_draft" / "figures"

# ── universal tier values ──────────────────────────────────────────────────────
_PT_TO_PX = 0.35278          # 1pt = 0.35278mm = 0.35278px in these SVGs
SVG_TITLE = 8.0 * _PT_TO_PX  # 2.8222 px
SVG_LABEL = SVG_TITLE * 16 / 20
SVG_SMALL = SVG_TITLE * 13 / 20
TIERS = (SVG_TITLE, SVG_LABEL, SVG_SMALL)

ALL_SVG_FILES = [
    "fig1/fig1.svg",
    "fig2/fig2.svg",
    "fig3/fig3.svg",
    "fig4/fig4.svg",
    "fig5/fig5.svg",
]

FONT_SIZE_PAT = re.compile(r"font-size:(\d+\.?\d*)px")

# Tolerance for tier matching (fraction of tier value).
# A size is assigned to the highest tier it's within ±TOLERANCE of.
TOLERANCE = 0.15

# Font-family strings to normalize → Helvetica
_BAD_FAMILIES = [
    "font-family:Sans",
    "font-family:Arial, Helvetica, 'DejaVu Sans', sans-serif",
    "font-family:sans-serif",
]


def snap_to_tier(size: float) -> float:
    for tier in TIERS:
        if abs(size - tier) / tier <= TOLERANCE:
            return tier
    return min(TIERS, key=lambda t: abs(size - t))


def normalize_svg(path: Path, dry_run: bool) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    counts: dict[str, int] = {"font_size": 0, "font_family": 0}

    new_text = text
    for bad in _BAD_FAMILIES:
        if bad in new_text:
            n = new_text.count(bad)
            counts["font_family"] += n
            if not dry_run:
                new_text = new_text.replace(bad, "font-family:Helvetica")

    def replace(m: re.Match) -> str:
        original = float(m.group(1))
        snapped = snap_to_tier(original)
        # Use 1e-3 tolerance: ignores rounding noise (e.g. 2.822 vs 2.8222)
        # while catching real tier differences (tiers are ≥0.4px apart).
        if abs(snapped - original) > 1e-3:
            counts["font_size"] += 1
            return f"font-size:{snapped:.5g}px"
        return m.group(0)

    new_text = FONT_SIZE_PAT.sub(replace, new_text)
    if not dry_run and (counts["font_size"] or counts["font_family"]):
        path.write_text(new_text, encoding="utf-8")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Report changes without writing")
    parser.add_argument("svgs", nargs="*",
                        help="Relative paths under figures/ (default: all five)")
    args = parser.parse_args()

    targets = args.svgs if args.svgs else ALL_SVG_FILES

    print(f"Universal tiers: "
          f"TITLE {SVG_TITLE:.4f}px ({SVG_TITLE/_PT_TO_PX:.1f}pt)  "
          f"LABEL {SVG_LABEL:.4f}px ({SVG_LABEL/_PT_TO_PX:.1f}pt)  "
          f"SMALL {SVG_SMALL:.4f}px ({SVG_SMALL/_PT_TO_PX:.1f}pt)")
    print()

    for rel in targets:
        path = FIGS / rel
        if not path.exists():
            print(f"SKIP (not found): {rel}")
            continue
        counts = normalize_svg(path, dry_run=args.dry_run)
        verb = "would change" if args.dry_run else "changed"
        print(f"{rel}: {verb} {counts['font_size']} font-size, "
              f"{counts['font_family']} font-family")


if __name__ == "__main__":
    main()
