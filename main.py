import traceback

import tcod

import color
import exceptions
import input_handlers
import setup_game


def save_game(handler: input_handlers.BaseEventHandler, filename: str) -> None:
    """Save the game to a file if the current event handler has an active Engine"""
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print(f"Saved game to {filename}")


def main() -> None:
    screen_width = 80
    screen_height = 50

    # TCOD tileset
    # tileset = tcod.tileset.load_tilesheet(
    #     "data/dejavu16x16_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    # )

    # Ascii tileset
    tileset = tcod.tileset.load_tilesheet(
        "data/16x16_sb_ascii.png", 16, 16, tcod.tileset.CHARMAP_CP437
    )

    # Truetype font tileset
    # tileset = tcod.tileset.load_truetype_font(
    #     "data/Example.ttf",
    #     tile_width=16,
    #     tile_height=16,
    # )

    handler: input_handlers.BaseEventHandler = setup_game.MainMenu()

    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title="Tombs of the Ancient Kings",
        vsync=True,
    ) as context:
        root_console = tcod.Console(screen_width, screen_height, order="F")

        try:
            while True:
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console)

                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        handler = handler.handle_events(event)
                except Exception:  # Handle exceptions in game.
                    traceback.print_exc()  # Print error to stderr.
                    # Then print the error to the message log.
                    if isinstance(handler, input_handlers.EventHandler):
                        handler.engine.message_log.add_message(
                            traceback.format_exc(), color.error
                        )
        except exceptions.QuitWithoutSaving:
            raise
        except (SystemExit, BaseException):  # Save and quit.
            save_game(handler, "savegame.sav")
            raise


if __name__ == "__main__":
    main()
