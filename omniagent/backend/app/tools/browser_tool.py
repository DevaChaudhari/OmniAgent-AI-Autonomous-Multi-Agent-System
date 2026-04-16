from playwright.sync_api import sync_playwright

def browse_website(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        content = page.content()

        browser.close()

    return content[:1000]
