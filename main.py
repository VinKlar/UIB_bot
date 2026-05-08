import asyncio
import os
import json
import httpx
from dotenv import load_dotenv

from bot.conveyor import send_message

load_dotenv()

TOKEN = os.getenv("MAX_TOKEN")
API_URL = "https://platform-api.max.ru"

STATE = False

with open("users/users.json", "r", encoding="utf-8") as file:
    USERS = json.load(file)

if not TOKEN:
    raise ValueError("MAX_TOKEN не найден. Проверь файл .env")


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

    return response.json()

USER_STATE = {}

async def handle_update(update: dict):
    print("___________")
    # print(json.dumps(update, indent=2, ensure_ascii=False))

    message = update.get("message", {})
    update_type = update.get("update_type")
    user_id = message['sender']['user_id']
    chat_id = message["recipient"]["chat_id"]
    text = (
        message
        .get("body", {})
        .get("text", "")
        .strip()
    )
    print(USER_STATE, USERS.get(str(user_id)) is None)

    if message.get("body", {}).get("text", "") == '/start':
        await send_message(chat_id, '/start')
        return
    if USERS.get(str(user_id)) is None:

        if USER_STATE.get(user_id) == 'NAPR':

            USER_STATE[user_id] = 'GROUP'

            await send_message(
                chat_id,
                update['callback']['payload'],
                text='Группа',
                ch_g=True
            )

        elif USER_STATE.get(user_id) == 'GROUP':
            USERS[str(user_id)] = update['callback']['payload']
            print(USERS)
            USER_STATE[user_id] = 'DONE'
            with open("users/users.json", "w", encoding="utf-8") as file:
                json.dump(
                    USERS,
                    file,
                    ensure_ascii=False,
                    indent=2
                )

            await send_message(chat_id, 
                               'push_button', 
                               text = "Выберете пункт:")

        else:
            USER_STATE[user_id] = 'NAPR'
            await send_message(
                chat_id,
                'group',
                text='Нет данных'
            )
        return

    
    await send_message(chat_id, text if update_type == 'message_created' else 'push_button', text = update.get("callback", {}).get('payload',''))


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