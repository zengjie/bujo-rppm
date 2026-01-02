from __future__ import annotations

from pathlib import Path

import fitz

from .calendar_model import CalendarModel
from .config import Layout, Settings, Theme, Typography
from .link_manager import LinkManager
from .page_map import build_page_map
from .render import (
    FontManager,
    PageContext,
    Renderer,
    generate_collection_index,
    generate_collection_page,
    generate_cover,
    generate_daily_log,
    generate_daily_log_continuation,
    generate_future_log,
    generate_guide_goals,
    generate_guide_how_to_reflect,
    generate_guide_intention,
    generate_guide_practice,
    generate_guide_set_up_logs,
    generate_guide_system,
    generate_main_index,
    generate_monthly_action_plan,
    generate_monthly_timeline,
    generate_weekly_action_plan,
    generate_weekly_reflection,
    generate_year_index,
 )
from .validation import ValidationReport


class BulletJournalGenerator:
    def __init__(
        self,
        settings: Settings | None = None,
        layout: Layout | None = None,
        theme: Theme | None = None,
        typography: Typography | None = None,
        asset_root: Path | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.layout = layout or Layout()
        self.theme = theme or Theme()
        self.typography = typography or Typography()
        self.asset_root = asset_root or Path(".")

    def generate(self) -> tuple[fitz.Document, ValidationReport]:
        calendar = CalendarModel.for_year(self.settings.year)
        page_map = build_page_map(self.settings, calendar)

        doc = fitz.open()
        for _ in range(page_map.total_pages):
            doc.new_page(width=self.layout.target_width, height=self.layout.target_height)

        links = LinkManager()
        font_manager = FontManager(self.typography, self.asset_root)
        renderer = Renderer(doc, self.layout, self.theme, self.typography, font_manager, links)
        ctx = PageContext(
            renderer=renderer,
            calendar=calendar,
            page_map=page_map,
            settings=self.settings,
            layout=self.layout,
            theme=self.theme,
            typography=self.typography,
        )

        generate_cover(ctx, page_map.cover)
        generate_main_index(ctx, page_map.main_index)
        generate_year_index(ctx, page_map.year_index)

        generate_collection_index(ctx, page_map.collection_index_c, "C")
        generate_collection_index(ctx, page_map.collection_index_d, "D")

        generate_guide_system(ctx, page_map.guide_start)
        generate_guide_set_up_logs(ctx, page_map.guide_start + 1)
        generate_guide_practice(ctx, page_map.guide_start + 2)
        generate_guide_how_to_reflect(ctx, page_map.guide_start + 3)
        generate_guide_intention(ctx, page_map.guide_start + 4)
        generate_guide_goals(ctx, page_map.guide_start + 5)

        for quarter in range(self.settings.num_future_log_pages):
            generate_future_log(ctx, page_map.future_log_start + quarter, quarter + 1)

        for month_idx in range(12):
            generate_monthly_timeline(ctx, page_map.month_timeline(month_idx), month_idx)
            generate_monthly_action_plan(ctx, page_map.month_action_plan(month_idx), month_idx)

        for week_idx in range(calendar.weeks_in_year):
            generate_weekly_action_plan(ctx, page_map.weekly_action(week_idx))
            generate_weekly_reflection(ctx, page_map.weekly_reflection(week_idx))

        for month in calendar.months:
            for day in range(1, month.days + 1):
                day_of_year = calendar.day_of_year(month.index, day)
                for page_in_day in range(self.settings.pages_per_day):
                    page_idx = page_map.daily_page(day_of_year, page_in_day)
                    if page_in_day == 0:
                        generate_daily_log(ctx, page_idx, month.index, day)
                    else:
                        generate_daily_log_continuation(ctx, page_idx, month.index, day)

        total_collections = self.settings.num_collections_per_index * self.settings.num_collection_indexes
        for collection_idx in range(total_collections):
            index_page = (
                page_map.collection_index_c
                if collection_idx < self.settings.num_collections_per_index
                else page_map.collection_index_d
            )
            page_idx = page_map.collection_page(collection_idx)
            generate_collection_page(ctx, page_idx, index_page)

        invalid_links = links.apply(doc)
        report = ValidationReport(
            missing_fonts=font_manager.missing_fonts(),
            invalid_links=invalid_links,
            expected_pages=page_map.total_pages,
            actual_pages=len(doc),
        )
        return doc, report

    def save(self, doc: fitz.Document, output_path: str) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)
        doc.close()
