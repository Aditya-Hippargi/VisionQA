"""
VisionQA Browser Agent (Stealth Version - Fixed)
Uses manual stealth script injection to avoid import errors.
"""

import asyncio
import os
import shutil
import random
from datetime import datetime
from pathlib import Path

# Try to import Playwright
try:
    from playwright.async_api import async_playwright, Page
except ImportError:
    print("❌ Critical Import Error. Run: pip install playwright")
    exit(1)

# --- CONFIGURATION ---
VIEWPORT_SIZE = {"width": 1920, "height": 1080}
SCROLL_DURATION_SECONDS = 20
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

class BrowserRecorder:
    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir = self.output_dir / "temp_video"
        self.temp_dir.mkdir(exist_ok=True)

    async def _apply_stealth(self, page: Page):
        """
        Manually injects stealth scripts to hide automation flags.
        This fixes the 'ImportError' by not relying on the external library function.
        """
        # 1. Mask the webdriver property
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # 2. Mock languages and plugins to look real
        await page.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        # 3. Mask Chrome-specific automation variables
        await page.add_init_script("""
            window.chrome = { runtime: {} };
            const originalQuery = window.navigator.permissions.query;
            return window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
        """)

    async def _human_mouse_move(self, page: Page):
        """Moves the mouse in a random, curvy human-like path."""
        try:
            for _ in range(3):
                x = random.randint(100, 1000)
                y = random.randint(100, 800)
                await page.mouse.move(x, y, steps=10)
                await page.wait_for_timeout(random.randint(100, 300))
        except Exception:
            pass

    async def _handle_popups(self, page: Page):
        """Handles Cookies AND Amazon-style 'Continue' barriers."""
        print("   🛡️  Checking for popups/barriers...")
        
        # 1. Generic Cookie Buttons
        cookie_texts = ["Accept", "Accept All", "Allow", "I Agree", "Got it", "Consent"]
        for text in cookie_texts:
            try:
                btn = page.get_by_role("button", name=text, exact=False)
                if await btn.count() > 0 and await btn.is_visible():
                    print(f"      ↳ Clicking cookie button: '{text}'")
                    await btn.first.click()
                    return
            except: continue

        # 2. Amazon-specific "Continue"
        try:
            amazon_btn = page.get_by_text("Continue shopping", exact=False)
            if await amazon_btn.count() > 0 and await amazon_btn.is_visible():
                 print("      ↳ ⚠️ Detected Amazon Block. Attempting to click through...")
                 await amazon_btn.first.click()
                 await page.wait_for_timeout(2000)
        except: pass

    async def _smooth_scroll(self, page: Page):
        print("   📜 Starting smooth scroll...")
        total_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = VIEWPORT_SIZE["height"]
        steps = 40
        step_height = (total_height - viewport_height) / steps
        delay_ms = (SCROLL_DURATION_SECONDS * 1000) / steps

        for i in range(steps):
            next_y = step_height * (i + 1)
            await page.evaluate(f"window.scrollTo(0, {next_y})")
            
            if i % 5 == 0: 
                await self._human_mouse_move(page)
                
            await page.wait_for_timeout(delay_ms)
        
        await page.wait_for_timeout(2000)

    async def record_session(self, url: str) -> str:
        print(f"\n🎥 Starting Browser Session for: {url}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = url.replace("https://", "").replace("http://", "").replace("www.", "").split('/')[0]
        final_filename = f"{safe_name}_{timestamp}.mp4"
        final_path = self.output_dir / final_filename

        async with async_playwright() as p:
            # Launch with "Stealth" flags
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled", 
                    "--no-sandbox",
                    "--disable-infobars"
                ]
            )
            
            context = await browser.new_context(
                record_video_dir=self.temp_dir,
                record_video_size=VIEWPORT_SIZE,
                viewport=VIEWPORT_SIZE,
                user_agent=USER_AGENT,
                locale="en-US",
                timezone_id="America/New_York"
            )

            try:
                page = await context.new_page()
                
                # ACTIVATE MANUAL STEALTH
                await self._apply_stealth(page)
                
                print("   🌐 Navigating (Stealth Mode ON)...")
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                await page.wait_for_timeout(3000)
                await self._handle_popups(page)
                await self._human_mouse_move(page)
                await self._smooth_scroll(page)

                print("   💾 Saving video...")
                await context.close()
                await browser.close()
                
                video_files = list(self.temp_dir.glob("*.webm")) + list(self.temp_dir.glob("*.mp4"))
                if not video_files: return None
                
                latest_video = max(video_files, key=os.path.getctime)
                shutil.move(str(latest_video), str(final_path))
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                
                print(f"   ✅ Recording Complete: {final_path}")
                return str(final_path)

            except Exception as e:
                print(f"   ❌ Browser Error: {e}")
                await context.close()
                await browser.close()
                return None

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com"
    r = BrowserRecorder()
    asyncio.run(r.record_session(url))