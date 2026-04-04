import re
from pathlib import Path
from playwright.sync_api import sync_playwright

# Robust path handling: find the project root regardless of where script is run
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
syllabi_folder = PROJECT_ROOT / "data" / "syllabi"
syllabi_folder.mkdir(parents=True, exist_ok=True)

# Exact syllabus card title we want
target_title = "BIOL 1101K Section 01 (50337)"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(PROJECT_ROOT / "playwright_user_data"),
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )

    page = context.new_page()

    try:
        print("Opening Simple Syllabus library...")
        page.goto(
            "https://ggc.simplesyllabus.com/en-US/syllabus-library",
            wait_until="domcontentloaded"
        )

        print("Log in if needed.")
        input("When you are fully logged in and can see the library page, press Enter here...")

        page.wait_for_timeout(3000)

        print("Clicking School of Science and Technology...")
        page.get_by_text("School of Science and Technology", exact=False).click()
        page.wait_for_timeout(5000)

        input("When the Science and Technology syllabus cards are visible, press Enter here...")

        # Save screenshot of visible cards
        page.screenshot(
            path="data/syllabi/science_cards_visible.png",
            full_page=True
        )

        print("Locating exact BIOL card...")

        # Find the exact visible title text
        title_locator = page.locator("app-library-doc-card p.doc-term-title").filter(
            has_text=re.compile(re.escape(target_title), re.IGNORECASE)
        ).first

        if title_locator.count() == 0:
            raise RuntimeError(f"Could not find visible BIOL card title for {target_title!r}")

        resolved_title = title_locator.inner_text().strip()
        print("Found visible card title:", resolved_title)

        # Find the parent card
        card = title_locator.locator("xpath=ancestor::app-library-doc-card[1]").first

        if card.count() == 0:
            raise RuntimeError("Found the BIOL title, but could not find the parent app-library-doc-card.")

        # Save card HTML for debugging
        card_html = card.inner_html()
        Path("data/syllabi/target_card.html").write_text(card_html, encoding="utf-8")

        print("Looking for clickable links inside the BIOL card...")
        links = card.locator("a")

        link_count = links.count()
        print("Link count inside card:", link_count)

        doc_href = None

        for i in range(link_count):
            href = links.nth(i).get_attribute("href")
            print(f"Link {i} href:", href)

            if href and "/doc/" in href:
                doc_href = href
                break

        if not doc_href:
            raise RuntimeError("Found the BIOL card, but no /doc/ link was found inside it.")

        print("Navigating directly to doc link...")
        page.goto(doc_href, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        print("Final URL:", page.url)

        if "/doc/" not in page.url:
            page.screenshot(
                path="data/syllabi/failed_exact_card_click.png",
                full_page=True
            )
            print("Still not on doc page. Screenshot saved to data/syllabi/failed_exact_card_click.png")
            input("Inspect browser, then press Enter to close...")
        else:
            text = page.locator("body").inner_text().strip()

            output_file = syllabi_folder / "sample_syllabus.txt"
            output_file.write_text(text, encoding="utf-8")

            print("Saved to:", output_file.resolve())
            print("Character count:", len(text))
            input("Press Enter to close...")

    except Exception as e:
        print("\nERROR:")
        print(e)
        page.screenshot(
            path="data/syllabi/error_state.png",
            full_page=True
        )
        print("Saved screenshot to data/syllabi/error_state.png")
        input("Inspect browser, then press Enter to close...")

    finally:
        context.close()