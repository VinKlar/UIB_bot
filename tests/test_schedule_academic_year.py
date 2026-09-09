import unittest
from datetime import date
from pathlib import Path

from scheduler.schedule import DayParser, Scheduler
from scheduler.scheduler_parser import Period, parse_json
from bot.handlers import format_lesson


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AcademicYearTests(unittest.TestCase):
    def test_week_containing_september_first_is_odd(self):
        parser = DayParser(date(2026, 8, 31))

        self.assertEqual(parser.parse(date(2026, 9, 1)), 1)
        self.assertEqual(parser.parse(date(2026, 9, 6)), 6)

    def test_week_after_first_academic_week_is_even(self):
        parser = DayParser(date(2026, 8, 31))

        self.assertEqual(parser.parse(date(2026, 9, 7)), 7)
        self.assertEqual(parser.parse(date(2026, 9, 13)), 13)

    def test_academic_week_parity_continues_alternating(self):
        parser = DayParser(date(2026, 8, 31))

        self.assertEqual(parser.parse(date(2026, 9, 14)), 0)

    def test_period_crossing_new_year_is_valid(self):
        period = Period.model_validate({"from": "19.10", "to": "16.01"})
        self.assertLess(period.start, period.end)
        self.assertEqual(period.end.year, period.start.year + 1)

    def test_schedule_without_teacher_can_be_loaded(self):
        source = PROJECT_ROOT / "scheduler" / "jsons" / "1122а.json"
        parsed = parse_json(source.read_text(encoding="utf-8"))
        self.assertTrue(any(not subject.teachers for subject in parsed.subjects))

        scheduler = Scheduler()
        scheduler.parse_group(parsed)
        self.assertIn(parsed.meta.group, scheduler.groups)

    def test_all_current_schedule_json_files_load(self):
        json_dir = PROJECT_ROOT / "scheduler" / "jsons"
        scheduler = Scheduler()

        for source in json_dir.glob("*.json"):
            with self.subTest(source=source.name):
                scheduler.parse_group(parse_json(source.read_text(encoding="utf-8")))

    def test_lesson_output_contains_teacher(self):
        source = PROJECT_ROOT / "scheduler" / "jsons" / "1122а.json"
        scheduler = Scheduler()
        parsed = parse_json(source.read_text(encoding="utf-8"))
        scheduler.parse_group(parsed)

        lesson = next(
            lesson
            for day in scheduler.groups[parsed.meta.group].days.values()
            for lesson in day.lessons
            if lesson.subject.teacher
        )
        text = format_lesson(lesson)

        self.assertIn("Преподаватель:", text)
        self.assertIn(lesson.subject.teacher, text)


if __name__ == "__main__":
    unittest.main()
