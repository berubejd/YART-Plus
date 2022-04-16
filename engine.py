from __future__ import annotations

import lzma
import pickle
from typing import TYPE_CHECKING

from tcod.console import Console

import exceptions
import render_functions
from camera import Camera
from message_log import MessageLog

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap, GameWorld


class Engine:
    """Manage game responsibilities such as drawing the screen, handling events, etc."""

    game_map: GameMap
    game_world: GameWorld

    camera: Camera

    def __init__(
        self,
        player: Actor,
    ) -> None:
        self.message_log = MessageLog()
        self.mouse_location: tuple[int, int] = (0, 0)
        self.player = player

    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass  # Ignore impossible actions from npcs

    def update_fov(self) -> None:
        """Recompute the field of view of the player"""
        self.camera.update(self.player)
        self.game_map.update_fov(self.player)

        # Add visible tiles to the explored tile list
        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console) -> None:
        """Render the game to the console"""
        ## Update the game map to its offscreen console
        self.game_map.render()

        ## Render the game world viewport to the main console
        self.camera.render_viewport(console=console, map=self.game_map.console)

        # Render the user interface
        self.message_log.render(console=console, x=21, y=44, width=40, height=5)

        render_functions.render_bar_classic(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=14,
        )

        render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(0, 42),
        )

        render_functions.render_names_at_mouse_location(
            console=console, x=1, y=1, engine=self
        )

    def save_as(self, filename: str) -> None:
        with lzma.open(filename, "wb") as file:
            pickle.dump(self, file)
