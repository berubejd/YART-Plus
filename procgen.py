from __future__ import annotations

import random
from typing import TYPE_CHECKING, Iterator

import tcod

import entity_factories
import tile_types
from game_map import GameMap

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> tuple[int, int]:
        """Return the center of the rectangle room as a tuple"""
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> tuple[slice, slice]:
        """Return a tuple containing a slice of the map inside the rectangle room"""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another room"""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


def place_entities(
    room: RectangularRoom,
    dungeon: GameMap,
    max_monsters: int,
    monster_chances: dict[int, list[tuple[Entity, int]]],
    max_items: int,
    item_chances: dict[int, list[tuple[Entity, int]]],
    floor_number: int,
) -> None:
    """Place monsters and items in a room"""
    number_of_monsters = random.randint(0, max_monsters)
    number_of_items = random.randint(0, max_items)

    monsters: list[Entity] = get_entities_at_random(
        monster_chances, number_of_monsters, floor_number
    )
    items: list[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    )

    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.spawn(dungeon, x, y)


def get_entities_at_random(
    weighted_chances_by_floor: dict[int, list[tuple[Entity, int]]],
    number_of_entities: int,
    floor: int,
) -> list[Entity]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    chosen_entities = random.choices(
        entities, weights=entity_weighted_chance_values, k=number_of_entities
    )

    return chosen_entities


def tunnel_between(
    start: tuple[int, int], end: tuple[int, int]
) -> Iterator[tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end

    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    max_monsters_per_room: int,
    monster_chances: dict[int, list[tuple[Entity, int]]],
    max_items_per_room: int,
    item_chances: dict[int, list[tuple[Entity, int]]],
    engine: Engine,
    padding: int = 4,
) -> GameMap:
    """Generate a new dungeon map using randomly placed non-overlapping rooms"""
    """We may generate fewer than max rooms due to room collisions"""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: list[RectangularRoom] = []

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        # Randomly position the room ensuring some padding around the map edges
        x = random.randint(padding, dungeon.width - padding - room_width - 1)
        y = random.randint(padding, dungeon.height - padding - room_height - 1)

        new_room = RectangularRoom(x, y, room_width, room_height)

        # Run through the other rooms and see if they intersect with this one
        if any(new_room.intersects(other_room) for other_room in rooms):
            # new_room intersects with another room, so generate a new one
            continue

        # Dig out this new room
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # This is the first room so start the player here
            player.place(*new_room.center, dungeon)
        else:
            # Dig a tunnel to the previous room
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

        place_entities(
            new_room,
            dungeon,
            max_monsters_per_room,
            monster_chances,
            max_items_per_room,
            item_chances,
            engine.game_world.current_floor,
        )

        dungeon.tiles[new_room.center] = tile_types.down_stairs
        dungeon.downstairs_location = new_room.center

        # Add the new room to the list of valid rooms in the dungeon
        rooms.append(new_room)

    return dungeon
