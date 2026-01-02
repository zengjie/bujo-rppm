from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class Typography:
    font_path_regular: str = "fonts/EBGaramond-Regular.ttf"
    font_path_italic: str = "fonts/EBGaramond-Italic.ttf"
    font_name_regular: str = "EBGaramond"
    font_name_italic: str = "EBGaramondIt"
    fallback_regular: str = "helv"
    fallback_italic: str = "helvI"

    sizes: Dict[str, int] = field(default_factory=lambda: {
        "title_cover": 48,
        "title_page": 52,
        "header": 32,
        "subheader": 28,
        "body": 32,
        "nav": 24,
        "footer": 22,
        "small": 24,
        "tiny": 20,
        "day_number": 26,
    })

    arrow_size_large: int = 14
    arrow_size_small: int = 10
    subheader_spacing: int = 55
