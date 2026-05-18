from bot.router import Router
from bot.conveyor import send_message, send_file
from datetime import date
from datetime import datetime, timedelta
from datetime import date
from bot.calendar_keyboard import create_calendar_buttons


router = Router()

@router.bot_started()
async def start_handler(event, context):
    user_key = str(event.user_id)

    if context["USERS"].get(user_key) is None:
        context["USER_STATE"][event.user_id] = "WAIT_FACULTY"

        await send_message(
            event.chat_id,
            "faculty"
        )
        return

    await send_message(
        event.chat_id,
        "/start"
    )

@router.message("/start")
async def start_handler(event, context):
    user_key = str(event.user_id)

    if context["USERS"].get(user_key) is None:
        context["USER_STATE"][event.user_id] = "WAIT_FACULTY"

        await send_message(
            event.chat_id,
            "faculty"
        )
        return

    await send_message(
        event.chat_id,
        "/start"
    )

FACULTY_DIRECTIONS = {
    "faculty_agro": "directions_agro",
    "faculty_engineering": "directions_engineering",
    "faculty_vet": "directions_vet",
    "faculty_ict": "directions_ict",
    "faculty_food": "directions_food",
    "faculty_econom": "directions_econom",
    "faculty_law": "directions_law"
}


@router.state("WAIT_FACULTY")
async def wait_faculty_handler(event, context):
    if event.type != "callback":
        await send_message(
            event.chat_id,
            "faculty"
        )
        return

    scen_name = FACULTY_DIRECTIONS.get(event.payload)

    if not scen_name:
        await send_message(
            event.chat_id,
            "faculty"
        )
        return

    context["USER_STATE"][event.user_id] = "WAIT_DIRECTION"

    await send_message(
        event.chat_id,
        scen_name
    )


@router.state("WAIT_DIRECTION")
async def wait_direction_handler(event, context):
    if event.type != "callback":
        await send_message(
            event.chat_id,
            "faculty",
            text="Нажмите кнопку с направлением"
        )
        return

    context["USER_STATE"][event.user_id] = "WAIT_GROUP"

    await send_message(
        event.chat_id,
        event.payload,
        text="Группа",
        ch_g=True
    )


@router.state("WAIT_GROUP")
async def wait_group_handler(event, context):
    if event.type != "callback":
        await send_message(
            event.chat_id,
            "group",
            text="Нажмите кнопку с группой"
        )
        return

    user_key = str(event.user_id)

    context["USERS"][user_key] = {
        "group": event.payload
    }

    context["save_users"](context["USERS"])

    context["USER_STATE"].pop(event.user_id, None)

    await send_message(
        event.chat_id,
        "push_button",
        text=f"Группа сохранена: {event.payload}"
    )


@router.message("Сегодня")
async def today_handler(event, context):
    await send_message(
        event.chat_id,
        "push_button",
        text="Расписание на сегодня"
    )


@router.message("Завтра")
async def tomorrow_handler(event, context):
    await send_message(
        event.chat_id,
        "push_button",
        text="Расписание на завтра"
    )


@router.callback("today")
async def today_callback_handler(event, context):
    lesson_index = 0

    lines = []
    for item in context['sched'].get_day(datetime.now().date(), context['FGS'][context['USERS'][str(event.user_id)]['group']]):
        print(item)
        if lesson_index != item.index:
            lesson_index = item.index

            lines.append(f"{lesson_index} пара")

        lines.append(
            f"  {item.subject.name} ({item.cabinet}) - "
            f"{'Лекция' if item.is_lecture() else item.type}"
        )

    text = "\n".join(lines)
    if not text:
        text = "На эту дату занятий нет"
    else:
        text = f"Расписание на {datetime.now().date()}\n"+text

    await send_message(
        event.chat_id,
        "push_button",
        text=text
    )

@router.callback("all")
async def all_callback_handler(event, context):
    
    
    await send_file(
        event.chat_id,
        f"scheduler/xls/{context['FGS'][context['USERS'][str(event.user_id)]['group']]}.xls",
        text="Общее расписание"
    )


@router.callback("tomorrow")
async def tomorrow_callback_handler(event, context):

    lesson_index = 0

    lines = []

    for item in context['sched'].get_day(datetime.now().date() + timedelta(days=1), context['FGS'][context['USERS'][str(event.user_id)]['group']]):

        if lesson_index != item.index:
            lesson_index = item.index

            lines.append(f"{lesson_index} пара")

        lines.append(
            f"  {item.subject.name} ({item.cabinet}) - "
            f"{'Лекция' if item.is_lecture() else item.type}"
        )

    text = "\n".join(lines)
    if not text:
        text = "На эту дату занятий нет"
    else:
        text = f"Расписание на {datetime.now().date() + timedelta(days=1)}\n"+text

    await send_message(
        event.chat_id,
        "push_button",
        text=text
    )

@router.callback("select_date")
async def select_date_handler(event, context):
    context["USER_STATE"][event.user_id] = "WAIT_DATE"

    await send_message(
        event.chat_id,
        "select_date",
        text="Введите дату в формате ДД.ММ.ГГГГ\nНапример: 15.05.2026"
    )

@router.callback("cancel")
async def select_date_handler(event, context):
    context["USER_STATE"].pop(
        event.user_id,
        None
    )

    await send_message(
        event.chat_id,
        "push_button",
        text="Выберите действие: "
    )

@router.state("WAIT_DATE")
async def wait_date_handler(event, context):

    if event.type != "message":
        await send_message(
            event.chat_id,
            "select_date",
            text="Введите дату текстом в формате ДД.ММ.ГГГГ"
        )
        return

    try:
        selected_date = datetime.strptime(
            event.text,
            "%d.%m.%Y"
        ).date()

    except ValueError:
        await send_message(
            event.chat_id,
            "select_date",
            text="Неверный формат даты. Введите так: 15.05.2026"
        )
        return

    context["USER_STATE"].pop(event.user_id, None)

    lesson_index = 0
    lines = []

    group = context['FGS'][context['USERS'][str(event.user_id)]['group']]

    try:
        result = context["sched"].get_day(
            selected_date,
            group
        )

    except Exception as e:
        print("Ошибка get_day:", e)
        result = []

    for item in result:

        if lesson_index != item.index:
            lesson_index = item.index
            lines.append(f"{lesson_index} пара")

        lines.append(
            f"  {item.subject.name} ({item.cabinet}) - "
            f"{'Лекция' if item.is_lecture() else item.type}"
        )

    text = "\n".join(lines)

    if not text:
        text = "На эту дату занятий нет"
    else:
        text = f"Расписание на {selected_date}\n"+text

    await send_message(
        event.chat_id,
        "push_button",
        text=text
    )

@router.callback()
async def callback_handler(event, context):
    payload = event.payload

    if payload == "ignore":
        return

    if payload.startswith("date:"):
        selected_date = payload.replace("date:", "")

        await send_message(
            event.chat_id,
            "push_button",
            text=f"Вы выбрали дату: {selected_date}"
        )
        return

@router.message()
async def unknown_message_handler(event, context):
    await send_message(
        event.chat_id,
        "push_button",
        text=f"Не понял сообщение: {event.text}"
    )


# @router.callback()
# async def unknown_callback_handler(event, context):
#     await send_message(
#         event.chat_id,
#         "push_button",
#         text=f"Неизвестная кнопка: {event.payload}"
#     )