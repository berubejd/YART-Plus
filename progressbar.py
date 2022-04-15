import tcod


def progress_bar(
    progress: int,
    length: int = 20,
    msg_prefix: str = "",
    msg_prefix_length: int = 0,
    msg_complete: str = "Complete!",
    complete: int = 100,
    display_percentage: bool = True,
    color: tuple[int, int, int] = (255, 255, 255),
) -> str:
    """
    Display a progress bar with optional messaging
    The only required parameter is 'progress' which should represent a percentage expressed as an integer between 0 and 100.
    By setting 'complete' to zero it is possible to work as a countdown timer, as well.
    """

    FILL_CHAR = "#"
    BLANK_CHAR = " "

    if progress < 0 or progress > 100:
        raise ValueError("Progress must be a value between 0 and 100")

    if len(msg_complete) > length:
        raise ValueError("Message must be shorter than progress bar length!")

    if msg_prefix_length == 0:
        msg_prefix_length = len(msg_prefix)

    if progress != complete:
        progress_length = int(progress / 100 * length)

        # Ensure that the progress bar is always at least 1 character long unless complete
        if progress > 0 and progress_length == 0:
            progress_length = 1

        fill = "#" * progress_length
    else:
        fill = msg_complete
        length = f"^{length}"  # type: ignore

    percent = f"{int(progress):3}%" if display_percentage else ""

    return f"\r{msg_prefix:{msg_prefix_length}} \n[ {tcod.COLCTRL_FORE_RGB:c}{color[0]:c}{color[1]:c}{color[2]:c}{fill:{length}}{tcod.COLCTRL_STOP:c} ] {percent}"
