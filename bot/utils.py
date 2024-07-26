def progress_bar(progress: float, width=40):
    pos = int(width * progress)
    return "-" * pos + "◉" + "-" * (width - pos - 1)


def get_duration(duration: str):
    seconds = 0
    for i, part in enumerate(reversed(duration.split(":"))):
        seconds += int(part) * 60**i
    return seconds
