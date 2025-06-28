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

    # Region popup handling with detailed debug
    try:
        print("🌍 Checking for region popup...")

        # List all visible buttons for debugging exact text
        buttons = await page.query_selector_all("button")
        print(f"🔎 Found {len(buttons)} buttons:")
        for i, b in enumerate(buttons):
            try:
                text = await b.inner_text()
                if text.strip():
                    print(f"🔘 [{i}] Button text: '{text.strip()}'")
            except Exception:
                pass

        # Log frames info
        frames = page.frames
        print(f"🧩 Total frames: {len(frames)}")
        for f in frames:
            print(f"🧩 Frame name: '{f.name}', URL: {f.url}")

        # Screenshot before clicking region popup
        await page.screenshot(path="region_popup_before.png")

        # Try waiting for the exact "United Kingdom" button text (case & spaces sensitive)
        await page.wait_for_selector("button:has-text('United Kingdom')", timeout=15000)
        uk_button = await page.query_selector("button:has-text('United Kingdom')")
        if uk_button and await uk_button.is_visible():
            print("✅ Clicking 'United Kingdom' button...")
            await uk_button.click()
            await asyncio.sleep(2)
        else:
            print("❌ 'United Kingdom' button not found or not visible.")

        # Screenshot after clicking
        await page.screenshot(path="region_popup_after.png")

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
