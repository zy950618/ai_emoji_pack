from __future__ import annotations

from pathlib import Path
from statistics import pstdev
from typing import Any

from PIL import Image, ImageFilter, ImageSequence


def _image_stats(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        frame_count = getattr(image, "n_frames", 1)
        probe = image.convert("RGBA").resize((64, 64))
        pixels = list(probe.getdata())
    opaque = [pixel for pixel in pixels if pixel[3] > 12]
    rgb = [(pixel[0], pixel[1], pixel[2]) for pixel in opaque] or [(0, 0, 0)]
    luminance = [int(0.299 * r + 0.587 * g + 0.114 * b) for r, g, b in rgb]
    colors = {(r // 16, g // 16, b // 16) for r, g, b in rgb}
    edge_image = probe.convert("L").filter(ImageFilter.FIND_EDGES)
    edge_strength = sum(edge_image.getdata()) / (64 * 64)
    return {
        "frame_count": frame_count,
        "unique_color_bins": len(colors),
        "luminance_stdev": float(pstdev(luminance)) if len(luminance) > 1 else 0.0,
        "edge_strength": float(edge_strength),
        "opaque_ratio": len(opaque) / max(1, len(pixels)),
    }


def check_non_flat_asset(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    stats = _image_stats(target)
    passed = stats["unique_color_bins"] >= 24 and stats["luminance_stdev"] >= 18 and stats["edge_strength"] >= 5
    return {
        "check": "non_flat_asset",
        "passed": passed,
        "score": min(100, int(stats["unique_color_bins"] * 1.5 + stats["luminance_stdev"] + stats["edge_strength"])),
        "reason": "layered pixels detected" if passed else "asset is too flat or lacks edges",
        "metrics": stats,
    }


def check_dynamic_asset(path: str | Path, min_frames: int = 4) -> dict[str, Any]:
    target = Path(path)
    with Image.open(target) as image:
        frames = [frame.convert("RGBA").resize((32, 32)) for frame in ImageSequence.Iterator(image)]
    frame_count = len(frames)
    movement = 0
    if frame_count >= 2:
        first = list(frames[0].getdata())
        movement = max(sum(1 for a, b in zip(first, list(frame.getdata())) if a != b) for frame in frames[1:])
    passed = frame_count >= min_frames and movement > 120
    return {
        "check": "dynamic_asset",
        "passed": passed,
        "frame_count": frame_count,
        "movement_pixels": movement,
        "reason": "multi-frame motion detected" if passed else "dynamic asset lacks enough frames or motion",
    }


def check_sticker_readability(path: str | Path) -> dict[str, Any]:
    stats = _image_stats(Path(path))
    passed = stats["edge_strength"] >= 5 and stats["opaque_ratio"] >= 0.16
    return {
        "check": "sticker_readability",
        "passed": passed,
        "score": min(100, int(stats["edge_strength"] * 4 + stats["opaque_ratio"] * 80)),
        "reason": "thumbnail silhouette is readable" if passed else "thumbnail silhouette is weak",
        "metrics": stats,
    }


def check_asset_diversity(paths: list[str | Path]) -> dict[str, Any]:
    signatures = []
    for path in paths:
        stats = _image_stats(Path(path))
        signatures.append((stats["unique_color_bins"] // 5, int(stats["luminance_stdev"]) // 8, int(stats["edge_strength"]) // 4))
    diversity = len(set(signatures))
    passed = diversity >= min(3, len(paths)) if paths else False
    return {
        "check": "asset_diversity",
        "passed": passed,
        "diversity": diversity,
        "asset_count": len(paths),
        "reason": "asset set has varied visual signatures" if passed else "asset set is visually repetitive",
    }
