from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Optional

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
    def position(self) -> Point:
        """Return a Point containing the top-left corner of the room"""
        return Point(self.x1, self.y1)

    @property
    def end(self) -> Point:
        """Return a Point containing the bottom-right corner of the room"""
        return Point(self.x2, self.y2)

    @property
    def size(self) -> Point:
        """Return a Point containing the width and height of the room"""
        return Point(self.x2 - self.x1, self.y2 - self.y1)

    @property
    def center(self) -> tuple[int, int]:
        """Return the center of the rectangle room as a tuple"""
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> tuple[slice, slice]:
        """Return a tuple containing a slice of the map inside the rectangle room"""
        return slice(self.x1, self.x2), slice(self.y1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another room"""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )

    def encloses(self, other: RectangularRoom) -> bool:
        """Return True if this room encloses another room"""
        return (
            self.x1 <= other.x1
            and self.x2 >= other.x2
            and self.y1 <= other.y1
            and self.y2 >= other.y2
        )

    def has_point(self, x: int, y: int) -> bool:
        """Return True if the point is inside the rectangle room"""
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def grow(self, growth: int) -> RectangularRoom:
        """Return a new RectangularRoom with the same center as this one, but with a size of this room + growth"""
        return RectangularRoom(
            self.x1 - growth,
            self.y1 - growth,
            self.size.x + growth * 2,
            self.size.y + growth * 2,
        )

    def __str__(self) -> str:
        return f"({self.x1}, {self.y1}, {self.x2}, {self.y2})"


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @staticmethod
    def UP() -> Point:
        return Point(0, -1)

    @staticmethod
    def DOWN() -> Point:
        return Point(0, 1)

    @staticmethod
    def LEFT() -> Point:
        return Point(-1, 0)

    @staticmethod
    def RIGHT() -> Point:
        return Point(1, 0)

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)


class Room:
    def __init__(self, room: RectangularRoom, is_room: bool = True) -> None:
        self.room = room
        self.ready_walls = {"n": True, "e": True, "s": True, "w": True}
        self.is_room = is_room


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


def generate_paper_dungeon(
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    max_monsters_per_room: int,
    monster_chances: dict[int, list[tuple[Entity, int]]],
    max_items_per_room: int,
    item_chances: dict[int, list[tuple[Entity, int]]],
    engine: Engine,
    complexity: int = 1,
    min_corridor_length: int = 4,
    max_corridor_length: int = 12,
    seed_room_size: int = 8,
) -> GameMap:
    """Generate a new dungeon map using randomly placed non-overlapping rooms"""
    """We may generate fewer than max rooms due to room collisions"""
    player = engine.player
    map = GameMap(engine, map_width, map_height, entities=[player])

    # Create the initial dungeon generator
    dungeon = Dungeon(map_width=map_width, map_height=map_height)

    # Add the seed room
    dungeon.add_room(
        RectangularRoom(
            int(map_width / 2 - seed_room_size / 2),
            int(map_height / 2 - seed_room_size / 2),
            seed_room_size,
            seed_room_size,
        )
    )

    for _ in range(complexity * 8):
        new_room = dungeon.add_random_corridor(
            room=dungeon.get_random_room(),
            length=random.randrange(min_corridor_length, max_corridor_length),
            connecting=False,
        )

        if new_room:
            # Attempt to create room at end of corridor
            w = random.randrange(room_min_size, room_max_size)
            h = random.randrange(room_min_size, room_max_size)
            dungeon.add_room(RectangularRoom(new_room.x - 1, new_room.y - 1, w, h))

    # "Completed" dungeon generation

    # Create the map from the dungeon
    for corridor_cell in dungeon.corridors:
        map.tiles[corridor_cell.x][corridor_cell.y] = tile_types.floor

    # Add rooms and corridors to tilemap
    for room in dungeon.rooms:
        map.tiles[room.room.inner] = tile_types.floor

    # Place the player somewhere in the dungeon
    start_room = dungeon.rooms[random.randrange(len(dungeon.rooms))]
    player.place(*start_room.room.center, map)

    # Place the monsters
    for room in dungeon.rooms:
        if room == start_room:
            # Disable monster spawning in the starting room
            max_monsters = 0
        else:
            max_monsters = max_monsters_per_room

        place_entities(
            room.room,
            map,
            max_monsters,
            monster_chances,
            max_items_per_room,
            item_chances,
            engine.game_world.current_floor,
        )

    # Find room to contain the stairs
    while True:
        exit_room = dungeon.rooms[random.randrange(len(dungeon.rooms))]
        if not exit_room == start_room:
            break

    # Place stairs in the selected room
    map.tiles[exit_room.room.center] = tile_types.down_stairs
    map.downstairs_location = exit_room.room.center

    return map


class Dungeon:
    def __init__(self, map_width: int, map_height: int, padding: int = 4) -> None:
        # Track rooms and doors
        self.data: dict = {}
        self.doorPos: dict = {}
        self.rooms: list[Room] = []
        self.corridors: list[Point] = []

        # Configure "padding" around the map to keep rooms from being placed on the edge
        self.padding = padding

        # Set map borders
        self.borders = RectangularRoom(
            padding, padding, map_width - (padding * 2), map_height - (padding * 2)
        )

    # Map generation functions

    def add_room(self, new_room: RectangularRoom) -> None:
        room = Room(new_room)

        if not self.in_limits(new_room):
            return

        self.rooms.append(room)

        for x in range(new_room.position.x, new_room.end.x):
            for y in range(new_room.position.y, new_room.end.y):
                self._set_data(x, y, room)

    def add_random_corridor(
        self, room: Room, length: int, connecting: bool
    ) -> Optional[Point]:
        position: Optional[Point] = None
        direction: Optional[Point] = None

        walls = room.ready_walls
        if len(walls) == 0:
            return

        # Select a wall to create a corridor from and remove it so we don't use it again
        k = list(walls.keys())
        random.shuffle(k)
        k = k[0]

        room.ready_walls.pop(k)

        # Set up the direction to send corridor based on chosen wall
        starting_room: RectangularRoom = room.room

        if k == "n":
            position = Point(
                math.floor(starting_room.position.x + (starting_room.size.x / 2)),
                starting_room.position.y,
            )
            direction = Point.UP()

        if k == "s":
            position = Point(
                math.floor(starting_room.position.x + (starting_room.size.x / 2)),
                starting_room.position.y + starting_room.size.y - 1,
            )
            direction = Point.DOWN()

        if k == "e":
            position = Point(
                starting_room.position.x + starting_room.size.x - 1,
                math.floor(starting_room.position.y + (starting_room.size.y / 2)),
            )
            direction = Point.RIGHT()

        if k == "w":
            position = Point(
                starting_room.position.x,
                math.floor(starting_room.position.y + (starting_room.size.y / 2)),
            )
            direction = Point.LEFT()

        # Check to see if the new corridor is going to intersect anything
        todo: list[dict] = []
        touched_another_room: bool = False

        if not position or not direction:
            return

        for _ in range(length):
            position += direction

            # Ensure we are not outside the map
            if not self.in_limits(
                RectangularRoom(position.x, position.y, 1, 1).grow(self.padding)
            ):
                return

            # Grab room data, if available
            r = self.get_data(position.x, position.y)

            if not r:
                todo.append(
                    {
                        "position": position,
                        "val": {
                            "isCorridor": True,
                            "room": RectangularRoom(position.x, position.y, 1, 1),
                        },
                    }
                )
            else:
                touched_another_room = True
                break

        if touched_another_room or not connecting:
            for i in range(len(todo)):
                t = todo[i]
                t_pos = t["position"]
                self._set_data(t_pos.x, t_pos.y, t["val"])
                self.corridors.append(t_pos)

            if not touched_another_room:
                return position
            else:
                return

        return position

    def get_random_room(self) -> Room:
        return self.rooms[random.randrange(len(self.rooms))]

    # Helper functions

    @staticmethod
    def _key(x, y):
        return f"{x}:{y}"

    def get_data(self, x, y):
        return self.data.get(self._key(x, y))

    def _set_data(self, x, y, val):
        if self.borders.has_point(x, y):
            self.data[self._key(x, y)] = val
        else:
            return

    def _remove_data(self, x, y, _val):
        self.data.pop(self._key(x, y))

    def in_limits(self, room: RectangularRoom):
        return self.borders.encloses(room)
