import requests
import discord
import asyncio

# Replace with your bot token and channel ID
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))


# Product URL and headers
PRODUCT_URL = 'PRODUCT_URL = 'https://www.popmart.com/gb/products/1159/SKULLPANDA-Aisling-Figure'
HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

# Check function
def is_in_stock():
    response = requests.get(PRODUCT_URL, headers=HEADERS)
    if response.status_code != 200:
        print("Failed to fetch page")
        return False

    return "Add to Cart" in response.text or "add to cart" in response.text.lower()

# Discord bot setup
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
                    await channel.send("🎉 The SKULLPANDA plush is back in stock! Go go go!\n" + PRODUCT_URL)
                    already_notified = True
            else:
                already_notified = False  # reset if it goes out of stock again
        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(10)  # check every 10 seconds
        

client.run(TOKEN)
