import asyncio
import random
from playwright.async_api import async_playwright

# Configuration
TARGET_URL = "https://caredent.net"  # Replace with your URL
NUM_VISITS = 5                         # Total page visits to generate
CONCURRENT_USERS = 2                    # Simultaneous sessions

async def simulate_visitor(user_id, p):
    # Launch browser with a common desktop User-Agent
    browser = await p.chromium.launch(headless=False)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 720}
    )
    page = await context.new_page()

    try:
        print(f"[User {user_id}] Navigating to {TARGET_URL}...")
        await page.goto(TARGET_URL, wait_until="networkidle")

        # Simulate natural scrolling
        scroll_height = random.randint(300, 800)
        await page.mouse.wheel(0, scroll_height)
        print(f"[User {user_id}] Scrolled down page.")

        # Dwell time (stay on page 3 to 7 seconds)
        dwell = random.uniform(3, 7)
        await asyncio.sleep(dwell)

        # Optional: Click a random internal link if available
        links = await page.query_selector_all("a[href^='/'], a[href^='" + TARGET_URL + "']")
        if links:
            random_link = random.choice(links)
            await random_link.click()
            await page.wait_for_load_state("networkidle")
            print(f"[User {user_id}] Clicked internal link.")
            await asyncio.sleep(2)

    except Exception as e:
        print(f"[User {user_id}] Error: {e}")
    finally:
        await context.close()
        await browser.close()

async def main():
    async with async_playwright() as p:
        tasks = []
        for i in range(1, NUM_VISITS + 1):
            tasks.append(simulate_visitor(i, p))
            if len(tasks) >= CONCURRENT_USERS:
                await asyncio.gather(*tasks)
                tasks = []
        if tasks:
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
