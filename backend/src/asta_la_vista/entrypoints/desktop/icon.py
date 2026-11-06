"""Draws the app icon (the favicon: a white "A" on a green rounded square) with Pillow.

Drawing it in code avoids committing binary images: the build script saves it as the PNG that
PyInstaller turns into the ``.ico``/``.icns`` icons of the executable, the window and the Dock.
"""

from PIL import Image, ImageDraw

_GREEN = "#204c39"
_WHITE = "#f7f8f5"
# Same geometry as frontend/src/lib/assets/favicon.svg, on a 64x64 grid.
_LETTER = [(17, 46), (28, 17), (36, 17), (47, 46), (39, 46), (37, 39), (26, 39), (24, 46)]
_COUNTER = [(28, 32), (35, 32), (32, 22)]


def render(size: int = 256) -> Image.Image:
    scale = size * 4 / 64  # draw large, then downsample for smooth edges
    big = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(big)
    draw.rounded_rectangle((0, 0, size * 4 - 1, size * 4 - 1), radius=14 * scale, fill=_GREEN)
    draw.polygon([(x * scale, y * scale) for x, y in _LETTER], fill=_WHITE)
    draw.polygon([(x * scale, y * scale) for x, y in _COUNTER], fill=_GREEN)
    return big.resize((size, size), Image.Resampling.LANCZOS)
