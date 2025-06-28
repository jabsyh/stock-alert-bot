import discord
import asyncio
import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import cv2
import numpy as np
from aiohttp import web

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
PRODUCT_URL = "https://www.popmart.com/gb/products/1160/skullpanda-l-impressionnisme-series-plush-doll"
TEMPLATE_PATH = "buy_now_template.png"

# Threshold for template matching (higher = stricter)
MATCH_THRESHOLD = 0.95

async def is_in_stock(channel):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            )

            try:
                # Use 15 seconds timeout here to avoid 60s timeout hangs
                await page.goto(PRODUCT_URL, timeout=15000, wait_until="networkidle")
            except PlaywrightTimeoutError:
                print("⚠️ Page.goto timeout, retrying with domcontentloaded wait...")
                # Retry with a lighter wait condition
                await page.goto(PRODUCT_URL, timeout=15000, wait_until="domcontentloaded")

            # Take full page screenshot for template matching
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
            loc = np.where(res >= MATCH_THRESHOLD)

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

# --- Simple HTTP server to keep Railway awake ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def run_http_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", "8080")))
    await site.start()
    print("🌐 HTTP server started, keeping bot awake on port 8080")

# --- Discord bot setup ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    already_notified = False

    # Start the HTTP server in background
    asyncio.create_task(run_http_server())

    while True:
        try:
            in_stock = await is_in_stock(channel)
            if in_stock:
                if not already_notified:
                    await channel.send(
                        f"🎉 The plush is **in stock**! 🛒\n{PRODUCT_URL}"
                    )
                    already_notified = True
            else:
                already_notified = False

        except Exception as e:
            print("Bot error:", e)

        # Check every 10 seconds (can lower but beware of rate limits)
        await asyncio.sleep(10)

client.run(TOKEN)
