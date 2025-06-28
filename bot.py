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

            # Wait for either "ADD TO CART" or "BUY NOW" button text
            try:
                # Wait max 10s for add to cart or buy now button to appear
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
