from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import fitz

from bujo.calendar_model import CalendarModel
from bujo.config import Layout, Settings, Theme, Typography
from bujo.page_map import PageMap
from .primitives import Renderer


FOOTER_TEXTS = {
    "daily_log": (
        "This is your |Daily Log,| designed to declutter your mind and keep you focused "
        "throughout the day. |Rapid Log| your thoughts as they bubble up. Add a note page "
        "with the Dot S template if you need more space for notes. You'll find this in "
        "Document settings in the toolbar."
    ),
    "weekly_action": (
        "Write down only what you can get done this week. Think of this as your weekly "
        "commitments. If something is too big, break into smaller steps. When you're done, "
        "number the top three things that would make this week a success."
    ),
    "weekly_reflection": (
        "Tidy your weekly entries. Update the monthly timeline and action plan. Acknowledge "
        "up to three things that moved you toward, and up to three things that moved you away, "
        "from the life you want/who you want to be, in a few sentences. Migrate only relevant "
        "|Actions| into the next week's Action Plan. Enact any insight from your reflection "
        "into the action plan."
    ),
    "collection_index": (
        "Use this index to organize and group related information by topic. We call them "
        "|Collections.| Common Collections include goals, fitness trackers, reading lists, "
        "class notes, and more. To keep your Collections organized, simply add your Collection "
        "to the list and use the links to quickly find your content."
    ),
    "future_log": (
        "The Future log is a |Collection| where you can store |actions| and |events| that fall "
        "outside the current month. More than just being a type of calendar, the Future log also "
        "provides an overview of your commitments over time."
    ),
    "monthly_timeline": (
        "This page is your |Timeline.| Though it can be used as a traditional calendar by adding "
        "upcoming events, it's recommended to use the Timeline to log events after they've happened. "
        "This will provide a more accurate and useful record of your life."
    ),
    "monthly_action": (
        "This page is your |Monthly Action Plan.| It's designed to help you organize and prioritize "
        "your monthly |tasks.| It consists of new tasks, Future Log items scheduled for this month, "
        "and any important unfinished tasks from the previous month."
    ),
}


@dataclass(frozen=True)
class PageContext:
    renderer: Renderer
    calendar: CalendarModel
    page_map: PageMap
    settings: Settings
    layout: Layout
    theme: Theme
    typography: Typography


def generate_cover(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    page.draw_rect(page.rect, color=ctx.theme.black, fill=ctx.theme.black)

    left_margin = 50
    title_y = ctx.layout.target_height * 0.15

    lightning_scale = 8.0
    lightning_x = left_margin
    lightning_y = title_y + 20
    ctx.renderer.draw_lightning_white(page, lightning_x, lightning_y, scale=lightning_scale)

    text_x = left_margin + 130

    bullet_size = 90
    ctx.renderer.add_text(page, "Bullet", text_x, title_y, bullet_size, ctx.theme.white)

    journal_y = title_y + 95
    ctx.renderer.add_text(page, "Journal", text_x, journal_y, bullet_size, ctx.theme.white)

    year_y = journal_y + 130
    year_size = 140
    ctx.renderer.add_text(page, str(ctx.settings.year), text_x, year_y, year_size, ctx.theme.white)


def generate_main_index(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_text(page, "Index A", ctx.layout.content_left, ctx.layout.content_top + 10, ctx.typography.sizes["title_page"])

    y = ctx.layout.content_top + 80
    row_height = 52

    guide_links = [
        ("Bullet Journal Guide", ctx.page_map.guide_start),
        ("Set up logs", ctx.page_map.guide_start + 1),
        ("The Practice Overview", ctx.page_map.guide_start + 2),
        ("How to reflect", ctx.page_map.guide_start + 3),
        ("Intention", ctx.page_map.guide_start + 4),
        ("Goals", ctx.page_map.guide_start + 5),
        ("Future log", ctx.page_map.future_log_start),
    ]

    for text, dest in guide_links:
        ctx.renderer.add_nav_link(page_idx, text, dest, ctx.layout.content_left, y, ctx.typography.sizes["body"], with_arrow=False)
        arrow_y = y + ctx.typography.sizes["body"] * 0.65
        arrow_x = ctx.layout.content_right - 25
        ctx.renderer.draw_arrow_right(page, arrow_x, arrow_y, ctx.typography.arrow_size_large)
        arrow_link_rect = (arrow_x - 10, y - 5, ctx.layout.content_right, y + ctx.typography.sizes["body"] + 5)
        ctx.renderer.links.add(page_idx, arrow_link_rect, dest)
        page.draw_line(
            fitz.Point(ctx.layout.content_left, y + 40),
            fitz.Point(ctx.layout.content_right, y + 40),
            color=ctx.theme.line,
            width=0.5,
        )
        y += row_height

    y += 35

    month_col_width = 180
    week_col_start = ctx.layout.content_left + month_col_width + 50

    ctx.renderer.add_text(page, "Monthly logs", ctx.layout.content_left, y, ctx.typography.sizes["body"])
    ctx.renderer.add_text(page, "Weekly logs", week_col_start, y, ctx.typography.sizes["body"])
    y += 55

    available_height = ctx.layout.content_bottom - y - 20
    month_row_height = available_height // 12

    week_starts = [1, 6, 10, 14, 19, 23, 27, 32, 36, 40, 45, 49]
    week_area_width = ctx.layout.content_right - week_col_start
    week_num_width = 95

    for month_idx in range(12):
        month = ctx.calendar.months[month_idx]
        month_page = ctx.page_map.month_timeline(month_idx)

        text_y = y + (month_row_height - ctx.typography.sizes["small"]) / 2 - 10

        ctx.renderer.add_text(page, month.name, ctx.layout.content_left, text_y, ctx.typography.sizes["small"])
        month_arrow_x = ctx.layout.content_left + 120
        month_arrow_y = text_y + ctx.typography.sizes["small"] * 0.65
        ctx.renderer.draw_arrow_right(page, month_arrow_x, month_arrow_y, ctx.typography.arrow_size_small)
        month_link_rect = (
            ctx.layout.content_left - 5,
            text_y - 5,
            month_col_width,
            text_y + ctx.typography.sizes["small"] + 5,
        )
        ctx.renderer.links.add(page_idx, month_link_rect, month_page)

        sep_x = week_col_start - 25
        page.draw_line(
            fitz.Point(sep_x, y),
            fitz.Point(sep_x, y + month_row_height - 12),
            color=ctx.theme.line,
            width=0.5,
        )

        week_start = week_starts[month_idx]
        week_end = week_starts[month_idx + 1] if month_idx < 11 else ctx.calendar.weeks_in_year + 1

        for i, w in enumerate(range(week_start, week_end)):
            week_page = ctx.page_map.weekly_action(w - 1)
            week_x = week_col_start + i * week_num_width

            ctx.renderer.add_text(page, str(w), week_x, text_y, ctx.typography.sizes["small"])
            week_arrow_x = week_x + 30
            week_arrow_y = text_y + ctx.typography.sizes["small"] * 0.65
            ctx.renderer.draw_arrow_right(page, week_arrow_x, week_arrow_y, ctx.typography.arrow_size_small)
            week_link_rect = (
                week_x - 5,
                text_y - 5,
                week_x + week_num_width - 5,
                text_y + ctx.typography.sizes["small"] + 5,
            )
            ctx.renderer.links.add(page_idx, week_link_rect, week_page)

        line_y = y + month_row_height - 12
        page.draw_line(
            fitz.Point(ctx.layout.content_left, line_y),
            fitz.Point(ctx.layout.content_right, line_y),
            color=ctx.theme.line,
            width=0.5,
        )
        y += month_row_height


def generate_year_index(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_text(page, "Index B", ctx.layout.content_left, ctx.layout.content_top + 10, ctx.typography.sizes["title_page"])
    ctx.renderer.add_text(page, "Daily logs", ctx.layout.content_left, ctx.layout.content_top + 75, ctx.typography.sizes["body"])

    y = ctx.layout.content_top + 130
    available_height = ctx.layout.content_bottom - y - 60
    month_block_height = available_height // 12

    days_per_row = 16
    day_col_start = ctx.layout.content_left + 115
    day_col_width = ctx.layout.content_right - day_col_start - 20
    day_spacing = day_col_width / days_per_row

    for month in ctx.calendar.months:
        row1_y = y + 8
        row2_y = y + month_block_height / 2 + 2

        ctx.renderer.add_text(page, month.name, ctx.layout.content_left, row1_y, ctx.typography.sizes["small"])

        row_gap = row2_y - row1_y - ctx.typography.sizes["tiny"]
        v_padding = min(8, row_gap / 2 - 1)

        for day in range(1, min(month.days + 1, 17)):
            link_left = day_col_start + (day - 1) * day_spacing
            link_right = link_left + day_spacing

            text_width = ctx.renderer.get_text_width(str(day), ctx.typography.sizes["tiny"])
            text_x = link_left + (day_spacing - text_width) / 2
            ctx.renderer.add_text(page, str(day), text_x, row1_y, ctx.typography.sizes["tiny"])

            day_of_year = ctx.calendar.day_of_year(month.index, day)
            dest_page = ctx.page_map.daily_page(day_of_year)
            link_rect = (link_left, row1_y - v_padding, link_right, row1_y + ctx.typography.sizes["tiny"] + v_padding)
            ctx.renderer.links.add(page_idx, link_rect, dest_page)

        for day in range(17, month.days + 1):
            link_left = day_col_start + (day - 17) * day_spacing
            link_right = link_left + day_spacing

            text_width = ctx.renderer.get_text_width(str(day), ctx.typography.sizes["tiny"])
            text_x = link_left + (day_spacing - text_width) / 2
            ctx.renderer.add_text(page, str(day), text_x, row2_y, ctx.typography.sizes["tiny"])

            day_of_year = ctx.calendar.day_of_year(month.index, day)
            dest_page = ctx.page_map.daily_page(day_of_year)
            link_rect = (link_left, row2_y - v_padding, link_right, row2_y + ctx.typography.sizes["tiny"] + v_padding)
            ctx.renderer.links.add(page_idx, link_rect, dest_page)

        line_y = y + month_block_height - 8
        page.draw_line(
            fitz.Point(ctx.layout.content_left, line_y),
            fitz.Point(ctx.layout.content_right, line_y),
            color=ctx.theme.line,
            width=0.5,
        )

        y += month_block_height

    ctx.renderer.add_bottom_nav(page_idx, [("Index", ctx.page_map.main_index)])


def generate_collection_index(ctx: PageContext, page_idx: int, letter: str) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, f"Index {letter}", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    y = ctx.layout.content_top + 130
    line_spacing = 60
    num_lines = ctx.settings.num_collections_per_index

    collection_offset = 0 if letter == "C" else ctx.settings.num_collections_per_index

    for i in range(num_lines):
        line_y = y + i * line_spacing
        page.draw_line(
            fitz.Point(ctx.layout.content_left, line_y),
            fitz.Point(ctx.layout.content_right, line_y),
            color=ctx.theme.line,
            width=0.5,
        )

        arrow_y = line_y + line_spacing / 2
        arrow_x = ctx.layout.content_right - 22
        ctx.renderer.draw_arrow_right(page, arrow_x, arrow_y, ctx.typography.arrow_size_large)

        collection_idx = collection_offset + i
        collection_page = ctx.page_map.collection_page(collection_idx)
        link_rect = (arrow_x - 15, arrow_y - 15, ctx.layout.content_right, arrow_y + 15)
        ctx.renderer.links.add(page_idx, link_rect, collection_page)

    bottom_line_y = y + num_lines * line_spacing
    page.draw_line(
        fitz.Point(ctx.layout.content_left, bottom_line_y),
        fitz.Point(ctx.layout.content_right, bottom_line_y),
        color=ctx.theme.line,
        width=0.5,
    )

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["collection_index"])


def generate_guide_system(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    font_body = 26
    line_height = 1.5

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "The Bullet Journal Guide: System", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    y = ctx.layout.content_top + 100

    ctx.renderer.add_text(page, "Description", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    y += ctx.typography.subheader_spacing
    desc_text = (
        "The Bullet Journal Method is a mindfulness practice that's designed to work like a "
        "productivity system. Be it for your career, education, family, or health, BuJo offers a lot of "
        "resources for how to help you |write a better life.| The best way to learn how to Bullet Journal "
        "is to experience it. This guide is designed to help you get up and running with the basics. "
        "Below is a list of resources to help you level up your practice."
    )
    height = ctx.renderer.draw_rich_text(page, desc_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 40, line_height)
    y += height + 20

    ctx.renderer.add_text(page, "Rapid logging", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    y += ctx.typography.subheader_spacing
    rapid_text = (
        "Rapid Logging allows you to quickly capture and categorize your thoughts and feelings as "
        "bulleted lists. Each bullet represents one of four categories of information:"
    )
    height = ctx.renderer.draw_rich_text(page, rapid_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 40, line_height)
    y += height + 15

    symbol_x = ctx.layout.content_left + 12
    desc_x = ctx.layout.content_left + 45
    symbol_size = 12

    dash_y = y + font_body * 0.65
    page.draw_line(fitz.Point(symbol_x - 2, dash_y), fitz.Point(symbol_x + symbol_size, dash_y), color=ctx.theme.black, width=2)
    ctx.renderer.add_text(page, "Notes (things to remember)", desc_x, y, font_body)
    y += font_body * line_height

    dot_y = y + font_body * 0.65
    dot_r = 4
    page.draw_circle(fitz.Point(symbol_x + dot_r, dot_y), dot_r, color=ctx.theme.black, fill=ctx.theme.black)
    ctx.renderer.add_text(page, "Actions (things to do)", desc_x, y, font_body)
    y += font_body * line_height

    line_y_center = y + font_body * 0.65
    line_len = 14
    for offset in [-4, 4]:
        page.draw_line(
            fitz.Point(symbol_x - 2, line_y_center + offset),
            fitz.Point(symbol_x + line_len - 2, line_y_center + offset),
            color=ctx.theme.black, width=1.8,
        )
    ctx.renderer.add_text(page, "Moods (things felt, emotionally or physically)", desc_x, y, font_body)
    y += font_body * line_height

    circle_y = y + font_body * 0.65
    circle_r = 5
    page.draw_circle(fitz.Point(symbol_x + circle_r, circle_y), circle_r, color=ctx.theme.black, width=1.8)
    ctx.renderer.add_text(page, "Events (things we experience)", desc_x, y, font_body)
    y += font_body * line_height

    y += 15

    action_note = (
        "Note that we use a dot instead of checkboxes for actions. That's because they have four states "
        "that allows us to monitor the status of an action:"
    )
    height = ctx.renderer.draw_rich_text(page, action_note, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 40, line_height)
    y += height + 15

    state_symbol_x = ctx.layout.content_left + 12
    state_desc_x = ctx.layout.content_left + 45

    dot_y = y + font_body * 0.65
    page.draw_circle(fitz.Point(state_symbol_x + dot_r, dot_y), dot_r, color=ctx.theme.black, fill=ctx.theme.black)
    ctx.renderer.add_text(page, "Incomplete", state_desc_x, y, font_body)
    y += font_body * line_height

    x_y = y + font_body * 0.65
    x_size = 8
    page.draw_line(
        fitz.Point(state_symbol_x, x_y - x_size / 2),
        fitz.Point(state_symbol_x + x_size, x_y + x_size / 2),
        color=ctx.theme.black, width=2,
    )
    page.draw_line(
        fitz.Point(state_symbol_x, x_y + x_size / 2),
        fitz.Point(state_symbol_x + x_size, x_y - x_size / 2),
        color=ctx.theme.black, width=2,
    )
    ctx.renderer.add_text(page, "Complete", state_desc_x, y, font_body)
    y += font_body * line_height

    arrow_y = y + font_body * 0.65
    arrow_size = 8
    page.draw_line(
        fitz.Point(state_symbol_x, arrow_y - arrow_size / 2),
        fitz.Point(state_symbol_x + arrow_size, arrow_y),
        color=ctx.theme.black, width=2,
    )
    page.draw_line(
        fitz.Point(state_symbol_x, arrow_y + arrow_size / 2),
        fitz.Point(state_symbol_x + arrow_size, arrow_y),
        color=ctx.theme.black, width=2,
    )
    ctx.renderer.add_text(page, "Migrated (moved)", state_desc_x, y, font_body)
    y += font_body * line_height

    dot_y = y + font_body * 0.65
    page.draw_circle(fitz.Point(state_symbol_x + dot_r, dot_y), dot_r, color=ctx.theme.black, fill=ctx.theme.black)
    ctx.renderer.add_text(page, "Irrelevant", state_desc_x, y, font_body)
    text_width = ctx.renderer.get_text_width("Irrelevant", font_body)
    strike_y = y + font_body * 0.65
    page.draw_line(
        fitz.Point(state_symbol_x, strike_y),
        fitz.Point(state_desc_x + text_width, strike_y),
        color=ctx.theme.black, width=1,
    )


def generate_guide_set_up_logs(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    font_body = 22
    font_small = 19
    line_height = 1.35

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Set up your logs", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    y = ctx.layout.content_top + 95
    get_started_x = ctx.layout.content_right - 110

    ctx.renderer.add_text(page, "Future log", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    ctx.renderer.add_text(page, "Get started", get_started_x, y, font_small)
    ctx.renderer.draw_arrow_right(page, ctx.layout.content_right - 15, y + font_small / 2, ctx.typography.arrow_size_small)
    link_rect = (get_started_x - 5, y - 5, ctx.layout.content_right, y + font_small + 5)
    ctx.renderer.links.add(page_idx, link_rect, ctx.page_map.future_log_start)
    y += ctx.typography.subheader_spacing

    future_text = (
        "The Future Log lets you see your future. It is an outline of the life you're choosing to write. "
        "The Future log is a |Collection| where you can store |actions| and |events| that fall outside the "
        "current month. More than just being a type of calendar, the Future log also provides an "
        "overview of your commitments over time."
    )
    height = ctx.renderer.draw_rich_text(page, future_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 30, line_height)
    y += height + 10

    page.draw_line(fitz.Point(ctx.layout.content_left, y), fitz.Point(ctx.layout.content_right, y), color=ctx.theme.black, width=0.5)
    y += 15

    ctx.renderer.add_text(page, "Monthly log", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    ctx.renderer.add_text(page, "Get started", get_started_x, y, font_small)
    ctx.renderer.draw_arrow_right(page, ctx.layout.content_right - 15, y + font_small / 2, ctx.typography.arrow_size_small)
    link_rect = (get_started_x - 5, y - 5, ctx.layout.content_right, y + font_small + 5)
    ctx.renderer.links.add(page_idx, link_rect, ctx.page_map.monthly_start)
    y += ctx.typography.subheader_spacing

    monthly_intro = "Two pages to reset, reprioritize, and recommit to what you allow into your life every month."
    height = ctx.renderer.draw_rich_text(page, monthly_intro, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 30, line_height)
    y += height + 10

    col_width = (ctx.layout.content_width - 40) // 2
    col1_x = ctx.layout.content_left
    col2_x = ctx.layout.content_left + col_width + 25

    ctx.renderer.add_text(page, "Timeline", col1_x, y, font_body, italic=True)
    ctx.renderer.add_text(page, "Action Plan", col2_x, y, font_body, italic=True)
    y += font_body * 1.3

    timeline_text = (
        "The first page is your |Timeline.| Though it can be used as a traditional calendar "
        "by adding upcoming events, it's recommended to use the Timeline to log "
        "events after they've happened."
    )
    action_plan_text = (
        "The next page is your Monthly |Action Plan.| It's designed to help you organize "
        "and prioritize your monthly |Tasks.| It consists of new Tasks, Future Log items "
        "scheduled for this month."
    )

    h1 = ctx.renderer.draw_rich_text(page, timeline_text, col1_x, y, font_body, col_width - 10, line_height)
    h2 = ctx.renderer.draw_rich_text(page, action_plan_text, col2_x, y, font_body, col_width - 10, line_height)
    y += max(h1, h2) + 10

    page.draw_line(fitz.Point(ctx.layout.content_left, y), fitz.Point(ctx.layout.content_right, y), color=ctx.theme.black, width=0.5)
    y += 15

    ctx.renderer.add_text(page, "Weekly log", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    ctx.renderer.add_text(page, "Get started", get_started_x, y, font_small)
    ctx.renderer.draw_arrow_right(page, ctx.layout.content_right - 15, y + font_small / 2, ctx.typography.arrow_size_small)
    link_rect = (get_started_x - 5, y - 5, ctx.layout.content_right, y + font_small + 5)
    ctx.renderer.links.add(page_idx, link_rect, ctx.page_map.weekly_start)
    y += ctx.typography.subheader_spacing

    ctx.renderer.add_text(page, "Reflection", col1_x, y, font_body, italic=True)
    ctx.renderer.add_text(page, "Action plan", col2_x, y, font_body, italic=True)
    y += font_body * 1.3

    reflection_text = (
        "Tidy your weekly entries. Update the monthly timeline and action plan. "
        "Acknowledge up to three things that moved you toward, and up to three "
        "things that moved you away. Migrate only relevant |Actions| into the next week's Action Plan."
    )
    weekly_action_text = (
        "Write down only what you can get done this week. Think of this as your weekly "
        "commitments. If something is too big, break into smaller steps. When you're "
        "done, number the top three things."
    )

    h1 = ctx.renderer.draw_rich_text(page, reflection_text, col1_x, y, font_body, col_width - 10, line_height)
    h2 = ctx.renderer.draw_rich_text(page, weekly_action_text, col2_x, y, font_body, col_width - 10, line_height)
    y += max(h1, h2) + 10

    page.draw_line(fitz.Point(ctx.layout.content_left, y), fitz.Point(ctx.layout.content_right, y), color=ctx.theme.black, width=0.5)
    y += 15

    ctx.renderer.add_text(page, "Daily log", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    ctx.renderer.add_text(page, "Get started", get_started_x, y, font_small)
    ctx.renderer.draw_arrow_right(page, ctx.layout.content_right - 15, y + font_small / 2, ctx.typography.arrow_size_small)
    link_rect = (get_started_x - 5, y - 5, ctx.layout.content_right, y + font_small + 5)
    ctx.renderer.links.add(page_idx, link_rect, ctx.page_map.daily_start)
    y += ctx.typography.subheader_spacing

    daily_text = (
        "The Daily Log is designed to declutter your mind and keep you focused throughout the day. "
        "|Rapid Log| your thoughts as they bubble up."
    )
    ctx.renderer.draw_rich_text(page, daily_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 30, line_height)


def generate_guide_practice(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    font_body = 24
    line_height = 1.5

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "The Practice", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    y = ctx.layout.content_top + 100

    intro_text = (
        "Writing things down is important, but it's only half of the equation. We can quickly "
        "accumulate so much information that it's overwhelming. Reflection helps you slow down, "
        "make sense of your experiences, and align with what truly matters. In the Bullet Journal "
        "Method, reflection isn't about dwelling on the past--it's about learning from it to move "
        "forward with clarity over and over again. It's a practice."
    )
    height = ctx.renderer.draw_rich_text(page, intro_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 40, line_height)
    y += height + 20

    name_text = (
        "Rapid logging, the foundation of Bullet Journaling, lets you Record your experience by "
        "|N.A.M.E.,| organizing it into |N|otes, |A|ctions, |M|oods, and |E|vents. Reflection builds on this "
        "by helping you |T.A.M.E.| your Record, turning raw information into insights, and then "
        "putting those insights into action."
    )
    height = ctx.renderer.draw_rich_text(page, name_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 40, line_height)
    y += height + 25

    tame_intro = (
        "|T.A.M.E.| is a step-by-step process for reflection, be it daily, weekly, or monthly. It helps you "
        "make sense of your experiences and turn insights into action. Here's how it works:"
    )
    height = ctx.renderer.draw_rich_text(page, tame_intro, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 40, line_height)
    y += height + 25

    tame_steps = [
        ("1. T - Tidy", "your record. Cross off completed tasks, migrate unfinished ones, and declutter what no longer matters. This clears mental and physical space."),
        ("2. A - Acknowledge", "your actions: Look back on what happened. Identify a few things that aligned with your intention and a few that didn't. For example, did a meeting help you focus on your goal, or did an unexpected distraction pull you off track?"),
        ("3. M - Migrate", "what matters. Let go of what doesn't. Yes, this means rewriting open actions into the day, weekly, or the month where they will get done. It's about getting clear on what we're committing to in each stretch of time."),
        ("4. E - Enact", "your insights into your Action plans. Set clear priorities for the next day, week, or month to stay on course."),
    ]

    for step_title, step_desc in tame_steps:
        ctx.renderer.add_text(page, step_title, ctx.layout.content_left + 20, y, font_body)
        title_width = ctx.renderer.get_text_width(step_title, font_body)
        height = ctx.renderer.draw_rich_text(
            page,
            step_desc,
            ctx.layout.content_left + 25 + title_width,
            y,
            font_body,
            ctx.layout.content_width - 65 - title_width,
            line_height,
        )
        y += max(height, font_body * line_height) + 15


def generate_guide_how_to_reflect(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    font_body = 24
    line_height = 1.5

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "How to reflect", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    y = ctx.layout.content_top + 100

    ctx.renderer.add_text(page, "Daily reflection", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    y += ctx.typography.subheader_spacing
    daily_text = (
        "Tidy your daily entries. Acknowledge up to three things that moved you toward, and up to "
        "three things that moved you away, from the life you want/who you want to be, with an up "
        "or down arrow next to the entry. Migrate: Identify what needs to be carried forward into "
        "tomorrow's plan. Enact any daily insight by writing them down as actions."
    )
    height = ctx.renderer.draw_rich_text(page, daily_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 40, line_height)
    y += height + 25

    ctx.renderer.add_text(page, "Weekly reflection", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    y += ctx.typography.subheader_spacing
    weekly_text = (
        "Tidy your weekly entries. Update the monthly timeline and action plan. Acknowledge up "
        "to three things that moved you toward, and up to three things that moved you away, from "
        "the life you want/who you want to be, in a few sentences. Migrate only relevant |Actions| into "
        "the next week's Action Plan. Enact any insight from your reflection into the action plan. "
        "Prioritize your action plan based on your intention or insight. |Take action.|"
    )
    height = ctx.renderer.draw_rich_text(page, weekly_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 40, line_height)
    y += height + 25

    ctx.renderer.add_text(page, "Monthly reflection", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    y += ctx.typography.subheader_spacing
    monthly_text = (
        "Tidy up your record for the last month. Acknowledge up to three things that moved you "
        "toward, and up to three things that moved you away, from the life you want/who you want "
        "to be, in short paragraphs. Migrate Actions that matter for the month ahead. Enact insights "
        "from your reflection onto your monthly action plan. Prioritize your action plan based on "
        "your intention or insight. |Take action.|"
    )
    ctx.renderer.draw_rich_text(page, monthly_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 40, line_height)


def generate_guide_intention(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    footer_font = 22

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Intention", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    grid_top = ctx.layout.content_top + 100
    grid_bottom = ctx.layout.content_bottom - 160
    ctx.renderer.draw_dot_grid(page, grid_top, grid_bottom)

    footer_y = ctx.layout.content_bottom - 140
    page.draw_line(
        fitz.Point(ctx.layout.content_left, footer_y),
        fitz.Point(ctx.layout.content_right, footer_y),
        color=ctx.theme.black,
        width=0.5,
    )
    footer_y += 15

    ctx.renderer.draw_lightning(page, ctx.layout.content_left, footer_y + 5, scale=1.8)

    footer_text = (
        "An intention is a commitment to a process. Intentions bring meaning into our lives now, so that we "
        "can navigate our lives based on what it is as opposed to what may be. They're powerful tools that we "
        "can use to instantly direct our focus for as long as we need. We set an intention to use as our compass."
    )
    ctx.renderer.draw_rich_text(page, footer_text, ctx.layout.content_left + 45, footer_y, footer_font, ctx.layout.content_width - 75, 1.4)


def generate_guide_goals(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    footer_font = 22

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Goals", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    grid_top = ctx.layout.content_top + 100
    grid_bottom = ctx.layout.content_bottom - 160
    ctx.renderer.draw_dot_grid(page, grid_top, grid_bottom)

    footer_y = ctx.layout.content_bottom - 140
    page.draw_line(
        fitz.Point(ctx.layout.content_left, footer_y),
        fitz.Point(ctx.layout.content_right, footer_y),
        color=ctx.theme.black,
        width=0.5,
    )
    footer_y += 15

    ctx.renderer.draw_lightning(page, ctx.layout.content_left, footer_y + 5, scale=1.8)

    footer_text = (
        "A goal is the definition of an outcome. Goals help us articulate what we want, transforming ephemeral "
        "desires into tangible targets, lofty dreams into fixed destinations. Taking time to carefully define our "
        "destinations, can provide a much needed sense of purpose and direction."
    )
    ctx.renderer.draw_rich_text(page, footer_text, ctx.layout.content_left + 45, footer_y, footer_font, ctx.layout.content_width - 75, 1.4)


def generate_future_log(ctx: PageContext, page_idx: int, quarter: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Future Log", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    start_idx = (quarter - 1) * 3
    months = ctx.calendar.months[start_idx:start_idx + 3]

    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 115, ctx.layout.content_bottom - 130)

    y = ctx.layout.content_top + 115
    month_height = (ctx.layout.content_height - 265) // 3

    for i, month in enumerate(months):
        my = y + i * month_height
        ctx.renderer.add_text(page, month.name, ctx.layout.content_left, my, ctx.typography.sizes["body"])
        page.draw_line(
            fitz.Point(ctx.layout.content_left, my + 45),
            fitz.Point(ctx.layout.content_right, my + 45),
            color=ctx.theme.black,
            width=0.5,
        )

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["future_log"])


def generate_monthly_timeline(ctx: PageContext, page_idx: int, month_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    month = ctx.calendar.months[month_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, month.name, ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 115, ctx.layout.content_bottom - 130)

    y = ctx.layout.content_top + 115
    day_height = (ctx.layout.content_height - 265) / month.days

    for day in range(1, month.days + 1):
        day_y = y + (day - 1) * day_height + ctx.typography.sizes["day_number"] / 2
        ctx.renderer.add_text(page, str(day), ctx.layout.content_left, day_y, ctx.typography.sizes["day_number"])

        day_of_year = ctx.calendar.day_of_year(month_idx, day)
        dest_page = ctx.page_map.daily_page(day_of_year)
        link_rect = (
            ctx.layout.content_left - 5,
            day_y - 5,
            ctx.layout.content_left + 35,
            day_y + ctx.typography.sizes["day_number"] + 5,
        )
        ctx.renderer.links.add(page_idx, link_rect, dest_page)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["monthly_timeline"])
    ctx.renderer.add_bottom_nav(page_idx, [("Year", ctx.page_map.year_index)])


def generate_monthly_action_plan(ctx: PageContext, page_idx: int, month_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    month = ctx.calendar.months[month_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, month.name, ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 115, ctx.layout.content_bottom - 130)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["monthly_action"])


def draw_date_range_input(ctx: PageContext, page: fitz.Page, x: float, y: float, font_size: float = 24) -> None:
    line_width = 25
    slash_spacing = 8

    current_x = x
    line_y = y + font_size - 2

    page.draw_line(
        fitz.Point(current_x, line_y),
        fitz.Point(current_x + line_width, line_y),
        color=ctx.theme.gray,
        width=0.8,
    )
    current_x += line_width + slash_spacing
    ctx.renderer.add_text(page, "/", current_x, y, font_size, ctx.theme.black)
    current_x += 12
    page.draw_line(
        fitz.Point(current_x, line_y),
        fitz.Point(current_x + line_width, line_y),
        color=ctx.theme.gray,
        width=0.8,
    )
    current_x += line_width + 20

    ctx.renderer.add_text(page, "to", current_x, y, font_size, ctx.theme.black, italic=True)
    current_x += 30

    page.draw_line(
        fitz.Point(current_x, line_y),
        fitz.Point(current_x + line_width, line_y),
        color=ctx.theme.gray,
        width=0.8,
    )
    current_x += line_width + slash_spacing
    ctx.renderer.add_text(page, "/", current_x, y, font_size, ctx.theme.black)
    current_x += 12
    page.draw_line(
        fitz.Point(current_x, line_y),
        fitz.Point(current_x + line_width, line_y),
        color=ctx.theme.gray,
        width=0.8,
    )


def generate_weekly_action_plan(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Weekly Action plan", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    draw_date_range_input(ctx, page, ctx.layout.content_right - 220, ctx.layout.content_top + 55, 22)

    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 115, ctx.layout.content_bottom - 130)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["weekly_action"])


def generate_weekly_reflection(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Weekly Reflection", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    draw_date_range_input(ctx, page, ctx.layout.content_right - 220, ctx.layout.content_top + 55, 22)

    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 115, ctx.layout.content_bottom - 130)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["weekly_reflection"])


def generate_daily_log(ctx: PageContext, page_idx: int, month_idx: int, day: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.year_index, ctx.layout.content_left, ctx.layout.content_top + 5)

    month_name = ctx.calendar.months[month_idx].name
    monthly_page = ctx.page_map.month_timeline(month_idx)
    monthly_text_width = ctx.renderer.get_text_width(month_name, ctx.typography.sizes["nav"])
    ctx.renderer.add_nav_link(
        page_idx,
        month_name,
        monthly_page,
        ctx.layout.content_right - monthly_text_width - 40,
        ctx.layout.content_top + 5,
    )

    date_label = ctx.calendar.date_label(month_idx, day)
    ctx.renderer.add_text(page, date_label, ctx.layout.content_left, ctx.layout.content_top + 70, ctx.typography.sizes["title_page"])

    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 145, ctx.layout.content_bottom - 130)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["daily_log"])


def generate_daily_log_continuation(ctx: PageContext, page_idx: int, month_idx: int, day: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.year_index, ctx.layout.content_left, ctx.layout.content_top + 5)

    month_name = ctx.calendar.months[month_idx].name
    monthly_page = ctx.page_map.month_timeline(month_idx)
    monthly_text_width = ctx.renderer.get_text_width(month_name, ctx.typography.sizes["nav"])
    ctx.renderer.add_nav_link(
        page_idx,
        month_name,
        monthly_page,
        ctx.layout.content_right - monthly_text_width - 40,
        ctx.layout.content_top + 5,
    )

    date_label = ctx.calendar.date_label(month_idx, day)
    ctx.renderer.add_text(page, date_label, ctx.layout.content_left, ctx.layout.content_top + 70, ctx.typography.sizes["title_page"])

    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 145, ctx.layout.content_bottom - 30)


def generate_collection_page(ctx: PageContext, page_idx: int, index_page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", index_page_idx, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 50, ctx.layout.content_bottom - 30)
