import requests
import discord
import asyncio
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

API_URL = "https://prod-intl-api.popmart.com/shop/v1/shop/productDetails?spuId=1159&s=2da56cae115f2a55a850fe3e06a9c5b0&t=1751122344"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def is_in_stock():
    try:
        response = requests.get(API_URL, headers=HEADERS)
        if response.status_code != 200:
            print("Failed to fetch API:", response.status_code)
            return False

        data = response.json()
        if data.get("code") != "OK":
            print("API error:", data.get("message"))
            return False

        product = data.get("data", {})
        is_available = product.get("isAvailable", False)
        skus = product.get("skus", [])

        if not is_available or not skus:
            return False

        stock = skus[0].get("stock", {}).get("onlineStock", 0)
        return stock > 0
    except Exception as e:
        print("Exception in is_in_stock:", e)
        return False

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    channel = client.get_channel(CHANNEL_ID)

    already_notified = False

    while True:
        try:
            if is_in_stock():
                if not already_notified:
                    await channel.send("🎉 The SKULLPANDA plush is back in stock! Go get it now!\n" + API_URL)
                    already_notified = True
            else:
                already_notified = False  # reset if out of stock again
        except Exception as e:
            print("Error in loop:", e)

        await asyncio.sleep(10)  # check every 10 seconds

client.run(TOKEN)
