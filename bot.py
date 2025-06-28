import discord
import asyncio
import os
from playwright.sync_api import sync_playwright

# Bot token and channel ID from environment
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Headless browser stock check
def is_in_stock():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.popmart.com/gb/products/1159/SKULLPANDA-Aisling-Figure", timeout=60000)

            # Wait for the page to load relevant content
            page.wait_for_selector("button", timeout=10000)

            # Check if "add to cart" or "buy now" is visible in the HTML
            content = page.content().lower()
            browser.close()

            return "add to cart" in content or "buy now" in content

    except Exception as e:
        print("Playwright error:", e)
        return False

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')
    channel = client.get_channel(CHANNEL_ID)

    already_notified = False

    while True:
        try:
            if is_in_stock():
                if not already_notified:
                    await channel.send("🎉 The SKULLPANDA plush is **in stock**! 🛒\nhttps://www.popmart.com/gb/products/1159/SKULLPANDA-Aisling-Figure")
                    already_notified = True
            else:
                already_notified = False  # Reset if out of stock again
        except Exception as e:
            print("Bot error:", e)

        await asyncio.sleep(10)  # Check every 10 seconds

client.run(TOKEN)
