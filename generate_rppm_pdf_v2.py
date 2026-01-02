#!/usr/bin/env python3
"""
Generate Bullet Journal PDF optimized for reMarkable Paper Pro Move (rPPM).
Version 2: Full design fidelity with original PDF.

Features:
- EB Garamond Regular + Italic fonts
- Dot grid background on all log pages
- Lightning icon in footer sections
- Complete footer explanatory text
- Arrow-style navigation links
- Full weekly links in main index
"""

import fitz
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional

# =============================================================================
# CONSTANTS
# =============================================================================

# Target PDF dimensions (rPPM)
TARGET_WIDTH = 954
TARGET_HEIGHT = 1696
TOOLBAR_HEIGHT = 130
MARGIN_SIDE = 25
MARGIN_BOTTOM = 100

# Content area
CONTENT_LEFT = MARGIN_SIDE
CONTENT_RIGHT = TARGET_WIDTH - MARGIN_SIDE
CONTENT_TOP = TOOLBAR_HEIGHT
CONTENT_BOTTOM = TARGET_HEIGHT - MARGIN_BOTTOM
CONTENT_WIDTH = CONTENT_RIGHT - CONTENT_LEFT
CONTENT_HEIGHT = CONTENT_BOTTOM - CONTENT_TOP

# Font paths (using project-local fonts from Google Fonts)
FONT_PATH_REGULAR = "fonts/EBGaramond-Regular.ttf"
FONT_PATH_ITALIC = "fonts/EBGaramond-Italic.ttf"
FONT_NAME_REGULAR = "EBGaramond"
FONT_NAME_ITALIC = "EBGaramondIt"

# Font sizes (scaled from original 1620x2160 to 954x1696)
# Index pages use larger fonts for easier tapping
FONT_SIZES = {
    "title_cover": 48,
    "title_page": 52,       # Index titles - increased from 44
    "header": 32,
    "subheader": 28,
    "body": 32,             # Index body text - increased from 24
    "nav": 24,
    "footer": 22,
    "small": 24,            # Month names - increased from 18
    "tiny": 20,             # Week/day numbers - increased from 14
    "day_number": 26,       # Monthly timeline day numbers - larger for visibility
}

# Arrow sizes for vector drawing
ARROW_SIZE_LARGE = 14      # For main Index page links
ARROW_SIZE_SMALL = 10      # For week numbers

# Spacing constants
SUBHEADER_SPACING = 55     # Spacing after subheaders before body text

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (1, 1, 1)
COLOR_GRAY = (0.5, 0.5, 0.5)
COLOR_LIGHT_GRAY = (0.85, 0.85, 0.85)
COLOR_DOT_GRID = (0.82, 0.82, 0.82)
COLOR_LINE = (0.85, 0.85, 0.85)
COLOR_GOLD = (1, 0.84, 0)

# Dot grid parameters
DOT_SPACING = 50  # Spacing between dots
DOT_SIZE = 1      # Size of each square dot

# Page structure constants
PAGES_PER_DAY = 1           # 1 page per daily log
PAGES_PER_COLLECTION = 1    # 1 page per collection
NUM_GUIDE_PAGES = 6
NUM_FUTURE_LOG_PAGES = 4    # 4 quarters
NUM_MONTHS = 12
NUM_WEEKS = 53
NUM_DAYS = 365
NUM_COLLECTIONS_PER_INDEX = 18
NUM_COLLECTION_INDEXES = 2

# Days per month (non-leap year)
DAYS_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]
MONTH_ABBREVS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Calculate page offsets dynamically
PAGE_COVER = 1
PAGE_MAIN_INDEX = 2
PAGE_YEAR_INDEX = 3
PAGE_COLLECTION_INDEX_C = 4
PAGE_COLLECTION_INDEX_D = 5
PAGE_GUIDE_START = 6
PAGE_FUTURE_LOG_START = PAGE_GUIDE_START + NUM_GUIDE_PAGES  # 12
PAGE_MONTHLY_START = PAGE_FUTURE_LOG_START + NUM_FUTURE_LOG_PAGES  # 16
PAGE_WEEKLY_START = PAGE_MONTHLY_START + NUM_MONTHS * 2  # 40
PAGE_DAILY_START = PAGE_WEEKLY_START + NUM_WEEKS * 2  # 146
PAGE_COLLECTION_START = PAGE_DAILY_START + NUM_DAYS * PAGES_PER_DAY  # 876
TOTAL_PAGES = PAGE_COLLECTION_START + NUM_COLLECTIONS_PER_INDEX * NUM_COLLECTION_INDEXES * PAGES_PER_COLLECTION - 1  # 947


def get_daily_page_start(month_idx: int) -> int:
    """Calculate the starting page number for daily logs of a given month (0-indexed)."""
    days_before = sum(DAYS_PER_MONTH[:month_idx])
    return PAGE_DAILY_START + days_before * PAGES_PER_DAY


def get_monthly_timeline_page(month_idx: int) -> int:
    """Get the monthly timeline page number for a given month (0-indexed)."""
    return PAGE_MONTHLY_START + month_idx * 2


def get_collection_page(collection_idx: int) -> int:
    """Get the starting page number for a collection (0-indexed, 0-35)."""
    return PAGE_COLLECTION_START + collection_idx * PAGES_PER_COLLECTION


# Pre-calculate daily page starts for each month
DAILY_PAGE_STARTS = [get_daily_page_start(i) for i in range(NUM_MONTHS)]

# =============================================================================
# FOOTER TEXTS
# =============================================================================

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


# =============================================================================
# DATA CLASS
# =============================================================================

@dataclass
class DeferredLink:
    page_num: int
    rect: Tuple[float, float, float, float]
    dest_page: int


# =============================================================================
# GENERATOR CLASS
# =============================================================================

class BulletJournalGenerator:

    def __init__(self):
        self.doc = fitz.open()
        self.deferred_links: List[DeferredLink] = []
        self.fonts_registered = {}

    # -------------------------------------------------------------------------
    # Font Management
    # -------------------------------------------------------------------------

    def register_fonts(self, page: fitz.Page):
        """Register both Regular and Italic fonts on a page."""
        page_num = page.number
        if page_num not in self.fonts_registered:
            try:
                page.insert_font(fontname=FONT_NAME_REGULAR, fontfile=FONT_PATH_REGULAR)
                page.insert_font(fontname=FONT_NAME_ITALIC, fontfile=FONT_PATH_ITALIC)
                self.fonts_registered[page_num] = True
            except Exception as e:
                print(f"Font registration warning on page {page_num}: {e}")
                self.fonts_registered[page_num] = False

    # -------------------------------------------------------------------------
    # Basic Drawing Functions
    # -------------------------------------------------------------------------

    def create_page(self) -> fitz.Page:
        return self.doc.new_page(width=TARGET_WIDTH, height=TARGET_HEIGHT)

    def add_text(self, page: fitz.Page, text: str, x: float, y: float,
                 font_size: float = 24, color: Tuple = COLOR_BLACK, italic: bool = False):
        """Add text to page."""
        self.register_fonts(page)
        font = FONT_NAME_ITALIC if italic else FONT_NAME_REGULAR
        fontfile = FONT_PATH_ITALIC if italic else FONT_PATH_REGULAR
        page.insert_text(fitz.Point(x, y + font_size), text,
                         fontsize=font_size, fontname=font, fontfile=fontfile, color=color)

    def get_text_width(self, text: str, font_size: float) -> float:
        """Estimate text width."""
        return fitz.get_text_length(text, fontname="helv", fontsize=font_size) * 0.95

    def draw_rich_text(self, page: fitz.Page, text: str, x: float, y: float,
                       font_size: float = 22, max_width: float = None, line_height: float = 1.4):
        """Draw text with |italic| markers."""
        if max_width is None:
            max_width = CONTENT_WIDTH - 60

        # Split by italic markers
        parts = text.split('|')
        words_with_style = []

        for i, part in enumerate(parts):
            is_italic = (i % 2 == 1)
            for word in part.split():
                words_with_style.append((word, is_italic))

        # Word wrap and render
        current_x = x
        current_y = y
        space_width = self.get_text_width(" ", font_size)

        for word, is_italic in words_with_style:
            word_width = self.get_text_width(word, font_size)

            if current_x + word_width > x + max_width:
                current_x = x
                current_y += font_size * line_height

            self.add_text(page, word, current_x, current_y, font_size, COLOR_BLACK, italic=is_italic)
            current_x += word_width + space_width

        return current_y - y + font_size * line_height

    # -------------------------------------------------------------------------
    # Dot Grid Background (Vector-based for crisp rendering)
    # -------------------------------------------------------------------------

    def create_dot_grid_xobject(self):
        """Create dot grid as a reusable XObject for efficient rendering."""
        if hasattr(self, 'dot_grid_xref'):
            return  # Already created

        # Create a temporary page to build the dot grid
        temp_doc = fitz.open()
        temp_page = temp_doc.new_page(width=CONTENT_WIDTH, height=CONTENT_HEIGHT)

        # Use Shape for efficient batch drawing
        shape = temp_page.new_shape()

        dot_size = DOT_SIZE
        y = 0
        while y < CONTENT_HEIGHT:
            x = 0
            while x < CONTENT_WIDTH:
                rect = fitz.Rect(x, y, x + dot_size, y + dot_size)
                shape.draw_rect(rect)
                x += DOT_SPACING
            y += DOT_SPACING

        # Commit all shapes at once with black fill
        shape.finish(color=COLOR_BLACK, fill=COLOR_BLACK)
        shape.commit()

        # Store the xref for reuse
        self.dot_grid_xref = temp_page.get_contents()[0]
        self.dot_grid_doc = temp_doc
        print(f"  Created vector dot grid template")

    def draw_dot_grid(self, page: fitz.Page, start_y: float = None, end_y: float = None):
        """Draw vector dot grid using efficient Shape batching."""
        if start_y is None:
            start_y = CONTENT_TOP + 60
        if end_y is None:
            end_y = CONTENT_BOTTOM - 130

        # Use Shape for efficient batch drawing
        shape = page.new_shape()

        dot_size = DOT_SIZE
        y = start_y
        while y < end_y:
            x = CONTENT_LEFT
            while x < CONTENT_RIGHT:
                rect = fitz.Rect(x, y, x + dot_size, y + dot_size)
                shape.draw_rect(rect)
                x += DOT_SPACING
            y += DOT_SPACING

        # Commit all shapes at once with black fill
        shape.finish(color=COLOR_BLACK, fill=COLOR_BLACK)
        shape.commit()

    # -------------------------------------------------------------------------
    # Lightning Icon
    # -------------------------------------------------------------------------

    def draw_lightning(self, page: fitz.Page, x: float, y: float, scale: float = 1.8):
        """Draw lightning bolt icon."""
        # Lightning bolt polygon points (relative)
        points = [
            (8, 0), (15, 0), (9, 10), (16, 10),
            (0, 26), (5, 13), (0, 13), (8, 0)
        ]
        # Scale and translate
        scaled_points = [fitz.Point(x + p[0] * scale, y + p[1] * scale) for p in points]
        page.draw_polyline(scaled_points, color=COLOR_BLACK, fill=COLOR_BLACK, closePath=True)

    # -------------------------------------------------------------------------
    # Vector Arrow Drawing (matching original PDF style)
    # -------------------------------------------------------------------------

    def draw_arrow_right(self, page: fitz.Page, x: float, y: float,
                         size: float = ARROW_SIZE_LARGE, color: tuple = COLOR_BLACK):
        """Draw right-pointing arrow matching original PDF style.

        Original PDF uses classic arrow shape: horizontal shaft + chevron head.
        Arrow dimensions approximately 24x20 in original (scaled proportionally).

        Args:
            page: PDF page object
            x: Left edge x coordinate
            y: Center y coordinate
            size: Arrow size (controls overall scale)
            color: Stroke and fill color
        """
        # Scale factors based on original 24x20 arrow
        shaft_length = size * 1.2
        head_size = size * 0.6
        stroke_width = size * 0.12

        # Arrow tip position
        tip_x = x + shaft_length
        tip_y = y

        # Draw shaft (horizontal line)
        page.draw_line(
            fitz.Point(x, y),
            fitz.Point(tip_x - head_size * 0.3, y),
            color=color, width=stroke_width
        )

        # Draw arrow head (two diagonal lines from tip)
        # Upper diagonal
        page.draw_line(
            fitz.Point(tip_x, tip_y),
            fitz.Point(tip_x - head_size, tip_y - head_size * 0.7),
            color=color, width=stroke_width
        )
        # Lower diagonal
        page.draw_line(
            fitz.Point(tip_x, tip_y),
            fitz.Point(tip_x - head_size, tip_y + head_size * 0.7),
            color=color, width=stroke_width
        )

    def draw_arrow_left(self, page: fitz.Page, x: float, y: float,
                        size: float = ARROW_SIZE_LARGE, color: tuple = COLOR_BLACK):
        """Draw left-pointing arrow matching original PDF style.

        Args:
            page: PDF page object
            x: Right edge x coordinate (arrow points left from here)
            y: Center y coordinate
            size: Arrow size
            color: Stroke and fill color
        """
        shaft_length = size * 1.2
        head_size = size * 0.6
        stroke_width = size * 0.12

        # Arrow tip position
        tip_x = x
        tip_y = y

        # Draw shaft
        page.draw_line(
            fitz.Point(x + shaft_length, y),
            fitz.Point(tip_x + head_size * 0.3, y),
            color=color, width=stroke_width
        )

        # Draw arrow head
        page.draw_line(
            fitz.Point(tip_x, tip_y),
            fitz.Point(tip_x + head_size, tip_y - head_size * 0.7),
            color=color, width=stroke_width
        )
        page.draw_line(
            fitz.Point(tip_x, tip_y),
            fitz.Point(tip_x + head_size, tip_y + head_size * 0.7),
            color=color, width=stroke_width
        )

    # -------------------------------------------------------------------------
    # Footer Section
    # -------------------------------------------------------------------------

    def draw_footer_section(self, page: fitz.Page, footer_type: str):
        """Draw footer with lightning icon and explanation text."""
        if footer_type not in FOOTER_TEXTS:
            return

        y = CONTENT_BOTTOM - 125

        # Separator line
        page.draw_line(fitz.Point(CONTENT_LEFT, y - 15),
                       fitz.Point(CONTENT_RIGHT, y - 15),
                       color=COLOR_BLACK, width=0.5)

        # Lightning icon (same as Intention/Goals pages)
        self.draw_lightning(page, CONTENT_LEFT, y + 5, scale=1.8)

        # Footer text
        text = FOOTER_TEXTS[footer_type]
        self.draw_rich_text(page, text, CONTENT_LEFT + 45, y,
                            font_size=FONT_SIZES["footer"], max_width=CONTENT_WIDTH - 75)

    # -------------------------------------------------------------------------
    # Navigation Links
    # -------------------------------------------------------------------------

    def add_nav_link(self, page_num: int, text: str, dest_page: int,
                     x: float, y: float, font_size: float = None, with_arrow: bool = True):
        """Add navigation link with optional left arrow (vector drawn)."""
        if font_size is None:
            font_size = FONT_SIZES["nav"]

        page = self.doc[page_num]

        # Calculate text starting position
        text_x = x
        if with_arrow:
            # Draw vector left arrow before text
            # Note: add_text renders at y + font_size (baseline), so text visual center ≈ y + font_size * 0.65
            arrow_size = font_size * 0.5
            arrow_y = y + font_size * 0.65
            self.draw_arrow_left(page, x, arrow_y, arrow_size)
            text_x = x + arrow_size * 1.5 + 8  # Space after arrow

        self.add_text(page, text, text_x, y, font_size)

        # Link covers arrow + text area
        text_width = self.get_text_width(text, font_size)
        link_rect = (x - 5, y - 2, text_x + text_width + 10, y + font_size + 6)
        self.deferred_links.append(DeferredLink(page_num, link_rect, dest_page))

    def add_bottom_nav(self, page_num: int, links: List[Tuple[str, int]]):
        """Add bottom navigation links."""
        y = TARGET_HEIGHT - 50
        x = CONTENT_RIGHT - 10

        for text, dest_page in reversed(links):
            text_width = self.get_text_width(text, FONT_SIZES["nav"])
            x = x - text_width - 30
            self.add_nav_link(page_num, text, dest_page, x, y, with_arrow=False)

    def apply_deferred_links(self):
        """Apply all deferred links."""
        for link in self.deferred_links:
            if link.dest_page <= len(self.doc):
                page = self.doc[link.page_num]
                page.insert_link({
                    "kind": fitz.LINK_GOTO,
                    "page": link.dest_page - 1,
                    "from": fitz.Rect(link.rect)
                })

    # -------------------------------------------------------------------------
    # Page Generators
    # -------------------------------------------------------------------------

    def generate_cover(self, page_num: int):
        """Generate cover page with black background and white text (To-do 2025 style)."""
        page = self.doc[page_num]

        # Black background
        page.draw_rect(page.rect, color=COLOR_BLACK, fill=COLOR_BLACK)

        # Layout: Large lightning on left as design element, text to the right
        left_margin = 50
        title_y = TARGET_HEIGHT * 0.15

        # Draw large lightning bolt as vertical design element
        lightning_scale = 8.0
        lightning_x = left_margin
        lightning_y = title_y + 20
        self.draw_lightning_white(page, lightning_x, lightning_y, scale=lightning_scale)

        # Text area to the right of lightning
        text_x = left_margin + 130

        # "Bullet"
        bullet_size = 90
        self.add_text(page, "Bullet", text_x, title_y, bullet_size, COLOR_WHITE)

        # "Journal"
        journal_y = title_y + 95
        self.add_text(page, "Journal", text_x, journal_y, bullet_size, COLOR_WHITE)

        # "2026" - extra large
        year_y = journal_y + 130
        year_size = 140
        self.add_text(page, "2026", text_x, year_y, year_size, COLOR_WHITE)

    def draw_lightning_white(self, page: fitz.Page, x: float, y: float, scale: float = 1.8):
        """Draw white lightning bolt icon."""
        points = [
            (8, 0), (15, 0), (9, 10), (16, 10),
            (0, 26), (5, 13), (0, 13), (8, 0)
        ]
        scaled_points = [(x + px * scale, y + py * scale) for px, py in points]
        shape = page.new_shape()
        shape.draw_polyline([fitz.Point(px, py) for px, py in scaled_points])
        shape.finish(fill=COLOR_WHITE, closePath=True)
        shape.commit()

    def generate_main_index(self, page_num: int):
        """Generate main index (Index A) with complete navigation.

        Optimized for better vertical space utilization and easier tapping.
        """
        page = self.doc[page_num]

        # Title
        self.add_text(page, "Index A", CONTENT_LEFT, CONTENT_TOP + 10, FONT_SIZES["title_page"])

        # Guide section - increased row height for larger fonts
        y = CONTENT_TOP + 80
        row_height = 52  # Increased from 38

        guide_links = [
            ("Bullet Journal Guide", PAGE_GUIDE_START),
            ("Set up logs", PAGE_GUIDE_START + 1),
            ("The Practice Overview", PAGE_GUIDE_START + 2),
            ("How to reflect", PAGE_GUIDE_START + 3),
            ("Intention", PAGE_GUIDE_START + 4),
            ("Goals", PAGE_GUIDE_START + 5),
            ("Future log", PAGE_FUTURE_LOG_START),
        ]

        for text, dest in guide_links:
            self.add_nav_link(page_num, text, dest, CONTENT_LEFT, y, FONT_SIZES["body"], with_arrow=False)
            # Vector arrow on right side
            arrow_y = y + FONT_SIZES["body"] * 0.65
            arrow_x = CONTENT_RIGHT - 25
            self.draw_arrow_right(page, arrow_x, arrow_y, ARROW_SIZE_LARGE)
            # Add clickable link for the arrow area (aligned with text position)
            arrow_link_rect = (arrow_x - 10, y - 5, CONTENT_RIGHT, y + FONT_SIZES["body"] + 5)
            self.deferred_links.append(DeferredLink(page_num, arrow_link_rect, dest))
            page.draw_line(fitz.Point(CONTENT_LEFT, y + 40), fitz.Point(CONTENT_RIGHT, y + 40),
                           color=COLOR_LINE, width=0.5)
            y += row_height

        y += 35  # More space before section

        # Section headers with more spacing
        month_col_width = 180  # Wider month column
        week_col_start = CONTENT_LEFT + month_col_width + 50  # More gap between columns

        self.add_text(page, "Monthly logs", CONTENT_LEFT, y, FONT_SIZES["body"])
        self.add_text(page, "Weekly logs", week_col_start, y, FONT_SIZES["body"])
        y += 55  # More space after headers

        # Calculate available space for 12 month rows
        available_height = CONTENT_BOTTOM - y - 20
        month_row_height = available_height // 12

        # Week ranges for each month (approximate)
        week_starts = [1, 6, 10, 14, 19, 23, 27, 32, 36, 40, 45, 49]

        # Week number spacing - spread across available width
        week_area_width = CONTENT_RIGHT - week_col_start
        week_num_width = 95  # Wider spacing for sparser layout

        for month_idx in range(NUM_MONTHS):
            month = MONTH_NAMES[month_idx]
            month_page = get_monthly_timeline_page(month_idx)

            # Calculate vertical center offset for text within row
            text_y = y + (month_row_height - FONT_SIZES["small"]) / 2 - 10

            # Month name on left (vertically centered)
            self.add_text(page, month, CONTENT_LEFT, text_y, FONT_SIZES["small"])
            # Arrow after month name
            month_arrow_x = CONTENT_LEFT + 120
            month_arrow_y = text_y + FONT_SIZES["small"] * 0.65
            self.draw_arrow_right(page, month_arrow_x, month_arrow_y, ARROW_SIZE_SMALL)
            # Clickable area for month
            month_link_rect = (CONTENT_LEFT - 5, text_y - 5, month_col_width, text_y + FONT_SIZES["small"] + 5)
            self.deferred_links.append(DeferredLink(page_num, month_link_rect, month_page))

            # Vertical separator line between month and weeks
            sep_x = week_col_start - 25
            page.draw_line(fitz.Point(sep_x, y), fitz.Point(sep_x, y + month_row_height - 12),
                           color=COLOR_LINE, width=0.5)

            # Week numbers - sparser layout (vertically centered)
            week_start = week_starts[month_idx]
            week_end = week_starts[month_idx + 1] if month_idx < 11 else 54

            for i, w in enumerate(range(week_start, week_end)):
                week_page = PAGE_WEEKLY_START + (w - 1) * 2
                week_x = week_col_start + i * week_num_width

                # Week number (vertically centered)
                self.add_text(page, str(w), week_x, text_y, FONT_SIZES["small"])
                # Arrow after week number
                week_arrow_x = week_x + 30
                week_arrow_y = text_y + FONT_SIZES["small"] * 0.65
                self.draw_arrow_right(page, week_arrow_x, week_arrow_y, ARROW_SIZE_SMALL)
                # Clickable area
                week_link_rect = (week_x - 5, text_y - 5, week_x + week_num_width - 5, text_y + FONT_SIZES["small"] + 5)
                self.deferred_links.append(DeferredLink(page_num, week_link_rect, week_page))

            # Horizontal separator line at bottom of row
            line_y = y + month_row_height - 12
            page.draw_line(fitz.Point(CONTENT_LEFT, line_y), fitz.Point(CONTENT_RIGHT, line_y),
                           color=COLOR_LINE, width=0.5)
            y += month_row_height

    def generate_year_index(self, page_num: int):
        """Generate year index (Index B) with all 365 days.

        Days split into two rows per month: 1-15 on first row, 16+ on second row.
        """
        page = self.doc[page_num]

        # Title
        self.add_text(page, "Index B", CONTENT_LEFT, CONTENT_TOP + 10, FONT_SIZES["title_page"])

        # Subtitle with whitespace
        self.add_text(page, "Daily logs", CONTENT_LEFT, CONTENT_TOP + 75, FONT_SIZES["body"])

        # Calculate layout - 12 months, each with 2 rows of days
        y = CONTENT_TOP + 130
        available_height = CONTENT_BOTTOM - y - 60  # Leave space for bottom nav
        month_block_height = available_height // 12  # Height per month block

        # Day layout constants
        days_per_row = 16  # First row: 1-16, second row: 17-31 (max 15 days)
        day_col_start = CONTENT_LEFT + 115  # Start of day numbers (room for "September")
        day_col_width = CONTENT_RIGHT - day_col_start - 20  # Leave right margin
        day_spacing = day_col_width / days_per_row  # Fixed spacing for 16 columns

        for month_idx in range(NUM_MONTHS):
            month_name = MONTH_NAMES[month_idx]
            days = DAYS_PER_MONTH[month_idx]
            start_page = DAILY_PAGE_STARTS[month_idx]

            # Row positions
            row1_y = y + 8
            row2_y = y + month_block_height / 2 + 2

            # Month name on left, aligned with first row
            self.add_text(page, month_name, CONTENT_LEFT, row1_y, FONT_SIZES["small"])

            # Vertical padding for click areas (must not overlap between rows)
            row_gap = row2_y - row1_y - FONT_SIZES["tiny"]
            v_padding = min(8, row_gap / 2 - 1)  # Ensure no vertical overlap

            # First row: days 1-16
            for day in range(1, min(days + 1, 17)):
                link_left = day_col_start + (day - 1) * day_spacing
                link_right = link_left + day_spacing  # No overlap with next day

                # Center text within click area
                text_width = self.get_text_width(str(day), FONT_SIZES["tiny"])
                text_x = link_left + (day_spacing - text_width) / 2
                self.add_text(page, str(day), text_x, row1_y, FONT_SIZES["tiny"])

                dest_page = start_page + (day - 1) * PAGES_PER_DAY
                link_rect = (link_left, row1_y - v_padding, link_right, row1_y + FONT_SIZES["tiny"] + v_padding)
                self.deferred_links.append(DeferredLink(page_num, link_rect, dest_page))

            # Second row: days 17-31 (max 15 days)
            for day in range(17, days + 1):
                link_left = day_col_start + (day - 17) * day_spacing
                link_right = link_left + day_spacing  # No overlap with next day

                # Center text within click area
                text_width = self.get_text_width(str(day), FONT_SIZES["tiny"])
                text_x = link_left + (day_spacing - text_width) / 2
                self.add_text(page, str(day), text_x, row2_y, FONT_SIZES["tiny"])

                dest_page = start_page + (day - 1) * PAGES_PER_DAY
                link_rect = (link_left, row2_y - v_padding, link_right, row2_y + FONT_SIZES["tiny"] + v_padding)
                self.deferred_links.append(DeferredLink(page_num, link_rect, dest_page))

            # Separator line at bottom of month block
            line_y = y + month_block_height - 8
            page.draw_line(fitz.Point(CONTENT_LEFT, line_y), fitz.Point(CONTENT_RIGHT, line_y),
                           color=COLOR_LINE, width=0.5)

            y += month_block_height

        self.add_bottom_nav(page_num, [("Index", PAGE_MAIN_INDEX)])

    def generate_collection_index(self, page_num: int, letter: str):
        """Generate collection index page.

        Optimized with larger line spacing for easier writing and tapping.
        """
        page = self.doc[page_num]

        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)
        self.add_text(page, f"Index {letter}", CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["title_page"])

        # Grid lines with increased spacing - start below title
        y = CONTENT_TOP + 130
        line_spacing = 60
        num_lines = NUM_COLLECTIONS_PER_INDEX

        # Index C: collections 0-17, Index D: collections 18-35
        collection_offset = 0 if letter == "C" else NUM_COLLECTIONS_PER_INDEX

        for i in range(num_lines):
            line_y = y + i * line_spacing
            page.draw_line(fitz.Point(CONTENT_LEFT, line_y), fitz.Point(CONTENT_RIGHT, line_y),
                           color=COLOR_LINE, width=0.5)

            # Vector arrow on right side (centered in writing area BELOW the line)
            arrow_y = line_y + line_spacing / 2
            arrow_x = CONTENT_RIGHT - 22
            self.draw_arrow_right(page, arrow_x, arrow_y, ARROW_SIZE_LARGE)

            # Link to collection page using helper function
            collection_idx = collection_offset + i
            collection_page = get_collection_page(collection_idx)
            link_rect = (arrow_x - 15, arrow_y - 15, CONTENT_RIGHT, arrow_y + 15)
            self.deferred_links.append(DeferredLink(page_num, link_rect, collection_page))

        # Bottom line to close the last row
        bottom_line_y = y + num_lines * line_spacing
        page.draw_line(fitz.Point(CONTENT_LEFT, bottom_line_y), fitz.Point(CONTENT_RIGHT, bottom_line_y),
                       color=COLOR_LINE, width=0.5)

        # Footer
        self.draw_footer_section(page, "collection_index")

    def generate_guide_page(self, page_num: int, title: str, sections: List[Tuple[str, str]]):
        """Generate a guide page with multiple sections."""
        page = self.doc[page_num]

        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)
        self.add_text(page, title, CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["header"])

        y = CONTENT_TOP + 100

        for section_title, section_content in sections:
            if section_title:
                self.add_text(page, section_title, CONTENT_LEFT, y, FONT_SIZES["subheader"])
                y += 35

            height = self.draw_rich_text(page, section_content, CONTENT_LEFT, y,
                                         FONT_SIZES["body"], max_width=CONTENT_WIDTH - 20)
            y += height + 25

    # -------------------------------------------------------------------------
    # Specialized Guide Pages (Pages 6-11)
    # -------------------------------------------------------------------------

    def generate_guide_system(self, page_num: int):
        """Page 6: The Bullet Journal Guide: System - Description, Rapid logging, Learn more."""
        page = self.doc[page_num]
        font_body = 26  # 33 * 0.8
        font_small = 22  # 27 * 0.8
        line_height = 1.5

        # Navigation
        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)

        # Title
        self.add_text(page, "The Bullet Journal Guide: System", CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["header"])

        y = CONTENT_TOP + 100

        # Description section
        self.add_text(page, "Description", CONTENT_LEFT, y, FONT_SIZES["subheader"])
        y += SUBHEADER_SPACING
        desc_text = (
            "The Bullet Journal Method is a mindfulness practice that's designed to work like a "
            "productivity system. Be it for your career, education, family, or health, BuJo offers a lot of "
            "resources for how to help you |write a better life.| The best way to learn how to Bullet Journal "
            "is to experience it. This guide is designed to help you get up and running with the basics. "
            "Below is a list of resources to help you level up your practice."
        )
        height = self.draw_rich_text(page, desc_text, CONTENT_LEFT, y, font_body, CONTENT_WIDTH - 40, line_height)
        y += height + 20

        # Rapid logging section
        self.add_text(page, "Rapid logging", CONTENT_LEFT, y, FONT_SIZES["subheader"])
        y += SUBHEADER_SPACING
        rapid_text = (
            "Rapid Logging allows you to quickly capture and categorize your thoughts and feelings as "
            "bulleted lists. Each bullet represents one of four categories of information:"
        )
        height = self.draw_rich_text(page, rapid_text, CONTENT_LEFT, y, font_body, CONTENT_WIDTH - 40, line_height)
        y += height + 15

        # Bullet types (all drawn as SVG/vector graphics)
        symbol_x = CONTENT_LEFT + 12
        desc_x = CONTENT_LEFT + 45
        symbol_size = 12

        # — Notes (horizontal dash)
        dash_y = y + font_body * 0.65
        page.draw_line(fitz.Point(symbol_x - 2, dash_y),
                       fitz.Point(symbol_x + symbol_size, dash_y),
                       color=COLOR_BLACK, width=2)
        self.add_text(page, "Notes (things to remember)", desc_x, y, font_body)
        y += font_body * line_height

        # • Actions (filled circle/dot)
        dot_y = y + font_body * 0.65
        dot_r = 4
        page.draw_circle(fitz.Point(symbol_x + dot_r, dot_y), dot_r,
                         color=COLOR_BLACK, fill=COLOR_BLACK)
        self.add_text(page, "Actions (things to do)", desc_x, y, font_body)
        y += font_body * line_height

        # = Moods (two horizontal lines)
        line_y_center = y + font_body * 0.65
        line_len = 14
        for offset in [-4, 4]:
            page.draw_line(fitz.Point(symbol_x - 2, line_y_center + offset),
                           fitz.Point(symbol_x + line_len - 2, line_y_center + offset),
                           color=COLOR_BLACK, width=1.8)
        self.add_text(page, "Moods (things felt, emotionally or physically)", desc_x, y, font_body)
        y += font_body * line_height

        # ○ Events (hollow circle)
        circle_y = y + font_body * 0.65
        circle_r = 5
        page.draw_circle(fitz.Point(symbol_x + circle_r, circle_y), circle_r,
                         color=COLOR_BLACK, width=1.8)
        self.add_text(page, "Events (things we experience)", desc_x, y, font_body)
        y += font_body * line_height

        y += 15

        # Action states explanation (use vector dot in text)
        action_note = (
            "Note that we use a dot instead of checkboxes for actions. That's because they have four states "
            "that allows us to monitor the status of an action:"
        )
        height = self.draw_rich_text(page, action_note, CONTENT_LEFT, y, font_body, CONTENT_WIDTH - 40, line_height)
        y += height + 15

        # Action states (all drawn as SVG/vector graphics)
        state_symbol_x = CONTENT_LEFT + 12
        state_desc_x = CONTENT_LEFT + 45

        # • Incomplete (filled dot)
        dot_y = y + font_body * 0.65
        page.draw_circle(fitz.Point(state_symbol_x + dot_r, dot_y), dot_r,
                         color=COLOR_BLACK, fill=COLOR_BLACK)
        self.add_text(page, "Incomplete", state_desc_x, y, font_body)
        y += font_body * line_height

        # × Complete (X mark)
        x_y = y + font_body * 0.65
        x_size = 8
        page.draw_line(fitz.Point(state_symbol_x, x_y - x_size/2),
                       fitz.Point(state_symbol_x + x_size, x_y + x_size/2),
                       color=COLOR_BLACK, width=2)
        page.draw_line(fitz.Point(state_symbol_x, x_y + x_size/2),
                       fitz.Point(state_symbol_x + x_size, x_y - x_size/2),
                       color=COLOR_BLACK, width=2)
        self.add_text(page, "Complete", state_desc_x, y, font_body)
        y += font_body * line_height

        # > Migrated (arrow/chevron)
        arrow_y = y + font_body * 0.65
        arrow_size = 8
        page.draw_line(fitz.Point(state_symbol_x, arrow_y - arrow_size/2),
                       fitz.Point(state_symbol_x + arrow_size, arrow_y),
                       color=COLOR_BLACK, width=2)
        page.draw_line(fitz.Point(state_symbol_x, arrow_y + arrow_size/2),
                       fitz.Point(state_symbol_x + arrow_size, arrow_y),
                       color=COLOR_BLACK, width=2)
        self.add_text(page, "Migrated (moved)", state_desc_x, y, font_body)
        y += font_body * line_height

        # • Irrelevant (filled dot with strikethrough from dot through text)
        dot_y = y + font_body * 0.65
        page.draw_circle(fitz.Point(state_symbol_x + dot_r, dot_y), dot_r,
                         color=COLOR_BLACK, fill=COLOR_BLACK)
        self.add_text(page, "Irrelevant", state_desc_x, y, font_body)
        # Strikethrough line starting from the dot
        text_width = self.get_text_width("Irrelevant", font_body)
        strike_y = y + font_body * 0.65
        page.draw_line(fitz.Point(state_symbol_x, strike_y),
                       fitz.Point(state_desc_x + text_width, strike_y),
                       color=COLOR_BLACK, width=1)
        y += font_body * line_height

    def generate_guide_set_up_logs(self, page_num: int):
        """Page 7: Set up your logs - Future/Monthly/Weekly/Daily log descriptions with Get started links."""
        page = self.doc[page_num]
        font_body = 22  # 27 * 0.8
        font_small = 19  # 24 * 0.8
        line_height = 1.35

        # Navigation
        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)

        # Title
        self.add_text(page, "Set up your logs", CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["header"])

        y = CONTENT_TOP + 95

        # Get started link position
        get_started_x = CONTENT_RIGHT - 110

        # Future log section
        self.add_text(page, "Future log", CONTENT_LEFT, y, FONT_SIZES["subheader"])
        self.add_text(page, "Get started", get_started_x, y, font_small)
        self.draw_arrow_right(page, CONTENT_RIGHT - 15, y + font_small / 2, ARROW_SIZE_SMALL)
        link_rect = (get_started_x - 5, y - 5, CONTENT_RIGHT, y + font_small + 5)
        self.deferred_links.append(DeferredLink(page_num, link_rect, PAGE_FUTURE_LOG_START))
        y += SUBHEADER_SPACING

        future_text = (
            "The Future Log lets you see your future. It is an outline of the life you're choosing to write. "
            "The Future log is a |Collection| where you can store |actions| and |events| that fall outside the "
            "current month. More than just being a type of calendar, the Future log also provides an "
            "overview of your commitments over time."
        )
        height = self.draw_rich_text(page, future_text, CONTENT_LEFT, y, font_body, CONTENT_WIDTH - 30, line_height)
        y += height + 10

        # Separator
        page.draw_line(fitz.Point(CONTENT_LEFT, y), fitz.Point(CONTENT_RIGHT, y), color=COLOR_BLACK, width=0.5)
        y += 15

        # Monthly log section
        self.add_text(page, "Monthly log", CONTENT_LEFT, y, FONT_SIZES["subheader"])
        self.add_text(page, "Get started", get_started_x, y, font_small)
        self.draw_arrow_right(page, CONTENT_RIGHT - 15, y + font_small / 2, ARROW_SIZE_SMALL)
        link_rect = (get_started_x - 5, y - 5, CONTENT_RIGHT, y + font_small + 5)
        self.deferred_links.append(DeferredLink(page_num, link_rect, PAGE_MONTHLY_START))
        y += SUBHEADER_SPACING

        monthly_intro = "Two pages to reset, reprioritize, and recommit to what you allow into your life every month."
        height = self.draw_rich_text(page, monthly_intro, CONTENT_LEFT, y, font_body, CONTENT_WIDTH - 30, line_height)
        y += height + 10

        # Two columns for Timeline and Action Plan
        col_width = (CONTENT_WIDTH - 40) // 2
        col1_x = CONTENT_LEFT
        col2_x = CONTENT_LEFT + col_width + 25

        # Timeline header
        self.add_text(page, "Timeline", col1_x, y, font_body, italic=True)
        self.add_text(page, "Action Plan", col2_x, y, font_body, italic=True)
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

        # Draw both columns and track heights
        h1 = self.draw_rich_text(page, timeline_text, col1_x, y, font_body, col_width - 10, line_height)
        h2 = self.draw_rich_text(page, action_plan_text, col2_x, y, font_body, col_width - 10, line_height)
        y += max(h1, h2) + 10

        # Separator
        page.draw_line(fitz.Point(CONTENT_LEFT, y), fitz.Point(CONTENT_RIGHT, y), color=COLOR_BLACK, width=0.5)
        y += 15

        # Weekly log section
        self.add_text(page, "Weekly log", CONTENT_LEFT, y, FONT_SIZES["subheader"])
        self.add_text(page, "Get started", get_started_x, y, font_small)
        self.draw_arrow_right(page, CONTENT_RIGHT - 15, y + font_small / 2, ARROW_SIZE_SMALL)
        link_rect = (get_started_x - 5, y - 5, CONTENT_RIGHT, y + font_small + 5)
        self.deferred_links.append(DeferredLink(page_num, link_rect, PAGE_WEEKLY_START))
        y += SUBHEADER_SPACING

        # Reflection header
        self.add_text(page, "Reflection", col1_x, y, font_body, italic=True)
        self.add_text(page, "Action plan", col2_x, y, font_body, italic=True)
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

        # Draw both columns and track heights
        h1 = self.draw_rich_text(page, reflection_text, col1_x, y, font_body, col_width - 10, line_height)
        h2 = self.draw_rich_text(page, weekly_action_text, col2_x, y, font_body, col_width - 10, line_height)
        y += max(h1, h2) + 10

        # Separator
        page.draw_line(fitz.Point(CONTENT_LEFT, y), fitz.Point(CONTENT_RIGHT, y), color=COLOR_BLACK, width=0.5)
        y += 15

        # Daily log section
        self.add_text(page, "Daily log", CONTENT_LEFT, y, FONT_SIZES["subheader"])
        self.add_text(page, "Get started", get_started_x, y, font_small)
        self.draw_arrow_right(page, CONTENT_RIGHT - 15, y + font_small / 2, ARROW_SIZE_SMALL)
        link_rect = (get_started_x - 5, y - 5, CONTENT_RIGHT, y + font_small + 5)
        self.deferred_links.append(DeferredLink(page_num, link_rect, PAGE_DAILY_START))
        y += SUBHEADER_SPACING

        daily_text = (
            "The Daily Log is designed to declutter your mind and keep you focused throughout the day. "
            "|Rapid Log| your thoughts as they bubble up."
        )
        self.draw_rich_text(page, daily_text, CONTENT_LEFT, y, font_body, CONTENT_WIDTH - 30, line_height)

    def generate_guide_practice(self, page_num: int):
        """Page 8: The Practice - T.A.M.E. reflection process explanation."""
        page = self.doc[page_num]
        font_body = 24  # 30 * 0.8
        line_height = 1.5

        # Navigation
        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)

        # Title
        self.add_text(page, "The Practice", CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["header"])

        y = CONTENT_TOP + 100

        # Introduction
        intro_text = (
            "Writing things down is important, but it's only half of the equation. We can quickly "
            "accumulate so much information that it's overwhelming. Reflection helps you slow down, "
            "make sense of your experiences, and align with what truly matters. In the Bullet Journal "
            "Method, reflection isn't about dwelling on the past--it's about learning from it to move "
            "forward with clarity over and over again. It's a practice."
        )
        height = self.draw_rich_text(page, intro_text, CONTENT_LEFT, y, font_body, CONTENT_WIDTH - 40, line_height)
        y += height + 20

        # N.A.M.E. and T.A.M.E.
        name_text = (
            "Rapid logging, the foundation of Bullet Journaling, lets you Record your experience by "
            "|N.A.M.E.,| organizing it into |N|otes, |A|ctions, |M|oods, and |E|vents. Reflection builds on this "
            "by helping you |T.A.M.E.| your Record, turning raw information into insights, and then "
            "putting those insights into action."
        )
        height = self.draw_rich_text(page, name_text, CONTENT_LEFT, y, font_body, CONTENT_WIDTH - 40, line_height)
        y += height + 25

        # T.A.M.E. explanation
        tame_intro = (
            "|T.A.M.E.| is a step-by-step process for reflection, be it daily, weekly, or monthly. It helps you "
            "make sense of your experiences and turn insights into action. Here's how it works:"
        )
        height = self.draw_rich_text(page, tame_intro, CONTENT_LEFT, y, font_body, CONTENT_WIDTH - 40, line_height)
        y += height + 25

        # T.A.M.E. steps
        tame_steps = [
            ("1. T - Tidy", "your record. Cross off completed tasks, migrate unfinished ones, and declutter what no longer matters. This clears mental and physical space."),
            ("2. A - Acknowledge", "your actions: Look back on what happened. Identify a few things that aligned with your intention and a few that didn't. For example, did a meeting help you focus on your goal, or did an unexpected distraction pull you off track?"),
            ("3. M - Migrate", "what matters. Let go of what doesn't. Yes, this means rewriting open actions into the day, weekly, or the month where they will get done. It's about getting clear on what we're committing to in each stretch of time."),
            ("4. E - Enact", "your insights into your Action plans. Set clear priorities for the next day, week, or month to stay on course."),
        ]

        for step_title, step_desc in tame_steps:
            # Bold title
            self.add_text(page, step_title, CONTENT_LEFT + 20, y, font_body)
            title_width = self.get_text_width(step_title, font_body)
            # Description continues after title
            height = self.draw_rich_text(page, step_desc, CONTENT_LEFT + 25 + title_width, y,
                                         font_body, CONTENT_WIDTH - 65 - title_width, line_height)
            y += max(height, font_body * line_height) + 15

    def generate_guide_how_to_reflect(self, page_num: int):
        """Page 9: How to reflect - Daily/Weekly/Monthly reflection guides."""
        page = self.doc[page_num]
        font_body = 24  # 30 * 0.8
        line_height = 1.5

        # Navigation
        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)

        # Title
        self.add_text(page, "How to reflect", CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["header"])

        y = CONTENT_TOP + 100

        # Daily reflection
        self.add_text(page, "Daily reflection", CONTENT_LEFT, y, FONT_SIZES["subheader"])
        y += SUBHEADER_SPACING
        daily_text = (
            "Tidy your daily entries. Acknowledge up to three things that moved you toward, and up to "
            "three things that moved you away, from the life you want/who you want to be, with an up "
            "or down arrow next to the entry. Migrate: Identify what needs to be carried forward into "
            "tomorrow's plan. Enact any daily insight by writing them down as actions."
        )
        height = self.draw_rich_text(page, daily_text, CONTENT_LEFT, y, font_body, CONTENT_WIDTH - 40, line_height)
        y += height + 25

        # Weekly reflection
        self.add_text(page, "Weekly reflection", CONTENT_LEFT, y, FONT_SIZES["subheader"])
        y += SUBHEADER_SPACING
        weekly_text = (
            "Tidy your weekly entries. Update the monthly timeline and action plan. Acknowledge up "
            "to three things that moved you toward, and up to three things that moved you away, from "
            "the life you want/who you want to be, in a few sentences. Migrate only relevant |Actions| into "
            "the next week's Action Plan. Enact any insight from your reflection into the action plan. "
            "Prioritize your action plan based on your intention or insight. |Take action.|"
        )
        height = self.draw_rich_text(page, weekly_text, CONTENT_LEFT, y, font_body, CONTENT_WIDTH - 40, line_height)
        y += height + 25

        # Monthly reflection
        self.add_text(page, "Monthly reflection", CONTENT_LEFT, y, FONT_SIZES["subheader"])
        y += SUBHEADER_SPACING
        monthly_text = (
            "Tidy up your record for the last month. Acknowledge up to three things that moved you "
            "toward, and up to three things that moved you away, from the life you want/who you want "
            "to be, in short paragraphs. Migrate Actions that matter for the month ahead. Enact insights "
            "from your reflection onto your monthly action plan. Prioritize your action plan based on "
            "your intention or insight. |Take action.|"
        )
        self.draw_rich_text(page, monthly_text, CONTENT_LEFT, y, font_body, CONTENT_WIDTH - 40, line_height)

    def draw_lightning_bolt(self, page: fitz.Page, x: float, y: float, size: float = 20):
        """Draw a simple lightning bolt icon."""
        # Lightning bolt shape points (simplified zigzag)
        points = [
            fitz.Point(x + size * 0.5, y),              # Top
            fitz.Point(x + size * 0.15, y + size * 0.45),  # Left bend
            fitz.Point(x + size * 0.45, y + size * 0.45),  # Middle left
            fitz.Point(x + size * 0.2, y + size),       # Bottom
            fitz.Point(x + size * 0.55, y + size * 0.55),  # Right bend
            fitz.Point(x + size * 0.35, y + size * 0.55),  # Middle right
        ]
        shape = page.new_shape()
        shape.draw_polyline(points)
        shape.finish(fill=COLOR_BLACK, closePath=True)
        shape.commit()

    def generate_guide_intention(self, page_num: int):
        """Page 10: Intention - Writing page with dot grid and bottom footer."""
        page = self.doc[page_num]
        footer_font = 22  # 27 * 0.8

        # Navigation
        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)

        # Title
        self.add_text(page, "Intention", CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["header"])

        # Dot grid for writing area
        grid_top = CONTENT_TOP + 100
        grid_bottom = CONTENT_BOTTOM - 160  # Adjusted for smaller footer
        self.draw_dot_grid(page, grid_top, grid_bottom)

        # Footer section with lightning icon (same style as other pages)
        footer_y = CONTENT_BOTTOM - 140
        page.draw_line(fitz.Point(CONTENT_LEFT, footer_y), fitz.Point(CONTENT_RIGHT, footer_y),
                       color=COLOR_BLACK, width=0.5)
        footer_y += 15

        # Lightning icon (same as draw_footer_section)
        self.draw_lightning(page, CONTENT_LEFT, footer_y + 5, scale=1.8)

        footer_text = (
            "An intention is a commitment to a process. Intentions bring meaning into our lives now, so that we "
            "can navigate our lives based on what it is as opposed to what may be. They're powerful tools that we "
            "can use to instantly direct our focus for as long as we need. We set an intention to use as our compass."
        )
        self.draw_rich_text(page, footer_text, CONTENT_LEFT + 45, footer_y, footer_font, CONTENT_WIDTH - 75, 1.4)

    def generate_guide_goals(self, page_num: int):
        """Page 11: Goals - Writing page with dot grid and bottom footer."""
        page = self.doc[page_num]
        footer_font = 22  # 27 * 0.8

        # Navigation
        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)

        # Title
        self.add_text(page, "Goals", CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["header"])

        # Dot grid for writing area
        grid_top = CONTENT_TOP + 100
        grid_bottom = CONTENT_BOTTOM - 160  # Adjusted for smaller footer
        self.draw_dot_grid(page, grid_top, grid_bottom)

        # Footer section with lightning icon (same style as other pages)
        footer_y = CONTENT_BOTTOM - 140
        page.draw_line(fitz.Point(CONTENT_LEFT, footer_y), fitz.Point(CONTENT_RIGHT, footer_y),
                       color=COLOR_BLACK, width=0.5)
        footer_y += 15

        # Lightning icon (same as draw_footer_section)
        self.draw_lightning(page, CONTENT_LEFT, footer_y + 5, scale=1.8)

        footer_text = (
            "A goal is the definition of an outcome. Goals help us articulate what we want, transforming ephemeral "
            "desires into tangible targets, lofty dreams into fixed destinations. Taking time to carefully define our "
            "destinations, can provide a much needed sense of purpose and direction."
        )
        self.draw_rich_text(page, footer_text, CONTENT_LEFT + 45, footer_y, footer_font, CONTENT_WIDTH - 75, 1.4)

    def generate_future_log(self, page_num: int, quarter: int):
        """Generate future log page (3 months per page, 4 pages total).

        Args:
            quarter: 1-4, indicating which quarter (Q1=Jan-Mar, Q2=Apr-Jun, etc.)
        """
        page = self.doc[page_num]

        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)
        self.add_text(page, "Future Log", CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["title_page"])

        # 3 months per quarter
        all_months = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        start_idx = (quarter - 1) * 3
        months = all_months[start_idx:start_idx + 3]

        # Draw dot grid - start below title
        self.draw_dot_grid(page, CONTENT_TOP + 115, CONTENT_BOTTOM - 130)

        y = CONTENT_TOP + 115
        month_height = (CONTENT_HEIGHT - 265) // 3  # Divide space for 3 months vertically

        for i, month in enumerate(months):
            my = y + i * month_height

            # Month header
            self.add_text(page, month, CONTENT_LEFT, my, FONT_SIZES["body"])
            # Line below month name - offset by font size + padding
            page.draw_line(fitz.Point(CONTENT_LEFT, my + 45),
                           fitz.Point(CONTENT_RIGHT, my + 45),
                           color=COLOR_BLACK, width=0.5)

        self.draw_footer_section(page, "future_log")

    def generate_monthly_timeline(self, page_num: int, month_name: str, days: int, start_page: int):
        """Generate monthly timeline page."""
        page = self.doc[page_num]

        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)
        self.add_text(page, month_name, CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["title_page"])

        # Draw dot grid - start below title
        self.draw_dot_grid(page, CONTENT_TOP + 115, CONTENT_BOTTOM - 130)

        y = CONTENT_TOP + 115
        day_height = (CONTENT_HEIGHT - 265) / days

        for day in range(1, days + 1):
            # Offset by half font height for better vertical centering in each row
            day_y = y + (day - 1) * day_height + FONT_SIZES["day_number"] / 2
            self.add_text(page, str(day), CONTENT_LEFT, day_y, FONT_SIZES["day_number"])

            # Link to daily page (each day has 2 pages)
            dest_page = start_page + (day - 1) * 2
            link_rect = (CONTENT_LEFT - 5, day_y - 5, CONTENT_LEFT + 35, day_y + FONT_SIZES["day_number"] + 5)
            self.deferred_links.append(DeferredLink(page_num, link_rect, dest_page))

        self.draw_footer_section(page, "monthly_timeline")
        self.add_bottom_nav(page_num, [("Year", PAGE_YEAR_INDEX)])

    def generate_monthly_action_plan(self, page_num: int, month_name: str):
        """Generate monthly action plan page."""
        page = self.doc[page_num]

        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)
        self.add_text(page, month_name, CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["title_page"])

        # Draw dot grid - start below title
        self.draw_dot_grid(page, CONTENT_TOP + 115, CONTENT_BOTTOM - 130)

        self.draw_footer_section(page, "monthly_action")

    def draw_date_range_input(self, page: fitz.Page, x: float, y: float, font_size: float = 24):
        """Draw date range input field: __/__ to __/__"""
        line_width = 25
        slash_spacing = 8

        current_x = x
        line_y = y + font_size - 2

        # First date: __/__
        page.draw_line(fitz.Point(current_x, line_y),
                       fitz.Point(current_x + line_width, line_y),
                       color=COLOR_GRAY, width=0.8)
        current_x += line_width + slash_spacing
        self.add_text(page, "/", current_x, y, font_size, COLOR_BLACK)
        current_x += 12
        page.draw_line(fitz.Point(current_x, line_y),
                       fitz.Point(current_x + line_width, line_y),
                       color=COLOR_GRAY, width=0.8)
        current_x += line_width + 20

        # "to" in italic
        self.add_text(page, "to", current_x, y, font_size, COLOR_BLACK, italic=True)
        current_x += 30

        # Second date: __/__
        page.draw_line(fitz.Point(current_x, line_y),
                       fitz.Point(current_x + line_width, line_y),
                       color=COLOR_GRAY, width=0.8)
        current_x += line_width + slash_spacing
        self.add_text(page, "/", current_x, y, font_size, COLOR_BLACK)
        current_x += 12
        page.draw_line(fitz.Point(current_x, line_y),
                       fitz.Point(current_x + line_width, line_y),
                       color=COLOR_GRAY, width=0.8)

    def generate_weekly_action_plan(self, page_num: int):
        """Generate weekly action plan page."""
        page = self.doc[page_num]

        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)
        self.add_text(page, "Weekly Action plan", CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["title_page"])

        # Date range input (matching original PDF style)
        self.draw_date_range_input(page, CONTENT_RIGHT - 220, CONTENT_TOP + 55, 22)

        # Draw dot grid - start below title
        self.draw_dot_grid(page, CONTENT_TOP + 115, CONTENT_BOTTOM - 130)

        self.draw_footer_section(page, "weekly_action")

    def generate_weekly_reflection(self, page_num: int):
        """Generate weekly reflection page."""
        page = self.doc[page_num]

        self.add_nav_link(page_num, "Index", PAGE_MAIN_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)
        self.add_text(page, "Weekly Reflection", CONTENT_LEFT, CONTENT_TOP + 50, FONT_SIZES["title_page"])

        # Date range input (matching original PDF style)
        self.draw_date_range_input(page, CONTENT_RIGHT - 220, CONTENT_TOP + 55, 22)

        # Draw dot grid - start below title
        self.draw_dot_grid(page, CONTENT_TOP + 115, CONTENT_BOTTOM - 130)

        self.draw_footer_section(page, "weekly_reflection")

    def generate_daily_log(self, page_num: int, date_label: str, monthly_page: int, month_name: str = ""):
        """Generate daily log page."""
        page = self.doc[page_num]

        # Navigation - Index B (Year Index) on left, Month name on right
        self.add_nav_link(page_num, "Index", PAGE_YEAR_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)
        # Monthly link on the right side with full month name
        monthly_text = month_name if month_name else "Monthly log"
        monthly_text_width = self.get_text_width(monthly_text, FONT_SIZES["nav"])
        self.add_nav_link(page_num, monthly_text, monthly_page,
                          CONTENT_RIGHT - monthly_text_width - 40, CONTENT_TOP + 5)

        # Date header
        self.add_text(page, date_label, CONTENT_LEFT, CONTENT_TOP + 70, FONT_SIZES["title_page"])

        # Draw dot grid - start below date header (70 + 52pt font + padding)
        self.draw_dot_grid(page, CONTENT_TOP + 145, CONTENT_BOTTOM - 130)

        self.draw_footer_section(page, "daily_log")

    def generate_daily_log_continuation(self, page_num: int, date_label: str, monthly_page: int, month_name: str = ""):
        """Generate daily log continuation page (page 2 of each day)."""
        page = self.doc[page_num]

        # Navigation - Index B (Year Index) on left, Month name on right
        self.add_nav_link(page_num, "Index", PAGE_YEAR_INDEX, CONTENT_LEFT, CONTENT_TOP + 5)
        # Monthly link on the right side with full month name
        monthly_text = month_name if month_name else "Monthly log"
        monthly_text_width = self.get_text_width(monthly_text, FONT_SIZES["nav"])
        self.add_nav_link(page_num, monthly_text, monthly_page,
                          CONTENT_RIGHT - monthly_text_width - 40, CONTENT_TOP + 5)

        # Date header (same as page 1, continued)
        self.add_text(page, date_label, CONTENT_LEFT, CONTENT_TOP + 70, FONT_SIZES["title_page"])

        # Draw dot grid - start below date header, no footer on continuation page
        self.draw_dot_grid(page, CONTENT_TOP + 145, CONTENT_BOTTOM - 30)

    def generate_collection_page(self, page_num: int, index_page: int = 4):
        """Generate blank collection page.

        Args:
            page_num: Page number (0-indexed)
            index_page: Index page to link back to (4=Index C, 5=Index D)
        """
        page = self.doc[page_num]

        self.add_nav_link(page_num, "Index", index_page, CONTENT_LEFT, CONTENT_TOP + 5)

        # Draw dot grid
        self.draw_dot_grid(page, CONTENT_TOP + 50, CONTENT_BOTTOM - 30)

    # -------------------------------------------------------------------------
    # Main Generation
    # -------------------------------------------------------------------------

    def generate(self):
        """Generate complete PDF."""
        print("Generating rPPM Bullet Journal PDF v2...")

        # Create all pages using calculated total
        print(f"  Creating {TOTAL_PAGES} pages...")
        for _ in range(TOTAL_PAGES):
            self.create_page()

        # Page 1: Cover
        print(f"  [{PAGE_COVER}] Cover")
        self.generate_cover(PAGE_COVER - 1)

        # Page 2: Main Index
        print(f"  [{PAGE_MAIN_INDEX}] Main Index")
        self.generate_main_index(PAGE_MAIN_INDEX - 1)

        # Page 3: Year Index
        print(f"  [{PAGE_YEAR_INDEX}] Year Index")
        self.generate_year_index(PAGE_YEAR_INDEX - 1)

        # Pages 4-5: Collection Indexes
        print(f"  [{PAGE_COLLECTION_INDEX_C}-{PAGE_COLLECTION_INDEX_D}] Collection Indexes")
        self.generate_collection_index(PAGE_COLLECTION_INDEX_C - 1, "C")
        self.generate_collection_index(PAGE_COLLECTION_INDEX_D - 1, "D")

        # Guide pages (Pages 6-11)
        print(f"  [{PAGE_GUIDE_START}-{PAGE_GUIDE_START + NUM_GUIDE_PAGES - 1}] Guide pages")
        self.generate_guide_system(PAGE_GUIDE_START - 1)           # Page 6
        self.generate_guide_set_up_logs(PAGE_GUIDE_START)          # Page 7
        self.generate_guide_practice(PAGE_GUIDE_START + 1)         # Page 8
        self.generate_guide_how_to_reflect(PAGE_GUIDE_START + 2)   # Page 9
        self.generate_guide_intention(PAGE_GUIDE_START + 3)        # Page 10
        self.generate_guide_goals(PAGE_GUIDE_START + 4)            # Page 11

        # Future Log (4 pages, 3 months each)
        future_log_end = PAGE_FUTURE_LOG_START + NUM_FUTURE_LOG_PAGES - 1
        print(f"  [{PAGE_FUTURE_LOG_START}-{future_log_end}] Future Log")
        for quarter in range(1, NUM_FUTURE_LOG_PAGES + 1):
            self.generate_future_log(PAGE_FUTURE_LOG_START - 1 + (quarter - 1), quarter)

        # Monthly pages (Timeline + Action Plan for each month)
        monthly_end = PAGE_MONTHLY_START + NUM_MONTHS * 2 - 1
        print(f"  [{PAGE_MONTHLY_START}-{monthly_end}] Monthly pages")
        page_idx = PAGE_MONTHLY_START - 1
        for month_idx in range(NUM_MONTHS):
            month_name = MONTH_NAMES[month_idx]
            days = DAYS_PER_MONTH[month_idx]
            start_page = DAILY_PAGE_STARTS[month_idx]

            self.generate_monthly_timeline(page_idx, month_name, days, start_page)
            page_idx += 1

            self.generate_monthly_action_plan(page_idx, month_name)
            page_idx += 1

        # Weekly pages (Action Plan + Reflection for each week)
        weekly_end = PAGE_WEEKLY_START + NUM_WEEKS * 2 - 1
        print(f"  [{PAGE_WEEKLY_START}-{weekly_end}] Weekly pages")
        page_idx = PAGE_WEEKLY_START - 1
        for week in range(NUM_WEEKS):
            self.generate_weekly_action_plan(page_idx)
            page_idx += 1
            self.generate_weekly_reflection(page_idx)
            page_idx += 1

        # Daily pages
        daily_end = PAGE_DAILY_START + NUM_DAYS * PAGES_PER_DAY - 1
        print(f"  [{PAGE_DAILY_START}-{daily_end}] Daily pages")
        page_idx = PAGE_DAILY_START - 1

        for month_idx in range(NUM_MONTHS):
            month_name = MONTH_NAMES[month_idx]
            month_abbrev = MONTH_ABBREVS[month_idx]
            days = DAYS_PER_MONTH[month_idx]
            monthly_page = get_monthly_timeline_page(month_idx)

            for day in range(1, days + 1):
                date_label = f"{month_abbrev} {day}"
                self.generate_daily_log(page_idx, date_label, monthly_page, month_name)
                page_idx += 1

        # Collection pages
        total_collections = NUM_COLLECTIONS_PER_INDEX * NUM_COLLECTION_INDEXES
        collection_end = PAGE_COLLECTION_START + total_collections * PAGES_PER_COLLECTION - 1
        print(f"  [{PAGE_COLLECTION_START}-{collection_end}] Collection pages")
        for collection_idx in range(total_collections):
            # First 18 link back to Index C, last 18 link back to Index D
            index_page = PAGE_COLLECTION_INDEX_C if collection_idx < NUM_COLLECTIONS_PER_INDEX else PAGE_COLLECTION_INDEX_D
            page_idx = PAGE_COLLECTION_START - 1 + collection_idx
            self.generate_collection_page(page_idx, index_page)

        # Apply links
        print("  Applying links...")
        self.apply_deferred_links()

        print(f"\nGenerated {len(self.doc)} pages")
        return self.doc

    def save(self, output_path: str):
        self.doc.save(output_path)
        self.doc.close()
        print(f"Saved to {output_path}")


def main():
    generator = BulletJournalGenerator()
    generator.generate()

    output_path = "output/BulletJournal_rPPM_v2.pdf"
    Path("output").mkdir(exist_ok=True)
    generator.save(output_path)

    print("\n" + "=" * 50)
    print("GENERATION COMPLETE")
    print("=" * 50)
    print(f"Output: {output_path}")
    print(f"Size: {TARGET_WIDTH} x {TARGET_HEIGHT} px")


if __name__ == "__main__":
    main()
