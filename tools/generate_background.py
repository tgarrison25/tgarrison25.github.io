"""
Wall Drawing: 54 dissections of the 3x3 square.

Executed from written instructions:

    Take a square, three units by three units, ruled into a 3x3 grid of unit
    cells. Consider every way to partition the square into rectangles whose
    corners fall on grid points. Two partitions are the same if one becomes the
    other by a rotation (90, 180, 270) or a reflection of the square; keep only
    one from each such family. There are exactly fifty-four. Draw all fifty-four,
    arranged in a grid of nine columns and six rows, in order of increasing
    complexity. Glue the squares together into a super-rectangle where the
    squares meet at the edges. Color the regions of each with bright hues --
    red, blue, yellow -- so that no two regions sharing an edge share a color,
    using the fewest colors the drawing allows.

Two things here are computed, not assumed:

  * that there are exactly fifty-four dissections up to symmetry, and
  * how many colors the glued figure needs.

The gluing happens before the coloring, so the adjacency constraint crosses the
seams between squares and the whole super-rectangle is one graph. Minimality is
settled by SAT: a proper 3-coloring is shown to be impossible before a 4-coloring
is accepted.

Writes ../assets/mondrian.svg
"""

from pathlib import Path

from pysat.solvers import Minisat22

N = 3
COLS, ROWS = 9, 6

# Bright hues. The fourth is only reached if the figure forces it -- and it does.
PALETTE = ["#F5334E", "#1F8FF5", "#FFD21E", "#2ECC5B"]
PALETTE_NAMES = ["red", "blue", "yellow", "green"]
INK = "#111111"


# -- every partition of the square into rectangles -------------------------

def all_tilings():
    """Exact cover of the NxN cells by axis-aligned rectangles."""
    full = (1 << (N * N)) - 1
    out = []

    def bit(x, y):
        return 1 << (y * N + x)

    def rec(covered, rects):
        if covered == full:
            out.append(tuple(sorted(rects)))
            return
        # Always fill the first uncovered cell, so each tiling is built once.
        idx = next(i for i in range(N * N) if not (covered >> i) & 1)
        cy, cx = divmod(idx, N)
        for w in range(1, N - cx + 1):
            for h in range(1, N - cy + 1):
                mask, ok = 0, True
                for dy in range(h):
                    for dx in range(w):
                        b = bit(cx + dx, cy + dy)
                        if covered & b:
                            ok = False
                            break
                        mask |= b
                    if not ok:
                        break
                if ok:
                    rec(covered | mask, rects + [(cx, cy, cx + w, cy + h)])

    rec(0, [])
    return out


# -- reduce modulo the symmetries of the square ----------------------------

SYMMETRIES = [
    lambda x, y: (x, y),
    lambda x, y: (y, N - x),
    lambda x, y: (N - x, N - y),
    lambda x, y: (N - y, x),
    lambda x, y: (N - x, y),
    lambda x, y: (x, N - y),
    lambda x, y: (y, x),
    lambda x, y: (N - y, N - x),
]


def apply_sym(tiling, f):
    moved = []
    for x1, y1, x2, y2 in tiling:
        ax, ay = f(x1, y1)
        bx, by = f(x2, y2)
        moved.append((min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)))
    return tuple(sorted(moved))


def canonical(tiling):
    return min(apply_sym(tiling, f) for f in SYMMETRIES)


# -- the glued figure -------------------------------------------------------

def glue(classes):
    """Lay the dissections out 9 x 6 and return every region in absolute units."""
    regions = []
    for idx, tiling in enumerate(classes):
        ox, oy = (idx % COLS) * N, (idx // COLS) * N
        for x1, y1, x2, y2 in tiling:
            regions.append((ox + x1, oy + y1, ox + x2, oy + y2, idx))
    return regions


def adjacent(a, b):
    """True if two regions share a boundary segment of positive length."""
    ax1, ay1, ax2, ay2 = a[:4]
    bx1, by1, bx2, by2 = b[:4]
    if ax2 == bx1 or bx2 == ax1:                     # vertical contact
        return min(ay2, by2) - max(ay1, by1) > 0
    if ay2 == by1 or by2 == ay1:                     # horizontal contact
        return min(ax2, bx2) - max(ax1, bx1) > 0
    return False


def build_edges(regions, wrap=True):
    """Adjacency over the whole super-rectangle, seams included.

    With wrap=True the figure is treated as a torus: the right edge is adjacent to
    the left and the bottom to the top. The drawing is used as a repeating CSS
    background, so without this the tile's own edges meet copies of themselves and
    like colors end up touching across the repeat.
    """
    n = len(regions)
    W, H = COLS * N, ROWS * N
    edges = set()

    for i in range(n):
        for j in range(i + 1, n):
            if adjacent(regions[i], regions[j]):
                edges.add((i, j))

    if wrap:
        for i in range(n):
            ax1, ay1, ax2, ay2 = regions[i][:4]
            for j in range(n):
                if i == j:
                    continue
                bx1, by1, bx2, by2 = regions[j][:4]
                if ax1 == 0 and bx2 == W and min(ay2, by2) - max(ay1, by1) > 0:
                    edges.add((min(i, j), max(i, j)))
                if ay1 == 0 and by2 == H and min(ax2, bx2) - max(ax1, bx1) > 0:
                    edges.add((min(i, j), max(i, j)))

    return sorted(edges)


# -- coloring ---------------------------------------------------------------

def try_coloring(n, edges, k):
    """Proper k-coloring of the whole figure via SAT, or None if impossible."""
    def var(v, c):
        return v * k + c + 1

    with Minisat22(bootstrap_with=[]) as s:
        for v in range(n):
            s.add_clause([var(v, c) for c in range(k)])          # some color
            for c in range(k):
                for d in range(c + 1, k):
                    s.add_clause([-var(v, c), -var(v, d)])       # only one
        for u, v in edges:
            for c in range(k):
                s.add_clause([-var(u, c), -var(v, c)])           # not equal
        if k > 1:
            s.add_clause([var(0, 0)])                            # break symmetry

        if not s.solve():
            return None
        model = set(l for l in s.get_model() if l > 0)
        return [next(c for c in range(k) if var(v, c) in model) for v in range(n)]


def fewest_colors(n, edges):
    for k in range(1, len(PALETTE) + 1):
        colors = try_coloring(n, edges, k)
        if colors is not None:
            return k, colors
        print(f"  {k} colors: proved impossible")
    raise AssertionError("four colors should always suffice for a planar figure")


# -- draw -------------------------------------------------------------------

def to_svg(regions, colors, unit=40):
    """unit only sets the intrinsic display size; the viewBox stays in grid units,
    so the CSS background is unaffected by it."""
    w, h = COLS * N, ROWS * N
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w * unit}" height="{h * unit}">',
        '  <!-- The 54 dissections of the 3x3 square, one per symmetry class,',
        '       ordered by increasing complexity, glued into one rectangle and',
        '       then properly colored as a single figure across the seams.',
        '       Generated by tools/generate_background.py -->',
        f'  <rect width="{w}" height="{h}" fill="{PALETTE[0]}"/>',
        f'  <g stroke="{INK}" stroke-width="0.11" stroke-linejoin="miter" '
        'shape-rendering="crispEdges">',
    ]
    current = -1
    for (x1, y1, x2, y2, which), c in zip(regions, colors):
        if which != current:
            current = which
            lines.append(f'    <!-- {which + 1} -->')
        lines.append(
            f'    <rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" '
            f'fill="{PALETTE[c]}"/>'
        )
    lines.append('  </g>')
    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def main():
    raw = all_tilings()
    classes = sorted({canonical(t) for t in raw})
    assert len(classes) == 54, f"expected fifty-four, enumerated {len(classes)}"

    # Increasing complexity: fewer rectangles first, then a stable tiebreak.
    classes.sort(key=lambda t: (len(t), t))

    regions = glue(classes)
    edges = build_edges(regions)
    print(f"{len(raw)} partitions, {len(classes)} up to symmetry")
    print(f"glued figure: {len(regions)} regions, {len(edges)} shared edges")

    k, colors = fewest_colors(len(regions), edges)
    print(f"  {k} colors: {', '.join(PALETTE_NAMES[:k])}")

    # Independent check of the drawing that actually gets written.
    for u, v in edges:
        assert colors[u] != colors[v], "adjacent regions share a color"

    out = Path(__file__).resolve().parent.parent / "assets" / "mondrian.svg"
    out.write_text(to_svg(regions, colors), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
