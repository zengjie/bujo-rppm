from dataclasses import dataclass
from typing import List, Tuple

import fitz


@dataclass
class DeferredLink:
    page_idx: int
    rect: Tuple[float, float, float, float]
    dest_page_idx: int


class LinkManager:
    def __init__(self) -> None:
        self._links: List[DeferredLink] = []

    @property
    def links(self) -> List[DeferredLink]:
        return self._links

    def add(self, page_idx: int, rect: Tuple[float, float, float, float], dest_page_idx: int) -> None:
        self._links.append(DeferredLink(page_idx=page_idx, rect=rect, dest_page_idx=dest_page_idx))

    def apply(self, doc: fitz.Document) -> List[DeferredLink]:
        invalid: List[DeferredLink] = []
        total_pages = len(doc)
        for link in self._links:
            if 0 <= link.dest_page_idx < total_pages:
                page = doc[link.page_idx]
                page.insert_link({
                    "kind": fitz.LINK_GOTO,
                    "page": link.dest_page_idx,
                    "from": fitz.Rect(link.rect),
                })
            else:
                invalid.append(link)
        return invalid
