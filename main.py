import asyncio
import json
import os

import httpx
from dotenv import load_dotenv

from bot.handlers import router

load_dotenv()

TOKEN = os.getenv("MAX_TOKEN")
API_URL = "https://platform-api.max.ru"
USERS_PATH = "users/users.json"

USER_STATE = {}

if not TOKEN:
    raise ValueError("MAX_TOKEN не найден. Проверь файл .env")


def load_users():
    try:
        with open(USERS_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_users(users):
    with open(USERS_PATH, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=2)


USERS = load_users()


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


async def handle_update(update: dict):
    print("___________")
    print(json.dumps(update, indent=2, ensure_ascii=False))

    context = {
        "USERS": USERS,
        "USER_STATE": USER_STATE,
        "save_users": save_users
    }

    await router.dispatch(update, context)


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