from dataclasses import dataclass
from typing import List

from .link_manager import DeferredLink


@dataclass
class ValidationReport:
    missing_fonts: List[str]
    invalid_links: List[DeferredLink]
    expected_pages: int
    actual_pages: int

    @property
    def ok(self) -> bool:
        return not self.missing_fonts and not self.invalid_links and self.expected_pages == self.actual_pages

    def summary_lines(self) -> List[str]:
        lines = []
        if self.expected_pages != self.actual_pages:
            lines.append(f"page-count mismatch: expected {self.expected_pages}, got {self.actual_pages}")
        if self.missing_fonts:
            lines.append(f"missing fonts: {len(self.missing_fonts)}")
        if self.invalid_links:
            lines.append(f"invalid links: {len(self.invalid_links)}")
        if not lines:
            lines.append("validation ok")
        return lines
