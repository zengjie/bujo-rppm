# bujo-rppm

[![Build and Release PDF](https://github.com/zengjie/bujo-rppm/actions/workflows/build-release.yml/badge.svg)](https://github.com/zengjie/bujo-rppm/actions/workflows/build-release.yml)

A Bullet Journal PDF generator optimized for the reMarkable Paper Pro Move (rPPM) e-ink tablet.

## Quick Download

Download pre-built PDFs from [GitHub Releases](https://github.com/zengjie/bujo-rppm/releases/latest). Each release includes PDFs for the previous, current, and next year.

## Features

- **Full year calendar structure**: Cover, indexes, future logs, monthly spreads, weekly spreads, and daily pages
- **rPPM-optimized layout**: 954 x 1696 pixel pages with a 130px top safe zone for the toolbar
- **Interactive navigation**: Internal PDF links for quick navigation between sections
- **Customizable settings**: Configure pages per day, collections, and index structure
- **Dot grid background**: Subtle dot grid for handwriting alignment
- **EB Garamond typography**: Clean, professional font styling

## Page Types

The generated journal includes:

| Section | Description |
|---------|-------------|
| Cover | Year title page with lightning bolt design |
| Main Index | Navigation hub linking to all sections |
| Year Index | 12-month calendar overview with week links |
| Collection Indexes | Organize notes by topic (C and D sections) |
| Guide Pages | Symbol reference, system overview, practice tips |
| Future Log | 4 quarterly spreads for long-term planning |
| Monthly Spreads | Timeline and action plan for each month |
| Weekly Spreads | Action plan and reflection for each week |
| Daily Logs | One or more pages per day for rapid logging |
| Collection Pages | Blank pages for themed collections |

## Installation

Requires Python 3.10+ and [uv](https://github.com/astral-sh/uv).

```bash
# Clone the repository
git clone https://github.com/zengjie/bujo-rppm.git
cd bujo-rppm

# Download required fonts
./download_fonts.sh

# Set up virtual environment and install dependencies
uv venv
uv sync
```

## Usage

Generate the PDF:

```bash
# Generate for current year
uv run python main.py

# Generate for a specific year
uv run python main.py 2025
```

Output is saved to `output/BulletJournal_rPPM_<year>.pdf`.

## Configuration

Edit `bujo/config/settings.py` to customize:

```python
@dataclass(frozen=True)
class Settings:
    year: int                     # Target year (set via command line)
    pages_per_day: int = 1        # Daily log pages per day
    pages_per_collection: int = 1 # Pages per collection entry
    num_guide_pages: int = 6      # Introductory guide pages
    num_future_log_pages: int = 4 # Quarterly future log pages
    num_collections_per_index: int = 18  # Collections per index
    num_collection_indexes: int = 2      # Number of collection indexes
```

## Project Structure

```
bujo-rppm/
├── main.py              # Entry point
├── bujo/                # Core generator module
│   ├── generator.py     # Main BulletJournalGenerator class
│   ├── calendar_model.py # Year/month/week calculations
│   ├── page_map.py      # Page numbering and navigation
│   ├── link_manager.py  # Internal PDF link handling
│   ├── validation.py    # Output validation
│   ├── config/          # Configuration dataclasses
│   │   ├── settings.py  # User-configurable settings
│   │   ├── layout.py    # Page dimensions and margins
│   │   ├── theme.py     # Colors
│   │   └── typography.py # Font sizes
│   └── render/          # Page rendering
│       ├── pages.py     # Page generators for each type
│       └── primitives.py # Drawing utilities
├── fonts/               # EB Garamond font files
└── output/              # Generated PDFs
```

## Dependencies

- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF generation and manipulation
- [EB Garamond](https://github.com/octaviopardo/EBGaramond12) - Typography

## Automated Builds

This project uses GitHub Actions for CI/CD:

- **CI** (`ci.yml`): Runs on every push and pull request to `main`. Validates Python syntax.
- **Build and Release** (`build-release.yml`): Triggered by version tags (`v*`) or manual dispatch. Generates PDFs for the previous, current, and next year, then uploads them as release assets.

To create a new release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## License

MIT
