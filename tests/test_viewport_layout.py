"""Viewport layout and overflow regression test suite.

Ensures that:
1. Body and card elements fit within screen height without vertical scrolling on short screens (e.g. iPhone SE 375x667).
2. The width-to-height aspect ratio of #question remains consistent across mobile and desktop.
3. The title does not overflow or exceed the width of the question box.
"""

from __future__ import annotations

import os
import shutil
import socket
import threading
from collections.abc import Generator
from typing import Any

import pytest
from werkzeug.serving import make_server

from slurdletwo import create_app

VIEWPORT_BENCHMARKS = [
    {
        "name": "iPhone SE",
        "width": 375,
        "height": 667,
        "min_ratio": 0.52,
        "max_ratio": 0.65,
    },
    {
        "name": "Samsung Galaxy S21",
        "width": 360,
        "height": 800,
        "min_ratio": 0.50,
        "max_ratio": 0.65,
    },
    {
        "name": "iPhone 15",
        "width": 393,
        "height": 852,
        "min_ratio": 0.55,
        "max_ratio": 0.68,
    },
    {
        "name": "Pixel 9",
        "width": 412,
        "height": 924,
        "min_ratio": 0.58,
        "max_ratio": 0.70,
    },
    {
        "name": "Desktop 1080p",
        "width": 1280,
        "height": 900,
        "min_ratio": 0.55,
        "max_ratio": 0.68,
    },
]


def _find_system_chrome() -> str | None:
    """Detect available Chrome binary on host."""
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return shutil.which("google-chrome") or shutil.which("chromium")


@pytest.fixture(scope="module")
def live_server_url() -> Generator[str]:
    """Spins up a lightweight ephemeral server for live browser tests."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    app = create_app()
    server = make_server("127.0.0.1", port, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}/"

    server.shutdown()


def test_template_responsive_invariants() -> None:
    """Verify that template source files contain the required responsive classes."""
    base_path = os.path.join(
        os.path.dirname(__file__), "..", "src", "slurdletwo", "templates", "base.jinja"
    )
    index_path = os.path.join(
        os.path.dirname(__file__), "..", "src", "slurdletwo", "templates", "index.jinja"
    )

    with open(base_path, encoding="utf-8") as f:
        base_src = f.read()

    with open(index_path, encoding="utf-8") as f:
        index_src = f.read()

    # 1. Base template ensures compact mobile body and card padding
    assert "p-3 sm:p-4" in base_src, (
        "Body must use p-3 sm:p-4 to prevent mobile vertical overflow"
    )
    assert 'id="question"' in base_src, "Card must have id='question' landmark"
    assert "p-4 sm:p-8" in base_src, "Card must use p-4 sm:p-8 for responsive padding"

    # 2. Index template ensures fluid clamp typography and proportional spacing
    assert "clamp(2.75rem" in index_src, (
        "Title must use fluid clamp typography to prevent mobile overhang"
    )
    assert "mb-5 sm:mb-6" in index_src, (
        "Title must retain generous bottom margin to prevent squishing"
    )
    assert "space-y-2.5 sm:space-y-4" in index_src, (
        "Target list must use proportional spacing"
    )
    assert "py-2.5 px-3.5 sm:p-4" in index_src, (
        "Target buttons must use responsive touch-safe padding"
    )


@pytest.mark.parametrize(
    "viewport",
    VIEWPORT_BENCHMARKS,
    ids=lambda v: f"{v['name']}-{v['width']}x{v['height']}",
)
def test_viewport_no_overflow_and_ratio(
    live_server_url: str, viewport: dict[str, Any]
) -> None:
    """Ensure that on every benchmark viewport, content fits vertically and card aspect ratio is preserved."""
    chrome_bin = _find_system_chrome()
    if not chrome_bin:
        pytest.skip("Chrome binary not available for headless browser layout test")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("Playwright not installed in current environment")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome_bin, headless=True)
        page = browser.new_page(
            viewport={"width": viewport["width"], "height": viewport["height"]}
        )
        page.goto(live_server_url)

        metrics = page.evaluate("""() => {
            const html = document.documentElement;
            const card = document.getElementById('question');
            const h1 = document.querySelector('h1');
            const qBox = card.querySelector('.text-center > div');

            return {
                scrollHeight: html.scrollHeight,
                innerHeight: window.innerHeight,
                cardWidth: card.offsetWidth,
                cardHeight: card.offsetHeight,
                titleWidth: h1.offsetWidth,
                questionWidth: qBox.offsetWidth
            };
        }""")

        browser.close()

        # Invariant 1: Document must never exceed viewport height (zero vertical scrollbars)
        assert metrics["scrollHeight"] <= metrics["innerHeight"], (
            f"Page overflowed vertically on {viewport['name']}! "
            f"scrollHeight={metrics['scrollHeight']}px > innerHeight={metrics['innerHeight']}px"
        )

        # Invariant 2: Card aspect ratio (W / H) must remain within harmonious bounds
        card_ratio = metrics["cardWidth"] / metrics["cardHeight"]
        assert viewport["min_ratio"] <= card_ratio <= viewport["max_ratio"], (
            f"Card aspect ratio {card_ratio:.3f} on {viewport['name']} out of bounds "
            f"[{viewport['min_ratio']}, {viewport['max_ratio']}]"
        )

        # Invariant 3: Title must never be wider than the question container
        assert metrics["titleWidth"] <= metrics["questionWidth"] + 5, (
            f"Title width {metrics['titleWidth']}px exceeds question box {metrics['questionWidth']}px "
            f"on {viewport['name']}"
        )
