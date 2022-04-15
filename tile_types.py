from typing import Tuple

import numpy as np

# Tile graphics structured type compatible with Console.tiles_rgb.
graphic_dt = np.dtype(
    [
        ("ch", np.int32),  # Unicode codepoint.
        ("fg", "3B"),  # 3 unsigned bytes, for RGB colors.
        ("bg", "3B"),
    ]
)

# Tile struct used for statically defined tile data.
tile_dt = np.dtype(
    [
        ("walkable", bool),  # True if this tile can be walked over
        ("transparent", bool),  # True if this tile doesn't block FOV
        ("dark", graphic_dt),  # Graphics for when this tile is not in FOV
        ("light", graphic_dt),  # Graphics for when this tile is in FOV
    ]
)


def new_tile(
    *,  # Force use of keyword arguments
    walkable: bool,
    transparent: bool,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:  # type: ignore
    """Helper function for defining individual tile types"""
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)


# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("."), (62, 64, 68), (52, 54, 57)),
    light=(ord("."), (62, 64, 68), (69, 71, 76)),
)

wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("#"), (41, 42, 45), (32, 33, 35)),
    light=(ord("#"), (52, 54, 57), (42, 42, 45)),
)

down_stairs = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(">"), (200, 200, 200), (52, 54, 57)),
    light=(ord(">"), (200, 200, 200), (62, 64, 68)),
)
