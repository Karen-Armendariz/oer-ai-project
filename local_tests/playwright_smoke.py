from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:8000"


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{BASE_URL}/health", wait_until="domcontentloaded")
        body_text = page.locator("body").inner_text().strip()
        if '"status":"ok"' not in body_text.replace(" ", ""):
            raise RuntimeError(f"Health check failed. Body was: {body_text}")

        page.goto(f"{BASE_URL}/docs", wait_until="domcontentloaded")
        if "OER RAG API" not in page.title():
            raise RuntimeError("Docs page title did not contain API name.")

        browser.close()


if __name__ == "__main__":
    main()
