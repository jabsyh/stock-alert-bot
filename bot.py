import discord
import asyncio
import os
import time
from playwright.async_api import async_playwright
import cv2
import numpy as np

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
URL = "https://www.popmart.com/gb/products/1159/SKULLPANDA-Aisling-Figure"
TEMPLATE_PATH = "buy_now_template.png"  # make sure this is the correct path


async def is_in_stock():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
                )
            )

            await page.goto(
                URL,
                timeout=60000,
                wait_until="networkidle"
            )

            screenshot_path = "/tmp/page_full.png"
            await page.screenshot(path=screenshot_path, full_page=True)

            img_rgb = cv2.imread(screenshot_path)
            template = cv2.imread(TEMPLATE_PATH)

            if img_rgb is None:
                print("❌ Failed to load the full page screenshot.")
                await browser.close()
                return False
            if template is None:
                print(f"❌ Failed to load template image at {TEMPLATE_PATH}")
                await browser.close()
                return False

            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

            w, h = template_gray.shape[::-1]

            res = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            threshold = 0.8
            loc = np.where(res >= threshold)

            found = False
            for pt in zip(*loc[::-1]):
                print(f"✅ Found 'Buy Now' button at location: {pt}")
                found = True
                break

            await browser.close()
            return found

    except Exception as e:
        print("Playwright error:", e)
        return False


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    last_notify = 0
    cooldown = 60  # seconds

    while True:
        try:
            in_stock = await is_in_stock()
            now = time.time()
            if in_stock:
                if now - last_notify > cooldown:
                    await channel.send(
                        f"🎉 The SKULLPANDA plush is **in stock**! 🛒\n{URL}"
                    )
                    last_notify = now
            await asyncio.sleep(10)
        except Exception as e:
            print("Bot error:", e)
            await asyncio.sleep(10)


client.run(TOKEN)
