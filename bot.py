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
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

            await page.goto(
                "https://www.popmart.com/gb/products/1159/SKULLPANDA-Aisling-Figure",
                timeout=60000,
                wait_until="networkidle"
            )

            await dismiss_popups(page)

            # Wait up to 15 seconds for a product element or add to cart button
            try:
                await page.wait_for_selector("button:has-text('Add to Cart'), h1", timeout=15000)
            except Exception as e:
                print("⏳ Selector wait timeout:", e)

            # Save screenshot for debugging (every time)
            await page.screenshot(path="page_debug.png", full_page=True)
            print("📸 Saved screenshot as page_debug.png")

            # Look for Add to Cart or Buy Now buttons
            add_to_cart_button = await page.query_selector("button:has-text('Add to Cart')")
            buy_now_button = await page.query_selector("button:has-text('Buy Now')")

            await browser.close()

            return add_to_cart_button is not None or buy_now_button is not None

    except Exception as e:
        print("❌ Playwright error:", e)
        try:
            await page.screenshot(path="error_debug.png", full_page=True)
            print("📸 Saved error screenshot as error_debug.png")
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
