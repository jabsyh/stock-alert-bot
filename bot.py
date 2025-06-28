import discord
import asyncio
import os
from playwright.async_api import async_playwright

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

async def dismiss_popups(page):
    # General popups on main page
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

    # Region popup might be inside iframe(s)
    try:
        print("🌍 Checking for region popup inside frames...")

        # Iterate all frames to find the UK button
        for frame in page.frames:
            buttons = await frame.query_selector_all("button:has-text('United Kingdom')")
            if buttons:
                for uk_button in buttons:
                    visible = await uk_button.is_visible()
                    print(f"🔎 Found 'United Kingdom' button in frame {frame.url}, visible? {visible}")
                    if visible:
                        print("✅ Clicking 'United Kingdom' button...")
                        await uk_button.click()
                        await asyncio.sleep(2)
                        return  # exit after clicking

        print("❌ No 'United Kingdom' button found in any frame.")

    except Exception as e:
        print("❌ Region popup handling failed:", e)



async def is_in_stock(channel):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            )

            await page.goto(
                "https://www.popmart.com/gb/products/1159/SKULLPANDA-Aisling-Figure",
                timeout=30000,
                wait_until="domcontentloaded"
            )

            await dismiss_popups(page)

            try:
                await page.wait_for_selector("button:has-text('Add to Cart'), button:has-text('Buy Now')", timeout=15000)
            except Exception as e:
                print("Selector wait timeout:", e)

            # Save and upload screenshot of the full page for debug
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
