from playwright.async_api import async_playwright
import asyncio

# <div>API documentation
# 		<div class="url svelte-3n2nxs">https://diffusers-unofficial-sdxl-turbo-i2i-t2i.hf.space/--replicas/ou9nv/</div></div>

# This is the element that contains the API key we need to get

async def test():
    async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://diffusers-unofficial-sdxl-turbo-i2i-t2i.hf.space/?view=api")
            ai_api_key = await page.get_attribute('.url.svelte-3n2nxs.svelte-3n2nxs', 'textContent')
            print (ai_api_key)
            # Close the browser
            await browser.close()

async def read_sources():
     """
     Read the folders and files in the sources directory on the website
     """



if __name__ == "__main__":
    asyncio.run(test())