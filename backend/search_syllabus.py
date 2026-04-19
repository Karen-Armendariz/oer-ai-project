import re
from pathlib import Path
from playwright.sync_api import sync_playwright

# Robust path handling: find the project root regardless of where script is run
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "syllabi" / "search_results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:180]


def infer_school(course_query: str) -> str | None:
    query = course_query.upper().strip()

    school_map = {
        "ARTS": "School of Liberal Arts",
        "ENGL": "School of Liberal Arts",
        "HIST": "School of Liberal Arts",
        "ITEC": "School of Science and Technology",
        "BIOL": "School of Science and Technology",
    }

    for prefix, school in school_map.items():
        if query.startswith(prefix):
            return school

    return None


def collect_visible_cards(page):
    cards = page.locator("app-library-doc-card")
    count = cards.count()

    results = []
    for i in range(count):
        card = cards.nth(i)

        title_locator = card.locator("p.doc-term-title").first
        if title_locator.count() == 0:
            continue

        title = title_locator.inner_text().strip()

        links = card.locator("a")
        link_count = links.count()

        doc_href = None
        for j in range(link_count):
            href = links.nth(j).get_attribute("href")
            if href and "/doc/" in href:
                doc_href = href
                break

        results.append({
            "title": title,
            "href": doc_href,
            "index": i
        })

    return results


def find_best_match(cards, course_query: str):
    query = course_query.upper().strip()

    exact = []
    partial = []

    for card in cards:
        title_upper = card["title"].upper()
        if query in title_upper:
            partial.append(card)

            # Prefer titles that start with term + query
            if re.search(rf"\b{re.escape(query)}\b", title_upper):
                exact.append(card)

    if exact:
        return exact[0], exact, partial

    if partial:
        return partial[0], exact, partial

    return None, exact, partial


def main():
    course_query = input("Enter course code (example: ARTS 1100): ").strip()

    if not course_query:
        print("No course entered. Exiting.")
        return

    school_name = infer_school(course_query)

    print("Course query:", course_query)
    if school_name:
        print("Inferred school:", school_name)
    else:
        print("Could not infer school automatically. You may need to click the right school manually.")

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

            if school_name:
                print(f"Clicking {school_name}...")
                page.get_by_text(school_name, exact=False).click()
                page.wait_for_timeout(5000)
                input(f"When the {school_name} syllabus cards are visible, press Enter here...")
            else:
                input("Navigate to the correct school manually, then press Enter here...")

            page.screenshot(
                path=str(OUTPUT_DIR / "visible_cards.png"),
                full_page=True
            )

            print("Collecting visible syllabus cards...")
            visible_cards = collect_visible_cards(page)
            print(f"Visible card count: {len(visible_cards)}")

            links_file = OUTPUT_DIR / "visible_cards.txt"
            with links_file.open("w", encoding="utf-8") as f:
                for card in visible_cards:
                    f.write(f"{card['title']}\n{card['href']}\n\n")

            best_match, exact_matches, partial_matches = find_best_match(visible_cards, course_query)

            print(f"Partial matches found: {len(partial_matches)}")
            print(f"Exact-style matches found: {len(exact_matches)}")

            if not best_match:
                print("No visible match found for that course.")
                print(f"Saved visible card list to: {links_file.resolve()}")
                input("Inspect the browser, then press Enter to close...")
                return

            print("Best match selected:")
            print(best_match["title"])
            print(best_match["href"])

            if not best_match["href"]:
                raise RuntimeError("Found a matching card, but no /doc/ link was available.")

            print("Navigating directly to syllabus doc...")
            page.goto(best_match["href"], wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            print("Final URL:", page.url)

            if "/doc/" not in page.url:
                page.screenshot(
                    path=str(OUTPUT_DIR / "failed_doc_navigation.png"),
                    full_page=True
                )
                print("Did not land on a doc page.")
                input("Inspect the browser, then press Enter to close...")
                return

            text = page.locator("body").inner_text().strip()

            filename = safe_filename(best_match["title"]) + ".txt"
            output_file = OUTPUT_DIR / filename
            output_file.write_text(text, encoding="utf-8")

            print("Saved to:", output_file.resolve())
            print("Character count:", len(text))
            input("Press Enter to close...")

        except Exception as e:
            print("\nERROR:")
            print(e)
            page.screenshot(
                path=str(OUTPUT_DIR / "error_state.png"),
                full_page=True
            )
            print(f"Saved screenshot to: {(OUTPUT_DIR / 'error_state.png').resolve()}")
            input("Inspect the browser, then press Enter to close...")

        finally:
            context.close()


if __name__ == "__main__":
    main()