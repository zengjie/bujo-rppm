from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import calendar
from typing import List


@dataclass(frozen=True)
class MonthInfo:
    index: int
    name: str
    abbrev: str
    days: int
    start_day_of_year: int


@dataclass(frozen=True)
class CalendarModel:
    year: int
    months: List[MonthInfo]
    total_days: int
    weeks_in_year: int

    @classmethod
    def for_year(cls, year: int) -> "CalendarModel":
        months: List[MonthInfo] = []
        day_cursor = 0
        for month in range(1, 13):
            days = calendar.monthrange(year, month)[1]
            info = MonthInfo(
                index=month - 1,
                name=calendar.month_name[month],
                abbrev=calendar.month_abbr[month],
                days=days,
                start_day_of_year=day_cursor,
            )
            months.append(info)
            day_cursor += days

        weeks_in_year = date(year, 12, 28).isocalendar().week
        return cls(year=year, months=months, total_days=day_cursor, weeks_in_year=weeks_in_year)

    def month(self, month_idx: int) -> MonthInfo:
        return self.months[month_idx]

    def day_of_year(self, month_idx: int, day: int) -> int:
        return self.months[month_idx].start_day_of_year + (day - 1)

    def date_label(self, month_idx: int, day: int) -> str:
        return f"{self.months[month_idx].abbrev} {day}"
