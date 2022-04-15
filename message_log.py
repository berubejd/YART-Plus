import textwrap
from typing import Iterable, Reversible

import tcod

import color


class Message:
    def __init__(self, text: str, fg: tuple[int, int, int]) -> None:
        self.plain_text = text
        self.fg = fg
        self.count = 1

    @property
    def full_text(self) -> str:
        if self.count > 1:
            return f"{self.plain_text} (x{self.count})"
        return self.plain_text


class MessageLog:
    def __init__(self) -> None:
        self.messages: list[Message] = []

    def add_message(
        self, text: str, fg: tuple[int, int, int] = color.white, *, stack: bool = True
    ) -> None:
        """
        Add a message to the log
        text - message text
        fg - text color
        stack - if True, messages will be stacked with previous messages of the same type
        """
        if stack and self.messages and self.messages[-1].plain_text == text:
            self.messages[-1].count += 1
        else:
            self.messages.append(Message(text, fg))

    def render(
        self, console: tcod.Console, x: int, y: int, width: int, height: int
    ) -> None:
        """
        Render the message log to the console
        x, y, width, height - render area
        """
        self.render_messages(console, x, y, width, height, self.messages)

    @staticmethod
    def wrap(string: str, width: int) -> Iterable[str]:
        """
        Wrap a string to fit the width
        """
        for line in string.splitlines():
            yield from textwrap.wrap(line, width, expand_tabs=True)

    @classmethod
    def render_messages(
        cls,
        console: tcod.Console,
        x: int,
        y: int,
        width: int,
        height: int,
        messages: Reversible[Message],
    ) -> None:
        """
        Render the messages provided
        messages - rendered starting at the last message and working backwards
        """
        y_offset = height - 1

        for message in reversed(messages):
            for line in reversed(list(cls.wrap(message.full_text, width))):
                console.print(
                    x=x,
                    y=y + y_offset,
                    string=line,
                    fg=message.fg,
                )
                y_offset -= 1

                if y_offset < 0:
                    return
