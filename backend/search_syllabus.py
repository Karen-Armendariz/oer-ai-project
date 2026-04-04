import re
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

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
        "MATH": "School of Science and Technology",
        "CHEM": "School of Science and Technology",
        "PHYS": "School of Science and Technology",
        "BCHM": "School of Science and Technology",
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

            if re.search(rf"\b{re.escape(query)}\b", title_upper):
                exact.append(card)

    if exact:
        return exact[0]

    if partial:
        return partial[0]

    return None


def wait_for_library_ready(page):
    page.goto(
        "https://ggc.simplesyllabus.com/en-US/syllabus-library",
        wait_until="domcontentloaded"
    )

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)

    if "/login" in page.url.lower():
        raise RuntimeError(
            "Simple Syllabus redirected to login. Your saved Playwright session may have expired. "
            "Log in again manually once using your working scraper, then retry."
        )


def wait_for_school_cards(page, school_name: str):
    page.get_by_text(school_name, exact=False).click()

    page.locator("app-library-doc-card").first.wait_for(
        state="visible",
        timeout=15000
    )
    page.wait_for_timeout(2000)


def scrape_syllabus(course_query: str):
    school_name = infer_school(course_query)

    if not school_name:
        raise RuntimeError(
            f"Could not infer school from course query: {course_query}"
        )

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROJECT_ROOT / "playwright_user_data"),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = context.new_page()

        try:
            print("Opening Simple Syllabus library...")
            wait_for_library_ready(page)

            print(f"Clicking {school_name}...")
            wait_for_school_cards(page, school_name)

            page.screenshot(
                path=str(OUTPUT_DIR / "visible_cards.png"),
                full_page=True
            )

            print("Collecting visible syllabus cards...")
            visible_cards = collect_visible_cards(page)

            if not visible_cards:
                raise RuntimeError("No visible syllabus cards were found on the page.")

            links_file = OUTPUT_DIR / "visible_cards.txt"
            with links_file.open("w", encoding="utf-8") as f:
                for card in visible_cards:
                    f.write(f"{card['title']}\n{card['href']}\n\n")

            best_match = find_best_match(visible_cards, course_query)

            if not best_match:
                raise RuntimeError(f"No visible match found for course: {course_query}")

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
                raise RuntimeError("Did not land on a syllabus doc page.")

            text = page.locator("body").inner_text().strip()

            filename = safe_filename(best_match["title"]) + ".txt"
            output_file = OUTPUT_DIR / filename
            output_file.write_text(text, encoding="utf-8")

            return {
                "course_query": course_query,
                "matched_title": best_match["title"],
                "doc_url": page.url,
                "file": str(output_file),
                "characters": len(text)
            }

        except PlaywrightTimeoutError as e:
            page.screenshot(
                path=str(OUTPUT_DIR / "timeout_error_state.png"),
                full_page=True
            )
            raise RuntimeError(f"Timed out while scraping syllabus: {e}") from e

        except Exception as e:
            page.screenshot(
                path=str(OUTPUT_DIR / "error_state.png"),
                full_page=True
            )
            raise

        finally:
            context.close()


if __name__ == "__main__":
    course = input("Enter course (ex: BIOL 1101K): ").strip()

    if not course:
        print("No course entered. Exiting.")
    else:
        try:
            result = scrape_syllabus(course)
            print("\nDone.")
            print("Matched title:", result["matched_title"])
            print("Saved to:", result["file"])
            print("Character count:", result["characters"])
        except Exception as e:
            print("\nERROR:")
            print(e)