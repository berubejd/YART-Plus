from __future__ import annotations
from turtle import width

from typing import TYPE_CHECKING

import tcod

import color
from progressbar import progress_bar

if TYPE_CHECKING:
    from tcod import Console

    from engine import Engine
    from game_map import GameMap


def get_names_at_location(x: int, y: int, game_map: GameMap) -> str:
    if not game_map.in_bounds(x, y) or not game_map.visible[x, y]:
        return ""

    names = ", ".join(
        entity.name for entity in game_map.entities if entity.x == x and entity.y == y
    )

    return names.capitalize()


def render_bar(
    console: Console, current_value: int, maximum_value: int, total_width: int
) -> None:
    bar_width = int(float(current_value) / maximum_value * total_width)

    console.draw_rect(x=0, y=45, width=total_width, height=1, ch=1, bg=color.bar_empty)

    if bar_width > 0:
        console.draw_rect(
            x=0, y=45, width=bar_width, height=1, ch=1, bg=color.bar_filled
        )

    console.print(
        x=1, y=45, string=f"HP: {current_value}/{maximum_value}", fg=color.bar_text
    )


def render_bar_classic(
    console: Console, current_value: int, maximum_value: int, total_width: int
) -> None:

    padding = len(str(maximum_value))

    if current_value < maximum_value * 0.25:
        color = (255, 48, 48)
    else:
        color = (0, 96, 0)

    new_bar = progress_bar(
        progress=int(current_value / maximum_value * 100),
        length=total_width,
        complete=0,
        msg_prefix=f"Hit Points ({current_value:{padding}}/{maximum_value:{padding}})",
        msg_complete="DEAD!",
        color=color,
        display_percentage=False,
    )

    console.print(x=1, y=45, string=new_bar, alignment=tcod.LEFT)


def render_dungeon_level(
    console: Console, dungeon_level: int, location: tuple[int, int]
) -> None:
    """Render the dungeon level at the given location of the screen"""
    x, y = location
    message = f"Dungeon Level: {dungeon_level}"

    console.print(
        x=x,
        y=y,
        string=f"{message:^{console.width}}",
    )


def render_names_at_mouse_location(
    console: Console, x: int, y: int, engine: Engine
) -> None:
    mouse_x, mouse_y = engine.mouse_location

    names_at_mouse_location = get_names_at_location(
        x=mouse_x, y=mouse_y, game_map=engine.game_map
    )

    console.print(x=x, y=y, string=names_at_mouse_location)
