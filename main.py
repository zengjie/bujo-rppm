#!/usr/bin/env python3
"""
Generate Bullet Journal PDF optimized for reMarkable Paper Pro Move (rPPM).
"""

from pathlib import Path

from bujo import BulletJournalGenerator
from bujo.config import Settings


def main() -> None:
    settings = Settings()
    generator = BulletJournalGenerator(settings=settings, asset_root=Path("."))
    doc, report = generator.generate()
    generator.save(doc, settings.output_path)

    print("\n" + "=" * 50)
    print("GENERATION COMPLETE")
    print("=" * 50)
    print(f"Output: {settings.output_path}")

    for line in report.summary_lines():
        print(f"Validation: {line}")


if __name__ == "__main__":
    main()
