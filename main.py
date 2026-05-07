import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("MAX_TOKEN")
API_URL = "https://platform-api.max.ru"


if not TOKEN:
    raise ValueError("MAX_TOKEN не найден. Проверь файл .env")


async def send_message(chat_id: int, text: str):
    url = f"{API_URL}/messages"

    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }

    params = {
        "chat_id": chat_id
    }

    json_data = {
        "text": text
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            params=params,
            json=json_data
        )

    print("SEND STATUS:", response.status_code)
    print("SEND RESPONSE:", response.text)


async def send_keyboard(chat_id: int):
    url = f"{API_URL}/messages"

    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }

    params = {
        "chat_id": chat_id
    }

    json_data = {
        "text": "Выбери действие:",
        "attachments": [
            {
                "type": "inline_keyboard",
                "payload": {
                    "buttons": [
                        [
                            {
                                "type": "message",
                                "text": "Сегодня",
                                "payload": "Сегодня"
                            },
                            {
                                "type": "message",
                                "text": "Завтра",
                                "payload": "Завтра"
                            }
                        ],
                        [
                            {
                                "type": "message",
                                "text": "Неделя",
                                "payload": "Неделя"
                            }
                        ]
                    ]
                }
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            params=params,
            json=json_data
        )

    print("KEYBOARD STATUS:", response.status_code)
    print("KEYBOARD RESPONSE:", response.text)


async def get_updates(marker=None):
    url = f"{API_URL}/updates"

    headers = {
        "Authorization": TOKEN
    }

    params = {
        "limit": 100,
        "timeout": 30
    }

    if marker:
        params["marker"] = marker

    async with httpx.AsyncClient(timeout=40) as client:
        response = await client.get(
            url,
            headers=headers,
            params=params
        )

    print("GET UPDATES STATUS:", response.status_code)

    return response.json()


async def handle_update(update: dict):
    update_type = update.get("update_type")

    if update_type != "message_created":
        return

    message = update.get("message", {})
    chat_id = message["recipient"]["chat_id"]

    text = (
        message
        .get("body", {})
        .get("text", "")
        .strip()
    )

    print("TEXT RAW:", repr(text))
    print("UPDATE:", update)

    
    await send_keyboard(chat_id)

    if text == "Сегодня":
        await send_message(chat_id, "Расписание на сегодня")

    elif text == "Завтра":
        await send_message(chat_id, "Расписание на завтра")

    elif text == "Неделя":
        await send_message(chat_id, "Расписание на неделю")

    else:
        await send_message(chat_id, f"Ты написал: {text}")


async def main():
    marker = None

    print("Бот запущен")

    while True:
        try:
            data = await get_updates(marker)

            updates = data.get("updates", [])

            for update in updates:
                marker = update.get("marker")
                await handle_update(update)

        except Exception as e:
            print("Ошибка:", e)
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())