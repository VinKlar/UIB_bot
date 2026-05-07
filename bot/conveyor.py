import copy
import os
import json
import httpx
from dotenv import load_dotenv

with open("bot/scen.json", "r", encoding="utf-8") as file:
    SCEN = json.load(file)
with open("bot/buttons_groups.json", "r", encoding="utf-8") as file:
    GROUPS = json.load(file)

load_dotenv()

TOKEN = os.getenv("MAX_TOKEN")
API_URL = "https://platform-api.max.ru"

async def send_message(chat_id: int, scen, **data):
    if data.get('ch_g') == True:
        print('|||||_____________________________________________________')
    url = f"{API_URL}/messages"

    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }

    params = {
        "chat_id": chat_id
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            params=params,
            json=await scen_worker(scen, **data)
        )

async def create_keyboard(buttons):
    return {
        "attachments": [
            {
                "type": "inline_keyboard",
                "payload": {
                    "buttons": buttons
                }
            }
        ]
    }
    
async def scen_worker(scen, **data):
    
    if data.get('ch_g') == True:
        print('|||||')
        tmp_scen = copy.deepcopy(GROUPS[scen])
    else:
        tmp_scen = copy.deepcopy(SCEN[scen])
    tmp_scen['text'] = tmp_scen['text'].format(text=data.get('text'))

    if tmp_scen.get('buttons'):
        data_respons = {
            "text": tmp_scen['text'],
            **await create_keyboard(tmp_scen['buttons'])
        }
    else:
        data_respons = {
            "text": tmp_scen['text']
        }
    return data_respons
