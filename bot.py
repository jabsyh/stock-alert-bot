async def is_in_stock():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(
                "https://www.popmart.com/gb/products/1159/SKULLPANDA-Aisling-Figure",
                timeout=60000,
            )

            await dismiss_popups(page)

            # Wait for the product title or add to cart button to appear (adjust selector as needed)
            try:
                # Wait up to 15 seconds for "Add to Cart" button or product title
                await page.wait_for_selector("button:has-text('Add to Cart'), h1.product-title", timeout=15000)
            except Exception:
                # Timeout — element not found, probably out of stock or page didn't load fully
                await browser.close()
                return False

            # Now check if the add to cart button is present
            add_to_cart_button = await page.query_selector("button:has-text('Add to Cart')")
            buy_now_button = await page.query_selector("button:has-text('Buy Now')")

            await browser.close()

            return add_to_cart_button is not None or buy_now_button is not None

    except Exception as e:
        print("Playwright error:", e)
        try:
            await page.screenshot(path="error_debug.png")
        except Exception:
            pass
        return False
