"""Generate the app's Windows icon and matching preview image."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SIZE = 256
SCALE = 4
CANVAS = SIZE * SCALE


def point(x: float, y: float) -> tuple[int, int]:
    return round(x * SCALE), round(y * SCALE)


def gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGBA", size)
    draw = ImageDraw.Draw(image)
    height = size[1]
    for y in range(height):
        amount = y / max(1, height - 1)
        color = tuple(round(a + (b - a) * amount) for a, b in zip(top, bottom))
        draw.line((0, y, size[0], y), fill=(*color, 255))
    return image


def make_icon() -> Image.Image:
    # Deep-space tile with a softly rounded silhouette.
    background = gradient((CANVAS, CANVAS), (7, 19, 33), (13, 38, 55))
    tile_mask = Image.new("L", (CANVAS, CANVAS), 0)
    ImageDraw.Draw(tile_mask).rounded_rectangle(
        (4 * SCALE, 4 * SCALE, 252 * SCALE, 252 * SCALE),
        radius=52 * SCALE,
        fill=255,
    )
    background.putalpha(tile_mask)

    # Globe and its subtle radial grid.
    cx, cy, radius = 128, 137, 82
    globe_mask = Image.new("L", (CANVAS, CANVAS), 0)
    ImageDraw.Draw(globe_mask).ellipse(
        (point(cx - radius, cy - radius), point(cx + radius, cy + radius)), fill=255
    )
    globe = gradient((CANVAS, CANVAS), (25, 84, 101), (8, 28, 47))
    globe.putalpha(globe_mask)
    background.alpha_composite(globe)

    grid = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid)
    for width in (46, 104, 154):
        grid_draw.ellipse(
            (point(cx - width / 2, cy - radius), point(cx + width / 2, cy + radius)),
            outline=(112, 226, 224, 94),
            width=2 * SCALE,
        )
    for height in (38, 91, 145):
        grid_draw.ellipse(
            (point(cx - radius, cy - height / 2), point(cx + radius, cy + height / 2)),
            outline=(112, 226, 224, 82),
            width=2 * SCALE,
        )
    grid.putalpha(Image.composite(grid.getchannel("A"), Image.new("L", grid.size, 0), globe_mask))
    background.alpha_composite(grid)

    # Stylized Greenland and a bright fracture line suggest glacier change.
    land = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    land_draw = ImageDraw.Draw(land)
    greenland = [
        (102, 78), (116, 72), (126, 80), (128, 91), (140, 99), (139, 112),
        (150, 120), (145, 133), (134, 140), (129, 154), (117, 160), (109, 150),
        (98, 146), (96, 132), (88, 121), (92, 108), (85, 98), (92, 87),
    ]
    land_draw.polygon([point(x, y) for x, y in greenland], fill=(160, 239, 225, 245))
    land_draw.line(
        [point(111, 82), point(106, 99), point(116, 111), point(109, 126), point(121, 137), point(118, 153)],
        fill=(34, 133, 151, 255),
        width=3 * SCALE,
        joint="curve",
    )
    land.putalpha(Image.composite(land.getchannel("A"), Image.new("L", land.size, 0), globe_mask))
    background.alpha_composite(land)

    # Teal SAR orbit, with a warm observation marker at the crossing.
    orbit = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    orbit_draw = ImageDraw.Draw(orbit)
    orbit_draw.ellipse(
        (point(32, 82), point(225, 192)),
        outline=(77, 220, 219, 245),
        width=3 * SCALE,
    )
    orbit = orbit.rotate(25, resample=Image.Resampling.BICUBIC, center=point(128, 137))
    background.alpha_composite(orbit)

    # Small satellite glyph on the orbit.
    satellite = ImageDraw.Draw(background)
    satellite.polygon([point(183, 54), point(195, 60), point(188, 72), point(176, 66)], fill=(244, 185, 100, 255))
    satellite.polygon([point(168, 54), point(177, 57), point(172, 67), point(163, 64)], fill=(105, 216, 225, 255))
    satellite.polygon([point(194, 62), point(203, 66), point(198, 76), point(189, 72)], fill=(105, 216, 225, 255))
    satellite.line([point(177, 67), point(171, 77)], fill=(244, 185, 100, 255), width=2 * SCALE)
    satellite.ellipse((point(167, 75), point(173, 81)), fill=(255, 209, 126, 255))

    # A compact change marker remains legible at taskbar sizes.
    satellite.ellipse((point(155, 125), point(171, 141)), fill=(255, 171, 105, 255), outline=(255, 235, 197, 255), width=2 * SCALE)
    satellite.ellipse((point(160, 130), point(166, 136)), fill=(255, 248, 224, 255))

    return background.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    icon = make_icon()
    icon.save(ASSETS / "dancing_with_the_sars.png", format="PNG", optimize=True)
    icon.save(
        ASSETS / "dancing_with_the_sars.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"Created {ASSETS / 'dancing_with_the_sars.ico'}")


if __name__ == "__main__":
    main()
