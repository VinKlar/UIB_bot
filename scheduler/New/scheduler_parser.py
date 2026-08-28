from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import  Optional

week_days : dict[str, int] = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}


def convert_date(value: str):
    parts = value.split(".") 
    return date(date.today().year, int(parts[1]), int(parts[0]))

class Meta (BaseModel): 
    group: str

class Period(BaseModel):
    start: date = Field(alias = "from")
    end: date = Field(alias = "to")

    @field_validator("start", "end", mode="before")
    @classmethod
    def convert_date(cls, value: str):
        return convert_date(value)

class SubjectPeriods(BaseModel):
    lecture: Optional[Period] = None
    practice: Optional[Period] = None

class Classroom(BaseModel):
    room: str
    in_date: Optional[date] = Field(default = None, alias = "date")
    until_date: Optional[date] = Field(default = None, alias = "until")
    from_date: Optional[date] = Field(default = None, alias = "from")

    @field_validator("in_date", "until_date", "from_date", mode="before")
    @classmethod
    def convert_date(cls, value: str):
        return convert_date(value)

class Lesson(BaseModel):
    type: str
    classroom: list[Classroom]

class Teacher(BaseModel):
    name: str
    groups: str = ""

class Subject (BaseModel):
    name: str
    period: SubjectPeriods
    nchet: dict[int, dict[int, Lesson]] # dict [weekday_index, dict[par_number, Lesson]]
    chet: dict[int, dict[int, Lesson]]
    teachers: list[Teacher]

    
    @field_validator("chet", "nchet", mode="before")
    @classmethod
    def convert_week(cls, value: dict[str, dict[str, Lesson]]):
        days_dict : dict[int, dict[int, Lesson]] = {}
        for day, inner in value.items():
            lesson_dict : dict[int, Lesson] = {}
            for par, lesson in inner.items():
                lesson_dict[int(par[4:])] = lesson
            days_dict[week_days[day]] = lesson_dict
        return days_dict

class GroupSchedule(BaseModel):
    meta: Meta
    subjects: list[Subject]

def parse_json(json: str):
    return GroupSchedule.model_validate_json(json)

if __name__ == "__main__":
    with open("test.json", encoding="utf-8") as file:
        parsed = parse_json(file.read())
        print(parsed.subjects[3].period.lecture)
