"""Static Owner admin UI loader."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


ADMIN_UI_TEMPLATE_NAME = "owner-admin-static-loop5-3"
ADMIN_UI_STATIC_SPLIT_STATUS = "preview-to-production-transplant"
ADMIN_UI_API_PREFIX = "/api/admin"
ADMIN_UI_ASSET_PREFIX = "/admin-assets"
ADMIN_UI_STATIC_PREFIX = "/admin-static"
ADMIN_STATIC_DIR = Path(__file__).resolve().parent / "admin_static"
ADMIN_HTML_PATH = ADMIN_STATIC_DIR / "admin.html"


@lru_cache(maxsize=1)
def load_admin_html() -> str:
    """Return the preview-derived static admin shell."""
    return ADMIN_HTML_PATH.read_text(encoding="utf-8")


V7_ADMIN_HTML = load_admin_html()
