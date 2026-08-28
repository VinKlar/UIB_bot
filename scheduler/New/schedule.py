from datetime import date
import scheduler.scheduler_parser as parser
from itertools import groupby

MIN_DATE = date(date.today().year, 1, 1)
MAX_DATE = date(date.today().year, 12, 30)

class DateRange:
    
    def __init__(self, start: date, end: date):
        if start > end:
           raise ValueError(f"Невалидный диапозон дат (start = {start} > end = {end})") 
        self.start = start
        self.end = end
    
    def in_range(self, date: date):
        return date >= self.start and date <= self.end

    def get_days(self):
        return self.end - self.start

    @staticmethod
    def make_from(period: parser.Period | None):
        if period:
            return DateRange(period.start, period.end)
        else:
            return DateRange(MIN_DATE, MAX_DATE)

class DayParser:
    
    def __init__(self, start: date):
        self.start = start # Должен быть понедельником!

    def make_index(self, week_day: int, even: bool):
        return int(even) * 7 + week_day

    def parse(self, day: date):
        week_number = (day - self.start).days // 7
        return (week_number) % 2 * 7 + day.weekday()



class LessonResult:
    
    def __init__(self, index: int, subject: str, classroom: list[str], teacher: str, subgroups: str, is_lecture: bool):
        self.index = index
        self.subject = subject
        self.classroom = classroom
        self.teacher = teacher
        self.subgroups = subgroups
        self.is_lecture = is_lecture


class Subject:
    
    def __init__(self, name: str, teacher: str, lecture_range: DateRange, practice_range: DateRange):
        self.name = name
        self.teacher = teacher
        self.lecture_range = lecture_range
        self.practice_range = practice_range
    
    @staticmethod
    def make_from(subject: parser.Subject):
        return Subject(
            subject.name, subject.teachers[0].name, 
            DateRange.make_from(subject.period.lecture), 
            DateRange.make_from(subject.period.practice)
        )
    

class LessonType:
    def __init__(self, source_str: str):
        self.is_lecture = source_str == "Л"
        if not self.is_lecture:
            splited = [x.strip() for x in source_str.split("|")]
            self.groups = {
                int(k) - 1: "".join(v[1] if len(v) > 1 else "" for v in g)
                for k, g in groupby(splited, key=lambda x: x[0])
            }

    @staticmethod
    def parse(to_parse: str):
        group_index = to_parse[0:1]
        if group_index.isdigit():
            return (int(group_index) - 1, to_parse[1:])
        else:
            return (0, "")

    def has_group(self, group: int):
        return group in self.groups
    
    def get_subgroups(self, group: int):
        return self.groups[group] if not self.is_lecture else ""


class LessonClassrooms:
    rooms:  list[tuple[DateRange | date, str]]

    def __init__(self, rooms: list[tuple[DateRange | date, str]]):
        self.rooms = rooms

    def get_classrooms(self, day: date):
        date_filtered = filter(lambda date_room: type(date_room[0]) is date and date_room[0] == day, self.rooms)
        date_filtered = list(map(lambda range_room: range_room[1], date_filtered))
        if len(date_filtered) > 0:
            return date_filtered
        
        range_filtered = filter(lambda range_room: type(range_room[0]) is DateRange and range_room[0].in_range(day), self.rooms)
        return list(map(lambda range_room: range_room[1], range_filtered))
    
    @staticmethod
    def parse_period(data: parser.Classroom, period: DateRange) -> tuple[DateRange | date, str]:
        if data.in_date: 
            return (data.in_date, data.room)
        
        start = period.start
        end = period.end
        if data.from_date: 
            start = data.from_date
        if data.until_date: 
            end = data.until_date
        
        return (DateRange(start, end), data.room)

    @staticmethod
    def make_from(data: list[parser.Classroom], period: DateRange):
        ranges = list(map(lambda room: LessonClassrooms.parse_period(room, period), data))
        return LessonClassrooms(ranges)


class Lesson:

    def __init__(self, index: int, subject: Subject, classroom: LessonClassrooms, type: LessonType):
        self.index = index
        self.subject = subject
        self.type = type
        self.classroom = classroom
    
    def check_group(self, group: int):
        if not self.type.is_lecture:
            return self.type.has_group(group)
        return True
    
    @staticmethod
    def make_from(data: parser.Lesson, index: int, subject: Subject):
        lesson_type = LessonType(data.type)
        date_range = subject.lecture_range if lesson_type.is_lecture else subject.practice_range
        classrooms = LessonClassrooms.make_from(data.classroom, date_range)
        return Lesson(index, subject, classrooms, lesson_type)

class LessonList:
    lessons : list[Lesson]

    def __init__(self):
        self.lessons = []

    def get_lessons(self, day: date, group: int):
        lesson_classrooms = map(lambda lesson: (lesson, lesson.classroom.get_classrooms(day)), self.lessons)
        filtered = filter(lambda lesson_rooms: lesson_rooms[0].check_group(group) and bool(lesson_rooms[1]), lesson_classrooms)
        sorted_by_index = sorted(filtered, key = lambda lesson_rooms: lesson_rooms[0].index)

        result = list(map(lambda lesson_rooms: LessonResult(
            lesson_rooms[0].index, lesson_rooms[0].subject.name, 
            lesson_rooms[1], lesson_rooms[0].subject.teacher, 
            lesson_rooms[0].type.get_subgroups(group), 
            lesson_rooms[0].type.is_lecture), sorted_by_index))

        return result

    def make_from(self, data: dict[int, parser.Lesson], subject: Subject):
        for index, lesson in data.items():
            self.lessons.append(Lesson.make_from(lesson, index, subject))


class GroupSchedule:
    days: list[LessonList] # week_day -> LessonList [7 odds week days, 7 even week days]
    day_parser: DayParser = DayParser(date(2025, 9, 1))

    def __init__(self):
        self.days = [LessonList() for _ in range(14)]

    def parse_week(self, data: dict[int, dict[int, parser.Lesson]], even: bool, subject: Subject):
        for day, lessons in data.items():
            day_index = self.day_parser.make_index(day, even)
            self.days[day_index].make_from(lessons, subject)


    def parse(self, data: list[parser.Subject]):
        for s in data:
            subject = Subject.make_from(s)
            self.parse_week(s.chet, True, subject)
            self.parse_week(s.nchet, False, subject)

    def get_day(self, day: date, group: int) -> list[LessonResult]:
        day_index = self.day_parser.parse(day)
        if day_index:
            lesson_list = self.days[day_index]
            return lesson_list.get_lessons(day, group)
        
        return []

class Scheduler:
    schedules: dict[str, tuple[GroupSchedule, int]]

    def __init__(self):
        self.schedules = {}

    def parse_group(self, data: parser.GroupSchedule):
        new_group = GroupSchedule()
        new_group.parse(data.subjects)
        groups = data.meta.group
        splited = groups.split(",")
        self.schedules.update(zip(splited, map(lambda i_str: (new_group, i_str[0]), enumerate(splited))))

    def get_day(self, day: date, group: str):
        scheduler, group_index = self.schedules[group]
        return scheduler.get_day(day, group_index)


if __name__ == "__main__":
    scheduler = Scheduler()
    with open("test.json", encoding="utf-8") as file:
        parsed = parser.parse_json(file.read())
        scheduler.parse_group(parsed)
    
    result = scheduler.get_day(date(2026, 3, 28), "8102") # date(2026, 2, 18)
    
    last_index = 0
    for item in result:
        if item.index != last_index:
            last_index = item.index
            print(f"{last_index} пара:")
        print(f"{item.subject} ({' | '.join(item.classroom)}) - {'Лекция' if item.is_lecture else 'Практика ' + ' | '.join(item.subgroups)}")