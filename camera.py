from typing import Optional

from tcod.console import Console

from entity import Entity


class Camera:
    def __init__(
        self,
        x: int,
        y: int,
        viewport_x: int,
        viewport_y: int,
        viewport_width: int,
        viewport_height: int,
        map_width: int,
        map_height: int,
    ) -> None:
        # Upper left corner of the viewport
        self.x = x
        self.y = y

        # Location of the viewport
        self.viewport_x = viewport_x
        self.viewport_y = viewport_y

        # Dimensions of the viewport
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        # Dimensions of the map
        self.map_width = map_width
        self.map_height = map_height

    @staticmethod
    def clamp(value: int, min_value: int, max_value: int) -> int:
        """Clamp a value between a minimum and maximum"""
        return max(min(max_value, value), min_value)

    def inside_viewport(self, x: int, y: int) -> bool:
        """Return True if x and y are inside of the viewport"""
        return (
            self.viewport_x <= x < self.viewport_x + self.viewport_width
            and self.viewport_y <= y < self.viewport_y + self.viewport_height
        )

    def viewport_to_map(self, x, y) -> tuple[int, int]:
        """Return the coordinates of the viewport relative to the map"""
        if (
            not self.viewport_x <= x < self.viewport_x + self.viewport_width
            or not self.viewport_y <= y < self.viewport_y + self.viewport_height
        ):
            return (x, y)

        map_x = self.x + x - self.viewport_x
        map_y = self.y + y - self.viewport_y
        return (map_x, map_y)

    def map_to_console(self, x, y) -> tuple[int, int]:
        """Return the coordinates of the map relative to the viewport"""
        viewport_x = x - self.x + self.viewport_x
        viewport_y = y - self.y + self.viewport_y
        return (viewport_x, viewport_y)

    def update(self, entity: Entity) -> None:
        """Update the camera to follow the player"""
        new_x = entity.x - int(self.viewport_width / 2)
        new_y = entity.y - int(self.viewport_height / 2)

        # Keep camera in bounds of the map
        self.x = self.clamp(new_x, 0, self.map_width - self.viewport_width)
        self.y = self.clamp(new_y, 0, self.map_height - self.viewport_height)

    def render_viewport(
        self,
        console: Console,
        map: Console,
        dest_x: Optional[int] = None,
        dest_y: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        """Render the viewport to the console"""
        if dest_x is None:
            dest_x = self.viewport_x

        if dest_y is None:
            dest_y = self.viewport_y

        if width is None:
            width = self.viewport_width

        if height is None:
            height = self.viewport_height

        map.blit(
            console,
            dest_x,
            dest_y,
            self.x,
            self.y,
            width,
            height,
        )
