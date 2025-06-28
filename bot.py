import discord
import asyncio
import os
from playwright.async_api import async_playwright

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

async def dismiss_popups(page):
    # Try to close cookie/privacy banners or modals if present
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
                await btn.click()
                await asyncio.sleep(1)
        except Exception:
            pass

async def is_in_stock():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(
                "https://www.popmart.com/gb/products/1159/SKULLPANDA-Aisling-Figure",
                timeout=60000,
            )

            # Dismiss popups/cookie banners
            await dismiss_popups(page)

            # Check for "ADD TO CART" or "BUY NOW" buttons
            try:
                await page.wait_for_selector("text=ADD TO CART", timeout=10000)
                in_stock = True
            except Exception:
                try:
                    await page.wait_for_selector("text=BUY NOW", timeout=5000)
                    in_stock = True
                except Exception:
                    in_stock = False

            await browser.close()
            return in_stock

    except Exception as e:
        print("Playwright error:", e)
        try:
            await page.screenshot(path="error_debug.png")
        except Exception:
            pass
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
            if await is_in_stock():
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
