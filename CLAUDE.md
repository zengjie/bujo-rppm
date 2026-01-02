# Bullet Journal PDF Generator for reMarkable Paper Pro Move

This project generates a Bullet Journal PDF optimized for reMarkable Paper Pro Move (rPPM).

## Project Structure

- `main.py` - Main entry point
- `bujo/` - Modular generator (config, calendar model, rendering, validation)
- `original/Bullet Journal.pdf` - Original reference PDF
- `output/BulletJournal_rPPM.pdf` - Generated output

## Usage

```bash
./download_fonts.sh
uv venv
uv sync
uv run python main.py
```

## Requirements

- Python 3.10+
- PyMuPDF (`fitz`) via `pyproject.toml`
- EB Garamond fonts downloaded to `fonts/` (use `./download_fonts.sh`)

## Output Specifications

- Page size: 954 x 1696 pixels
- Optimized for rPPM screen with top toolbar safe zone (130px)
- Dynamic page count based on calendar/year and settings
