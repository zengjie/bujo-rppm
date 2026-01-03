from __future__ import annotations

from dataclasses import dataclass
import fitz

from bujo.calendar_model import CalendarModel
from bujo.config import Layout, Settings, Theme, Typography
from bujo.page_map import PageMap
from .primitives import Renderer


FOOTER_TEXTS = {
    "daily_log": "Rapid log your thoughts as they bubble up.",
    "daily_log_week_end": "End of week: time to reflect and migrate.",
    "daily_log_month_end": "End of month: review, reflect, and plan ahead.",
    "weekly_action": "Write only what you can get done this week.",
    "weekly_reflection": "Tidy, acknowledge, migrate, enact.",
    "collection_index": "Organize related information by topic.",
    "future_log": "Store actions and events outside the current month.",
    "monthly_timeline": "Log events after they happen for an accurate record.",
    "monthly_action": "Organize and prioritize your monthly tasks.",
    "intention": "Intention is a commitment to a process. It guides your choices in the present moment.",
    "goals": "Goals define outcomes. They transform desires into tangible destinations.",
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


def _draw_cover_flow_field(page, layout, theme) -> None:
    """Draw flowing streamlines of golden dots on the cover.

    Creates visible flow patterns by tracing particles along a vector field,
    producing the coherent, directional movement seen in bird flocks (Boids).

    The streamlines flow naturally across the entire page.
    Text is rendered on top, so no exclusion zone needed.
    """
    import math

    # Golden color
    gold = theme.gold

    def flow_field(x: float, y: float) -> tuple[float, float]:
        """Calculate flow direction at any point.

        Uses a smooth analytical function to ensure continuous derivatives,
        preventing abrupt direction changes that cause jagged streamlines.
        """
        width = layout.target_width
        height = layout.target_height
        nx, ny = x / width, y / height  # Normalized coords [0, 1]

        # Base angle: nearly horizontal, curves smoothly downward
        base_angle = math.pi * 0.08

        # Smooth curvature that increases toward bottom-right
        curve_factor = nx * ny
        angle_offset = curve_factor * math.pi * 0.35

        # Gentle sinusoidal variation for organic feel
        wave = math.sin((nx + ny) * math.pi * 1.5) * 0.08

        # Final angle
        angle = base_angle + angle_offset + wave

        return math.cos(angle), math.sin(angle)

    def trace_streamline(start_x: float, start_y: float, num_dots: int, dot_spacing: float) -> list:
        """Trace a streamline using fine integration steps, sampling at regular arc-length intervals."""
        points = []
        x, y = start_x, start_y

        integration_step = 3.0
        distance_since_last_dot = 0.0
        max_steps = num_dots * int(dot_spacing / integration_step) + 500

        for _ in range(max_steps):
            if len(points) >= num_dots:
                break

            # Check bounds
            if x < 5 or x > layout.target_width - 5 or y < 5 or y > layout.target_height - 5:
                break

            # Record point if we've traveled enough distance
            if distance_since_last_dot >= dot_spacing:
                points.append((x, y))
                distance_since_last_dot = 0.0

            # Integrate one small step
            dx, dy = flow_field(x, y)
            x += dx * integration_step
            y += dy * integration_step
            distance_since_last_dot += integration_step

        return points

    shape = page.new_shape()

    # Generate streamlines from seed points
    # Sparse spacing for elegant, minimal look
    seed_spacing_x = 70
    seed_spacing_y = 55
    num_dots_per_line = 12
    dot_spacing = 22  # Arc-length distance between dots

    # Single pass for cleaner look
    seed_y = 15
    while seed_y < layout.target_height + 50:
        seed_x = -50
        while seed_x < layout.target_width + 30:
            # Trace streamline from this seed
            points = trace_streamline(seed_x, seed_y, num_dots_per_line, dot_spacing)

            # Draw dots along streamline with varying sizes
            for i, (px, py) in enumerate(points):
                # Size varies along streamline (larger in middle, taper at ends)
                t = i / max(len(points) - 1, 1)
                size_curve = math.sin(t * math.pi) * 0.6 + 0.4  # 0.4 to 1.0

                radius = 1.3 * size_curve

                if radius > 0.4:
                    rect = fitz.Rect(px - radius, py - radius, px + radius, py + radius)
                    shape.draw_oval(rect)

            seed_x += seed_spacing_x
        seed_y += seed_spacing_y

    shape.finish(color=gold, fill=gold)
    shape.commit()


def generate_cover(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    page.draw_rect(page.rect, color=ctx.theme.black, fill=ctx.theme.black)

    # Draw flow field pattern first (behind text)
    _draw_cover_flow_field(page, ctx.layout, ctx.theme)

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
        ("Symbol Reference", ctx.page_map.guide_start),
        ("The System", ctx.page_map.guide_start + 1),
        ("The Practice", ctx.page_map.guide_start + 2),
        ("Set up your logs", ctx.page_map.guide_start + 3),
        ("Intention", ctx.page_map.guide_start + 4),
        ("Goals", ctx.page_map.guide_start + 5),
        ("Future log", ctx.page_map.future_log_start),
    ]

    for i, (text, dest) in enumerate(guide_links):
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

    # Decorative separator between Guide section and calendar tables
    page.draw_line(
        fitz.Point(ctx.layout.content_left, y + 10),
        fitz.Point(ctx.layout.content_right, y + 10),
        color=ctx.theme.gray,
        width=1.5,
    )
    y += 35

    month_col_width = 180
    week_col_start = ctx.layout.content_left + month_col_width + 50

    ctx.renderer.add_text(page, "Monthly logs", ctx.layout.content_left, y, ctx.typography.sizes["body"])
    ctx.renderer.add_text(page, "Weekly logs", week_col_start, y, ctx.typography.sizes["body"])
    y += 55

    available_height = ctx.layout.content_bottom - y - 20
    month_row_height = available_height // 12

    # Get weeks grouped by their primary month (based on majority of days)
    weeks_by_month = ctx.calendar.compute_weeks_by_month()

    # Calculate dynamic week cell width based on max weeks in any month
    max_weeks_per_month = max(len(weeks) for weeks in weeks_by_month)
    available_week_width = ctx.layout.content_right - week_col_start
    week_cell_width = available_week_width // max_weeks_per_month

    # Track vertical separator position
    sep_x = week_col_start - 25
    sep_y_start = y

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

        # Display weeks that primarily belong to this month
        month_weeks = weeks_by_month[month_idx]
        font_size = ctx.typography.sizes["small"]
        for i, w in enumerate(month_weeks):
            week_page = ctx.page_map.weekly_action(w - 1)

            # Calculate centered position for week label + arrow within cell
            week_label = f"W{w}"
            label_width = ctx.renderer.get_text_width(week_label, font_size)
            arrow_width = ctx.typography.arrow_size_small + 5
            total_content_width = label_width + arrow_width
            cell_start = week_col_start + i * week_cell_width
            cell_center_offset = (week_cell_width - total_content_width) / 2
            week_x = cell_start + cell_center_offset

            ctx.renderer.add_text(page, week_label, week_x, text_y, font_size)
            week_arrow_x = week_x + label_width + 5
            week_arrow_y = text_y + font_size * 0.65
            ctx.renderer.draw_arrow_right(page, week_arrow_x, week_arrow_y, ctx.typography.arrow_size_small)

            # Clickable rect covers entire cell for easy tapping
            week_link_rect = (
                cell_start,
                text_y - 10,
                cell_start + week_cell_width,
                text_y + font_size + 10,
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

    # Draw single continuous vertical separator between months and weeks
    sep_y_end = y - 12
    page.draw_line(
        fitz.Point(sep_x, sep_y_start),
        fitz.Point(sep_x, sep_y_end),
        color=ctx.theme.line,
        width=0.5,
    )


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
    num_lines = ctx.settings.num_collections_per_index

    # Calculate dynamic line spacing to utilize available space
    footer_margin = 70
    available_height = ctx.layout.content_bottom - footer_margin - y
    line_spacing = available_height // num_lines

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
        # Make entire row clickable
        link_rect = (ctx.layout.content_left, line_y, ctx.layout.content_right, line_y + line_spacing)
        ctx.renderer.links.add(page_idx, link_rect, collection_page)

    bottom_line_y = y + num_lines * line_spacing
    page.draw_line(
        fitz.Point(ctx.layout.content_left, bottom_line_y),
        fitz.Point(ctx.layout.content_right, bottom_line_y),
        color=ctx.theme.line,
        width=0.5,
    )

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["collection_index"])


def generate_guide_symbol_reference(ctx: PageContext, page_idx: int) -> None:
    """Generate Symbol Reference page - quick reference for all symbols with elegant design."""
    page = ctx.renderer.doc[page_idx]
    font_header = 35
    font_section = 28
    font_desc = 28
    line_height = 1.8

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Symbol Reference", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    # Card dimensions and positions
    card_gap = 25
    card_padding = 20
    content_width = ctx.layout.content_width
    card_width = (content_width - card_gap * 2) // 3
    y_start = ctx.layout.content_top + 130

    # Card heights - calculate based on content
    card1_rows = 4  # N.A.M.E.
    card2_rows = 5  # Action States
    card3_rows = 3  # Signifiers
    row_height = font_desc * line_height
    max_rows = max(card1_rows, card2_rows, card3_rows)
    card_height = 45 + row_height * max_rows + card_padding

    # Card positions
    card1_x = ctx.layout.content_left
    card2_x = ctx.layout.content_left + card_width + card_gap
    card3_x = ctx.layout.content_left + card_width * 2 + card_gap * 2

    # Draw card backgrounds with subtle borders
    for card_x in [card1_x, card2_x, card3_x]:
        page.draw_rect(
            fitz.Rect(card_x, y_start, card_x + card_width, y_start + card_height),
            color=ctx.theme.gray,
            width=0.5,
        )

    symbol_x_offset = card_padding + 5
    desc_x_offset = card_padding + 50

    # Helper to draw symbols
    def draw_dash(x: float, y: float, size: int = 14) -> None:
        page.draw_line(fitz.Point(x, y), fitz.Point(x + size, y), color=ctx.theme.black, width=2.2)

    def draw_dot(x: float, y: float, r: int = 5) -> None:
        page.draw_circle(fitz.Point(x + r, y), r, color=ctx.theme.black, fill=ctx.theme.black)

    def draw_double_line(x: float, y: float, size: int = 14) -> None:
        for offset in [-4, 4]:
            page.draw_line(fitz.Point(x, y + offset), fitz.Point(x + size, y + offset), color=ctx.theme.black, width=1.8)

    def draw_circle_outline(x: float, y: float, r: int = 6) -> None:
        page.draw_circle(fitz.Point(x + r, y), r, color=ctx.theme.black, width=2)

    def draw_x_mark(x: float, y: float, size: int = 10) -> None:
        page.draw_line(fitz.Point(x, y - size / 2), fitz.Point(x + size, y + size / 2), color=ctx.theme.black, width=2.2)
        page.draw_line(fitz.Point(x, y + size / 2), fitz.Point(x + size, y - size / 2), color=ctx.theme.black, width=2.2)

    def draw_arrow_right(x: float, y: float, size: int = 10) -> None:
        page.draw_line(fitz.Point(x, y - size / 2), fitz.Point(x + size, y), color=ctx.theme.black, width=2.2)
        page.draw_line(fitz.Point(x, y + size / 2), fitz.Point(x + size, y), color=ctx.theme.black, width=2.2)

    def draw_arrow_left(x: float, y: float, size: int = 10) -> None:
        page.draw_line(fitz.Point(x + size, y - size / 2), fitz.Point(x, y), color=ctx.theme.black, width=2.2)
        page.draw_line(fitz.Point(x + size, y + size / 2), fitz.Point(x, y), color=ctx.theme.black, width=2.2)

    # Card 1: Rapid Logging (N.A.M.E.)
    ctx.renderer.add_text(page, "Rapid Logging", card1_x + card_padding, y_start + card_padding, font_section)
    y = y_start + card_padding + 45

    items1 = [
        (draw_dash, "Notes"),
        (draw_dot, "Actions"),
        (draw_double_line, "Moods"),
        (draw_circle_outline, "Events"),
    ]
    for draw_fn, label in items1:
        sym_y = y + font_desc * 0.55
        draw_fn(card1_x + symbol_x_offset, sym_y)
        ctx.renderer.add_text(page, label, card1_x + desc_x_offset, y, font_desc)
        y += row_height

    # Card 2: Action States
    ctx.renderer.add_text(page, "Action States", card2_x + card_padding, y_start + card_padding, font_section)
    y = y_start + card_padding + 45

    # Incomplete
    sym_y = y + font_desc * 0.55
    draw_dot(card2_x + symbol_x_offset, sym_y)
    ctx.renderer.add_text(page, "Incomplete", card2_x + desc_x_offset, y, font_desc)
    y += row_height

    # Complete
    sym_y = y + font_desc * 0.55
    draw_x_mark(card2_x + symbol_x_offset, sym_y)
    ctx.renderer.add_text(page, "Complete", card2_x + desc_x_offset, y, font_desc)
    y += row_height

    # Migrated
    sym_y = y + font_desc * 0.55
    draw_arrow_right(card2_x + symbol_x_offset, sym_y)
    ctx.renderer.add_text(page, "Migrated", card2_x + desc_x_offset, y, font_desc)
    y += row_height

    # Scheduled
    sym_y = y + font_desc * 0.55
    draw_arrow_left(card2_x + symbol_x_offset, sym_y)
    ctx.renderer.add_text(page, "Scheduled", card2_x + desc_x_offset, y, font_desc)
    y += row_height

    # Irrelevant
    sym_y = y + font_desc * 0.55
    draw_dot(card2_x + symbol_x_offset, sym_y)
    ctx.renderer.add_text(page, "Irrelevant", card2_x + desc_x_offset, y, font_desc)
    text_width = ctx.renderer.get_text_width("Irrelevant", font_desc)
    page.draw_line(fitz.Point(card2_x + symbol_x_offset, sym_y), fitz.Point(card2_x + desc_x_offset + text_width, sym_y), color=ctx.theme.black, width=1)

    # Card 3: Signifiers
    ctx.renderer.add_text(page, "Signifiers", card3_x + card_padding, y_start + card_padding, font_section)
    y = y_start + card_padding + 45
    icon_size = 12

    # Priority
    sym_y = y + font_desc * 0.55
    ctx.renderer.draw_star(page, card3_x + symbol_x_offset + 6, sym_y, icon_size)
    ctx.renderer.add_text(page, "Priority", card3_x + desc_x_offset, y, font_desc)
    y += row_height

    # Inspiration
    sym_y = y + font_desc * 0.6
    ctx.renderer.draw_lightbulb(page, card3_x + symbol_x_offset + 6, sym_y, icon_size)
    ctx.renderer.add_text(page, "Inspiration", card3_x + desc_x_offset, y, font_desc)
    y += row_height

    # Explore
    sym_y = y + font_desc * 0.55
    ctx.renderer.draw_eye(page, card3_x + symbol_x_offset + 6, sym_y, icon_size)
    ctx.renderer.add_text(page, "Explore", card3_x + desc_x_offset, y, font_desc)

    # Example section - calculate available space and distribute evenly
    example_start_y = y_start + card_height + 50
    available_height = ctx.layout.content_bottom - example_start_y - 30

    # Section title with decorative line
    ctx.renderer.add_text(page, "Example", ctx.layout.content_left, example_start_y, font_header)
    title_width = ctx.renderer.get_text_width("Example", font_header)
    page.draw_line(
        fitz.Point(ctx.layout.content_left + title_width + 15, example_start_y + font_header * 0.5),
        fitz.Point(ctx.layout.content_right, example_start_y + font_header * 0.5),
        color=ctx.theme.gray,
        width=0.5,
    )

    # Scenario subtitle
    subtitle_y = example_start_y + 50
    ctx.renderer.add_text(page, "Planning a Surprise Party", ctx.layout.content_left, subtitle_y, font_section, italic=True)

    # Calculate row parameters to fill available space
    header_y = subtitle_y + 50
    num_rows = 8
    row_area_height = available_height - (header_y - example_start_y) - 50
    line_h = row_area_height // num_rows  # Dynamic row height

    # Font sizes - keep original for example section
    font_hw = 34
    font_note = 19

    # Two-column layout
    col_gap = 50
    left_col_width = 380
    right_col_x = ctx.layout.content_left + left_col_width + col_gap

    # Column headers with underline
    ctx.renderer.add_text(page, "Recorded", ctx.layout.content_left, header_y, font_section)
    ctx.renderer.add_text(page, "After reflection", right_col_x, header_y, font_section)

    # Subtle header underline
    underline_y = header_y + 35
    page.draw_line(
        fitz.Point(ctx.layout.content_left, underline_y),
        fitz.Point(ctx.layout.content_left + left_col_width - 30, underline_y),
        color=ctx.theme.gray,
        width=0.5,
    )
    page.draw_line(
        fitz.Point(right_col_x, underline_y),
        fitz.Point(ctx.layout.content_right, underline_y),
        color=ctx.theme.gray,
        width=0.5,
    )

    example_y = underline_y + 20

    # Symbol alignment columns for left side
    sig_col = 0
    name_col = 35
    text_col = 70

    # Symbol size for example - larger
    ex_dot_r = 6
    ex_arrow = 13
    ex_x = 13

    def draw_ex_dot(x: float, y: float) -> None:
        page.draw_circle(fitz.Point(x + ex_dot_r, y), ex_dot_r, color=ctx.theme.black, fill=ctx.theme.black)

    def draw_ex_dash(x: float, y: float) -> None:
        page.draw_line(fitz.Point(x, y), fitz.Point(x + 18, y), color=ctx.theme.black, width=2.8)

    def draw_ex_double(x: float, y: float) -> None:
        for offset in [-6, 6]:
            page.draw_line(fitz.Point(x, y + offset), fitz.Point(x + 18, y + offset), color=ctx.theme.black, width=2.2)

    def draw_ex_circle(x: float, y: float) -> None:
        page.draw_circle(fitz.Point(x + 8, y), 8, color=ctx.theme.black, width=2.8)

    def draw_ex_x(x: float, y: float) -> None:
        page.draw_line(fitz.Point(x, y - ex_x / 2), fitz.Point(x + ex_x, y + ex_x / 2), color=ctx.theme.black, width=2.8)
        page.draw_line(fitz.Point(x, y + ex_x / 2), fitz.Point(x + ex_x, y - ex_x / 2), color=ctx.theme.black, width=2.8)

    def draw_ex_migrate(x: float, y: float) -> None:
        page.draw_line(fitz.Point(x, y - ex_arrow / 2), fitz.Point(x + ex_arrow, y), color=ctx.theme.black, width=2.8)
        page.draw_line(fitz.Point(x, y + ex_arrow / 2), fitz.Point(x + ex_arrow, y), color=ctx.theme.black, width=2.8)

    def draw_ex_schedule(x: float, y: float) -> None:
        page.draw_line(fitz.Point(x + ex_arrow, y - ex_arrow / 2), fitz.Point(x, y), color=ctx.theme.black, width=2.8)
        page.draw_line(fitz.Point(x + ex_arrow, y + ex_arrow / 2), fitz.Point(x, y), color=ctx.theme.black, width=2.8)

    # Example rows - each with clear structure
    left_x = ctx.layout.content_left

    # Row 1: Priority Action -> Completed
    sym_y = example_y + font_hw * 0.5
    ctx.renderer.draw_star(page, left_x + sig_col + 10, sym_y, 14)
    draw_ex_dot(left_x + name_col, sym_y)
    ctx.renderer.add_text(page, "Book venue", left_x + text_col, example_y, font_hw, italic=True)
    draw_ex_x(right_col_x + 3, sym_y)
    ctx.renderer.add_text(page, "completed", right_col_x + 28, example_y + 10, font_note, italic=True)
    example_y += line_h

    # Row 2: Action -> Migrated
    sym_y = example_y + font_hw * 0.5
    draw_ex_dot(left_x + name_col, sym_y)
    ctx.renderer.add_text(page, "Order cake", left_x + text_col, example_y, font_hw, italic=True)
    draw_ex_migrate(right_col_x, sym_y)
    ctx.renderer.add_text(page, "moved to tomorrow", right_col_x + 28, example_y + 10, font_note, italic=True)
    example_y += line_h

    # Row 3: Action -> Scheduled
    sym_y = example_y + font_hw * 0.5
    draw_ex_dot(left_x + name_col, sym_y)
    ctx.renderer.add_text(page, "Buy balloons", left_x + text_col, example_y, font_hw, italic=True)
    draw_ex_schedule(right_col_x, sym_y)
    ctx.renderer.add_text(page, "scheduled to Friday", right_col_x + 28, example_y + 10, font_note, italic=True)
    example_y += line_h

    # Row 4: Action -> Irrelevant
    sym_y = example_y + font_hw * 0.5
    draw_ex_dot(left_x + name_col, sym_y)
    ctx.renderer.add_text(page, "Print invites", left_x + text_col, example_y, font_hw, italic=True)
    striketext = "Print invites"
    ctx.renderer.add_text(page, striketext, right_col_x, example_y, font_hw, italic=True)
    strike_w = ctx.renderer.get_text_width(striketext, font_hw)
    page.draw_line(fitz.Point(right_col_x, sym_y), fitz.Point(right_col_x + strike_w, sym_y), color=ctx.theme.black, width=1.5)
    ctx.renderer.add_text(page, "use group chat", right_col_x + strike_w + 15, example_y + 10, font_note, italic=True)
    example_y += line_h

    # Row 5: Explore Note -> spawns new action
    sym_y = example_y + font_hw * 0.5
    ctx.renderer.draw_eye(page, left_x + sig_col + 10, sym_y, 14)
    draw_ex_dash(left_x + name_col, sym_y)
    ctx.renderer.add_text(page, "Music options?", left_x + text_col, example_y, font_hw, italic=True)
    draw_ex_dot(right_col_x + 3, sym_y)
    ctx.renderer.add_text(page, "Ask Tom for playlist", right_col_x + 28, example_y, font_hw, italic=True)
    ctx.renderer.add_text(page, "new action", right_col_x + 28, example_y + font_hw * 0.95, font_note, italic=True)
    example_y += line_h

    # Row 6: Inspiration Note -> unchanged
    sym_y = example_y + font_hw * 0.55
    ctx.renderer.draw_lightbulb(page, left_x + sig_col + 10, sym_y, 14)
    draw_ex_dash(left_x + name_col, sym_y)
    ctx.renderer.add_text(page, "80s theme!", left_x + text_col, example_y, font_hw, italic=True)
    ctx.renderer.add_text(page, "(unchanged)", right_col_x, example_y + 10, font_note, italic=True)
    example_y += line_h

    # Row 7: Event -> immutable
    sym_y = example_y + font_hw * 0.5
    draw_ex_circle(left_x + name_col - 3, sym_y)
    ctx.renderer.add_text(page, "Party 6pm", left_x + text_col, example_y, font_hw, italic=True)
    ctx.renderer.add_text(page, "(events are facts)", right_col_x, example_y + 10, font_note, italic=True)
    example_y += line_h

    # Row 8: Mood -> acknowledge marker
    sym_y = example_y + font_hw * 0.5
    draw_ex_double(left_x + name_col - 3, sym_y)
    ctx.renderer.add_text(page, "Nervous", left_x + text_col, example_y, font_hw, italic=True)
    ctx.renderer.add_text(page, "^", right_col_x + 6, example_y, font_hw, italic=True)
    ctx.renderer.add_text(page, "moved toward my goal", right_col_x + 35, example_y + 10, font_note, italic=True)


def generate_guide_system(ctx: PageContext, page_idx: int) -> None:
    """Generate The System page - elegant card-based layout for N.A.M.E. framework."""
    page = ctx.renderer.doc[page_idx]
    font_body = 28
    font_section = 25
    font_small = 25
    line_height = 1.45

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "The System", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    # Layout uses dynamic sizing to fill available space evenly

    y = ctx.layout.content_top + 100

    # Introduction - concise
    intro_text = (
        "The Bullet Journal Method is a mindfulness practice designed to work like a productivity system. "
        "Use |Rapid Logging| to capture thoughts quickly with minimal syntax."
    )
    height = ctx.renderer.draw_rich_text(page, intro_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 20, line_height)
    y += height + 35

    # N.A.M.E. Section with decorative title
    ctx.renderer.add_text(page, "N.A.M.E.", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    title_w = ctx.renderer.get_text_width("N.A.M.E.", ctx.typography.sizes["subheader"])
    page.draw_line(
        fitz.Point(ctx.layout.content_left + title_w + 15, y + ctx.typography.sizes["subheader"] * 0.45),
        fitz.Point(ctx.layout.content_right, y + ctx.typography.sizes["subheader"] * 0.45),
        color=ctx.theme.gray,
        width=0.5,
    )
    y += 45

    # N.A.M.E. cards - 2x2 grid with larger cards
    card_gap = 22
    card_width = (ctx.layout.content_width - card_gap) // 2
    card_height = 168  # Increased from 150
    card_padding = 22  # Increased from 18

    name_items = [
        ("N", "Notes", "dash", "Ideas, insights, information to remember. Capture what you learn."),
        ("A", "Actions", "dot", "Things to do - your tasks. The backbone of your productivity."),
        ("M", "Moods", "double", "How you feel, emotionally or physically. Track your inner state."),
        ("E", "Events", "circle", "Experiences, appointments, milestones. Record what happens."),
    ]

    positions = [
        (ctx.layout.content_left, y),
        (ctx.layout.content_left + card_width + card_gap, y),
        (ctx.layout.content_left, y + card_height + card_gap),
        (ctx.layout.content_left + card_width + card_gap, y + card_height + card_gap),
    ]

    def draw_symbol(sym_type: str, cx: float, cy: float, size: int = 20) -> None:
        if sym_type == "dash":
            page.draw_line(fitz.Point(cx - size / 2, cy), fitz.Point(cx + size / 2, cy), color=ctx.theme.black, width=3)
        elif sym_type == "dot":
            page.draw_circle(fitz.Point(cx, cy), size / 3, color=ctx.theme.black, fill=ctx.theme.black)
        elif sym_type == "double":
            for offset in [-size / 4, size / 4]:
                page.draw_line(fitz.Point(cx - size / 2, cy + offset), fitz.Point(cx + size / 2, cy + offset), color=ctx.theme.black, width=2.5)
        elif sym_type == "circle":
            page.draw_circle(fitz.Point(cx, cy), size / 3, color=ctx.theme.black, width=2.5)

    for i, (letter, name, sym_type, desc) in enumerate(name_items):
        cx, cy = positions[i]
        # Card border
        page.draw_rect(
            fitz.Rect(cx, cy, cx + card_width, cy + card_height),
            color=ctx.theme.gray,
            width=0.5,
        )
        # Large letter
        letter_x = cx + card_padding
        letter_y = cy + card_padding
        ctx.renderer.add_text(page, letter, letter_x, letter_y, 42)
        # Symbol after letter - increased spacing to prevent overlap
        sym_x = letter_x + 55
        sym_y = letter_y + 26
        draw_symbol(sym_type, sym_x, sym_y, 22)
        # Name - adjusted position for new symbol spacing
        ctx.renderer.add_text(page, name, cx + card_padding + 90, letter_y + 8, font_section + 2)
        # Description - multi-line with more vertical space
        ctx.renderer.draw_rich_text(page, desc, cx + card_padding, cy + card_padding + 68, font_small, card_width - card_padding * 2, 1.5)

    y = positions[2][1] + card_height + 38

    # Action States - horizontal flow with clearer design
    ctx.renderer.add_text(page, "Action States", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    title_w = ctx.renderer.get_text_width("Action States", ctx.typography.sizes["subheader"])
    page.draw_line(
        fitz.Point(ctx.layout.content_left + title_w + 15, y + ctx.typography.sizes["subheader"] * 0.45),
        fitz.Point(ctx.layout.content_right, y + ctx.typography.sizes["subheader"] * 0.45),
        color=ctx.theme.gray,
        width=0.5,
    )
    y += 32

    # Explanation text
    action_intro = "A dot can transform to reflect multiple states. Each transformation is a moment of reflection."
    ctx.renderer.add_text(page, action_intro, ctx.layout.content_left, y, font_small, italic=True)
    y += 38

    # Flow diagram - 5 states in a row
    flow_y = y + 28
    state_spacing = ctx.layout.content_width // 5
    states = [
        ("Incomplete", "dot"),
        ("Complete", "x"),
        ("Migrated", "arrow_r"),
        ("Scheduled", "arrow_l"),
        ("Irrelevant", "strike"),
    ]

    def draw_state_symbol(sym_type: str, cx: float, cy: float, size: int = 16) -> None:
        if sym_type == "dot":
            page.draw_circle(fitz.Point(cx, cy), size / 3, color=ctx.theme.black, fill=ctx.theme.black)
        elif sym_type == "x":
            hs = size / 2
            page.draw_line(fitz.Point(cx - hs, cy - hs), fitz.Point(cx + hs, cy + hs), color=ctx.theme.black, width=2.8)
            page.draw_line(fitz.Point(cx - hs, cy + hs), fitz.Point(cx + hs, cy - hs), color=ctx.theme.black, width=2.8)
        elif sym_type == "arrow_r":
            page.draw_line(fitz.Point(cx - size / 2, cy - size / 3), fitz.Point(cx + size / 2, cy), color=ctx.theme.black, width=2.8)
            page.draw_line(fitz.Point(cx - size / 2, cy + size / 3), fitz.Point(cx + size / 2, cy), color=ctx.theme.black, width=2.8)
        elif sym_type == "arrow_l":
            page.draw_line(fitz.Point(cx + size / 2, cy - size / 3), fitz.Point(cx - size / 2, cy), color=ctx.theme.black, width=2.8)
            page.draw_line(fitz.Point(cx + size / 2, cy + size / 3), fitz.Point(cx - size / 2, cy), color=ctx.theme.black, width=2.8)
        elif sym_type == "strike":
            # Dot with strikethrough extending to the right (simulating crossed-out text)
            page.draw_circle(fitz.Point(cx, cy), size / 3, color=ctx.theme.black, fill=ctx.theme.black)
            page.draw_line(fitz.Point(cx + size / 2, cy), fitz.Point(cx + size * 2.5, cy), color=ctx.theme.black, width=1.5)

    # Draw states
    for i, (name, sym_type) in enumerate(states):
        sx = ctx.layout.content_left + state_spacing * i + state_spacing // 2
        # Symbol
        draw_state_symbol(sym_type, sx, flow_y, 16)
        # Label below with more space
        label_w = ctx.renderer.get_text_width(name, font_small)
        ctx.renderer.add_text(page, name, sx - label_w // 2, flow_y + 35, font_small)

    # Draw connecting line from Incomplete through all states
    first_x = ctx.layout.content_left + state_spacing // 2 + 20
    last_x = ctx.layout.content_left + state_spacing * 4 + state_spacing // 2 - 20
    page.draw_line(
        fitz.Point(first_x, flow_y),
        fitz.Point(last_x, flow_y),
        color=ctx.theme.gray,
        width=1,
        dashes="[4 4]",
    )

    y = flow_y + 95

    # Signifiers section
    ctx.renderer.add_text(page, "Signifiers", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    title_w = ctx.renderer.get_text_width("Signifiers", ctx.typography.sizes["subheader"])
    page.draw_line(
        fitz.Point(ctx.layout.content_left + title_w + 15, y + ctx.typography.sizes["subheader"] * 0.45),
        fitz.Point(ctx.layout.content_right, y + ctx.typography.sizes["subheader"] * 0.45),
        color=ctx.theme.gray,
        width=0.5,
    )
    y += 36

    signifier_intro = "Add context to any bullet by placing a signifier in front:"
    ctx.renderer.add_text(page, signifier_intro, ctx.layout.content_left, y, font_small, italic=True)
    y += 45

    # Signifier cards - 3 columns with larger cards
    sig_card_gap = 28
    sig_card_width = (ctx.layout.content_width - sig_card_gap * 2) // 3
    sig_card_height = 165  # Increased from 145
    sig_padding = 24  # Increased from 20

    signifiers = [
        ("star", "Priority", "Important and urgent"),
        ("lightbulb", "Inspiration", "Great idea worth remembering"),
        ("eye", "Explore", "Requires further research"),
    ]

    for i, (icon_type, name, desc) in enumerate(signifiers):
        sx = ctx.layout.content_left + (sig_card_width + sig_card_gap) * i
        # Card
        page.draw_rect(
            fitz.Rect(sx, y, sx + sig_card_width, y + sig_card_height),
            color=ctx.theme.gray,
            width=0.5,
        )
        # Icon centered at top
        icon_cx = sx + sig_card_width // 2
        icon_cy = y + sig_padding + 32
        if icon_type == "star":
            ctx.renderer.draw_star(page, icon_cx, icon_cy, 26)
        elif icon_type == "lightbulb":
            ctx.renderer.draw_lightbulb(page, icon_cx, icon_cy, 26)
        elif icon_type == "eye":
            ctx.renderer.draw_eye(page, icon_cx, icon_cy, 26)
        # Name centered with more space
        name_w = ctx.renderer.get_text_width(name, font_section + 2)
        ctx.renderer.add_text(page, name, icon_cx - name_w // 2, y + sig_padding + 72, font_section + 2)
        # Description centered
        desc_w = ctx.renderer.get_text_width(desc, font_small - 2)
        ctx.renderer.add_text(page, desc, icon_cx - desc_w // 2, y + sig_padding + 112, font_small - 2)

    y += sig_card_height + 40

    # Footer note
    custom_text = "Define your own signifiers as your practice evolves. Keep it minimal - too many symbols slow you down."
    ctx.renderer.add_text(page, custom_text, ctx.layout.content_left, y, font_small - 2, italic=True)
    y += 50

    # Key insight box - fill remaining space to bottom margin
    insight_y = y
    bottom_margin = 35
    insight_height = ctx.layout.content_bottom - insight_y - bottom_margin
    insight_padding = 28
    page.draw_rect(
        fitz.Rect(ctx.layout.content_left, insight_y, ctx.layout.content_right, insight_y + insight_height),
        color=ctx.theme.gray,
        width=0.5,
    )
    # Title
    ctx.renderer.add_text(page, "The Core Insight", ctx.layout.content_left + insight_padding, insight_y + insight_padding, font_section)
    # Insight text with more breathing room
    insight_text = (
        "The power of Bullet Journal lies not in the symbols, but in the reflection they encourage. "
        "Every time you transform a bullet, you ask: does this still deserve my time and attention?"
    )
    ctx.renderer.draw_rich_text(
        page, insight_text,
        ctx.layout.content_left + insight_padding, insight_y + 65,
        font_small, ctx.layout.content_width - insight_padding * 2, 1.6
    )


def generate_guide_set_up_logs(ctx: PageContext, page_idx: int) -> None:
    """Generate Set up your logs page with elegant card-based layout."""
    page = ctx.renderer.doc[page_idx]
    font_body = 28
    font_small = 25
    font_section = 25
    line_height = 1.45
    card_padding = 20

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Set up your logs", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    # Calculate card dimensions to fill available space evenly
    y_start = ctx.layout.content_top + 120
    available_height = ctx.layout.content_bottom - y_start - 30
    card_gap = 20
    num_cards = 4
    card_height = (available_height - card_gap * (num_cards - 1)) // num_cards
    card_width = ctx.layout.content_width

    # Log definitions with descriptions
    logs = [
        {
            "name": "Future log",
            "link_target": ctx.page_map.future_log_start,
            "description": "The Future Log lets you see your future. Store |actions| and |events| that fall outside the current month. It provides an overview of your commitments over time.",
            "columns": None,
        },
        {
            "name": "Monthly log",
            "link_target": ctx.page_map.monthly_start,
            "description": "Two pages to reset, reprioritize, and recommit to what you allow into your life every month.",
            "columns": [
                ("Timeline", "Log events after they've happened. An accurate record of your life."),
                ("Action Plan", "Organize and prioritize monthly |Tasks.| New tasks and Future Log items."),
            ],
        },
        {
            "name": "Weekly log",
            "link_target": ctx.page_map.weekly_start,
            "description": None,
            "columns": [
                ("Reflection", "Tidy entries. Acknowledge what moved you toward and away. Migrate relevant |Actions.|"),
                ("Action plan", "Write only what you can get done this week. Number your top three priorities."),
            ],
        },
        {
            "name": "Daily log",
            "link_target": ctx.page_map.daily_start,
            "description": "Declutter your mind and stay focused. |Rapid Log| your thoughts as they bubble up. This is your main workspace - the heart of daily practice.",
            "columns": None,
        },
    ]

    y = y_start
    for log in logs:
        # Draw card border
        page.draw_rect(
            fitz.Rect(ctx.layout.content_left, y, ctx.layout.content_left + card_width, y + card_height),
            color=ctx.theme.gray,
            width=0.5,
        )

        # Log name with decorative line
        name_y = y + card_padding
        ctx.renderer.add_text(page, log["name"], ctx.layout.content_left + card_padding, name_y, ctx.typography.sizes["subheader"])
        title_w = ctx.renderer.get_text_width(log["name"], ctx.typography.sizes["subheader"])

        # Get started link at right side
        get_started_text = "Get started"
        get_started_w = ctx.renderer.get_text_width(get_started_text, font_small)
        get_started_x = ctx.layout.content_right - card_padding - get_started_w - 25
        ctx.renderer.add_text(page, get_started_text, get_started_x, name_y, font_small)
        ctx.renderer.draw_arrow_right(page, ctx.layout.content_right - card_padding - 10, name_y + font_small / 2, ctx.typography.arrow_size_small)

        # Decorative line between title and "Get started"
        line_start_x = ctx.layout.content_left + card_padding + title_w + 15
        line_end_x = get_started_x - 20
        page.draw_line(
            fitz.Point(line_start_x, name_y + ctx.typography.sizes["subheader"] * 0.45),
            fitz.Point(line_end_x, name_y + ctx.typography.sizes["subheader"] * 0.45),
            color=ctx.theme.gray,
            width=0.5,
        )

        # Link for entire header area
        link_rect = (get_started_x - 5, name_y - 5, ctx.layout.content_right - card_padding, name_y + font_small + 10)
        ctx.renderer.links.add(page_idx, link_rect, log["link_target"])

        content_y = name_y + ctx.typography.sizes["subheader"] + 15

        if log["description"]:
            # Single description
            ctx.renderer.draw_rich_text(
                page, log["description"],
                ctx.layout.content_left + card_padding, content_y,
                font_body, card_width - card_padding * 2, line_height
            )

        if log["columns"]:
            # Two-column layout
            col_gap = 30
            col_width = (card_width - card_padding * 2 - col_gap) // 2
            col1_x = ctx.layout.content_left + card_padding
            col2_x = col1_x + col_width + col_gap

            # If there's a description, start columns lower
            if log["description"]:
                content_y += font_body * line_height * 2 + 10

            for i, (col_title, col_desc) in enumerate(log["columns"]):
                col_x = col1_x if i == 0 else col2_x
                # Column title (italic)
                ctx.renderer.add_text(page, col_title, col_x, content_y, font_section, italic=True)
                # Column description
                ctx.renderer.draw_rich_text(
                    page, col_desc,
                    col_x, content_y + font_section * 1.3,
                    font_small, col_width - 10, line_height
                )

        y += card_height + card_gap


def generate_guide_practice(ctx: PageContext, page_idx: int) -> None:
    """Generate The Practice page - T.A.M.E. framework with elegant card-based layout."""
    page = ctx.renderer.doc[page_idx]
    font_body = 28
    font_section = 25
    font_small = 23
    line_height = 1.45

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "The Practice", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    y = ctx.layout.content_top + 100

    # Introduction - emphasizing N.A.M.E. -> T.A.M.E. cycle
    intro_text = (
        "|N.A.M.E.| captures your experiences. |T.A.M.E.| transforms them into clarity and action. "
        "Recording feeds reflection; reflection guides recording. This cycle is the heart of the practice."
    )
    height = ctx.renderer.draw_rich_text(page, intro_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 20, line_height)
    y += height + 30

    # T.A.M.E. Section with decorative title
    ctx.renderer.add_text(page, "T.A.M.E.", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    title_w = ctx.renderer.get_text_width("T.A.M.E.", ctx.typography.sizes["subheader"])
    page.draw_line(
        fitz.Point(ctx.layout.content_left + title_w + 15, y + ctx.typography.sizes["subheader"] * 0.45),
        fitz.Point(ctx.layout.content_right, y + ctx.typography.sizes["subheader"] * 0.45),
        color=ctx.theme.gray,
        width=0.5,
    )
    y += 40

    # Card layout - 2x2 grid with larger cards
    card_gap = 25
    card_width = (ctx.layout.content_width - card_gap) // 2
    card_height = 165
    card_padding = 22

    cards = [
        ("T", "Tidy", "x", "Cross off completed tasks. Strike through what no longer matters. Clear space before moving forward."),
        ("A", "Acknowledge", "updown", "Look back at what happened. Mark things that moved you toward or away from your goals."),
        ("M", "Migrate", "arrow", "Carry forward what still matters. Rewriting confirms your commitment to each task."),
        ("E", "Enact", "play", "Turn insights into action. Set clear priorities for the next day, week, or month."),
    ]

    positions = [
        (ctx.layout.content_left, y),
        (ctx.layout.content_left + card_width + card_gap, y),
        (ctx.layout.content_left, y + card_height + card_gap),
        (ctx.layout.content_left + card_width + card_gap, y + card_height + card_gap),
    ]

    def draw_tame_symbol(sym_type: str, cx: float, cy: float, size: int = 20) -> None:
        if sym_type == "x":
            # X mark for Tidy (crossing off)
            hs = size * 0.4
            page.draw_line(fitz.Point(cx - hs, cy - hs), fitz.Point(cx + hs, cy + hs), color=ctx.theme.black, width=3)
            page.draw_line(fitz.Point(cx - hs, cy + hs), fitz.Point(cx + hs, cy - hs), color=ctx.theme.black, width=3)
        elif sym_type == "updown":
            # Up and down arrows for Acknowledge (toward/away)
            # Up arrow
            page.draw_line(fitz.Point(cx - size * 0.2, cy - size * 0.15), fitz.Point(cx - size * 0.2, cy + size * 0.35), color=ctx.theme.black, width=2.5)
            page.draw_line(fitz.Point(cx - size * 0.35, cy + size * 0.05), fitz.Point(cx - size * 0.2, cy - size * 0.25), color=ctx.theme.black, width=2.5)
            page.draw_line(fitz.Point(cx - size * 0.05, cy + size * 0.05), fitz.Point(cx - size * 0.2, cy - size * 0.25), color=ctx.theme.black, width=2.5)
            # Down arrow
            page.draw_line(fitz.Point(cx + size * 0.2, cy - size * 0.35), fitz.Point(cx + size * 0.2, cy + size * 0.15), color=ctx.theme.black, width=2.5)
            page.draw_line(fitz.Point(cx + size * 0.05, cy - size * 0.05), fitz.Point(cx + size * 0.2, cy + size * 0.25), color=ctx.theme.black, width=2.5)
            page.draw_line(fitz.Point(cx + size * 0.35, cy - size * 0.05), fitz.Point(cx + size * 0.2, cy + size * 0.25), color=ctx.theme.black, width=2.5)
        elif sym_type == "arrow":
            # Forward arrow for Migrate
            page.draw_line(fitz.Point(cx - size * 0.35, cy), fitz.Point(cx + size * 0.35, cy), color=ctx.theme.black, width=2.5)
            page.draw_line(fitz.Point(cx + size * 0.1, cy - size * 0.3), fitz.Point(cx + size * 0.4, cy), color=ctx.theme.black, width=2.5)
            page.draw_line(fitz.Point(cx + size * 0.1, cy + size * 0.3), fitz.Point(cx + size * 0.4, cy), color=ctx.theme.black, width=2.5)
        elif sym_type == "play":
            # Play/action triangle for Enact
            pts = [
                fitz.Point(cx - size * 0.25, cy - size * 0.35),
                fitz.Point(cx - size * 0.25, cy + size * 0.35),
                fitz.Point(cx + size * 0.35, cy),
            ]
            page.draw_polyline(pts + [pts[0]], color=ctx.theme.black, width=2.5, closePath=True)

    for i, (letter, name, sym_type, desc) in enumerate(cards):
        cx, cy = positions[i]
        # Card border - subtle gray like The System page
        page.draw_rect(
            fitz.Rect(cx, cy, cx + card_width, cy + card_height),
            color=ctx.theme.gray,
            width=0.5,
        )
        # Large letter
        letter_x = cx + card_padding
        letter_y = cy + card_padding
        ctx.renderer.add_text(page, letter, letter_x, letter_y, 42)
        # Symbol after letter
        sym_x = letter_x + 55
        sym_y = letter_y + 26
        draw_tame_symbol(sym_type, sym_x, sym_y, 22)
        # Name - adjusted position
        ctx.renderer.add_text(page, name, cx + card_padding + 90, letter_y + 8, font_section + 2)
        # Description - multi-line
        ctx.renderer.draw_rich_text(page, desc, cx + card_padding, cy + card_padding + 60, font_small, card_width - card_padding * 2, 1.4)

    y = positions[2][1] + card_height + 40

    # Reflection Rhythm section with decorative title
    ctx.renderer.add_text(page, "Reflection Rhythm", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    title_w = ctx.renderer.get_text_width("Reflection Rhythm", ctx.typography.sizes["subheader"])
    page.draw_line(
        fitz.Point(ctx.layout.content_left + title_w + 15, y + ctx.typography.sizes["subheader"] * 0.45),
        fitz.Point(ctx.layout.content_right, y + ctx.typography.sizes["subheader"] * 0.45),
        color=ctx.theme.gray,
        width=0.5,
    )
    y += 40

    font_rhythm = 25
    font_detail = 24
    rhythm_line_height = 1.45
    indent = 20
    detail_indent = 40

    # Daily reflection
    ctx.renderer.draw_rich_text(page, "|Daily| - Every evening on Daily Log page", ctx.layout.content_left + indent, y, font_rhythm, ctx.layout.content_width - 60, rhythm_line_height)
    y += font_rhythm * rhythm_line_height + 4
    ctx.renderer.add_text(page, "Review today's entries. Cross off completed tasks.", ctx.layout.content_left + detail_indent, y, font_detail)
    y += font_detail * rhythm_line_height
    ctx.renderer.add_text(page, "Migrate unfinished items to tomorrow or Future Log.", ctx.layout.content_left + detail_indent, y, font_detail)
    y += font_detail * rhythm_line_height
    ctx.renderer.add_text(page, "Set 1-3 priorities for tomorrow.", ctx.layout.content_left + detail_indent, y, font_detail)
    y += font_detail * rhythm_line_height + 15

    # Weekly reflection
    ctx.renderer.draw_rich_text(page, "|Weekly| - Sunday on Weekly Reflection page", ctx.layout.content_left + indent, y, font_rhythm, ctx.layout.content_width - 60, rhythm_line_height)
    y += font_rhythm * rhythm_line_height + 4
    ctx.renderer.add_text(page, "Review Weekly Action plan: what got done, what didn't.", ctx.layout.content_left + detail_indent, y, font_detail)
    y += font_detail * rhythm_line_height
    ctx.renderer.add_text(page, "Acknowledge progress toward/away from goals.", ctx.layout.content_left + detail_indent, y, font_detail)
    y += font_detail * rhythm_line_height
    ctx.renderer.add_text(page, "Migrate remaining tasks. Set next week's focus.", ctx.layout.content_left + detail_indent, y, font_detail)
    y += font_detail * rhythm_line_height + 15

    # Monthly reflection
    ctx.renderer.draw_rich_text(page, "|Monthly| - Last day on Monthly Timeline page", ctx.layout.content_left + indent, y, font_rhythm, ctx.layout.content_width - 60, rhythm_line_height)
    y += font_rhythm * rhythm_line_height + 4
    ctx.renderer.add_text(page, "Review Monthly Timeline: events, patterns, surprises.", ctx.layout.content_left + detail_indent, y, font_detail)
    y += font_detail * rhythm_line_height
    ctx.renderer.add_text(page, "Check Intention and Goals pages. Are you on track?", ctx.layout.content_left + detail_indent, y, font_detail)
    y += font_detail * rhythm_line_height
    ctx.renderer.add_text(page, "Migrate incomplete items. Set next month's direction.", ctx.layout.content_left + detail_indent, y, font_detail)
    y += font_detail * rhythm_line_height + 20

    # Tip
    ctx.renderer.add_text(page, "Tip: On week/month end, Daily Log shows a Reflection link.", ctx.layout.content_left + indent, y, font_detail, italic=True)


def generate_guide_intention(ctx: PageContext, page_idx: int) -> None:
    """Generate Intention page - minimalist design with maximum writing space."""
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Intention", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    # Maximize dot grid space - extend to just above footer
    grid_top = ctx.layout.content_top + 100
    grid_bottom = ctx.layout.target_height - 70  # Leave space for footer
    ctx.renderer.draw_dot_grid(page, grid_top, grid_bottom)

    # Unified footer section
    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["intention"])


def generate_guide_goals(ctx: PageContext, page_idx: int) -> None:
    """Generate Goals page - minimalist design with maximum writing space."""
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Goals", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    # Maximize dot grid space - extend to just above footer
    grid_top = ctx.layout.content_top + 100
    grid_bottom = ctx.layout.target_height - 70  # Leave space for footer
    ctx.renderer.draw_dot_grid(page, grid_top, grid_bottom)

    # Unified footer section
    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["goals"])


def generate_future_log(ctx: PageContext, page_idx: int, quarter: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Future Log", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    start_idx = (quarter - 1) * 3
    months = ctx.calendar.months[start_idx:start_idx + 3]

    # Extend dot grid to just above footer (footer starts at target_height - 55)
    grid_start_y = ctx.layout.content_top + 115
    grid_end_y = ctx.layout.target_height - 70

    ctx.renderer.draw_dot_grid(page, grid_start_y, grid_end_y)

    # Distribute available space evenly among 3 months
    available_height = grid_end_y - grid_start_y
    month_height = available_height // 3

    for i, month in enumerate(months):
        my = grid_start_y + i * month_height
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

    # Extend dot grid to just above footer
    grid_start_y = ctx.layout.content_top + 115
    grid_end_y = ctx.layout.target_height - 70

    ctx.renderer.draw_dot_grid(page, grid_start_y, grid_end_y)

    # Distribute day numbers evenly in available height
    available_height = grid_end_y - grid_start_y
    day_height = available_height / month.days

    for day in range(1, month.days + 1):
        day_y = grid_start_y + (day - 1) * day_height + ctx.typography.sizes["day_number"] / 2
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


def generate_monthly_action_plan(ctx: PageContext, page_idx: int, month_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    month = ctx.calendar.months[month_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, month.name, ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    # Extend dot grid to just above footer
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 115, ctx.layout.target_height - 70)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["monthly_action"])


def _draw_clickable_week_date_range(ctx: PageContext, page_idx: int, week_num: int, x: float, y: float, font_size: float) -> None:
    """Draw week date range with clickable start/end dates linking to daily pages.

    If the week spans across years, clip dates to the current year boundaries.
    """
    import calendar as cal_module
    from datetime import date as date_type
    page = ctx.renderer.doc[page_idx]
    start_date, end_date = ctx.calendar.week_date_range(week_num)

    # Clip dates to current year boundaries
    year = ctx.calendar.year
    if start_date.year < year:
        start_date = date_type(year, 1, 1)  # Jan 1 of current year
    if end_date.year > year:
        end_date = date_type(year, 12, 31)  # Dec 31 of current year

    # Format: "Jan 1" - "Jan 4" with clickable dates
    start_label = f"{cal_module.month_abbr[start_date.month]} {start_date.day}"
    end_label = f"{cal_module.month_abbr[end_date.month]} {end_date.day}"
    separator = " - "

    current_x = x

    # Start date (always clickable since we clipped to current year)
    start_day_of_year = ctx.calendar.day_of_year(start_date.month - 1, start_date.day)
    start_page = ctx.page_map.daily_page(start_day_of_year)
    ctx.renderer.add_nav_link(page_idx, start_label, start_page, current_x, y, font_size, with_arrow=False)
    current_x += ctx.renderer.get_text_width(start_label, font_size)

    # Separator (non-clickable)
    ctx.renderer.add_text(page, separator, current_x, y, font_size, ctx.theme.gray)
    current_x += ctx.renderer.get_text_width(separator, font_size)

    # End date (always clickable since we clipped to current year)
    end_day_of_year = ctx.calendar.day_of_year(end_date.month - 1, end_date.day)
    end_page = ctx.page_map.daily_page(end_day_of_year)
    ctx.renderer.add_nav_link(page_idx, end_label, end_page, current_x, y, font_size, with_arrow=False)


def generate_weekly_action_plan(ctx: PageContext, page_idx: int, week_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    week_num = week_idx + 1

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, f"W{week_num} Action plan", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    # Auto-fill date range from calendar with clickable dates
    _draw_clickable_week_date_range(ctx, page_idx, week_num, ctx.layout.content_right - 180, ctx.layout.content_top + 55, 22)

    # Extend dot grid to just above footer
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 115, ctx.layout.target_height - 70)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["weekly_action"])


def generate_weekly_reflection(ctx: PageContext, page_idx: int, week_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    week_num = week_idx + 1

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, f"W{week_num} Reflection", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    # Auto-fill date range from calendar with clickable dates
    _draw_clickable_week_date_range(ctx, page_idx, week_num, ctx.layout.content_right - 180, ctx.layout.content_top + 55, 22)

    # Extend dot grid to just above footer
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 115, ctx.layout.target_height - 70)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["weekly_reflection"])


def generate_daily_log(ctx: PageContext, page_idx: int, month_idx: int, day: int) -> None:
    page = ctx.renderer.doc[page_idx]

    # Breadcrumb navigation: ← Index / January / W1
    # Larger spacing for touch-friendly operation on reMarkable
    nav_y = ctx.layout.content_top + 5
    nav_font = ctx.typography.sizes["nav"]
    sep = "/"
    sep_color = ctx.theme.gray
    touch_gap = 30  # Extra spacing between elements for finger tapping

    # ← Index (with arrow, clickable)
    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.year_index, ctx.layout.content_left, nav_y)

    # Calculate position after "← Index"
    index_text_width = ctx.renderer.get_text_width("Index", nav_font)
    arrow_offset = nav_font * 0.5 * 1.5 + 8  # arrow size + padding
    x = ctx.layout.content_left + arrow_offset + index_text_width + touch_gap

    # Separator
    ctx.renderer.add_text(page, sep, x, nav_y, nav_font, sep_color)
    x += ctx.renderer.get_text_width(sep, nav_font) + touch_gap

    # Check for reflection reminders first (affects breadcrumb structure)
    is_last_of_week = ctx.calendar.is_last_day_of_week(month_idx, day)
    is_last_of_month = ctx.calendar.is_last_day_of_month(month_idx, day)

    # Determine footer text based on day type
    footer_key = "daily_log"
    if is_last_of_month:
        footer_key = "daily_log_month_end"
    elif is_last_of_week:
        footer_key = "daily_log_week_end"

    # Month name (clickable, no arrow)
    month_name = ctx.calendar.months[month_idx].name
    monthly_page = ctx.page_map.month_timeline(month_idx)
    ctx.renderer.add_nav_link(page_idx, month_name, monthly_page, x, nav_y, with_arrow=False)
    x += ctx.renderer.get_text_width(month_name, nav_font) + touch_gap

    # Monthly Reflection link (placed right after month, if month end)
    if is_last_of_month:
        ctx.renderer.add_text(page, sep, x, nav_y, nav_font, sep_color)
        x += ctx.renderer.get_text_width(sep, nav_font) + touch_gap
        ctx.renderer.add_nav_link(page_idx, "Reflection", monthly_page, x, nav_y, with_arrow=False)
        x += ctx.renderer.get_text_width("Reflection", nav_font) + touch_gap

    # Separator before week
    ctx.renderer.add_text(page, sep, x, nav_y, nav_font, sep_color)
    x += ctx.renderer.get_text_width(sep, nav_font) + touch_gap

    # Week (clickable, no arrow)
    week_num = ctx.calendar.week_of_date(month_idx, day)
    week_label = f"W{week_num}"
    week_page = ctx.page_map.weekly_action(week_num - 1)
    ctx.renderer.add_nav_link(page_idx, week_label, week_page, x, nav_y, with_arrow=False)
    x += ctx.renderer.get_text_width(week_label, nav_font) + touch_gap

    # Weekly Reflection link (placed right after week, if week end)
    if is_last_of_week:
        weekly_reflection_page = ctx.page_map.weekly_reflection(week_num - 1)
        ctx.renderer.add_text(page, sep, x, nav_y, nav_font, sep_color)
        x += ctx.renderer.get_text_width(sep, nav_font) + touch_gap
        ctx.renderer.add_nav_link(page_idx, "Reflection", weekly_reflection_page, x, nav_y, with_arrow=False)

    # Include day-of-week abbreviation: "Mon, Jan 15"
    day_abbrev = ctx.calendar.day_of_week_abbrev(month_idx, day)
    date_label = f"{day_abbrev}, {ctx.calendar.date_label(month_idx, day)}"
    ctx.renderer.add_text(page, date_label, ctx.layout.content_left, ctx.layout.content_top + 70, ctx.typography.sizes["title_page"])

    # Extend dot grid to just above footer
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 145, ctx.layout.target_height - 70)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS[footer_key])


def generate_daily_log_continuation(ctx: PageContext, page_idx: int, month_idx: int, day: int) -> None:
    page = ctx.renderer.doc[page_idx]

    # Breadcrumb navigation: ← Index / January / W1
    # Larger spacing for touch-friendly operation on reMarkable
    nav_y = ctx.layout.content_top + 5
    nav_font = ctx.typography.sizes["nav"]
    sep = "/"
    sep_color = ctx.theme.gray
    touch_gap = 30  # Extra spacing between elements for finger tapping

    # ← Index (with arrow, clickable)
    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.year_index, ctx.layout.content_left, nav_y)

    # Calculate position after "← Index"
    index_text_width = ctx.renderer.get_text_width("Index", nav_font)
    arrow_offset = nav_font * 0.5 * 1.5 + 8  # arrow size + padding
    x = ctx.layout.content_left + arrow_offset + index_text_width + touch_gap

    # Separator
    ctx.renderer.add_text(page, sep, x, nav_y, nav_font, sep_color)
    x += ctx.renderer.get_text_width(sep, nav_font) + touch_gap

    # Month name (clickable, no arrow)
    month_name = ctx.calendar.months[month_idx].name
    monthly_page = ctx.page_map.month_timeline(month_idx)
    ctx.renderer.add_nav_link(page_idx, month_name, monthly_page, x, nav_y, with_arrow=False)
    x += ctx.renderer.get_text_width(month_name, nav_font) + touch_gap

    # Separator
    ctx.renderer.add_text(page, sep, x, nav_y, nav_font, sep_color)
    x += ctx.renderer.get_text_width(sep, nav_font) + touch_gap

    # Week (clickable, no arrow)
    week_num = ctx.calendar.week_of_date(month_idx, day)
    week_label = f"W{week_num}"
    week_page = ctx.page_map.weekly_action(week_num - 1)
    ctx.renderer.add_nav_link(page_idx, week_label, week_page, x, nav_y, with_arrow=False)

    # Include day-of-week abbreviation: "Mon, Jan 15"
    day_abbrev = ctx.calendar.day_of_week_abbrev(month_idx, day)
    date_label = f"{day_abbrev}, {ctx.calendar.date_label(month_idx, day)}"
    ctx.renderer.add_text(page, date_label, ctx.layout.content_left, ctx.layout.content_top + 70, ctx.typography.sizes["title_page"])

    # Continuation pages have no footer, extend grid closer to bottom
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 145, ctx.layout.target_height - 50)


def generate_collection_page(ctx: PageContext, page_idx: int, index_page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", index_page_idx, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 50, ctx.layout.content_bottom - 30)
