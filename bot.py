import discord
import asyncio
import os
from playwright.async_api import async_playwright
import cv2
import numpy as np

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
URL = "https://www.popmart.com/gb/products/1159/SKULLPANDA-Aisling-Figure"
template_path = "buy_now_template.png"  # Make sure this image is in your script's directory

async def is_in_stock(channel):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
                )
            )

            # Retry page.goto up to 3 times
            for attempt in range(3):
                try:
                    await page.goto(URL, timeout=60000, wait_until="domcontentloaded")
                    break
                except Exception as e:
                    print(f"Navigation attempt {attempt + 1} failed: {e}")
                    if attempt == 2:
                        await browser.close()
                        return False
                    await asyncio.sleep(3)

            # Take full page screenshot
            screenshot_path = "/tmp/page_full.png"
            await page.screenshot(path=screenshot_path, full_page=True)

            # Load images for template matching
            img_rgb = cv2.imread(screenshot_path)
            template = cv2.imread(template_path)

            if img_rgb is None:
                print("❌ Failed to load the full page screenshot.")
                await browser.close()
                return False
            if template is None:
                print(f"❌ Failed to load template image at {template_path}")
                await browser.close()
                return False

            # Convert to grayscale for better matching
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

            w, h = template_gray.shape[::-1]

            # Perform template matching
            res = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            threshold = 0.8  # Adjust threshold as needed
            loc = np.where(res >= threshold)

            found = False
            for pt in zip(*loc[::-1]):  # Switch x,y coordinates
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
    already_notified = False

    while True:
        try:
            if await is_in_stock(channel):
                if not already_notified:
                    await channel.send(
                        "🎉 The SKULLPANDA plush is **in stock**! 🛒\n"
                        f"{URL}"
                    )
                    already_notified = True
            else:
                already_notified = False
        except Exception as e:
            print("Bot error:", e)

        await asyncio.sleep(10)  # check every 10 seconds (adjust as desired)


client.run(TOKEN)
