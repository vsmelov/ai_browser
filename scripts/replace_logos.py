#!/usr/bin/env python3
"""
Replace all logo/icon files in packages/browseros/resources/icons with a resized
version of a base logo (new_logos/logo.png), preserving each file's dimensions
and format.
"""

import re
import base64
import io
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Install Pillow: pip install Pillow")

# Paths relative to repo root (script is in scripts/)
REPO_ROOT = Path(__file__).resolve().parent.parent
BASE_LOGO = REPO_ROOT / "new_logos" / "logo.png"
ICONS_DIR = REPO_ROOT / "packages" / "browseros" / "resources" / "icons"

# Size from filename patterns: product_logo_24.png -> 24, appicon_128.png -> 128
SIZE_PATTERN = re.compile(r"_(\d+)(?:_\d+x)?(?:_2x)?\.(png|svg|ico|xpm)$", re.I)
SIZE_PATTERN_ALT = re.compile(r"(\d+)x(\d+)(?:@2x)?\.(png|svg)$", re.I)


def get_target_size_from_path(file_path: Path) -> tuple[int, int] | None:
    """Infer (width, height) from filename. Returns None if unknown."""
    name = file_path.name
    # product_logo_24.png, product_logo_32.xpm, appicon_128.png
    m = SIZE_PATTERN.search(name)
    if m:
        s = int(m.group(1))
        return (s, s)
    # icon_256x256.png, icon_256x256@2x.png
    m = SIZE_PATTERN_ALT.search(name)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        if "@2x" in name.lower():
            w, h = w * 2, h * 2
        return (w, h)
    return None


def get_target_size_from_image(file_path: Path) -> tuple[int, int] | None:
    """Read image dimensions from file."""
    try:
        with Image.open(file_path) as im:
            return (im.width, im.height)
    except Exception:
        return None


def get_target_size(file_path: Path) -> tuple[int, int] | None:
    """Get target (width, height) from filename or existing image."""
    size = get_target_size_from_path(file_path)
    if size:
        return size
    return get_target_size_from_image(file_path)


def resize_logo(logo: Image.Image, width: int, height: int) -> Image.Image:
    """Resize logo to exact dimensions with high-quality resampling."""
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS
    return logo.resize((width, height), resample)


def replace_png(logo: Image.Image, dest: Path, width: int, height: int) -> bool:
    """Replace a PNG file with resized logo."""
    try:
        out = resize_logo(logo, width, height)
        if out.mode == "RGBA":
            out.save(dest, "PNG", optimize=True)
        else:
            out.convert("RGBA").save(dest, "PNG", optimize=True)
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def replace_ico(logo: Image.Image, dest: Path, sizes: list[tuple[int, int]] | None) -> bool:
    """Replace an ICO file. If sizes is None, read from existing file or use default set."""
    if sizes is None and dest.exists():
        try:
            with Image.open(dest) as im:
                sizes = getattr(im, "sizes", None) or [(im.width, im.height)]
        except Exception:
            sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    if sizes is None:
        sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    try:
        images = [resize_logo(logo, w, h) for w, h in sizes]
        images[0].save(dest, "ICO", sizes=[(im.width, im.height) for im in images])
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def image_to_xpm(im: Image.Image, name: str = "logo") -> str:
    """Convert PIL Image to XPM string (indexed color)."""
    im = im.convert("RGBA")
    w, h = im.size
    pix = im.load()
    colors = {}
    for y in range(h):
        for x in range(w):
            p = pix[x, y]
            if p not in colors:
                colors[p] = len(colors)
    ncolors = len(colors)
    cpp = 1 if ncolors <= 95 else 2  # chars per pixel
    color_list = sorted(colors.items(), key=lambda x: x[1])
    lines = [
        "/* XPM */",
        f'static char *{name}[] = {{',
        "/* columns rows colors chars-per-pixel */",
        f'"{w} {h} {ncolors} {cpp} ",',
    ]
    for i, (rgba, _) in enumerate(color_list):
        if len(rgba) == 4 and rgba[3] == 0:
            c = "None"
        else:
            r, g, b = rgba[0], rgba[1], rgba[2]
            c = f"#{r:02x}{g:02x}{b:02x}"
        if cpp == 1:
            ch = chr(32 + i)
        else:
            ch = chr(32 + (i // 95)) + chr(32 + (i % 95))
        lines.append(f'"{ch} c {c}",')
    for y in range(h):
        row = []
        for x in range(w):
            idx = colors[pix[x, y]]
            if cpp == 1:
                row.append(chr(32 + idx))
            else:
                row.append(chr(32 + (idx // 95)) + chr(32 + (idx % 95)))
        lines.append('"' + "".join(row) + '",')
    lines[-1] = lines[-1].rstrip(",")
    lines.append("};")
    return "\n".join(lines)


def replace_xpm(logo: Image.Image, dest: Path, width: int, height: int) -> bool:
    """Replace an XPM file with resized logo."""
    try:
        out = resize_logo(logo, width, height)
        name = dest.stem.replace("-", "_")
        xpm_str = image_to_xpm(out, name)
        dest.write_text(xpm_str, encoding="utf-8")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def replace_svg(logo: Image.Image, dest: Path, width: int, height: int) -> bool:
    """Replace SVG with one that embeds the resized logo as PNG (data URI)."""
    try:
        out = resize_logo(logo, width, height)
        buf = io.BytesIO()
        out.save(buf, "PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <image width="{width}" height="{height}" href="data:image/png;base64,{b64}"/>
</svg>'''
        dest.write_text(svg, encoding="utf-8")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def should_replace(path: Path) -> bool:
    """Return True to replace this file (replace all icons by default)."""
    return True


def main() -> None:
    if not BASE_LOGO.exists():
        raise SystemExit(f"Base logo not found: {BASE_LOGO}")

    if not ICONS_DIR.exists():
        raise SystemExit(f"Icons dir not found: {ICONS_DIR}")

    logo = Image.open(BASE_LOGO).convert("RGBA")
    print(f"Base logo: {BASE_LOGO} ({logo.width}x{logo.height})")
    print(f"Icons dir: {ICONS_DIR}\n")

    replaced = 0
    skipped = 0
    failed = 0

    for path in sorted(ICONS_DIR.rglob("*")):
        if not path.is_file():
            continue
        suf = path.suffix.lower()
        if suf not in (".png", ".ico", ".xpm", ".svg"):
            continue
        if not should_replace(path):
            print(f"Skip (non-logo): {path.relative_to(REPO_ROOT)}")
            skipped += 1
            continue

        size = get_target_size(path)
        if not size:
            # Fallback: SVG or unreadable -> 256; small tiles -> 128
            if suf == ".svg":
                size = (256, 256)
            else:
                print(f"Skip (unknown size): {path.relative_to(REPO_ROOT)}")
                skipped += 1
                continue

        w, h = size
        rel = path.relative_to(REPO_ROOT)
        ok = False
        if suf == ".png":
            ok = replace_png(logo, path, w, h)
        elif suf == ".ico":
            ok = replace_ico(logo, path, [size])
        elif suf == ".xpm":
            ok = replace_xpm(logo, path, w, h)
        elif suf == ".svg":
            ok = replace_svg(logo, path, w, h)

        if ok:
            print(f"OK {rel} -> {w}x{h}")
            replaced += 1
        else:
            print(f"FAIL {rel}")
            failed += 1

    # Also replace root logo.png for docs
    root_logo = REPO_ROOT / "packages" / "browseros" / "resources" / "logo.png"
    if root_logo.exists():
        try:
            with Image.open(root_logo) as im:
                w, h = im.width, im.height
        except Exception:
            w, h = 256, 256
        if replace_png(logo, root_logo, w, h):
            print(f"OK {root_logo.relative_to(REPO_ROOT)} -> {w}x{h}")
            replaced += 1

    print(f"\nDone: {replaced} replaced, {skipped} skipped, {failed} failed.")


if __name__ == "__main__":
    main()
