#!/usr/bin/env python3
"""
Generate Bullet Journal PDF optimized for reMarkable Paper Pro Move (rPPM).

Usage:
    python main.py          # Generate for current year
    python main.py 2025     # Generate for specific year
"""

import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from bujo import BulletJournalGenerator
from bujo.config import Settings


def main() -> None:
    if len(sys.argv) > 1:
        year = int(sys.argv[1])
    else:
        year = datetime.now().year

    output_path = f"output/BulletJournal_rPPM_{year}.pdf"
    settings = replace(Settings(), year=year, output_path=output_path)
    generator = BulletJournalGenerator(settings=settings, asset_root=Path("."))
    doc, report = generator.generate()
    generator.save(doc, output_path)

    print("\n" + "=" * 50)
    print("GENERATION COMPLETE")
    print("=" * 50)
    print(f"Output: {output_path}")

    for line in report.summary_lines():
        print(f"Validation: {line}")


if __name__ == "__main__":
    main()
