from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .calendar_model import CalendarModel
from .config import Settings


@dataclass(frozen=True)
class PageMap:
    cover: int
    main_index: int
    year_index: int
    collection_index_c: int
    collection_index_d: int
    guide_start: int
    future_log_start: int
    monthly_start: int
    weekly_start: int
    daily_start: int
    collection_start: int
    total_pages: int

    pages_per_day: int
    pages_per_collection: int
    num_collection_indexes: int
    num_collections_per_index: int

    def month_timeline(self, month_idx: int) -> int:
        return self.monthly_start + month_idx * 2

    def month_action_plan(self, month_idx: int) -> int:
        return self.monthly_start + month_idx * 2 + 1

    def weekly_action(self, week_idx: int) -> int:
        return self.weekly_start + week_idx * 2

    def weekly_reflection(self, week_idx: int) -> int:
        return self.weekly_start + week_idx * 2 + 1

    def daily_page(self, day_of_year: int, page_in_day: int = 0) -> int:
        return self.daily_start + day_of_year * self.pages_per_day + page_in_day

    def collection_page(self, collection_idx: int) -> int:
        return self.collection_start + collection_idx * self.pages_per_collection


@dataclass(frozen=True)
class PageCounts:
    guide_pages: int
    future_log_pages: int
    monthly_pages: int
    weekly_pages: int
    daily_pages: int
    collection_pages: int


def build_page_map(settings: Settings, calendar: CalendarModel) -> PageMap:
    cover = 0
    main_index = 1
    year_index = 2
    collection_index_c = 3
    collection_index_d = 4
    guide_start = 5

    future_log_start = guide_start + settings.num_guide_pages
    monthly_start = future_log_start + settings.num_future_log_pages
    weekly_start = monthly_start + 12 * 2
    daily_start = weekly_start + calendar.weeks_in_year * 2
    collection_start = daily_start + calendar.total_days * settings.pages_per_day

    total_collections = settings.num_collections_per_index * settings.num_collection_indexes
    total_pages = collection_start + total_collections * settings.pages_per_collection

    return PageMap(
        cover=cover,
        main_index=main_index,
        year_index=year_index,
        collection_index_c=collection_index_c,
        collection_index_d=collection_index_d,
        guide_start=guide_start,
        future_log_start=future_log_start,
        monthly_start=monthly_start,
        weekly_start=weekly_start,
        daily_start=daily_start,
        collection_start=collection_start,
        total_pages=total_pages,
        pages_per_day=settings.pages_per_day,
        pages_per_collection=settings.pages_per_collection,
        num_collection_indexes=settings.num_collection_indexes,
        num_collections_per_index=settings.num_collections_per_index,
    )


def build_page_counts(settings: Settings, calendar: CalendarModel) -> PageCounts:
    total_collections = settings.num_collections_per_index * settings.num_collection_indexes
    return PageCounts(
        guide_pages=settings.num_guide_pages,
        future_log_pages=settings.num_future_log_pages,
        monthly_pages=12 * 2,
        weekly_pages=calendar.weeks_in_year * 2,
        daily_pages=calendar.total_days * settings.pages_per_day,
        collection_pages=total_collections * settings.pages_per_collection,
    )
