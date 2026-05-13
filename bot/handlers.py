from bot.router import Router
from bot.conveyor import send_message

router = Router()


@router.message("/start")
async def start_handler(event, context):
    user_key = str(event.user_id)

    if context["USERS"].get(user_key) is None:
        context["USER_STATE"][event.user_id] = "WAIT_DIRECTION"

        await send_message(
            event.chat_id,
            "group",
            text="Выберите направление"
        )
        return

    await send_message(
        event.chat_id,
        "/start"
    )


@router.state("WAIT_DIRECTION")
async def wait_direction_handler(event, context):
    if event.type != "callback":
        await send_message(
            event.chat_id,
            "group",
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
    await send_message(
        event.chat_id,
        "push_button",
        text="Расписание на сегодня"
    )


@router.callback("tomorrow")
async def tomorrow_callback_handler(event, context):
    await send_message(
        event.chat_id,
        "push_button",
        text="Расписание на завтра"
    )


@router.message()
async def unknown_message_handler(event, context):
    await send_message(
        event.chat_id,
        "push_button",
        text=f"Не понял сообщение: {event.text}"
    )


@router.callback()
async def unknown_callback_handler(event, context):
    await send_message(
        event.chat_id,
        "push_button",
        text=f"Неизвестная кнопка: {event.payload}"
    )