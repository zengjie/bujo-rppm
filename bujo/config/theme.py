from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    black: tuple = (0, 0, 0)
    white: tuple = (1, 1, 1)
    gray: tuple = (0.5, 0.5, 0.5)
    light_gray: tuple = (0.85, 0.85, 0.85)
    dot_grid: tuple = (0.82, 0.82, 0.82)
    line: tuple = (0.85, 0.85, 0.85)
    gold: tuple = (1, 0.84, 0)
