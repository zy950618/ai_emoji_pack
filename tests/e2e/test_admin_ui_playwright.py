from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Page, expect, sync_playwright


ROOT = Path(__file__).resolve().parents[2]
SCREENSHOTS = Path(os.environ.get("AI_EMOJI_E2E_SCREENSHOTS", str(ROOT / ".ci-out" / "screenshots-loop3")))


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture()
def admin_server(tmp_path: Path):
    port = _free_port()
    state_path = tmp_path / "admin_state.json"
    env = os.environ.copy()
    env["AI_EMOJI_ADMIN_STATE_PATH"] = str(state_path)
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"{base_url}/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except Exception:
                time.sleep(0.2)
        else:
            raise RuntimeError("server did not start")
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()


def _shot(page: Page, name: str) -> None:
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SCREENSHOTS / name), full_page=True)


def _goto(page: Page, base_url: str, route: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.evaluate("(route) => go(route)", route)
    page.locator(f"#{route}.active").wait_for(timeout=10000)


def _refresh_route(page: Page, base_url: str, route: str) -> None:
    page.goto(f"{base_url}/?e2e={time.time_ns()}#{route}", wait_until="domcontentloaded")
    page.locator(f"#{route}.active").wait_for(timeout=10000)
    if route == "issues":
        page.evaluate("(route) => syncIssuesFromApi().then(() => { renderAll(); go(route); })", route)
    elif route == "failures":
        page.evaluate("(route) => syncFailuresFromApi().then(() => { renderAll(); go(route); })", route)
    elif route == "export":
        page.evaluate("(route) => syncExportsFromApi().then(() => { renderAll(); go(route); })", route)
    elif route == "generation":
        page.evaluate("(route) => syncPromptHistory().then(() => { renderAll(); go(route); })", route)
    else:
        page.evaluate("(route) => { renderAll(); go(route); }", route)
    page.locator(f"#{route}.active").wait_for(timeout=10000)


def test_admin_ui_loop3_persistent_e2e(admin_server: str):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        try:
            page.goto(admin_server, wait_until="networkidle")
            page.locator("#overview.active").wait_for(timeout=10000)
            _shot(page, "overview.png")

            issues_contract = page.context.request.get(f"{admin_server}/api/admin/issues").json()
            assert issues_contract["meta"]["dev_mock"] is False
            page.locator("#overview .card .primary").first.click()
            expect(page.locator("#issues.active")).to_be_visible()

            with page.expect_response("**/api/admin/issues?**"):
                page.locator("#i-priority").select_option("P0")
            expect(page.locator("#issues .item.p0")).to_have_count(1)
            _shot(page, "handling-center-filtered.png")

            with page.expect_response("**/api/admin/issues/ISS-1001/cancel") as cancel_response:
                page.locator("#issues .item.p0 .danger").first.click()
            assert cancel_response.value.json()["data"]["status"] == "cancelled"
            _refresh_route(page, admin_server, "issues")
            expect(page.locator("#issues .item.p0")).to_contain_text("status: cancelled")

            with page.expect_response("**/api/admin/issues/ISS-1001/requeue") as requeue_response:
                page.locator("#issues .item.p0 .row-actions button").nth(1).click()
            assert requeue_response.value.json()["data"]["status"] == "queued"
            _refresh_route(page, admin_server, "issues")
            expect(page.locator("#issues .item.p0")).to_contain_text("status: queued")
            _shot(page, "handling-center-after-requeue.png")

            _goto(page, admin_server, "failures")
            failure_2001 = page.locator("#failures .item").filter(has_text="FAIL-2001")
            expect(failure_2001).to_contain_text("失败原因")
            expect(failure_2001).to_contain_text("status:")
            with page.expect_response("**/api/admin/failures/FAIL-2001/cancel") as fail_cancel_response:
                failure_2001.locator(".danger").click()
            assert fail_cancel_response.value.json()["data"]["status"] == "cancelled"
            expect(failure_2001).to_contain_text("status: cancelled", timeout=10000)
            _refresh_route(page, admin_server, "failures")
            page.wait_for_function(
                "() => [...document.querySelectorAll('#failures .item')].some((el) => el.textContent.includes('FAIL-2001') && el.textContent.includes('status: cancelled'))",
                timeout=10000,
            )
            failure_2001 = page.locator("#failures .item").filter(has_text="FAIL-2001")
            expect(failure_2001).to_contain_text("status: cancelled")
            _shot(page, "failure-center-after-cancel.png")
            with page.expect_response("**/api/admin/failures/FAIL-2001/requeue") as fail_requeue_response:
                failure_2001.locator(".row-actions button").nth(1).click()
            assert fail_requeue_response.value.json()["data"]["status"] == "queued"
            expect(failure_2001).to_contain_text("status: queued", timeout=10000)
            _refresh_route(page, admin_server, "failures")
            page.wait_for_function(
                "() => [...document.querySelectorAll('#failures .item')].some((el) => el.textContent.includes('FAIL-2001') && el.textContent.includes('status: queued'))",
                timeout=10000,
            )
            failure_2001 = page.locator("#failures .item").filter(has_text="FAIL-2001")
            expect(failure_2001).to_contain_text("status: queued")

            _goto(page, admin_server, "generation")
            page.locator("#themeInput").fill("office cat")
            with page.expect_response("**/api/admin/prompt/generate") as prompt_response:
                page.locator("#generation .card").first.locator(".primary").first.click()
            prompt_payload = prompt_response.value.json()
            assert prompt_payload["data"]["source"] == "local"
            expect(page.locator("#promptBox")).to_contain_text("target platform")
            with page.expect_response("**/api/admin/prompt/optimize") as local_prompt_response:
                page.locator("#generation button").filter(has_text="优化设计词").click()
            assert local_prompt_response.value.json()["data"]["source"] == "local"
            with page.expect_response("**/api/admin/prompt/optimize-remote") as remote_prompt_response:
                page.locator("#generation button").filter(has_text="远程免费优化").click()
            assert remote_prompt_response.value.json()["data"]["source"] == "fallback"
            _refresh_route(page, admin_server, "generation")
            expect(page.locator("#promptHistory .item")).to_have_count(3)
            _shot(page, "generation-prompt-history.png")

            _goto(page, admin_server, "library")
            with page.expect_response("**/api/admin/sticker-packs?**"):
                page.locator("#f-platform").select_option("WeChat")
            expect(page.locator("#library tbody tr")).to_have_count(2)
            assert page.locator("#library tbody img").evaluate_all(
                "(imgs) => imgs.every((img) => img.src.includes('/admin-assets/') && img.naturalWidth > 0)"
            )
            _shot(page, "sticker-library-auto-filtered.png")

            _goto(page, admin_server, "qa")
            page.locator("#qa .danger").click()
            expect(page.locator("#toast.show")).to_contain_text("需要填写")

            _goto(page, admin_server, "export")
            page.locator("#export .actions button").nth(1).click()
            expect(page.locator("#export tbody tr")).to_have_count(4)
            page.locator("#export thead input[type=checkbox]").click(force=True)
            with page.expect_response("**/api/admin/exports/batch") as batch_response:
                page.locator("#export .title .primary").click()
            assert batch_response.value.json()["data"]["status"] == "exporting"
            expect(page.locator("#export tbody")).to_contain_text("exporting")
            _shot(page, "export-delivery-batch-export.png")

            with page.expect_response("**/api/admin/exports/EXP-005/run") as run_response:
                page.locator("#export tbody tr").first.locator(".primary").click()
            assert run_response.value.json()["data"]["status"] == "succeeded"
            _refresh_route(page, admin_server, "export")
            page.locator("#export .actions button").nth(1).click()
            expect(page.locator("#export tbody tr").first).to_contain_text("succeeded")

            _goto(page, admin_server, "settings")
            page.locator("#settings .card").nth(0).click()
            expect(page.locator("#platformRules.active")).to_be_visible()
            _shot(page, "system-platform-rules.png")
            _goto(page, admin_server, "settings")
            page.locator("#settings .card").nth(1).click()
            expect(page.locator("#generationSources.active")).to_be_visible()
            _shot(page, "system-generation-sources.png")

            page.locator("#themeSelect").select_option("forest")
            _refresh_route(page, admin_server, "generationSources")
            expect(page.locator("body")).to_have_attribute("data-theme", "forest")
            _shot(page, "theme-persisted-after-refresh.png")
        finally:
            browser.close()
