import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:8000"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_UVICORN = PROJECT_ROOT / ".venv" / "bin" / "uvicorn"


def wait_for_api(timeout_seconds: int = 120) -> None:
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    raise RuntimeError("API did not become ready in time.")


def start_server() -> subprocess.Popen:
    if not VENV_UVICORN.exists():
        raise RuntimeError("uvicorn not found in .venv. Install dependencies first.")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    env["HF_HOME"] = str(PROJECT_ROOT / ".cache" / "huggingface")

    process = subprocess.Popen(
        [str(VENV_UVICORN), "backend.api:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process


def run_playwright(headless: bool) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        page.goto(f"{BASE_URL}/docs", wait_until="domcontentloaded")
        page.wait_for_selector(".opblock", timeout=60000)
        if "OER RAG API" not in page.title():
            raise RuntimeError("Docs page did not load expected title.")

        health_block = page.locator(".opblock").filter(has_text="/health").first
        health_block.locator("button.opblock-summary-control").click()
        health_block.get_by_role("button", name="Try it out").click()
        health_block.get_by_role("button", name="Execute").click()
        page.get_by_text('"status": "ok"', exact=False).wait_for(timeout=30000)

        search_block = page.locator(".opblock").filter(has_text="/oer/search").first
        search_block.locator("button.opblock-summary-control").click()
        search_block.get_by_role("button", name="Try it out").click()
        editor = search_block.locator("textarea")
        editor.fill('{"course_query":"BIOL 1101K"}')
        search_block.get_by_role("button", name="Execute").click()
        page.get_by_text('"results"', exact=False).wait_for(timeout=120000)

        browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run UI Playwright tests.")
    parser.add_argument("--headless", action="store_true", help="Run browser headless.")
    parser.add_argument("--no-server", action="store_true", help="Assume API is already running.")
    args = parser.parse_args()

    server = None
    try:
        if not args.no_server:
            server = start_server()
            wait_for_api()

        run_playwright(headless=args.headless)
        return 0
    finally:
        if server and server.poll() is None:
            server.send_signal(signal.SIGINT)
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    sys.exit(main())
