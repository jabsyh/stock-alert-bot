import discord
import asyncio
import os
from playwright.async_api import async_playwright

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

async def dismiss_popups(page):
    # General popups
    popup_selectors = [
        "button:has-text('Accept')",
        "button:has-text('I agree')",
        "button:has-text('Close')",
        "div.cookie-banner button.close",
        "div#qc-cmp2-ui button[aria-label='Close']",
    ]

    for selector in popup_selectors:
        try:
            btn = await page.query_selector(selector)
            if btn:
                print(f"🧹 Clicking popup: {selector}")
                await btn.click()
                await asyncio.sleep(1)
        except Exception:
            pass

    # Region popup handling with retry
    for attempt in range(3):
        try:
            print(f"🌍 Checking for region popup attempt {attempt + 1}...")

            kingdom_btn = await page.query_selector("button:has-text('Kingdom')")
            if kingdom_btn and await kingdom_btn.is_visible():
                print("✅ Clicking 'Kingdom' button")
                await kingdom_btn.click()
                await asyncio.sleep(2)
                return

            # Check frames as well
            for frame in page.frames:
                btn = await frame.query_selector("button:has-text('Kingdom')")
                if btn and await btn.is_visible():
                    print(f"✅ Clicking 'Kingdom' button in frame {frame.url}")
                    await btn.click()
                    await asyncio.sleep(2)
                    return

            # If no button found, try pressing Escape to close overlay
            print("⏳ No 'Kingdom' button found, pressing Escape to close overlays")
            await page.keyboard.press("Escape")
            await asyncio.sleep(2)

        except Exception as e:
            print("❌ Region popup handling attempt failed:", e)

async def is_in_stock(channel):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            )

            await page.goto(
                "https://www.popmart.com/gb/products/1159/SKULLPANDA-Aisling-Figure",
                timeout=60000,
                wait_until="networkidle"
            )

            await dismiss_popups(page)

            try:
                await page.wait_for_selector(
                    "button:has-text('Add to Cart'), button:has-text('Buy Now')",
                    timeout=15000,
                )
            except Exception as e:
                print("Selector wait timeout:", e)

            screenshot_path = "/tmp/page_debug.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            await channel.send("📸 Here's the current page screenshot for debugging:", file=discord.File(screenshot_path))

            add_to_cart_button = await page.query_selector("button:has-text('Add to Cart')")
            buy_now_button = await page.query_selector("button:has-text('Buy Now')")

            await browser.close()

            return add_to_cart_button is not None or buy_now_button is not None

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
                        "🎉 The SKULLPANDA plush is **in stock**! 🛒\nhttps://www.popmart.com/gb/products/1159/SKULLPANDA-Aisling-Figure"
                    )
                    already_notified = True
            else:
                already_notified = False
        except Exception as e:
            print("Bot error:", e)

        await asyncio.sleep(10)

client.run(TOKEN)
