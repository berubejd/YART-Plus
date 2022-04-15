from __future__ import annotations

import random
from typing import TYPE_CHECKING, Iterable, Iterator, Optional

import numpy as np
from tcod.console import Console

import entity_factories
import tile_types
from entity import Actor, Item

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


max_items_by_floor = [
    (1, 1),
    (4, 2),
]

item_chances: dict[int, list[tuple[Entity, int]]] = {
    0: [(entity_factories.health_potion, 35)],
    2: [(entity_factories.confusion_scroll, 10)],
    4: [(entity_factories.lightning_scroll, 25), (entity_factories.sword, 5)],
    6: [(entity_factories.fireball_scroll, 25), (entity_factories.chain_mail, 15)],
}

max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

monster_chances: dict[int, list[tuple[Entity, int]]] = {
    0: [(entity_factories.orc, 80)],
    3: [(entity_factories.troll, 15)],
    5: [(entity_factories.troll, 30)],
    7: [(entity_factories.troll, 60)],
}


class GameMap:
    def __init__(
        self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()
    ) -> None:
        self.engine = engine
        self.width = width
        self.height = height
        self.entities = set(entities)

        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        # Track currently visible and previously visited but no longer visible tiles
        self.visible = np.full((width, height), fill_value=False, order="F")
        self.explored = np.full((width, height), fill_value=False, order="F")

        self.downstairs_location: tuple[int, int] = (0, 0)

    @property
    def gamemap(self) -> GameMap:
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """Return an iterator over all living actors on the map"""
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive
        )

    @property
    def items(self) -> Iterator[Item]:
        """Return an iterator over all items on the map"""
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_blocking_entity_at_location(self, x: int, y: int) -> Optional[Entity]:
        """Return the first entity at x, y that blocks movement"""
        for entity in self.entities:
            if entity.blocks_movement and entity.x == x and entity.y == y:
                return entity

        return None

    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        """Return the first actor at x, y"""
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor

        return None

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x and y are inside of the bounds of the map"""
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console) -> None:
        """
        Renders the map to the console

        If a tile is in the "visible" array, then draw it with the "light" colors
        If it isn't, but it's in the "explored" array, then draw it with the "dark" colors
        Otherwise, the default is "SHROUD"
        """
        console.tiles_rgb[0 : self.width, 0 : self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD,
        )

        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        for entity in entities_sorted_for_rendering:
            # Only draw entities that are in the "visible" array
            if self.visible[entity.x, entity.y]:
                console.print(
                    x=entity.x, y=entity.y, string=entity.char, fg=entity.color
                )


class GameWorld:
    """Holds GameMap settings as well as generates new maps when moving down stairs"""

    def __init__(
        self,
        *,
        engine: Engine,
        map_width: int,
        map_height: int,
        current_floor: int = 0,
    ) -> None:
        self.engine = engine

        self.map_width = map_width
        self.map_height = map_height

        self.current_floor = current_floor

    def generate_floor(self) -> None:
        """Increment floor number and generate new floor type"""
        self.current_floor += 1

        if random.randrange(100) < 70:
            self.generate_paper_floor()
        else:
            self.generate_procgen_floor()

    def generate_paper_floor(self) -> None:
        # Generate a "paper" dungeon most of the time
        from paperdungeon import generate_paper_dungeon

        print("Generating a paper dungeon...")

        room_min_size = 4
        room_max_size = 7

        min_corridor_length: int = room_min_size + 1
        max_corridor_length: int = room_max_size * 3

        base_complexity = 3
        complexity_by_floor = [
            (2, 1),
            (5, 2),
            (10, 3),
            (20, 4),
        ]
        scaled_complexity = base_complexity + get_max_value_for_floor(
            complexity_by_floor, self.current_floor
        )

        self.engine.game_map = generate_paper_dungeon(
            complexity=scaled_complexity,
            room_min_size=room_min_size,
            room_max_size=room_max_size,
            min_corridor_length=min_corridor_length,
            max_corridor_length=max_corridor_length,
            map_width=self.map_width,
            map_height=self.map_height,
            max_monsters_per_room=get_max_value_for_floor(
                max_monsters_by_floor, self.current_floor
            ),
            monster_chances=monster_chances,
            max_items_per_room=get_max_value_for_floor(
                max_items_by_floor, self.current_floor
            ),
            item_chances=item_chances,
            engine=self.engine,
        )

    def generate_procgen_floor(self) -> None:
        # Generate an "original" dungeon sometimes
        from procgen import generate_dungeon

        print("Generating a procgen dungeon...")

        room_min_size = 6
        room_max_size = 10

        max_rooms = 30

        self.engine.game_map = generate_dungeon(
            max_rooms=max_rooms,
            room_min_size=room_min_size,
            room_max_size=room_max_size,
            map_width=self.map_width,
            map_height=self.map_height,
            max_monsters_per_room=get_max_value_for_floor(
                max_monsters_by_floor, self.current_floor
            ),
            monster_chances=monster_chances,
            max_items_per_room=get_max_value_for_floor(
                max_items_by_floor, self.current_floor
            ),
            item_chances=item_chances,
            engine=self.engine,
        )


def get_max_value_for_floor(
    max_value_by_floor: list[tuple[int, int]], floor: int
) -> int:
    for floor_minimum, value in reversed(max_value_by_floor):
        if floor >= floor_minimum:
            return value

    return 0
