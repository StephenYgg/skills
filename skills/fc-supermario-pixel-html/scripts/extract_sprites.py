#!/usr/bin/env python
import argparse
import json
import sys
from pathlib import Path

from PIL import Image


def skill_dir_from_script():
    return Path(__file__).resolve().parents[1]


def load_manifest(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_sources(skill_dir):
    manifest = load_manifest(Path(skill_dir) / "assets" / "sprites" / "sprites.json")
    sources = {}
    for name, rel_path in manifest["sources"].items():
        path = Path(skill_dir) / rel_path
        if not path.is_file():
            raise FileNotFoundError(f"missing source image for {name}: {path}")
        sources[name] = Image.open(path).convert("RGBA")
    return sources


def validate_manifest(manifest, sources):
    errors = []
    outputs = set()
    ids = set()
    required = {"id", "category", "source", "bbox", "output"}

    if manifest.get("version") != 1:
        errors.append("manifest version must be 1")

    for index, sprite in enumerate(manifest.get("sprites", [])):
        missing = required - set(sprite)
        if missing:
            errors.append(f"sprite {index} missing fields: {', '.join(sorted(missing))}")
            continue

        sprite_id = sprite["id"]
        if sprite_id in ids:
            errors.append(f"duplicate sprite id: {sprite_id}")
        ids.add(sprite_id)

        output = sprite["output"]
        if output in outputs:
            errors.append(f"duplicate output: {output}")
        outputs.add(output)

        source_name = sprite["source"]
        if source_name not in sources:
            errors.append(f"{sprite_id}: unknown source {source_name}")
            continue

        bbox = sprite["bbox"]
        if len(bbox) != 4 or not all(isinstance(value, int) for value in bbox):
            errors.append(f"{sprite_id}: bbox must be four integers")
            continue

        x, y, width, height = bbox
        image_width, image_height = sources[source_name].size
        if width <= 0 or height <= 0:
            errors.append(f"{sprite_id}: bbox width and height must be positive")
        if x < 0 or y < 0 or x + width > image_width or y + height > image_height:
            errors.append(
                f"{sprite_id}: bbox {bbox} outside {source_name} {image_width}x{image_height}"
            )

    return errors


def remove_background(image, colors):
    if not colors:
        return image

    color_set = {tuple(color) for color in colors}
    result = image.copy()
    pixels = result.load()
    width, height = result.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a and (r, g, b) in color_set:
                pixels[x, y] = (r, g, b, 0)
    return result


def has_visible_pixels(image):
    alpha = image.getchannel("A")
    return alpha.getbbox() is not None


def crop_sprite(sprite, sources, background_colors):
    x, y, width, height = sprite["bbox"]
    crop = sources[sprite["source"]].crop((x, y, x + width, y + height))
    colors = sprite.get("transparent_colors", background_colors.get(sprite["source"], []))
    return remove_background(crop, colors)


def extract(skill_dir, check_only=False):
    manifest_path = Path(skill_dir) / "assets" / "sprites" / "sprites.json"
    manifest = load_manifest(manifest_path)
    sources = load_sources(skill_dir)
    errors = validate_manifest(manifest, sources)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    background_colors = manifest.get("background_colors", {})
    output_root = Path(skill_dir) / "assets" / "sprites"
    empty = []

    crops = []
    for sprite in manifest["sprites"]:
        crop = crop_sprite(sprite, sources, background_colors)
        if not has_visible_pixels(crop):
            empty.append(sprite["id"])
            continue
        crops.append((sprite, crop))

        if not check_only:
            output_path = output_root / sprite["output"]
            output_path.parent.mkdir(parents=True, exist_ok=True)
            crop.save(output_path)

    if empty:
        for sprite_id in empty:
            print(f"empty crop after background removal: {sprite_id}", file=sys.stderr)
        return 1

    if check_only:
        print(f"OK: {len(manifest['sprites'])} sprites validated")
    else:
        write_contact_sheet(output_root / "contact-sheet.png", crops)
        print(f"OK: extracted {len(manifest['sprites'])} sprites")
    return 0


def write_contact_sheet(path, crops):
    cell_width = 160
    cell_height = 118
    columns = 5
    rows = (len(crops) + columns - 1) // columns
    sheet = Image.new("RGBA", (columns * cell_width, rows * cell_height), (24, 32, 48, 255))

    for index, (sprite, crop) in enumerate(crops):
        column = index % columns
        row = index // columns
        x = column * cell_width
        y = row * cell_height

        checker = Image.new("RGBA", (cell_width, cell_height), (31, 41, 55, 255))
        for yy in range(0, cell_height, 8):
            for xx in range(0, cell_width, 8):
                if (xx // 8 + yy // 8) % 2 == 0:
                    for py in range(yy, min(yy + 8, cell_height)):
                        for px in range(xx, min(xx + 8, cell_width)):
                            checker.putpixel((px, py), (15, 23, 42, 255))
        sheet.alpha_composite(checker, (x, y))

        scale = max(1, min(4, (cell_width - 20) // max(crop.width, 1), (cell_height - 42) // max(crop.height, 1)))
        preview = crop.resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST)
        px = x + (cell_width - preview.width) // 2
        py = y + 8 + (cell_height - 42 - preview.height) // 2
        sheet.alpha_composite(preview, (px, py))

        # Tiny bitmap-free label placeholder: mark categories by colored strip.
        color = {
            "character": (96, 165, 250, 255),
            "enemy": (248, 113, 113, 255),
            "item": (250, 204, 21, 255),
            "effect": (251, 146, 60, 255),
            "level": (74, 222, 128, 255),
        }.get(sprite["category"], (203, 213, 225, 255))
        for yy in range(y + cell_height - 12, y + cell_height - 4):
            for xx in range(x + 8, x + cell_width - 8):
                sheet.putpixel((xx, yy), color)

    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate and crop FC pixel sprites.")
    parser.add_argument("--check", action="store_true", help="validate without writing images")
    parser.add_argument("--skill-dir", type=Path, default=skill_dir_from_script())
    args = parser.parse_args(argv)
    return extract(args.skill_dir, check_only=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
