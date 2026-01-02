from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    year: int = 2026
    pages_per_day: int = 2
    pages_per_collection: int = 1

    num_guide_pages: int = 6
    num_future_log_pages: int = 4
    num_collections_per_index: int = 18
    num_collection_indexes: int = 2

    output_path: str = "output/BulletJournal_rPPM.pdf"
