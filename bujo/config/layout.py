from dataclasses import dataclass, field


@dataclass(frozen=True)
class Layout:
    target_width: int = 954
    target_height: int = 1696
    toolbar_height: int = 130
    margin_side: int = 25
    margin_bottom: int = 100

    dot_spacing: int = 50
    dot_size: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "content_left", self.margin_side)
        object.__setattr__(self, "content_right", self.target_width - self.margin_side)
        object.__setattr__(self, "content_top", self.toolbar_height)
        object.__setattr__(self, "content_bottom", self.target_height - self.margin_bottom)
        object.__setattr__(self, "content_width", self.content_right - self.content_left)
        object.__setattr__(self, "content_height", self.content_bottom - self.content_top)

    content_left: int = field(init=False)
    content_right: int = field(init=False)
    content_top: int = field(init=False)
    content_bottom: int = field(init=False)
    content_width: int = field(init=False)
    content_height: int = field(init=False)
