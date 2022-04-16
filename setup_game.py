from __future__ import annotations

import copy
import lzma
import pickle
import traceback
from typing import Optional

import tcod

import color
import entity_factories
import input_handlers
from camera import Camera
from engine import Engine
from game_map import GameWorld

# Load the background image and remove the alpha channel.
background_image = tcod.image.load("data/menu_background.png")[:, :, :3]


def new_game() -> Engine:
    """Return a brand new game session as an Engine instance."""
    map_width = 160
    map_height = 100

    viewport_x = 2
    viewport_y = 2
    viewport_width = 76
    viewport_height = 39

    player = copy.deepcopy(entity_factories.player)
    engine = Engine(player=player)

    engine.game_world = GameWorld(
        engine=engine,
        map_width=map_width,
        map_height=map_height,
    )

    engine.game_world.generate_floor()

    engine.camera = Camera(
        x=engine.player.x,
        y=engine.player.y,
        viewport_x=viewport_x,
        viewport_y=viewport_y,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        map_width=engine.game_world.map_width,
        map_height=engine.game_world.map_height,
    )
    engine.camera.update(engine.player)

    engine.update_fov()

    engine.message_log.add_message(
        "Hello and welcome, adventurer, to yet another dungeon!", color.welcome_text
    )

    dagger = copy.deepcopy(entity_factories.dagger)
    leather_armor = copy.deepcopy(entity_factories.leather_armor)

    dagger.parent = player.inventory
    leather_armor.parent = player.inventory

    player.inventory.items.append(dagger)
    player.equipment.toggle_equip(dagger, add_message=False)

    player.inventory.items.append(leather_armor)
    player.equipment.toggle_equip(leather_armor, add_message=False)

    return engine


def load_game(filename: str) -> Engine:
    """Load a saved game from a file and return it as an Engine instance"""
    with lzma.open(filename, "rb") as f:
        engine = pickle.load(f)

    assert isinstance(engine, Engine)

    return engine


class MainMenu(input_handlers.BaseEventHandler):
    """Handle the main menu rendering and input."""

    def on_render(self, console: tcod.Console) -> None:
        """Render the main menu on a background image."""
        console.draw_semigraphics(background_image, 0, 0)

        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "TOMBS OF THE ANCIENT KINGS",
            fg=color.menu_title,
            alignment=tcod.CENTER,
        )
        console.print(
            console.width // 2,
            console.height - 2,
            "By (Your name here)",
            fg=color.menu_title,
            alignment=tcod.CENTER,
        )

        menu_width = 24
        for i, text in enumerate(
            ["[N] Play a new game", "[C] Continue last game", "[Q] Quit"]
        ):
            console.print(
                console.width // 2,
                console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg=color.menu_text,
                bg=color.black,
                alignment=tcod.CENTER,
                bg_blend=tcod.BKGND_ALPHA(64),
            )

    def ev_keydown(
        self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:
        if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
            print(f"Still in here? {event}")
            # A KeyDown event seems to be sent repeatedly from the last time the game was shutdown after restart
            # raise SystemExit(0)
        elif event.sym == tcod.event.K_c:
            try:
                return input_handlers.MainGameEventHandler(load_game("savegame.sav"))
            except FileNotFoundError:
                return input_handlers.PopupMessage(self, "No saved game to load!")
            except Exception as exc:
                traceback.print_exc()
                return input_handlers.PopupMessage(
                    self, f"Failed to load savegame:\n{exc}"
                )
        elif event.sym == tcod.event.K_n:
            return input_handlers.MainGameEventHandler(new_game())

        return None
