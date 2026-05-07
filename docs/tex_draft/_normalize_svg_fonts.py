"""Normalize font sizes in Inkscape assembly SVGs to 3-tier style guide values.

Each SVG has its own TITLE size (the largest existing size), from which LABEL
and SMALL are derived using the 20:16:13 ratios. Sizes within ±5% of a tier
boundary are snapped to that tier.

Run: uv run python docs/tex_draft/_normalize_svg_fonts.py --dry-run
     uv run python docs/tex_draft/_normalize_svg_fonts.py
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIGS = REPO_ROOT / "docs" / "tex_draft" / "figures"

# (TITLE_px, LABEL_px, SMALL_px) per SVG, derived from the largest existing size
SVG_TIERS: dict[str, tuple[float, float, float]] = {
    "fig1/fig1.svg":  (2.9,      2.9 * 16 / 20,      2.9 * 13 / 20),
    "fig2/fig2.svg":  (2.82222,  2.82222 * 16 / 20,  2.82222 * 13 / 20),
    "fig3/fig3.svg":  (2.50329,  2.50329 * 16 / 20,  2.50329 * 13 / 20),
    "fig4/fig4.svg":  (4.23333,  4.23333 * 16 / 20,  4.23333 * 13 / 20),
    "fig5/fig5.svg":  (4.23333,  4.23333 * 16 / 20,  4.23333 * 13 / 20),
}

FONT_SIZE_PAT = re.compile(r"font-size:(\d+\.?\d*)px")


def nearest_tier(size: float, title: float, label: float, small: float) -> float:
    return min([title, label, small], key=lambda t: abs(size - t))


def normalize_svg(path: Path, tiers: tuple[float, float, float], dry_run: bool) -> int:
    title, label, small = tiers
    text = path.read_text(encoding="utf-8")
    changes = 0

    # Fix stray font-family:Sans → font-family:Helvetica
    if "font-family:Sans" in text:
        if not dry_run:
            text = text.replace("font-family:Sans", "font-family:Helvetica")
        changes += text.count("font-family:Sans")

    def replace(m: re.Match) -> str:
        nonlocal changes
        original = float(m.group(1))
        snapped = nearest_tier(original, title, label, small)
        if abs(snapped - original) > 1e-6:
            changes += 1
            return f"font-size:{snapped:.5g}px"
        return m.group(0)

    new_text = FONT_SIZE_PAT.sub(replace, text)
    if not dry_run and changes:
        path.write_text(new_text, encoding="utf-8")
    return changes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    args = parser.parse_args()

    for rel, tiers in SVG_TIERS.items():
        path = FIGS / rel
        if not path.exists():
            print(f"SKIP (not found): {rel}")
            continue
        n = normalize_svg(path, tiers, dry_run=args.dry_run)
        verb = "would change" if args.dry_run else "changed"
        tiers_fmt = tuple(f"{t:.4g}" for t in tiers)
        print(f"{rel}: {verb} {n} values  (tiers: {tiers_fmt})")


if __name__ == "__main__":
    main()
