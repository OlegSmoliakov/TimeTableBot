from datetime import date, datetime, timedelta
from aiogram.utils.i18n import gettext as _, lazy_gettext as __


INT_TO_WEEKDAY = {
    1: __("Monday"),
    2: __("Tuesday"),
    3: __("Wednesday"),
    4: __("Thursday"),
    5: __("Friday"),
    6: __("Saturday"),
    7: __("Sunday"),
}

WEEKDAY_TO_INT = {
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6,
    "Sunday": 7,
}


def format_lesson(lesson: dict):
    start_time = datetime.strptime(lesson["startTime"], "%H:%M:%S")
    end_time = start_time + timedelta(hours=lesson["hoursSpan"])
    lesson_number = str(start_time.hour - 8) + "."

    indent = " " * (len(lesson_number) + 1)

    text = (
        f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n"
        f"{lesson_number} *{lesson["subjectName"]}*\n"
    )
    
    if lesson['subgroup'] is not None:
        subgroup = _("Subgroup")
        text += f"{indent}{subgroup}: {lesson['subgroup']}\n"

    text += (
        f"{indent}_{lesson['lessonType']}_\n"
        f"{indent}{lesson['professor']}\n"
        f"{indent}{lesson['classroom']}\n"
    )

    return text


def get_monday_date():
    current_date = date.today()
    if current_date.weekday() >= 5:
        days_ahead = 7 - current_date.weekday()
        return current_date + timedelta(days=days_ahead)
    else:
        return current_date


def format_lessons(day: dict):
    monday_date = get_monday_date()
    day_int = WEEKDAY_TO_INT[day["day"]]
    day_name = INT_TO_WEEKDAY[day_int]
    day_date = monday_date + timedelta(days=day_int - 1)
    title = f"*{day_name}, {day_date.strftime('%d.%m')}*\n\n"

    lessons = day["lessons"]
    for lesson in lessons:
        title += format_lesson(lesson) + "\n"

    return title


def format_timetable(data: list | dict):
    """
    Formats the timetable data into a readable text format.

    Args:
        data (list | dict): The timetable data to be formatted. It can be either a list of days or a dictionary representing a single day.

    Returns:
        str: The formatted timetable text.

    `IMPORTANT:` must use markdown for parse_mode
    """
    if isinstance(data, list):
        text = ""
        for day in data:
            text += format_lessons(day)

    elif isinstance(data, dict):
        text = format_lessons(data)

    return text.strip()
