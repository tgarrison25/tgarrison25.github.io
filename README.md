# Personal site

Static HTML and CSS. No build step, no dependencies, no JavaScript.

## Layout

```
index.html          Home
research/           Publications and preprints
talks/              Talks and slides
blog/               Post index + one post per file
photos/             Image grid
teaching/           Courses           (under "More")
cv/                 CV                (under "More")
404.html            Shown for bad URLs on GitHub Pages
css/style.css       All styling
assets/             Images, PDFs
```

## Editing

Every page is a complete HTML file. The navigation is copied into each one — if you
add or rename a tab you have to change it in all nine files. That is the cost of not
having a build step; find-and-replace handles it.

Mark the current page in the nav with `aria-current="page"` so it renders bold.

**New blog post:** copy `tools/post-template.html` into `blog/`, rename it, and change
the `<title>` and `<h1>`. The template lives outside `blog/` on purpose, so a draft is
never listed as a real post.

Then list it in `blog/index.html`, replacing the "nothing here yet" paragraph with:

```html
<ul class="post-list">
  <li>
    <time datetime="2026-09-01">Sep 2026</time>
    <a href="/blog/your-post.html">Your post title</a>
  </li>
</ul>
```

**Photos:** put images in `assets/photos/` and point the `<img src>` at them. Resize
to ~1600px wide first.

**Colors and fonts:** the variables at the top of `css/style.css`. Dark mode is a
second block of the same variables under `prefers-color-scheme: dark`.

**Background:** `assets/mondrian.svg` is generated, not hand-drawn — do not edit it
directly. Regenerate with:

```bash
python tools/generate_background.py
```

The script executes a written instruction in the Sol LeWitt manner: enumerate every
partition of a 3×3 square into rectangles on grid points, reduce modulo the eight
symmetries of the square, lay the survivors out 9×6 in order of increasing
complexity, glue them edge to edge, and color the resulting figure so that no two
regions sharing an edge share a hue.

Two facts are computed rather than assumed. There are exactly 54 dissections up to
symmetry (out of 322 total). The glued figure has 291 regions and 650 shared edges,
and needs **four** colors — the script proves 1, 2, and 3 unsatisfiable by SAT before
accepting 4. Because the gluing precedes the coloring, the constraint crosses the
seams; coloring each square independently would have needed only three.

Two knobs in `css/style.css`:

- `--pattern-opacity` — `0` turns it off, `0.38` is the light-mode default, `1` is
  full-strength. Dark mode has its own value.
- `--pattern-size` — width of the 27×18 tile in pixels. Height follows automatically;
  do not set it explicitly or the unit cells stop being square.

## Preview locally

```bash
python -m http.server 8000 --directory "C:\Users\thoma\Downloads\website"
```

Then open <http://localhost:8000>. Use a server rather than opening the files
directly — the pages use root-relative paths (`/css/style.css`), which do not
resolve over `file://`.

## Deploy to GitHub Pages

1. Create a GitHub account if you do not have one.
2. Create a repository named exactly `<yourusername>.github.io`, public, empty.
3. From this folder:

```bash
git init -b main && git add -A && git commit -m "Initial site" && git remote add origin https://github.com/<yourusername>/<yourusername>.github.io.git && git push -u origin main
```

4. The site is live at `https://<yourusername>.github.io` within a minute or two.

Every later `git push` redeploys automatically.

## Optional: math rendering

Add to the `<head>` of any page that needs it:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
        onload="renderMathInElement(document.body)"></script>
```

Then write `$x^2$` inline and `$$...$$` for display math.
