from datetime import date
import scheduler.scheduler_parser as scheduler_parser


class DateRange:
    
    def __init__(self, start: date, end: date):
        if start > end:
           raise ValueError(f"Невалидный диапозон дат (start = {start} > end = {end})") 
        self.__start = start
        self.__end = end
    
    @staticmethod
    def make_from(period: scheduler_parser.Period | None):
        if period:
            return DateRange(period.start, period.end)
        else:
            year = date.today().year
            return DateRange(date(year, 1, 1), date(year, 12, 30))

    def in_range(self, date: date):
        return date > self.__start and date < self.__end

class DayParser:
    
    def __init__(self, start: date, max_week: int = 100):
        self.start = start # Должен быть понедельником!
        self.max_week = max_week

    def make_index(self, week_day: int, even: bool):
        return int(even) * 7 + week_day

    def parse(self, day: date):
        week_number = (day - self.start).days // 7
        if week_number < self.max_week: 
            return (week_number + 1) % 2 * 7 + day.weekday()
        else:
            return None


class Subject:
    
    def __init__(self, name: str, teacher: str, lecture_range: DateRange, practice_range: DateRange):
        self.name = name
        self.teacher = teacher
        self.lecture_range = lecture_range
        self.practice_range = practice_range
    
    @staticmethod
    def make_from(subject: scheduler_parser.Subject):
        return Subject(
            subject.name, subject.teachers[0].name, 
            DateRange.make_from(subject.period.lecture), 
            DateRange.make_from(subject.period.practice)
        )

class Lesson:

    def __init__(self, index: int, subject: Subject, cabinet: str, type: str):
        self.index = index
        self.subject = subject
        self.cabinet = cabinet
        self.type = type

    def is_lecture(self):
        return self.type == "Л"
    
    def check_day(self, day : date):
        if self.is_lecture():
            return self.subject.lecture_range.in_range(day)
        return self.subject.practice_range.in_range(day)
    
    @staticmethod
    def make_from(data: scheduler_parser.Lesson, index: int, subject: Subject):
        return Lesson(index, subject, data.classroom[0].room, data.type)

class LessonList:
    lessons : list[Lesson]

    def __init__(self):
        self.lessons = []

    def get_subjects(self, day: date):
        filtered = list(filter(lambda lesson : lesson.check_day(day), self.lessons))
        filtered.sort(key = lambda lesson: lesson.index)
        return filtered

    def make_from(self, data: dict[int, scheduler_parser.Lesson], subject: Subject):
        for index, lesson in data.items():
            self.lessons.append(Lesson.make_from(lesson, index, subject))


class GroupSchedule:
    days: dict[int, LessonList]# week_day -> LessonList
    day_parser: DayParser = DayParser(date(2025, 9, 1))

    def __init__(self):
        self.days = {}

    def parse_week(self, data: dict[int, dict[int, scheduler_parser.Lesson]], even: bool, subject: Subject):
        for day, lessons in data.items():
            day_index = self.day_parser.make_index(day, even)
            if day_index not in self.days:
                self.days[day_index] = LessonList()
            self.days[day_index].make_from(lessons, subject)


    def parse(self, data: list[scheduler_parser.Subject]):
        for s in data:
            subject = Subject.make_from(s)
            self.parse_week(s.chet, True, subject)
            self.parse_week(s.nchet, False, subject)

    def get_day(self, day: date) -> list[Lesson]:
        day_index = self.day_parser.parse(day)
        if day_index:
            subject_list = self.days[day_index]
            return subject_list.get_subjects(day)
        
        return []

class Scheduler:
    groups: dict[str, GroupSchedule]
    
    def __init__(self):
        self.groups = {}

    def parse_group(self, data: scheduler_parser.GroupSchedule):
        new_group = GroupSchedule()
        new_group.parse(data.subjects)
        self.groups[data.meta.group] = new_group

    def get_day(self, day: date, group: str):
        return self.groups[group].get_day(day)


# from datetime import datetime, timedelta

# today = datetime.now().date()
    
# if __name__ == "__main__":
#     scheduler = Scheduler()
#     with open("scheduler/test.json", encoding="utf-8") as file:
#         parsed = scheduler_parser.parse_json(file.read())
#         scheduler.parse_group(parsed)
#     print(today +  + timedelta(days=1))
    
#     result = scheduler.get_day(today, "8101,02")
    
#     lesson_index = 0
#     for item in result:
#         if lesson_index != item.index:
#             lesson_index = item.index
#             print(f"{lesson_index} пара")
#         print(f"  {item.subject.name} ({item.cabinet}) - {'Лекция' if item.is_lecture() else item.type}")